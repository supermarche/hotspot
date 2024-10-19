#import geopandas as gpd
from shapely.geometry import Point, box
from pyproj import Transformer

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
if __name__ == "__main__":
    # Example usage
    center_point = (13.4, 51.13)  # Longitude, Latitude in WGS84
    distance_km = 1000  # Distance in kilometers

    # Create the square bounding box
    bbox_gdf = create_square_bbox_wgs84(center_point, distance_km)
    bbox_gdf.to_file("bbox", driver='ESRI Shapefile')
    # Display the result
    print(bbox_gdf)