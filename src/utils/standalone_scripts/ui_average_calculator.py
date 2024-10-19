import rasterio
import numpy as np
import glob
from rasterio.transform import from_bounds

def calculate_and_save_average_ui(directory, summer_months, winter_months, output_summer, output_winter):
    """
    Calculate and save the average Urban Index (UI) for summer and winter periods.

    Parameters:
        directory (str): Path to the directory containing GeoTIFF files.
        summer_months (list): List of summer months as strings in 'YYYY-MM' format.
        winter_months (list): List of winter months as strings in 'YYYY-MM' format.
        output_summer (str): Path to save the summer average GeoTIFF.
        output_winter (str): Path to save the winter average GeoTIFF.
    """
    summer_files = []
    winter_files = []

    # Find files for each period
    for month in summer_months:
        summer_files.extend(glob.glob(f"{directory}/*{month}*.tiff"))
    for month in winter_months:
        winter_files.extend(glob.glob(f"{directory}/*{month}*.tiff"))

    def calculate_mean_ui(file_list):
        if not file_list:
            return None

        ui_sum = None
        count = 0

        for file in file_list:
            with rasterio.open(file) as src:
                ui_data = src.read(1).astype(float)  # Read first band

                # Handle nodata values if present
                nodata_value = src.nodata
                if nodata_value is not None:
                    ui_data = np.where(ui_data == nodata_value, np.nan, ui_data)

                if ui_sum is None:
                    ui_sum = np.nan_to_num(ui_data)
                else:
                    ui_sum += np.nan_to_num(ui_data)

                count += 1

        # Calculate average by dividing by the count of files
        ui_average = ui_sum / count
        return ui_average

    def save_geotiff(output_path, ui_average, reference_file):
        """Save the UI average as a GeoTIFF file using the reference file for metadata."""
        with rasterio.open(reference_file) as src:
            profile = src.profile
            profile.update(dtype=rasterio.float32, count=1, compress='lzw')
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(ui_average.astype(rasterio.float32), 1)

    # Calculate average UI for summer and winter periods
    summer_avg_ui = calculate_mean_ui(summer_files)
    winter_avg_ui = calculate_mean_ui(winter_files)

    # Save the average UI for each period
    if summer_avg_ui is not None and summer_files:
        save_geotiff(output_summer, summer_avg_ui, summer_files[0])
        print(f"Summer average UI saved to {output_summer}")
    else:
        print("No valid data found for summer period.")

    if winter_avg_ui is not None and winter_files:
        save_geotiff(output_winter, winter_avg_ui, winter_files[0])
        print(f"Winter average UI saved to {output_winter}")
    else:
        print("No valid data found for winter period.")

# Directory where the UI GeoTIFF files are saved
directory = "../../data/ui"

# Define months for summer and winter periods (for northern hemisphere)
summer_months = ["2023-06", "2023-07", "2023-08"]
winter_months = ["2023-12", "2023-01", "2023-02"]

# Paths to save the output GeoTIFF files
output_summer = "../../data/ui/summer_UI.tiff"
output_winter = "../../data/ui/winter_UI.tiff"

# Calculate and save average UI for summer and winter periods
calculate_and_save_average_ui(directory, summer_months, winter_months, output_summer, output_winter)
