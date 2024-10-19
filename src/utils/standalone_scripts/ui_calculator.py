"""
NDBI and Urban Heat Islands:
Zha, Y., Gao, J., & Ni, S. (2003). Use of normalized difference built-up index in automatically mapping urban areas from TM imagery. International Journal of Remote Sensing, 24(3), 583-594.
Combining Indices for Urban Analysis:
Xu, H. (2008). A new index for delineating built-up land features in satellite imagery. International Journal of Remote Sensing, 29(14), 4269-4276.

"""

import requests
from pyproj import Transformer
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from datetime import datetime, timedelta
import rasterio
from io import BytesIO
from rasterio.transform import from_bounds
from rasterio.crs import CRS
import numpy as np
import secrets  # Replace this with your method of securely storing API credentials

# Replace with your client ID and client secret
client_id = secrets.client_name  # e.g., 'your_client_id'
client_secret = secrets.client_secret  # e.g., 'your_client_secret'

# OAuth session setup
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Obtain the access token
token = oauth.fetch_token(
    token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
    client_secret=client_secret,
    include_client_id=True
)

# Define the processing URL
url = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Define the bounding box for your area of interest
bbox = [14.9300, 51.1300, 14.9800, 51.1600]  # Replace with your coordinates

# Define the evalscript to calculate NDVI, NDBI, and NDBI - NDVI
evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["B04", "B08", "B11"],
        output: {
            bands: 3,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(sample) {
    var red = sample.B04;
    var nir = sample.B08;
    var swir = sample.B11;

    var ndvi = (nir - red) / (nir + red);
    var ndbi = (swir - nir) / (swir + nir);
    var ui = ndbi - ndvi;

    return [ui];
}
"""

# Function to save image data as GeoTIFF
def save_as_geotiff(data, filename, bbox, crs_epsg=4326, target_epsg=25833):
    """Save the downloaded image data as a GeoTIFF with specified EPSG code."""
    try:
        if data is None:
            print("No data to save.")
            return
        # Convert data to a BytesIO object
        image_data = BytesIO(data)

        # Open the image using rasterio
        with rasterio.open(image_data) as src:
            image_array = src.read()  # Read all bands

            # Get image dimensions
            bands, height, width = image_array.shape

            # Transform bbox from EPSG:4326 (WGS84) to target EPSG
            transformer = Transformer.from_crs(f"EPSG:{crs_epsg}", f"EPSG:{target_epsg}", always_xy=True)
            xmin, ymin = transformer.transform(bbox[0], bbox[1])
            xmax, ymax = transformer.transform(bbox[2], bbox[3])

            # Create a geospatial transform
            transform = from_bounds(xmin, ymin, xmax, ymax, width, height)

            # Define the coordinate reference system
            crs = CRS.from_epsg(target_epsg)

            # Write the data to a GeoTIFF file
            with rasterio.open(
                    filename,
                    'w',
                    driver='GTiff',
                    height=height,
                    width=width,
                    count=bands,
                    dtype=image_array.dtype,
                    crs=crs,
                    transform=transform
            ) as dst:
                dst.write(image_array)

            print(f"GeoTIFF saved successfully as {filename}.")
    except Exception as e:
        print(f"An error occurred while saving GeoTIFF: {e}")

# Loop through each month in 2023
for month in range(1, 13):
    # Create start and end date for the given month
    start_date = datetime(2023, month, 1).strftime("%Y-%m-%dT00:00:00Z")
    if month == 12:  # Handle December's end date
        end_date = "2023-12-31T23:59:59Z"
    else:  # Handle end of other months by rolling over to the next month minus a day
        end_date = (datetime(2023, month + 1, 1) - timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z")

    # Prepare the payload for processing for the given month
    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                }
            },
            "data": [{
                "dataFilter": {
                    "timeRange": {
                        "from": start_date,
                        "to": end_date
                    },
                    "maxCloudCoverage": 30.0
                },
                "type": "sentinel-2-l2a"
            }]
        },
        "output": {
            "responses": [{
                "identifier": "default",
                "format": {
                    "type": "image/tiff"
                }
            }]
        },
        "evalscript": evalscript
    }

    # Define headers for the request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token["access_token"]}'
    }

    # Submit the processing request for the current month
    response = requests.post(url, headers=headers, json=payload)

    # Check and download the response data if the request is successful
    if response.status_code == 200:
        print(f"Processing request for {start_date[:7]} successful. Saving data...")
        # Save the response data to a GeoTIFF file
        filename = f"../../data/ui/ui_{start_date[:7]}.tiff"
        save_as_geotiff(response.content, filename, bbox)
    else:
        print(f"Error for {start_date[:7]}: {response.status_code}")
        print("Response content:", response.json())

print("Processing completed for all months.")
