from sentinel_authenticator import authenticate_session
from sentinel_search import search_satellite_imagery
import secrets
from gis_helpers import save_as_geotiff
from sentinel2_downloader import Sentinel2Downloader
from sentinel3_download import Sentinel3Downloader

# Define secrets for both downloads
client_id = secrets.client_name
client_secret = secrets.client_secret

# Define the bounding box and time range (common for both satellites)
bbox = [14.9165, 51.0711, 15.0759, 51.2166]
time_range = {"from": "2023-01-01T00:00:00Z", "to": "2023-12-30T23:59:59Z"}
filters = "eo:cloud_cover < 30"

# Define the satellite types for both
satellite_types_s3 = ["sentinel-3-slstr"]
satellite_types_s2 = ["sentinel-2-l1c"]
s3_band = "S8"
s2_bands = ["B04", "B08", "B11", "B03"]


results = search_satellite_imagery(authenticate_session, bbox, time_range, satellite_types_s3, filters)

downloader_s3 = Sentinel3Downloader(
    client_id=client_id,
    client_secret=client_secret,
    bbox=bbox,
    time_range=time_range,
    band=s3_band,
    satellite_type="sentinel-3-slstr"
)

downloader_s2 = Sentinel2Downloader(
        client_id=client_id,
        client_secret=client_secret,
        bbox=bbox,
        time_range=time_range,
        bands=s2_bands,
        satellite_type="sentinel-2-l1c"
    )


intersecting_dates = results.get("intersecting_dates", [])


for date in intersecting_dates:
    current_time_range = {
        "from": f"{date}T00:00:00Z",
        "to": f"{date}T23:59:59Z"
    }
    data_s3 = downloader_s3.download_data(current_time_range)
    save_as_geotiff(data_s3, f"../data/Sentinel-3/{date}_{downloader_s3.satellite_type}_{s3_band}.tiff", bbox=bbox, bands=[s3_band])
    data_s2 = downloader_s2.download_data(current_time_range)
    save_as_geotiff(data_s2, f"../data/Sentinel-2/{date}_{downloader_s2.satellite_type}.tiff", bbox=bbox, bands=s2_bands)


