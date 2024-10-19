# sentinel_processors.py

import json
from io import BytesIO
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from gis_helpers import transform_bbox

class SentinelDownloader:
    def __init__(self, authenticator, bbox, time_range, bands, satellite_type):
        self.oauth, self.token = authenticator.get_oauth()
        self.bbox = bbox  # Expected in EPSG:4326
        self.time_range = time_range
        self.bands = bands
        self.satellite_type = satellite_type
        self.evalscript = None
        self.payload = None
        self.origin_epsg = 4326
        self.target_epsg = 25833
        self.create_evalscript()
        self.create_payload()

    def update_time(self, time_range):
        self.time_range = time_range
        self.create_payload()

    def create_evalscript(self):
        """Create the evalscript based on the specified bands."""
        bands_input = ', '.join([f'"{band}"' for band in self.bands])
        bands_formula = ', '.join([f'sample.{band}' for band in self.bands])
        bands_output = len(self.bands)

        self.evalscript = f"""
        //VERSION=3

        function setup() {{
          return {{
            input: [{bands_input}],
            output: {{
              bands: {bands_output},
              sampleType: "FLOAT32"
            }}
          }};
        }}

        function evaluatePixel(sample) {{
          return [{bands_formula}];
        }}
        """

    def create_payload(self):
        """Create the payload for the API request."""
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
            "output": {
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            }
        }

    def search_data(self):
        """Search the catalog for available imagery within the specified parameters."""
        search_payload = {
            "bbox": self.bbox,
            "datetime": f"{self.time_range['from']}/{self.time_range['to']}",
            "collections": [self.satellite_type],
            "filter": "eo:cloud_cover < 30",  # Include any desired filters
            # "distinct": "date",  # Remove the 'distinct' parameter
        }

        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search',
            json=search_payload,
        )

        response.raise_for_status()  # Ensure the response was successful

        response_json = response.json()
        features = response_json.get("features", [])
        return features

    def download_data(self):
        """Download data using the Process API."""
        try:
            response = self.oauth.post(
                'https://sh.dataspace.copernicus.eu/api/v1/process',
                headers={"Authorization": f"Bearer {self.token}"},
                json=self.payload
            )
            response.raise_for_status()
        except Exception as e:
            import pdb
            pdb.set_trace()
            print(f"Error during data download: {e}")
            return None
        return response.content

    def save_as_geotiff(self, data, filename):
        """Save the downloaded image data as a GeoTIFF with target EPSG."""
        try:
            if data is None:
                print("No data to save.")
                return
            image_data = BytesIO(data)
            with rasterio.open(image_data) as src:
                image_array = src.read()
                height, width = image_array.shape[1], image_array.shape[2]

                xmin, ymin, xmax, ymax = transform_bbox(self.bbox, self.origin_epsg, self.target_epsg)
                transform = from_bounds(xmin, ymin, xmax, ymax, width, height)
                crs = CRS.from_epsg(self.target_epsg)

                count = image_array.shape[0]

                with rasterio.open(
                    filename,
                    'w',
                    driver='GTiff',
                    height=height,
                    width=width,
                    count=count,
                    dtype=image_array.dtype,
                    crs=crs,
                    transform=transform
                ) as dst:
                    dst.write(image_array)

                print(f"GeoTIFF saved successfully as {filename}.")
        except Exception as e:
            print(f"An error occurred while saving GeoTIFF: {e}")

class Sentinel2Processor(SentinelDownloader):
    def __init__(self, authenticator, bbox, time_range, bands):
        super().__init__(authenticator, bbox, time_range, bands, satellite_type="sentinel-2-l1c")

class Sentinel3Processor(SentinelDownloader):
    def __init__(self, authenticator, bbox, time_range, bands):
        super().__init__(authenticator, bbox, time_range, bands, satellite_type="sentinel-3-slstr")
