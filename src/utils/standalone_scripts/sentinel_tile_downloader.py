import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from io import BytesIO
from PIL import Image
import numpy as np
import json
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from pyproj import Transformer
import boto3
import os
import secrets


class SentinelDownloader:
    def __init__(self, client_id, client_secret, bbox, time_range, bands, satellite_type="sentinel-2-l1c"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.bbox = bbox  # Expected in EPSG:4326 (latitude and longitude)
        self.time_range = time_range
        self.bands = bands
        self.satellite_type = satellite_type
        self.token = None
        self.oauth = None
        self.evalscript = None
        self.payload = None

        self.setup_session()
        self.create_evalscript()
        self.create_payload()

        self.origin_epsg = 4326
        self.target_epsg = 25833

        self.s3 = boto3.resource(
            's3',
            endpoint_url='https://eodata.dataspace.copernicus.eu',
            aws_access_key_id=secrets.aws_access_key,
            aws_secret_access_key=secrets.aws_secret_key,
            region_name='default'
        )

    def update_time(self, time_range):
        self.time_range = time_range
        self.create_payload()

    def setup_session(self):
        client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=client)
        self.token = self.oauth.fetch_token(
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            client_secret=self.client_secret,
            include_client_id=True
        )

        def sentinelhub_compliance_hook(response):
            response.raise_for_status()
            return response

        self.oauth.register_compliance_hook("access_token_response", sentinelhub_compliance_hook)

    def create_evalscript(self):
        bands_input = ', '.join([f'"{band}"' for band in self.bands])
        bands_output = len(self.bands)
        bands_formula = ', '.join([f'2.5 * sample.{band}' for band in self.bands])

        self.evalscript = f"""
        //VERSION=3

        function setup() {{
          return {{
            input: [{bands_input}],
            output: {{
              bands: {bands_output}
            }}
          }};
        }}

        function evaluatePixel(sample) {{
          return [{bands_formula}];
        }}
        """

    def create_payload(self):
        self.payload = {
            "input": {
                "bounds": {
                    "bbox": self.bbox
                },
                "data": [{
                    "type": self.satellite_type,
                    "dataFilter": {
                        "timeRange": self.time_range
                    }
                }]
            },
            "evalscript": self.evalscript,
            "tilingGrid": {
                "id": 0,
                "resolution": 10.0
            },
        }

    def search_data(self):
        """Search for available Sentinel data."""
        data = {
            "bbox": self.bbox,
            "datetime": f"{self.time_range['from']}/{self.time_range['to']}",
            "collections": [self.satellite_type],
            "filter": "eo:cloud_cover < 30"
        }
        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search',
            headers={"Authorization": f"Bearer {self.token}"},
            json=data,
        )

        if response.status_code == 200:
            content = json.loads(response.content)
            features = content.get("features", [])
            if features:
                return features
            else:
                raise ValueError("No available data found for the given search criteria.")
        else:
            raise Exception(f"Error occurred: {response.status_code}, {response.content}")

    def download_from_s3(self, bucket_name, s3_path, target_dir=""):
        """Download files from an S3 bucket using the provided S3 path."""
        bucket = self.s3.Bucket(bucket_name)
        files = bucket.objects.filter(Prefix=s3_path)
        if not list(files):
            raise FileNotFoundError(f"Could not find any files for {s3_path}")

        for file in files:
            file_path = os.path.join(target_dir, file.key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if not os.path.isdir(file_path):
                bucket.download_file(file.key, file_path)
                print(f"Downloaded {file.key} to {file_path}")

    def download_for_features(self, bucket_name, features, target_dir="../data/"):
        """
        Download Sentinel data based on features containing S3 paths.
        """
        for feature in features:
            s3_href = feature.get("assets", {}).get("data", {}).get("href")
            if s3_href:
                # Extract the S3 path from the href
                s3_path = s3_href.replace("s3://EODATA/", "")
                print(f"Attempting to download from S3 path: {s3_path}")
                try:
                    self.download_from_s3(bucket_name, s3_path, target_dir)
                except FileNotFoundError:
                    print(f"No files found for path: {s3_path}")
                except Exception as e:
                    print(f"Error occurred while downloading: {str(e)}")

    def save_as_geotiff(self, data, filename):
        try:
            image_data = BytesIO(data)
            image = Image.open(image_data)
            image_array = np.array(image)
            height, width = image_array.shape[:2]

            transformer = Transformer.from_crs(f"EPSG:{self.origin_epsg}", f"EPSG:{self.target_epsg}", always_xy=True)
            xmin, ymin = transformer.transform(self.bbox[0], self.bbox[1])
            xmax, ymax = transformer.transform(self.bbox[2], self.bbox[3])

            transform = from_bounds(xmin, ymin, xmax, ymax, width, height)
            crs = CRS.from_epsg(self.target_epsg)

            if image_array.ndim == 2:
                count = 1
            elif image_array.ndim == 3:
                count = image_array.shape[2]

            for i in range(count):
                band = self.bands[i]
                with rasterio.open(
                        f"../data/{band}_{filename}",
                        'w',
                        driver='GTiff',
                        height=height,
                        width=width,
                        count=1,
                        dtype=image_array.dtype,
                        crs=crs,
                        transform=transform
                ) as dst:
                    dst.write(image_array[:, :, i], 1)

                print(f"GeoTIFF saved successfully as {filename}.")
        except Exception as e:
            print(f"An error occurred while saving GeoTIFF: {e}")


if __name__ == "__main__":
    client_id = secrets.client_name
    client_secret = secrets.client_secret
    goerlitz_bbox = [14.9300, 51.1300, 14.9800, 51.1600]
    time_range = {
        "from": "2023-01-01T00:00:00Z",
        "to": "2023-12-30T23:59:59Z"
    }
    bands = ["B04", "B08", "B11", "B03"]

    downloader = SentinelDownloader(
        client_id=client_id,
        client_secret=client_secret,
        bbox=goerlitz_bbox,
        time_range=time_range,
        bands=bands,
        satellite_type="sentinel-2-l1c"
    )

    features = downloader.search_data()
    print("Available Data Features:", features)

    # Download files from S3 based on the provided S3 links in the features
    downloader.download_for_features(
        bucket_name="eodata",
        features=features,
        target_dir="../../data/"
    )
