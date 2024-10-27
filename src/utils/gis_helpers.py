#import geopandas as gpd
import json
from matplotlib import pyplot as plt
from rasterio.crs import CRS as rasterio_CRS
from pyproj import Transformer
from scipy.ndimage import gaussian_filter


def save_tiff_and_metadata(array_data, transform, crs_epsg, output_path, bands_metadata):
    """
    Saves the GeoTIFF data returned by SentinelHub and writes associated metadata to a separate JSON file.

    :param response_data: Binary content (GeoTIFF) from SentinelHub request
    :param output_path: Path to save the GeoTIFF file
    :param bands_metadata: Dictionary containing metadata for the bands
    """
    # Save the GeoTIFF file
    raster_crs = rasterio_CRS.from_epsg(crs_epsg)
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=array_data.shape[0],
        width=array_data.shape[1],
        count=array_data.shape[2],
        dtype=array_data.dtype,
        crs=raster_crs,
        transform=transform
    ) as dst:
        for i in range(array_data.shape[2]):
            dst.write(array_data[:, :, i], i + 1)  # Write each band

    # Save the metadata in a JSON file
    metadata_path = output_path.replace('.tiff', '_metadata.json')
    with open(metadata_path, 'w') as meta_file:
        json.dump(bands_metadata, meta_file)

    print(f"Data and metadata saved to {output_path} and {metadata_path}")


def convert_bbox_epsg25833_to_crs84(bbox):
    """
    Convert a bounding box from EPSG:25833 to EPSG:4326.
    Parameters:
    bbox (tuple): Bounding box in EPSG:25833 as (min_x, min_y, max_x, max_y).
    Returns:
    tuple: Bounding box in EPSG:4326 as (min_lon, min_lat, max_lon, max_lat).
    """
    transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
    min_x, min_y, max_x, max_y = bbox
    min_lon, min_lat = transformer.transform(min_x, min_y)
    max_lon, max_lat = transformer.transform(max_x, max_y)
    return [min_lon, min_lat, max_lon, max_lat]

def transform_bbox(bbox, origin_epsg, target_epsg):
    """
    Convert bounding box from one EPSG to another.
    """
    transformer = Transformer.from_crs(f"EPSG:{origin_epsg}", f"EPSG:{target_epsg}", always_xy=True)
    xmin, ymin = transformer.transform(bbox[0], bbox[1])
    xmax, ymax = transformer.transform(bbox[2], bbox[3])
    return xmin, ymin, xmax, ymax


import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy import stats


def aggregate_rasters(working_dir, out_dir, method='average'):
    ui_rasters = [os.path.join(working_dir, f) for f in os.listdir(working_dir) if f.endswith("_ui.tiff")]

    raster_stack = []

    # Read each UI raster and stack them in memory
    for ui_raster in ui_rasters:
        with rasterio.open(ui_raster) as src:
            raster_data = src.read(1).astype(float)  # Read the first band
            raster_data[raster_data == src.nodata] = np.nan  # Treat nodata as NaN

            # Ensure that all rasters have the same shape by resizing (if needed)
            if len(raster_stack) > 0:
                if raster_data.shape != raster_stack[0].shape:
                    print(f"Skipping {ui_raster}: shape mismatch with others.")
                    continue  # Skip if shape doesn't match

            raster_stack.append(raster_data)

    # Ensure all rasters have the same shape before stacking
    if len(raster_stack) == 0:
        raise ValueError("No valid rasters found for aggregation.")

    # Convert list to 3D numpy array (stack of 2D rasters)
    stacked_array = np.stack(raster_stack, axis=0)

    # Aggregation based on method
    if method == 'average':
        aggregated_raster = np.nanmean(stacked_array, axis=0)
    elif method == 'median':
        aggregated_raster = np.nanmedian(stacked_array, axis=0)
    elif method == 'max':
        aggregated_raster = np.nanmax(stacked_array, axis=0)
    elif method == 'min':
        aggregated_raster = np.nanmin(stacked_array, axis=0)

        # After calculating the mode, replace placeholder (-9999) back with NaN
        aggregated_raster[aggregated_raster == -9999] = np.nan

    # Save the aggregated raster
    with rasterio.open(ui_rasters[0]) as src:
        out_meta = src.meta.copy()
        out_meta.update(dtype='float32')

    output_file = os.path.join(out_dir, 'aggregated_ui.tiff')
    with rasterio.open(output_file, 'w', **out_meta) as dest:
        dest.write(aggregated_raster.astype('float32'), 1)

    return output_file


def plot_geotiff(tiff_file_path):
    # Open the GeoTIFF file
    with rasterio.open(tiff_file_path) as dataset:
        # Read the first band (for single-band GeoTIFFs)
        band1 = dataset.read(1)

        # Plot the data using matplotlib
        plt.figure(figsize=(10, 10))
        plt.imshow(band1, cmap='viridis')  # You can change 'viridis' to another colormap
        plt.colorbar(label='Pixel Values')  # Add a color bar
        plt.title('GeoTIFF Plot')
        plt.xlabel('X (pixels)')
        plt.ylabel('Y (pixels)')
        plt.show()



def calculate_utm_zone(longitude):
    return int((longitude + 180) / 6) % 60 + 1


def is_northern_hemisphere(latitude):
    return latitude >= 0


def calculate_centroid(north_lat, south_lat, east_lng, west_lng):
    centroid_lat = (north_lat + south_lat) / 2
    centroid_lng = (east_lng + west_lng) / 2
    return centroid_lat, centroid_lng


