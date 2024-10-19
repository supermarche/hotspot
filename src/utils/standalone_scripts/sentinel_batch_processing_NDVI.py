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
import secrets

# Define the OAuth session using previously authenticated client
client_id = secrets.client_name
client_secret = secrets.client_secret

# OAuth session setup (reusing from previous setup)
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Obtain the access token
token = oauth.fetch_token(
    token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
    client_secret=client_secret,
    include_client_id=True
)

# Define the batch processing URL
url = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Define the bounding box for Görlitz, DE (used in previous examples)
bbox = [14.9300, 51.1300, 14.9800, 51.1600]

# Define the evalscript for NDVI calculation and output as float
evalscript = """
//VERSION=3
function setup() {
    return {
        input: [{
            bands: ["B04", "B08"]
        }],
        output: [{
            id: "default",
            bands: 1,
            sampleType: "FLOAT32"  // Output in Float32 for precision
        }],
        mosaicking: Mosaicking.ORBIT
    }
}

function calcNDVI(sample) {
    var denom = sample.B04 + sample.B08;
    return ((denom != 0) ? (sample.B08 - sample.B04) / denom : 0.0);
}

function evaluatePixel(samples) {
    var max = 0;
    for (var i = 0; i < samples.length; i++) {
        var ndvi = calcNDVI(samples[i]);
        max = ndvi > max ? ndvi : max;
    }
    ndvi = max;
    return [ndvi];  // Return single-band NDVI as float
}
"""

# Reuse the save_as_geotiff function from before
def save_as_geotiff(data, filename, bbox, crs_epsg=4326, target_epsg=25833):
    """Save the downloaded image data as a GeoTIFF with EPSG:25833."""
    try:
        if data is None:
            print("No data to save.")
            return
        # Convert data to a BytesIO object
        image_data = BytesIO(data)

        # Open the image using rasterio
        with rasterio.open(image_data) as src:
            image_array = src.read(1)  # Read the first (and only) band

            # Get image dimensions
            height, width = image_array.shape

            # Transform bbox from EPSG:4326 (WGS84) to EPSG:25833
            transformer = Transformer.from_crs(f"EPSG:{crs_epsg}", f"EPSG:{target_epsg}", always_xy=True)
            xmin, ymin = transformer.transform(bbox[0], bbox[1])
            xmax, ymax = transformer.transform(bbox[2], bbox[3])

            # Create a geospatial transform
            transform = from_bounds(xmin, ymin, xmax, ymax, width, height)

            # Define the coordinate reference system
            crs = CRS.from_epsg(target_epsg)  # EPSG:25833

            # Write the data to a GeoTIFF file
            with rasterio.open(
                    filename,
                    'w',
                    driver='GTiff',
                    height=height,
                    width=width,
                    count=1,
                    dtype=image_array.dtype,
                    crs=crs,
                    transform=transform
            ) as dst:
                dst.write(image_array, 1)

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

    # Prepare the payload for batch processing for the given month
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
                    "maxCloudCoverage": 70.0
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
        filename = f"../../data/nvdi/ndvi_gorlitz_{start_date[:7]}.tiff"
        save_as_geotiff(response.content, filename, bbox)
    else:
        print(f"Error for {start_date[:7]}: {response.status_code}")
        print("Response content:", response.json())
