import glob

import rasterio
import numpy as np
import os


def calculate_ndvi(nir_band, red_band):
    """
    Calculates NDVI, handling cases where division by zero may occur.

    :param nir_band: Near-infrared band (e.g., B08 from Sentinel-2).
    :param red_band: Red band (e.g., B04 from Sentinel-2).
    :return: NDVI array, where invalid values (div/0) are set to NaN.
    """
    # Suppress warnings for invalid values (division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir_band - red_band) / (nir_band + red_band)
        ndvi[(nir_band + red_band) == 0] = np.nan  # Set NDVI to NaN where the denominator is 0

    return ndvi


def calculate_lst_multiband_rasters(sentinel2_path, sentinel3_path, output_path, ndvi_s=0.2, ndvi_v=0.8):
    """
    Calculates LST using Sentinel-2 and Sentinel-3 data from multi-band raster files.

    :param sentinel2_path: Path to Sentinel-2 multi-band raster (B03, B04, B08, B11).
    :param sentinel3_path: Path to Sentinel-3 multi-band raster (S8, S9).
    :param output_path: Path to save the output LST raster.
    :param ndvi_s: Threshold for soil NDVI (default: 0.2).
    :param ndvi_v: Threshold for vegetation NDVI (default: 0.8).
    """

    # Open Sentinel-2 raster (B03, B04, B08, B11)
    with rasterio.open(sentinel2_path) as src_sentinel2:
        green_band = src_sentinel2.read(1)  # B03
        red_band = src_sentinel2.read(2)  # B04
        nir_band = src_sentinel2.read(3)  # B08
        swir_band = src_sentinel2.read(4)  # B11
        sentinel2_meta = src_sentinel2.meta

    # Open Sentinel-3 raster (S8, S9)
    with rasterio.open(sentinel3_path) as src_sentinel3:
        s8_band = src_sentinel3.read(1)  # S8 (thermal infrared in Kelvin)
        s9_band = src_sentinel3.read(2)  # S9 (additional band, not used here)

    # Calculate NDVI from Sentinel-2

    ndvi = calculate_ndvi(nir_band, red_band)

    # Proportional Vegetation (PV)
    pv = np.where(ndvi < ndvi_s, 0, np.where(ndvi > ndvi_v, 1, ((ndvi - ndvi_s) / (ndvi_v - ndvi_s)) ** 2))

    # Land Surface Emissivity (LSE) based on NDVI and surface type
    water_emissivity = 0.991
    soil_emissivity = 0.966
    vegetation_emissivity = 0.973
    lse = np.where(ndvi < 0, water_emissivity,
                   vegetation_emissivity * pv + soil_emissivity * (1 - pv))

    # Constants for LST calculation
    lambda_s8 = 10.85 * 10 ** -6  # Central wavelength for Sentinel-3 SLSTR S8 (meters)
    rho = 1.438 * 10 ** -2  # Planck constant * speed of light / Boltzmann constant (m K)

    # Brightness Temperature (Convert from Kelvin to Celsius)
    bt_celsius = s8_band # - 273.15

    # Land Surface Temperature (LST)
    lst = bt_celsius / (1 + (lambda_s8 * bt_celsius / rho) * np.log(lse))

    # Update metadata for output (same as input, but with a single band)
    sentinel2_meta.update(driver='GTiff', dtype=rasterio.float32, count=1)

    # Save the LST raster
    with rasterio.open(output_path, 'w', **sentinel2_meta) as dst:
        dst.write(lst.astype(rasterio.float32), 1)

    print(f"LST raster saved to {output_path}")


def calculate_lst(working_dir):
    """
    Calculate LST for all matched Sentinel-2 and Sentinel-3 TIFF pairs in the working directory.

    :param working_dir: Directory containing 'Sentinel-2' and 'Sentinel-3' subdirectories with TIFF files.
    """
    sentinel2_dir = os.path.join(working_dir, 'Sentinel-2')
    sentinel3_dir = os.path.join(working_dir, 'Sentinel-3')
    lst_dir = os.path.join(working_dir, 'LST_days')
    os.makedirs(lst_dir, exist_ok=True)  # Create LST output directory if not exist

    # List all Sentinel-2 and Sentinel-3 TIFF files
    sentinel2_files = glob.glob(os.path.join(sentinel2_dir, '*.tiff'))
    sentinel3_files = glob.glob(os.path.join(sentinel3_dir, '*.tiff'))

    # Extract the dates from the filenames assuming format "s2_<date>.tiff" and "s3_<date>.tiff"
    sentinel2_dates = {os.path.basename(f).split('_')[1]: f for f in sentinel2_files}
    sentinel3_dates = {os.path.basename(f).split('_')[1]: f for f in sentinel3_files}

    # Find matching dates
    matching_dates = set(sentinel2_dates.keys()) & set(sentinel3_dates.keys())

    if not matching_dates:
        print("No matching dates found between Sentinel-2 and Sentinel-3 data.")
        return

    lst_files = []

    # For each matching date, calculate LST and save the result
    for date in sorted(matching_dates):
        sentinel2_path = sentinel2_dates[date]
        sentinel3_path = sentinel3_dates[date]
        output_path = os.path.join(lst_dir, f"LST_{date}.tiff")

        calculate_lst_multiband_rasters(sentinel2_path, sentinel3_path, output_path)
        lst_files.append(output_path)

    # Calculate the mean LST across all days
    if lst_files:
        lst_mean_path = os.path.join(working_dir, "LST_mean.tiff")
        calculate_mean_lst(lst_files, lst_mean_path)
        print(f"LST mean raster saved to {lst_mean_path}")
    else:
        print("No LST files created.")


def calculate_mean_lst(lst_files, output_path):
    """
    Calculate the mean LST from a list of LST TIFF files.

    :param lst_files: List of paths to LST TIFF files.
    :param output_path: Path to save the mean LST TIFF file.
    """
    # Open the first LST file to get metadata and shape
    with rasterio.open(lst_files[0]) as src:
        lst_meta = src.meta
        lst_meta.update(count=1)  # Update metadata to have only 1 band (for mean)
        lst_sum = np.zeros(src.shape, dtype=np.float32)
        lst_count = np.zeros(src.shape, dtype=np.int32)

    # Sum all LST rasters and count valid pixels
    for lst_file in lst_files:
        with rasterio.open(lst_file) as src:
            lst_data = src.read(1)  # Read the first band
            valid_mask = np.isfinite(lst_data)  # Check for valid (non-NaN) pixels
            lst_sum[valid_mask] += lst_data[valid_mask]
            lst_count[valid_mask] += 1

    # Avoid division by zero
    lst_mean = np.divide(lst_sum, lst_count, where=lst_count != 0)

    # Save the mean LST raster
    with rasterio.open(output_path, 'w', **lst_meta) as dst:
        dst.write(lst_mean.astype(np.float32), 1)

    print(f"Mean LST raster saved to {output_path}")

if __name__ == "__main__":
    # Example usage
    sentinel2_path = "/sentinel2_20240308.tiff"  # Sentinel-2 multi-band raster
    sentinel3_path = "/sentinel3_20240308.tiff"  # Sentinel-3 multi-band raster
    output_path = "/output_lst.tif"  # Path to save the LST result

    # Call the function to calculate and save LST
    calculate_lst_multiband_rasters(sentinel2_path, sentinel3_path, output_path)
