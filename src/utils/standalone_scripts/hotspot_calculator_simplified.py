import requests
from pyproj import Transformer
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from datetime import datetime, timedelta
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from rasterio.warp import reproject, Resampling
import numpy as np
import secrets  # Replace this with your method of securely storing API credentials
from io import BytesIO

# Replace 'secrets' with your actual client ID and client secret
client_id = secrets.client_name
client_secret = secrets.client_secret

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

# Define the bounding box for the area of interest (replace with your city's coordinates)
bbox = [14.9300, 51.1300, 14.9800, 51.1600]  # Example: Görlitz, DE

# Headers for the requests
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token["access_token"]}'
}

# Evalscript for Sentinel-2 NDVI calculation
sentinel_ndvi_evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["B04", "B08"],
        output: {
            bands: 1,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(sample) {
    var ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    return [ndvi];
}
"""

# Evalscript for Landsat 8 Thermal Band 10
landsat_thermal_evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["B10"],
        output: {
            bands: 1,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(sample) {
    return [sample.B10];
}
"""

# Function to save image data as GeoTIFF
def save_as_geotiff(data, filename, bbox, crs_epsg=4326, target_epsg=3857):
    try:
        if data is None:
            print("No data to save.")
            return
        image_data = BytesIO(data)
        with rasterio.open(image_data) as src:
            image_array = src.read(1)
            height, width = image_array.shape
            transformer = Transformer.from_crs(f"EPSG:{crs_epsg}", f"EPSG:{target_epsg}", always_xy=True)
            xmin, ymin = transformer.transform(bbox[0], bbox[1])
            xmax, ymax = transformer.transform(bbox[2], bbox[3])
            transform = from_bounds(xmin, ymin, xmax, ymax, width, height)
            crs = CRS.from_epsg(target_epsg)
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

# Function to perform thermal sharpening
def thermal_sharpening(ndvi_path, thermal_path, output_path):
    with rasterio.open(ndvi_path) as ndvi_src, rasterio.open(thermal_path) as thermal_src:
        # Read NDVI data
        ndvi = ndvi_src.read(1).astype('float32')
        ndvi[np.isinf(ndvi)] = np.nan  # Handle infinite values

        # Read thermal data and resample to NDVI resolution
        thermal = thermal_src.read(1).astype('float32')
        thermal_resampled = np.empty(ndvi.shape, dtype='float32')

        reproject(
            source=thermal,
            destination=thermal_resampled,
            src_transform=thermal_src.transform,
            src_crs=thermal_src.crs,
            dst_transform=ndvi_src.transform,
            dst_crs=ndvi_src.crs,
            resampling=Resampling.bilinear
        )

        # Mask invalid data
        ndvi_masked = np.ma.masked_invalid(ndvi)
        thermal_masked = np.ma.masked_invalid(thermal_resampled)

        # Calculate mean NDVI and thermal
        ndvi_mean = ndvi_masked.mean()
        thermal_mean = thermal_masked.mean()

        # Calculate regression coefficient (beta)
        beta_numerator = np.ma.sum((ndvi_masked - ndvi_mean) * (thermal_masked - thermal_mean))
        beta_denominator = np.ma.sum((ndvi_masked - ndvi_mean) ** 2)
        beta = beta_numerator / beta_denominator if beta_denominator != 0 else 0

        # Calculate sharpened thermal image
        thermal_sharpened = thermal_masked + beta * (ndvi_masked - ndvi_mean)
        thermal_sharpened = thermal_sharpened.filled(np.nan)  # Fill masked values with NaN

        # Save the sharpened thermal image
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=ndvi_src.height,
            width=ndvi_src.width,
            count=1,
            dtype='float32',
            crs=ndvi_src.crs,
            transform=ndvi_src.transform
        ) as dst:
            dst.write(thermal_sharpened.astype('float32'), 1)
        print(f"Sharpened thermal image saved as {output_path}.")

# Loop through each month in 2023
for month in range(1, 13):
    # Define start and end dates for the month
    start_date = datetime(2023, month, 1).strftime("%Y-%m-%dT00:00:00Z")
    if month == 12:
        end_date = "2023-12-31T23:59:59Z"
    else:
        end_date = (datetime(2023, month + 1, 1) - timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z")

    # Prepare payload for Sentinel-2 NDVI
    sentinel_payload = {
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
        "evalscript": sentinel_ndvi_evalscript
    }

    # Request Sentinel-2 NDVI data
    response_s2 = requests.post(url, headers=headers, json=sentinel_payload)
    if response_s2.status_code == 200:
        ndvi_data = response_s2.content
        ndvi_filename = f"ndvi_{start_date[:7]}.tiff"
        save_as_geotiff(ndvi_data, ndvi_filename, bbox)
    else:
        print(f"Error fetching Sentinel-2 data for {start_date[:7]}: {response_s2.status_code}")
        print("Response content:", response_s2.json())
        continue  # Skip to next month if there's an error

    # Prepare payload for Landsat 8 Thermal Band
    landsat_payload = {
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
                "type": "landsat-8-l1c"
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
        "evalscript": landsat_thermal_evalscript
    }

    # Request Landsat 8 Thermal data
    response_ls = requests.post(url, headers=headers, json=landsat_payload)
    if response_ls.status_code == 200:
        thermal_data = response_ls.content
        thermal_filename = f"thermal_{start_date[:7]}.tiff"
        save_as_geotiff(thermal_data, thermal_filename, bbox)
    else:
        print(f"Error fetching Landsat data for {start_date[:7]}: {response_ls.status_code}")
        print("Response content:", response_ls.json())
        continue  # Skip to next month if there's an error

    # Perform thermal sharpening
    sharpened_output_path = f"../../data/lst/sharpened_lst_{start_date[:7]}.tiff"
    thermal_sharpening(ndvi_filename, thermal_filename, sharpened_output_path)

print("Processing completed for all months.")
