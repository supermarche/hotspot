import pytest
from sentinelhub import SHConfig, SentinelHubRequest, BBox, CRS, MimeType, DataCollection
from src.utils.config import load_config
from sentinelhub import SHConfig, SentinelHubCatalog

def test_sentinelhub_connection():
    config = load_config()

    bbox = BBox([498263, 5666527, 500593, 5668959], crs=CRS(25833))
    catalog = SentinelHubCatalog(config)
    search_iterator = catalog.search(collection="sentinel-5p-l2", bbox=bbox,
                                     time=("2020-11-01", "2020-11-05"))

    timestamps = [ts.isoformat() for ts in search_iterator.get_timestamps()]
    assert len(timestamps) > 0
