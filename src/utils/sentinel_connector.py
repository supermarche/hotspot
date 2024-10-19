from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import secrets

class SentinelDownloader:
    def __init__(self, client_id, client_secret, bbox, time_range, bands, satellite_type="sentinel-2-l2a"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.bbox = bbox
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
                        "timeRange": {
                            "from": self.time_range['from'],
                            "to": self.time_range['to']
                        }
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
        if response.status_code == 200:
            return response.content
        else:
            response.raise_for_status()

    def save_data(self, data, filename):
        """Save the downloaded data to a file."""
        with open(filename, 'wb') as f:
            f.write(data)

# Usage example:

if __name__ == "__main__":
    # Your client credentials from the 'secrets' module
    client_id = secrets.client_name
    client_secret = secrets.client_secret

    # Define the bounding box for Görlitz (xmin, ymin, xmax, ymax)
    goerlitz_bbox = [14.9300, 51.1300, 15.0300, 51.2000]

    # Define the time range
    time_range = {
        "from": "2023-09-01T00:00:00Z",
        "to": "2023-09-30T23:59:59Z"
    }

    # Define the bands to be used
    bands = ["B02", "B03", "B04"]

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

    # Save the data to a file
    downloader.save_data(data, 'sentinel-2-l2a_gr.tiff')