def convert_bbox_to_utm(north_lat, south_lat, east_lng, west_lng):
    # Calculate the centroid of the bounding box
    centroid_lat, centroid_lng = calculate_centroid(north_lat, south_lat, east_lng, west_lng)

    # Determine the UTM zone from the centroid longitude
    utm_zone = calculate_utm_zone(centroid_lng)

    # Determine the hemisphere from the centroid latitude
    northern_hemisphere = is_northern_hemisphere(centroid_lat)

    # Construct the EPSG code
    if northern_hemisphere:
        epsg_code = 32600 + utm_zone  # Northern Hemisphere
    else:
        epsg_code = 32700 + utm_zone  # Southern Hemisphere

    # Create a transformer object
    transformer = Transformer.from_crs(
        "epsg:4326",  # Source CRS (WGS 84)
        f"epsg:{epsg_code}",  # Target CRS (UTM zone)
        always_xy=True  # Ensure (lon, lat) order
    )

    # Convert each corner of the bounding box
    west_x, north_y = transformer.transform(west_lng, north_lat)
    east_x, south_y = transformer.transform(east_lng, south_lat)

    # Return the UTM bounding box and CRS
    bounding_box_utm = {
        'north_y': north_y,
        'south_y': south_y,
        'west_x': west_x,
        'east_x': east_x
    }

    crs_info = {
        'utm_zone': utm_zone,
        'epsg_code': epsg_code,
        'northern_hemisphere': northern_hemisphere
    }

    return bounding_box_utm, crs_info


def smooth_raster(input_path, output_path, sigma=2, band_to_save=1):
    """
    Smooths a multi-band raster by applying a Gaussian filter to each band and saves a single-band output.

    Parameters:
    - input_path (str): Path to the input raster file or directory containing raster files.
    - output_path (str): Path to save the smoothed output raster or directory to save multiple smoothed rasters.
    - sigma (float): The standard deviation for the Gaussian filter. Higher values result in stronger smoothing.
    - band_to_save (int): The band index (1-based) to save in the output file.
    """
    # Ensure output directory exists if processing multiple files
    if os.path.isdir(input_path) and not os.path.exists(output_path):
        os.makedirs(output_path)

    if os.path.isdir(input_path) and os.path.isdir(output_path):
        # Loop over each .tif file in the input directory
        for filename in os.listdir(input_path):
            if filename.endswith(".tiff"):
                input_file = os.path.join(input_path, filename)
                output_file = os.path.join(output_path, filename)

                # Apply smoothing to the file
                _smooth_single_raster(input_file, output_file, sigma, band_to_save)

    elif os.path.isfile(input_path):
        # If input_path is a file, process it directly and check/create output directory if necessary
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        _smooth_single_raster(input_path, output_path, sigma, band_to_save)
    else:
        print("Invalid input or output path. Please ensure both are either directories or file paths.")


def _smooth_single_raster(input_file, output_file, sigma, band_to_save):
    """
    Smooths each band of a multi-band raster file and saves all bands as a multi-band output.

    Parameters:
    - input_file (str): Path to the input raster file.
    - output_file (str): Path to save the smoothed output raster.
    - sigma (float): The standard deviation for the Gaussian filter.
    """
    # Open the input raster file
    with rasterio.open(input_file) as src:
        profile = src.profile  # Copy the metadata profile
        profile.update(dtype=rasterio.float32)  # Update profile for output data type

        # Prepare an array to store all smoothed bands
        smoothed_bands = []

        # Read each band, apply smoothing, and append to the list
        for i in range(1, src.count + 1):
            band_data = src.read(i)
            smoothed_band = gaussian_filter(band_data, sigma=sigma)
            smoothed_bands.append(smoothed_band.astype(rasterio.float32))

        # Write all smoothed bands to the output raster file
        with rasterio.open(output_file, 'w', **profile) as dst:
            for idx, band_data in enumerate(smoothed_bands, start=1):
                dst.write(band_data, idx)

    print(f"Smoothed raster saved to {output_file}")



# gpd numpy conflict
"""
def create_square_bbox_wgs84(center_point, distance_km):
    '''
    Create a square bounding box (in kilometers) around a given point in WGS84.

    Parameters:
    - center_point: A tuple representing the (longitude, latitude) in WGS84.
    - distance_km: The distance in kilometers to define the size of the square bbox.

    Returns:
    - A GeoDataFrame containing the square bounding box in WGS84.
    '''
    # Define the EPSG codes
    wgs84 = 4326
    # UTM zone based on the center point (automatically selects appropriate UTM zone)
    utm_zone = 32633 if center_point[0] >= 0 else 32733

    # Create a transformer to convert from WGS84 to UTM (meters)
    transformer_to_utm = Transformer.from_crs(wgs84, utm_zone, always_xy=True)
    transformer_to_wgs84 = Transformer.from_crs(utm_zone, wgs84, always_xy=True)

    # Convert the center point to UTM (meters)
    center_utm_x, center_utm_y = transformer_to_utm.transform(center_point[0], center_point[1])

    # Define half the distance in meters (since the input is in kilometers)
    half_distance_m = (distance_km * 1000) / 2

    # Create the bounding box in UTM coordinates
    min_x = center_utm_x - half_distance_m
    max_x = center_utm_x + half_distance_m
    min_y = center_utm_y - half_distance_m
    max_y = center_utm_y + half_distance_m
    import pdb
    pdb.set_trace()
    # Convert the bounding box coordinates back to WGS84
    min_lon, min_lat = transformer_to_wgs84.transform(min_x, min_y)
    max_lon, max_lat = transformer_to_wgs84.transform(max_x, max_y)

    # Create the bounding box as a GeoDataFrame
    bbox_geom = box(min_lon, min_lat, max_lon, max_lat)
    gdf = gpd.GeoDataFrame(geometry=[bbox_geom], crs=f"EPSG:{wgs84}")

    return gdf
"""
