import os

import rasterio

from src.utils.gis_helpers import aggregate_rasters


def calculate_ui(working_dir, ndwi_threshold=0.3, mndwi_threshold=0.3, method='average'):
    sentinel2_dir = os.path.join(working_dir, 'Sentinel-2-weeks')

    for tiff_file in os.listdir(sentinel2_dir):
        # Skip files that are already processed (end with "_ui.tiff")
        if tiff_file.endswith("_ui.tiff"):
            print(f"Skipping {tiff_file}: already processed.")
            continue
        if tiff_file.endswith(".tiff"):
            file_path = os.path.join(sentinel2_dir, tiff_file)

            # Open the TIFF file
            with rasterio.open(file_path) as src:
                if src.count < 4:
                    print(f"Skipping {tiff_file}: not enough bands (requires 4 bands).")
                    continue
                # Read the bands needed for calculations
                b03 = src.read(1).astype(float)  # Green
                b04 = src.read(2).astype(float)  # Red
                b08 = src.read(3).astype(float)  # NIR
                b11 = src.read(4).astype(float)  # SWIR

                # Calculate NDWI: (B03 - B08) / (B03 + B08)
                ndwi = (b03 - b08) / (b03 + b08)

                # Calculate MNDWI: (B03 - B11) / (B03 + B11)
                mndwi = (b03 - b11) / (b03 + b11)

                # Water mask: both NDWI > ndwi_threshold and MNDWI > mndwi_threshold
                water_mask = (ndwi > ndwi_threshold) | (mndwi > mndwi_threshold)

                # Calculate UI: (B04 - B08) / (B04 + B08)
                ui = (b04 - b08) / (b04 + b08)

                # Apply water mask: set UI to -0.5 where water is detected
                ui[water_mask] = -0.5

                # Save the result as a new TIFF
                output_file = os.path.join(sentinel2_dir, tiff_file.replace(".tiff", "_ui.tiff"))
                out_meta = src.meta.copy()
                out_meta.update(count=1, dtype='float32')

                with rasterio.open(output_file, 'w', **out_meta) as dest:
                    dest.write(ui.astype('float32'), 1)
    return aggregate_rasters(sentinel2_dir, working_dir, method)
