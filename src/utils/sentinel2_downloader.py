from sentinel_authenticator import authenticate_session
from sentinel_search import search_satellite_imagery
import secrets
from gis_helpers import save_as_geotiff

class Sentinel2Downloader:
    def __init__(self, client_id, client_secret, bbox, time_range, bands, satellite_type="sentinel-2-l1c"):
        # Authenticate the session using provided credentials
        #self.client_id = client_id
        #self.client_secret = client_secret
        self.bbox = bbox  # Expected in EPSG:4326 (latitude and longitude)
        self.time_range = time_range
        self.bands = bands
        self.satellite_type = satellite_type
        self.origin_epsg = 4326
        self.target_epsg = 25833

        # Get authenticated session and token
        self.oauth, self.token = authenticate_session()

        # Create evalscript and payload template
        self.create_evalscript()
        self.payload_template = self.create_payload_template()

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

    def create_payload_template(self):
        """Create the template for the API request payload."""
        return {
            "input": {
                "bounds": {
                    "bbox": self.bbox
                },
                "data": [{
                    "type": self.satellite_type,
                    "dataFilter": {
                        "timeRange": {}  # To be filled in with each request
                    }
                }]
            },
            "output": {
                # TODO calculate resolution
                "width": 1500, # 1500
                "height": 1500,
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff"
                    }
                }]
            },
            "evalscript": self.evalscript
        }

    def update_payload_time(self, time_range):
        """Update the payload with a new time range."""
        self.payload_template["input"]["data"][0]["dataFilter"]["timeRange"] = time_range

    def download_data(self, time_range):
        """Download data using the Process API."""
        self.update_payload_time(time_range)
        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/process',
            headers={"Authorization": f"Bearer {self.token}"},
            json=self.payload_template
        )
        response.raise_for_status()
        return response.content



if __name__ == "__main__":
    #sentinel-2-l1c
    client_id = secrets.client_name
    client_secret = secrets.client_secret

    # Define the bounding box and time range
    bbox = [14.9165, 51.0711, 15.0759, 51.2166]
    time_range = {"from": "2023-01-01T00:00:00Z", "to": "2023-12-30T23:59:59Z"}
    bands = ["B04", "B08", "B11", "B03"]

    downloader = Sentinel2Downloader(
        client_id=client_id,
        client_secret=client_secret,
        bbox=bbox,
        time_range=time_range,
        bands=bands,
        satellite_type="sentinel-2-l1c"
    )

    filters = "eo:cloud_cover < 30"
    satellite_types = ["sentinel-2-l1c"]

    # Perform search
    results = search_satellite_imagery(authenticate_session, bbox, time_range, satellite_types, filters)
    intersecting_dates = results.get("intersecting_dates", [])

    # Loop through intersecting dates and download data for each date
    for date in intersecting_dates:
        current_time_range = {
            "from": f"{date}T00:00:00Z",
            "to": f"{date}T23:59:59Z"
        }
        data = downloader.download_data(current_time_range)
        save_as_geotiff(data, f"../data/Sentinel-2/{date}_{downloader.satellite_type}.tiff", bbox=bbox, bands=bands)
