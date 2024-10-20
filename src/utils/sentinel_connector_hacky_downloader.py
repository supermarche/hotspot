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
    def __init__(self, client_id, client_secret, bbox, time_range, satellite_type):
        self.client_id = client_id
        self.client_secret = client_secret
        self.bbox = bbox  # Expected in EPSG:4326 (latitude and longitude)
        self.time_range = time_range
        self.satellite_type = satellite_type
        self.token = None
        self.oauth = None
        self.payload = None

        self.setup_session()

        self.origin_epsg = 4326
        self.target_epsg = 25833

    def update_time(self, time_range):
        self.time_range = time_range

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

    def create_payload(self, evalscript):
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
            "output": {
                "width": 2000,
                "height": 2000
            },
            "evalscript": evalscript
        }

    def search_data(self):
        #https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search?collections=sentinel-2-l2a&bbox=13,45,14,46&limit=1&datetime=2020-12-10T00:00:00Z/2020-12-30T00:00:00Z&filter=eo:cloud_cover>90&fields=id,type,-geometry,bbox,properties,-links,-assets

        # DOKU:
        #https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/ApiReference.html#tag/catalog_item_search/operation/getCatalogItemSearch
        data = {
            "bbox": self.bbox,
            "datetime": f"{self.time_range['from']}/{self.time_range['to']}",
            "collections": [self.satellite_type],
            "limit": 50,
            "filter": "eo:cloud_cover < 30",
            "distinct": "date",
        }
        print(data)
        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search',
            headers={"Authorization": f"Bearer {self.token}"},
            json=data,

        )
        print(json.loads(response.content))

        return json.loads(response.content)["features"]

    def download_data(self, evalscript):
        """Download data using the Process API."""
        self.create_payload(evalscript)
        print(self.payload)
        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/process',
            headers={"Authorization": f"Bearer {self.token}", "Accept": "image/tiff"},
            json=self.payload
        )
        try:
            response.raise_for_status()
        except:
            import pdb
            pdb.set_trace()
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
                        f"../data/s3_sn_{band}_{filename}",
                        'w',
                        driver='GTiff',
                        height=height,
                        width=width,
                        count=1,
                        dtype=image_array.dtype,
                        crs=crs,
                        transform=transform
                ) as dst:
                    if count == 1:
                        dst.write(image_array[:, :], 1)
                    else:
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
    # BBox Sachsen
    #sachsen_bbox = [11.788898, 50.150604, 15.086860, 51.720930]
    #sachsen_bbox = [12.9300, 50.1300, 15.0300, 51.4000]

    # Define the time range
    time_range = {
        "from": "2024-04-12T00:00:00Z",
        "to": "2024-04-12T23:59:59Z"
    }

    # Define the bands to be used
    eval_b4_b8 = """
//VERSION=3
function setup() {
    return {
        input: ["B08"],
        output: {
            bands: 1,
            sampleType: "FLOAT32"
        }
    };
}

function evaluatePixel(samples) {
    return [samples.B08]
}    """

    eval_s8 = """
//VERSION 3
function setup() {
    return {
        input: ["S8"],
        output: {
            bands: 1,
            sampleType: "UINT16"
        }
    }
}

function evaluatePixel(samples) {
    return [samples.S8]
}
    """

    #bands = ["B04", "B08", "B11", "B03"]
    #bands = ["S8"]
    # Create an instance of the SentinelDownloader
    downloader = SentinelDownloader(
        client_id=client_id,
        client_secret=client_secret,
        bbox=goerlitz_bbox,
        time_range=time_range,
        satellite_type="sentinel-2-l2a"
        #satellite_type="sentinel-2-l1c"
        #satellite_type="sentinel-3-slstr"
    )

    search = downloader.search_data()
    print(search)
    for avalible_photo in search:
        current_time_range = {
            "from": f"{avalible_photo}T00:00:00Z",
            "to": f"{avalible_photo}T23:59:59Z"
        }
        downloader.update_time(current_time_range)
        data = downloader.download_data(eval_b4_b8)
        downloader.save_data(data, f"../data/B08_{avalible_photo}_{downloader.satellite_type}.tiff")
