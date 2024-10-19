import requests
from oauthlib.oauth2 import BackendApplicationClient
from rasterio import MemoryFile
from requests_oauthlib import OAuth2Session
from io import BytesIO
from PIL import Image
import numpy as np
import json
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from pyproj import Transformer  # For coordinate transformation
import secrets


from pyproj import Transformer

def convert_bbox_epsg25833_to_crs84(bbox):
    """
    Convert a bounding box from EPSG:25833 to EPSG:4326.

    Parameters:
    bbox (tuple): Bounding box in EPSG:25833 as (min_x, min_y, max_x, max_y).

    Returns:
    tuple: Bounding box in EPSG:4326 as (min_lon, min_lat, max_lon, max_lat).
    """
    # Create a transformer object for converting EPSG:25833 to EPSG:4326
    transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)

    # Extract the bounding box corners
    min_x, min_y, max_x, max_y = bbox

    # Transform each corner of the bounding box
    min_lon, min_lat = transformer.transform(min_x, min_y)
    max_lon, max_lat = transformer.transform(max_x, max_y)

    # Return the transformed bounding box
    return [min_lon, min_lat, max_lon, max_lat]


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

    def update_time(self, time_range):
        self.time_range = time_range
        self.create_payload()

    def setup_session(self):
        """Set up the OAuth session and fetch the access token."""
        # Token
        # https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings
        client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=client)
        # Get token for the session
        self.token = self.oauth.fetch_token(
            token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
            client_secret=self.client_secret,
            include_client_id=True
        )

        # Register compliance hook
        def sentinelhub_compliance_hook(response):
            response.raise_for_status()
            return response

        self.oauth.register_compliance_hook("access_token_response", sentinelhub_compliance_hook)

    def create_evalscript(self):
        """Create the evalscript based on the specified bands."""
        bands_input = ', '.join([f'"{band}"' for band in self.bands])
        bands_output = len(self.bands)

        self.evalscript = f"""
        //VERSION=3

        function setup() {{
          return {{
            input: [{bands_input}],
            output: {{
              bands: {bands_output},
              sampleType: "FLOAT32" // Ensure the output reflectance data range is maintained
            }}
          }};
        }}

        function evaluatePixel(sample) {{
          return [{', '.join([f'sample.{band}' for band in self.bands])}];
        }}
        """

    def create_payload(self):
        """Create the payload for the API request."""

        self.payload = {
            "input": {
                "bounds": {
                    "bbox": self.bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/25833"
                    }
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
                #"width": "10",
                #"height": "10",
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
        #https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search?collections=sentinel-2-l2a&bbox=13,45,14,46&limit=1&datetime=2020-12-10T00:00:00Z/2020-12-30T00:00:00Z&filter=eo:cloud_cover>90&fields=id,type,-geometry,bbox,properties,-links,-assets

        # DOKU:
        #https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/ApiReference.html#tag/catalog_item_search/operation/getCatalogItemSearch


        data = {
            "bbox": self.bbox,
            "datetime": f"{self.time_range['from']}/{self.time_range['to']}",
            "collections": [self.satellite_type],
            "filter": "eo:cloud_cover < 30",
            "distinct": "date",
        }

        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search',
            headers={"Authorization": f"Bearer {self.token}"},
            json=data,

        )
        #print(json.loads(response.content)["features"])
        return json.loads(response.content)["features"]

    def download_data(self):
        """Download data using the Process API."""
        try:
            response = self.oauth.post(
                'https://sh.dataspace.copernicus.eu/api/v1/process',
                headers={"Authorization": f"Bearer {self.token}"},
                json=self.payload
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Content: {response.text}")
            import pdb
            pdb.set_trace()
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            import pdb
            pdb.set_trace()
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            import pdb
            pdb.set_trace()
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
            import pdb
            pdb.set_trace()
        return response.content

    def save_data(self, data, filename):
        """Save the downloaded data to a file."""
        with open(filename, 'wb') as f:
            f.write(data)

    def save_geotiff_from_binary(self, data, filename):
        """
        Save a binary GeoTIFF file from data as a GeoTIFF file using rasterio.

        :param data: The binary GeoTIFF data
        :param filename: The output filename to save the GeoTIFF
        """
        try:
            # Open the binary data using rasterio's MemoryFile
            with MemoryFile(data) as memfile:
                with memfile.open() as dataset:
                    # Retrieve metadata
                    meta = dataset.meta

                    # Print basic information for verification
                    print(f"GeoTIFF metadata: {meta}")

                    # Update the metadata if necessary (e.g., changing data type, etc.)
                    # meta.update(dtype='float32', driver='GTiff') # Uncomment and modify if needed

                    # Read the entire dataset (or specific bands as needed)
                    data_array = dataset.read()

                    # Write to a new GeoTIFF file
                    with rasterio.open(filename, 'w', **meta) as dst:
                        dst.write(data_array)

            print(f"GeoTIFF saved successfully as {filename}.")
        except Exception as e:
            print(f"An error occurred while saving GeoTIFF: {e}")

    def save_as_geotiff(self, data, filename):
        """Save the downloaded image data as a GeoTIFF with EPSG:25833."""
        try:
            # Convert data to a BytesIO object
            image_data = BytesIO(data)

            # Open the image using PIL
            image = Image.open(image_data)

            # Convert the image to a numpy array
            image_array = np.array(image)

            # Get image dimensions
            height, width = image_array.shape[:2]

            # Transform bbox from EPSG:4326 (WGS84) to EPSG:25833
            transformer = Transformer.from_crs(f"EPSG:{self.origin_epsg}", f"EPSG:{self.target_epsg}", always_xy=True)
            xmin, ymin = transformer.transform(self.bbox[0], self.bbox[1])
            xmax, ymax = transformer.transform(self.bbox[2], self.bbox[3])

            # Create a geospatial transform
            transform = from_bounds(xmin, ymin, xmax, ymax, width, height)

            # Define the coordinate reference system
            crs = CRS.from_epsg(self.target_epsg)  # EPSG:25833

            # Determine the number of bands
            if image_array.ndim == 2:
                count = 1  # Grayscale image
            elif image_array.ndim == 3:
                count = image_array.shape[2]  # Number of color bands

            # Write the data to a GeoTIFF file
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
                if count == 1:
                    dst.write(image_array, 1)
                else:
                    for i in range(count):
                        dst.write(image_array[:, :, i], i + 1)

            print(f"GeoTIFF saved successfully as {filename}.")
        except Exception as e:
            print(f"An error occurred while saving GeoTIFF: {e}")

if __name__ == "__main__":
    # Your client credentials from the 'secrets' module
    client_id = secrets.client_name
    client_secret = secrets.client_secret

    # Define the bounding box for Görlitz (xmin, ymin, xmax, ymax in EPSG:4326)
    #goerlitz_bbox = [495000.0, 5664000.0, 496000.0, 5665000.0]
    goerlitz_bbox = [14.9300, 51.1300, 14.9800, 51.1600]

    # Define the time range
    time_range = {
        "from": "2022-10-01T00:00:00Z",
        "to": "2022-10-3123:59:59Z"
    }

    # Define the bands to be used
    #bands = ["B04", "B08", "B11", "B03"]
    bands = ["B04"] #, "B08", "B11", "B03"
    # Create an instance of the SentinelDownloader
    downloader = SentinelDownloader(
        client_id=client_id,
        client_secret=client_secret,
        bbox=goerlitz_bbox,
        time_range=time_range,
        bands=bands,
        satellite_type="sentinel-2-l1c"
    )

    search = downloader.search_data()

    for avalible_photo in search:
        curent_time_range = {
            "from": f"{avalible_photo}T00:00:00Z",
            "to": f"{avalible_photo}T23:59:59Z"
        }
        downloader.update_time(curent_time_range)
        data = downloader.download_data()
        downloader.save_geotiff_from_binary(data, f"{avalible_photo}_{downloader.satellite_type}.tiff")
        #downloader.save_as_geotiff(data, f"{avalible_photo}_{downloader.satellite_type}.tiff")