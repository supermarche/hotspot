import pytest
from sentinelhub import CRS, BBox, bbox_to_dimensions
from rasterio.transform import from_bounds
from src.utils.sentinel_data import SentinelData
from src.utils.gis_helpers import save_tiff_and_metadata
import os


def test_download_sentinel2_data(tmp_path):
    # Define test parameters
    bbox_coords = [498260, 5666530, 498290, 5666590]  # BBox for Görlitz/Zgorzelec
    crs = 32633  # CRS for EPSG:25833
    date_range = ('2020-06-12', '2020-06-13')
    resolution = 10  # Resolution in meters
    aoi_bbox = BBox(bbox=bbox_coords, crs=CRS(crs))
    aoi_size = bbox_to_dimensions(aoi_bbox, resolution=resolution)
    transform = from_bounds(*aoi_bbox, aoi_size[0], aoi_size[1])
    sentinel_data = SentinelData()  # Assuming SentinelData is your class

    # Test Sentinel-2 data download
    response = sentinel_data.download_sentinel2_data(bbox_coords, crs, date_range, resolution)

    assert len(response) > 0, "No Sentinel-2 data returned!"
    print("Sentinel-2 data downloaded successfully.")

    # Use the temporary directory for file output
    tiff_filepath = tmp_path / "test_output.tiff"
    bands_metadata_sentinel2 = {"bands": ["B03", "B04", "B08", "B11"]}

    # Save TIFF and metadata to temp file
    save_tiff_and_metadata(response, transform, crs, str(tiff_filepath), bands_metadata_sentinel2)

    # Assert that the .tiff file was created
    assert tiff_filepath.is_file(), f"Expected file {tiff_filepath} was not created!"

    # Check if the metadata file is also created
    metadata_path = str(tiff_filepath).replace('.tiff', '_metadata.json')
    metadata_file = tmp_path / metadata_path
    assert metadata_file.is_file(), f"Expected metadata file {metadata_file} was not created!"

    # Optionally, you can check the file contents or metadata (e.g., file size or format)
    assert tiff_filepath.stat().st_size > 0, "File is empty!"
    assert metadata_file.stat().st_size > 0, "Metadata file is empty!"

