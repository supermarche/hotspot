from oauthlib.oauth2 import BackendApplicationClient
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
            "evalscript": self.evalscript
        }

    def search_data(self):
        #https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search?collections=sentinel-2-l2a&bbox=13,45,14,46&limit=1&datetime=2020-12-10T00:00:00Z/2020-12-30T00:00:00Z&filter=eo:cloud_cover>90&fields=id,type,-geometry,bbox,properties,-links,-assets

        # DOKU:
        #https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/ApiReference.html#tag/catalog_item_search/operation/getCatalogItemSearch
        data = {
            "bbox": self.bbox,
            "datetime": f"{self.time_range['from']}/{self.time_range['to']}",
            "collections": [self.satellite_type],
            #"limit": 1000,
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
        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/process',
            headers={"Authorization": f"Bearer {self.token}"},
            json=self.payload
        )
        response.raise_for_status()
        return response.content

    def save_data(self, data, filename):
        """Save the downloaded data to a file."""
        with open(filename, 'wb') as f:
            f.write(data)

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
            crs = CRS.from_epsg(self.target_epsg) # EPSG:25833

            # Determine the number of bands
            if image_array.ndim == 2:
                count = 1  # Grayscale image
            elif image_array.ndim == 3:
                count = image_array.shape[2]  # Number of color bands

            # Write the data to a GeoTIFF file
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
    # Your client credentials from the 'secrets' module
    client_id = secrets.client_name
    client_secret = secrets.client_secret

    # Define the bounding box for Görlitz (xmin, ymin, xmax, ymax in EPSG:4326)
    goerlitz_bbox = [14.9300, 51.1300, 15.0300, 51.2000]

    # Define the time range
    time_range = {
        "from": "2023-01-01T00:00:00Z",
        "to": "2023-12-30T23:59:59Z"
    }

    # Define the bands to be used
    bands = ["B04", "B08", "B11", "B03"]

    # Create an instance of the SentinelDownloader
    downloader = SentinelDownloader(
        client_id=client_id,
        client_secret=client_secret,
        bbox=goerlitz_bbox,
        time_range=time_range,
        bands=bands
    )

    seearch = downloader.search_data()
    for avalible_photo in seearch:
        curent_time_range = {
            "from": f"{avalible_photo}T00:00:00Z",
            "to": f"{avalible_photo}T23:59:59Z"
        }
        downloader.update_time(curent_time_range)
        data = downloader.download_data()
        downloader.save_as_geotiff(data, f"{avalible_photo}_{downloader.satellite_type}.tiff")


