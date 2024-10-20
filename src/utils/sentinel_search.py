# satellite_search.py

from sentinel_authenticator import authenticate_session

class SatelliteSearchEngine:
    """A generic class to handle the search functionality for multiple satellites."""

    def __init__(self, authenticate_session):

        self.oauth, self.token = authenticate_session()

    def search_data(self, bbox, time_range, satellite_type, filters=None):
        """
        Search the catalog for available imagery within the specified parameters.

        Parameters:
        - bbox: list of floats in the format [min_lon, min_lat, max_lon, max_lat]
        - time_range: dict with 'from' and 'to' keys, e.g. {"from": "2023-01-01", "to": "2023-12-31"}
        - satellite_type: string representing the satellite collection, e.g. 'sentinel-2-l1c'
        - filters: dict containing optional filters like cloud cover (default: eo:cloud_cover < 30)

        Returns:
        - list of features found in the search query
        """
        default_filter = "eo:cloud_cover < 30"
        filter_query = filters if filters else default_filter

        search_payload = {
            "bbox": bbox,
            "datetime": f"{time_range['from']}/{time_range['to']}",
            "collections": [satellite_type],
            "limit": 100,
            "filter": filter_query,
            "distinct": "date",
        }

        response = self.oauth.post(
            'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search',
            headers={"Authorization": f"Bearer {self.token}"},
            json=search_payload,
        )
        try:
            response.raise_for_status()  # Ensure the response was successful
        except:
            import pdb
            pdb.set_trace()
        response_json = response.json()
        features = response_json.get("features", [])
        return features

def search_satellite_imagery(authenticate_session, bbox, time_range, satellite_types, filters):
    """
    Searches for satellite imagery data within a specified bounding box and time range for different satellite types.
    Filters the results based on the provided criteria and calculates the intersection of results for all satellite types.

    Parameters:
    -----------
    authenticate_session : object
        The authentication session object for initializing the SatelliteSearchEngine.
    bbox : list
        A list of coordinates defining the bounding box for the search.
        Example: [min_longitude, min_latitude, max_longitude, max_latitude].
    time_range : dict
        A dictionary specifying the time range for the search with keys "from" and "to".
        Example: {"from": "2023-01-01T00:00:00Z", "to": "2023-12-30T23:59:59Z"}.
    satellite_types : list
        A list of satellite types to search for.
        Example: ["sentinel-2-l1c", "sentinel-3-slstr"].
    filters : str
        The filtering condition for the search.
        Example: "eo:cloud_cover < 30".

    Returns:
    --------
    dict
        A dictionary containing results for each satellite type and their intersecting dates.
        The intersecting dates are stored under the key 'intersecting_dates'.
    """
    # Initialize the search class with authentication.
    satellite_search = SatelliteSearchEngine(authenticate_session)

    results_dict = {}
    for satellite_type in satellite_types:
        # Perform a search for satellite imagery with the specified parameters.
        results = satellite_search.search_data(bbox, time_range, satellite_type, filters)
        results_dict[satellite_type] = results
        # Print out the number of features found and a sample (if available).
        print(f"Number of features found: {len(results)} for {satellite_type}")
        if results:
            print("Sample feature:", results[0])

    # Convert each value in the dictionary to a set and calculate the intersection.
    intersection_result = set.intersection(*[set(value) for value in results_dict.values()])
    results_dict['intersecting_dates'] = intersection_result
    print(f"Number of features intersecting: {len(intersection_result)}")

    return results_dict


if __name__ == "__main__":
    # Define the input data
    # authenticate_session  imported function
    bbox = [14.9165, 51.0711, 15.0759, 51.2166]  # Example bounding box coordinates
    time_range = {"from": "2023-01-01T00:00:00Z", "to": "2023-12-30T23:59:59Z"}
    satellite_types = ["sentinel-2-l1c", "sentinel-3-slstr"]
    filters = "eo:cloud_cover < 60"

    # Call the function
    results = search_satellite_imagery(authenticate_session, bbox, time_range, satellite_types, filters)
    print(results)
