from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from io import BytesIO
from PIL import Image
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from pyproj import Transformer  # For coordinate transformation
import secrets


class SentinelDownloader:
    def __init__(self, client_id, client_secret, bbox, time_range, bands, satellite_type="sentinel-2-l2a"):
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

    def setup_session(self):
        """Set up the OAuth session and fetch the access token."""
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
                        f"{band}_{filename}",
                        'w',
                        driver='GTiff',
                        height=height,
                        width=width,
                        count=count,
                        dtype=image_array.dtype,
                        crs=crs,
                        transform=transform
                ) as dst:
                    dst.write(image_array[:, :, i], i + 1)

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
        "from": "2023-09-01T00:00:00Z",
        "to": "2023-09-30T23:59:59Z"
    }

    # Define the bands to be used
    bands = ["B04", "B08"]

    # Create an instance of the SentinelDownloader
    downloader = SentinelDownloader(
        client_id=client_id,
        client_secret=client_secret,
        bbox=goerlitz_bbox,
        time_range=time_range,
        bands=bands
    )

    # Download the data
    data = downloader.download_data()

    # Save the data as a GeoTIFF with geospatial metadata
    downloader.save_as_geotiff(data, 'sentinel-2-l2a_gr.tiff')
