import glob

import pytest
from src.utils.sentinel_data import SentinelData


def test_download_sentinel2_data():
    # Define test parameters
    bbox_coords = [498260, 5666530, 498290, 5666590]  # BBox for Görlitz/Zgorzelec
    crs = 32633  # CRS for EPSG:25833
    date_range = ('2020-06-12', '2020-06-13')
    resolution = 10  # Resolution in meters

    sentinel_data = SentinelData()  # Assuming SentinelData is your class

    # Test Sentinel-2 data download
    response = sentinel_data.download_sentinel2_data(bbox_coords, crs, date_range, resolution)
    assert len(response) > 0, "No Sentinel-2 data returned!"
    print("Sentinel-2 data downloaded successfully.")


def test_download_sentinel3_data():
    # Define test parameters
    bbox_coords = [498260, 5666530, 498290, 5666590]  # BBox for Görlitz/Zgorzelec
    crs = 32633  # CRS for EPSG:25833
    date_range = ('2020-06-12', '2020-06-13')
    resolution = 10  # Resolution in meters (for Sentinel-3)

    sentinel_data = SentinelData()  # Assuming SentinelData is your class
    print(f"Access Token: {sentinel_data.config.sh_token}")
    # Test Sentinel-3 data download
    response = sentinel_data.download_sentinel3_data(bbox_coords, crs, date_range, resolution)
    assert len(response) > 0, "No Sentinel-3 data returned!"
    print("Sentinel-3 data downloaded successfully.")

def test_search_data():
    # Define test parameters
    bbox_coords = [498260, 5666530, 498290, 5666590]  # BBox for Görlitz/Zgorzelec
    crs = 32633  # CRS for EPSG:25833
    date_range = ('2020-06-12', '2020-06-13')
    resolution = 10  # Resolution in meters (for Sentinel-3)

    sentinel_data = SentinelData()  # Assuming SentinelData is your class

    result = sentinel_data.search_data(bbox_coords, crs,date_range)
    assert result['sentinel_3'] == {'2020-06-12', '2020-06-13'}

def test_download_data_pack(tmp_path):
    # Define test parameters
    bbox_coords = [498260, 5666530, 498290, 5666590]  # BBox for Görlitz/Zgorzelec
    crs = 32633  # CRS for EPSG:25833
    date_range = ('2024-06-12', '2024-07-16')
    resolution = 10  # Resolution in meters (for Sentinel-3)

    sentinel_data = SentinelData()  # Assuming SentinelData is your class
    sentinel_data.download_data_pack(bbox_coords, crs, date_range, resolution, tmp_path, filter='eo:cloud_cover < 40')

    # Define the expected folder names (adjust based on your logic)
    folder1 = tmp_path / "Sentinel-2"
    folder2 = tmp_path / "Sentinel-3"

    # Assert the folders were created
    assert folder1.is_dir(), f"Expected folder {folder1} was not created."
    assert folder2.is_dir(), f"Expected folder {folder2} was not created."

    # Check that TIFF files exist in both folders
    tiff_files_folder1 = list(glob.glob(str(folder1) + "/*.tiff"))
    tiff_files_folder2 = list(glob.glob(str(folder2) + "/*.tiff"))

    assert len(tiff_files_folder1) > 0, f"No TIFF files found in {folder1}"
    assert len(tiff_files_folder2) > 0, f"No TIFF files found in {folder2}"

