from datetime import datetime, timedelta
import os
import os
import json
import pyproj
from datetime import datetime
import sentinelhub
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import requests
import sys
import rasterio
from rasterio.transform import from_bounds
#%reload_ext autoreload
#%autoreload 2
from rasterio.crs import CRS as rasterio_CRS
##################### SentinelHub package ##################
from sentinelhub import (
    SHConfig,
    DataCollection,
    SentinelHubCatalog,
    SentinelHubRequest,
    BBox,
    bbox_to_dimensions,
    CRS,
    MimeType,
    Geometry,
    MosaickingOrder,
    filter_times,
    generate_evalscript
)
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from s2cloudless import S2PixelCloudDetector, download_bands_and_valid_data_mask

##  Block 2
## Section 2 Set up Configurations Parameters
#################### Configure SentinelHub account #########################
############ The limitation of downloading can be viewed from Copernicus dashboard ##############
############ https://shapps.dataspace.copernicus.eu/dashboard/#/ ######
############ It only allows monthly 30,000 downloads ##################
############ Registering with multiple emails/accounts is allowed ######
########### Need to try ESA Network of Resources to get more quota #####

client_id = ''
client_secret = ''  ## These two lines sets up the user account


###################### Configuration ###################################
config = SHConfig()
config.sh_client_id = client_id
config.sh_client_secret = client_secret
config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
#######################################################################################

client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Get token for the session
token = oauth.fetch_token(token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
                          client_secret=client_secret, include_client_id=True)

# All requests using this session will have an access token automatically added
resp = oauth.get("https://sh.dataspace.copernicus.eu/configuration/v1/wms/instances")
print(resp.content)
def sentinelhub_compliance_hook(response):
    response.raise_for_status()
    return response

oauth.register_compliance_hook("access_token_response", sentinelhub_compliance_hook)

############################# Searching parameters ############################
catalog = SentinelHubCatalog(config=config)

raster_crs = rasterio_CRS.from_epsg(32633)  # Assuming WGS84 as CRS
# Update AOI and time period as per requirements (already provided earlier)
aoi_coords_wgs84 = [498263, 5666527, 500593, 5668959]  # SWNE (Hong Kong)
resolution = 10
aoi_bbox = BBox(bbox=aoi_coords_wgs84, crs=CRS(32633))
aoi_size = bbox_to_dimensions(aoi_bbox, resolution=resolution)
transform = from_bounds(*aoi_bbox, aoi_size[0], aoi_size[1])
start_date = "2024-03-01"
end_date = "2024-03-30"
time_interval = (start_date, end_date)

# Search for Sentinel-2 and Sentinel-3 data in the given time period
sentinel2_search = catalog.search(DataCollection.SENTINEL2_L2A, bbox=aoi_bbox, time=time_interval, filter='eo:cloud_cover < 50', )
sentinel3_search = catalog.search(DataCollection.SENTINEL3_SLSTR, bbox=aoi_bbox, time=time_interval, filter='eo:cloud_cover < 50', )

dates_sentinel2 = set([item['properties']['datetime'][:10] for item in sentinel2_search])
dates_sentinel3 = set([item['properties']['datetime'][:10] for item in sentinel3_search])
common_dates = list(sorted(dates_sentinel2.intersection(dates_sentinel3)))

# Define the Sentinel-2 and Sentinel-3 band scripts
evalscript_sentinel2 = """
    //VERSION=3
    function setup() {
        return {
            input: [{ bands: ["B03", "B04", "B08", "B11"], units: ["REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "REFLECTANCE"]}],
            output: { bands: 4, sampleType: "FLOAT32" }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B03, sample.B04, sample.B08, sample.B11];
    }
"""

evalscript_sentinel3 = """
    //VERSION=3
    function setup() {
        return {
            input: [{ bands: ["S8", "S9"], units: ["BRIGHTNESS_TEMPERATURE", "BRIGHTNESS_TEMPERATURE"] }],
            output: { bands: 2, sampleType: "FLOAT32" }
        };
    }

    function evaluatePixel(sample) {
        return [sample.S8, sample.S9];
    }
"""


def save_tiff_and_metadata(bands_data, transform, crs_epsg, output_path, bands_metadata):
    """
    Saves the GeoTIFF data returned by SentinelHub and writes associated metadata to a separate JSON file.

    :param response_data: Binary content (GeoTIFF) from SentinelHub request
    :param output_path: Path to save the GeoTIFF file
    :param bands_metadata: Dictionary containing metadata for the bands
    """
    # Save the GeoTIFF file
    raster_crs = rasterio_CRS.from_epsg(crs_epsg)
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=bands_data.shape[0],
        width=bands_data.shape[1],
        count=bands_data.shape[2],
        dtype=bands_data.dtype,
        crs=raster_crs,
        transform=transform
    ) as dst:
        for i in range(bands_data.shape[2]):
            dst.write(bands_data[:, :, i], i + 1)  # Write each band

    # Save the metadata in a JSON file
    metadata_path = output_path.replace('.tiff', '_metadata.json')
    with open(metadata_path, 'w') as meta_file:
        json.dump(bands_metadata, meta_file)

    print(f"Data and metadata saved to {output_path} and {metadata_path}")


# The rest of the code remains similar for downloading Sentinel-2 and Sentinel-3 data

def download_and_save_sentinel_data(data_collection, evalscript, dates, bbox, aoi_size, config, folder_name,
                                    bands_metadata):
    """
    Downloads SentinelHub data and saves it as GeoTIFF along with metadata.

    :param data_collection: SentinelHub data collection (e.g., Sentinel-2, Sentinel-3)
    :param evalscript: Evalscript to specify the bands to download
    :param dates: List of dates for which to download the data
    :param bbox: Bounding box for the area of interest
    :param aoi_size: Dimensions of the area of interest in pixels
    :param config: SentinelHub configuration object
    :param folder_name: Folder name prefix for saving the data
    :param bands_metadata: Metadata describing the bands
    """
    for date in dates:

        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=data_collection,
                    time_interval=(date+'T00:00:00Z', date+'T23:59:59.9Z')
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            size=aoi_size,
            config=config,
        )

        # Fetch the data from the request (GeoTIFF format)
        img_data = request.get_data()[0]  # GeoTIFF data in binary format
        print(request.get_filename_list())

        # Define the file path with timestamp
        timestamp = datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m%d") # T%H:%M:%S.%fZ _%H%M%S
        #time.now().strftime("%Y%m%d_%H%M%S")
        output_folder = f"data/{folder_name}"
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, f"{folder_name}_{timestamp}.tiff")

        # Save the TIFF file and metadata
        save_tiff_and_metadata(img_data, transform, raster_crs, output_path, bands_metadata)


# Example usage for Sentinel-2 and Sentinel-3:
# Sentinel-2

bands_metadata_sentinel2 = {"bands": ["B03", "B04", "B08", "B11"]}
download_and_save_sentinel_data(
    DataCollection.SENTINEL2_L1C.define_from("s2l1c", service_url=config.sh_base_url), evalscript_sentinel2, common_dates, aoi_bbox, aoi_size, config, "sentinel2",
    bands_metadata_sentinel2
)

# Sentinel-3
bands_metadata_sentinel3 = {"bands": ["S8", "S9"], "Unit":  "Kelvin"}
download_and_save_sentinel_data(
    DataCollection.SENTINEL3_SLSTR.define_from("s3slstr", service_url=config.sh_base_url), evalscript_sentinel3, common_dates, aoi_bbox, aoi_size, config, "sentinel3",
    bands_metadata_sentinel3
)
