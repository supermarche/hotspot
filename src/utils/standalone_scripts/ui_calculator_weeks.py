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
bbox = [14.9165, 51.0711, 15.0759, 51.2166]  # Replace with your coordinates

# Define the evalscript to calculate NDVI, NDBI, and NDBI - NDVI
evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["B04", "B08", "B11"],
        output: {
            bands: 1,
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
            image_array = src.read(1)  # Read the first (and only) band

            # Get image dimensions
            height, width = image_array.shape

            if image_array.max() > 0:

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
                        count=1,  # Single band
                        dtype=image_array.dtype,
                        crs=crs,
                        transform=transform
                ) as dst:
                    dst.write(image_array, 1)  # Write to the first (and only) band

                print(f"GeoTIFF saved successfully as {filename}.")
    except Exception as e:
        print(f"An error occurred while saving GeoTIFF: {e}")

# Loop through each week in 2023
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)
current_date = start_date

while current_date < end_date:
    week_end_date = current_date + timedelta(days=6)
    if week_end_date > end_date:
        week_end_date = end_date

    # Format the start and end date for the current week
    formatted_start_date = current_date.strftime("%Y-%m-%dT00:00:00Z")
    formatted_end_date = week_end_date.strftime("%Y-%m-%dT23:59:59Z")

    # Prepare the payload for processing for the given week
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
                        "from": formatted_start_date,
                        "to": formatted_end_date
                    },
                    "maxCloudCoverage": 30.0
                },
                "type": "sentinel-2-l2a"
            }]
        },
        "output": {
            "width": 1500,  # 1500
            "height": 1500,
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

    # Submit the processing request for the current week
    response = requests.post(url, headers=headers, json=payload)

    # Check and download the response data if the request is successful
    if response.status_code == 200:
        print(f"Processing request for week starting {formatted_start_date[:10]} successful. Saving data...")
        # Save the response data to a GeoTIFF file
        filename = f"../../data/ui/ui_{formatted_start_date[:10]}_to_{formatted_end_date[:10]}.tiff"
        save_as_geotiff(response.content, filename, bbox)
    else:
        print(f"Error for week starting {formatted_start_date[:10]}: {response.status_code}")
        print("Response content:", response.json())

    # Move to the next week
    current_date += timedelta(days=7)

print("Processing completed for all weeks.")
