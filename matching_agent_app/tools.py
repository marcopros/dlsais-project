from database.utils import getProfessionals, getCities
from matching_agent_app.utils import haversine, fetch_coordinates_for_cities



# ----------------------
# TOOL 1: find_professionals
# ----------------------
def find_professionals(profession: str, location: str) -> dict:
    """
    Find professionals based on profession and location match.

    Args:
        profession (str): The required profession (e.g., 'Electrician').
        location (str): The required city or area.

    Returns:
        dict: {
            'status': 'success' or 'no_results',
            'professionals': list of matching professional dicts,
            'message': description of what was done
        }
    """
    # Database query to find professionals filtering by profession and location
    matching = getProfessionals(profession, location)

    if not matching:
        return {
            "status": "error",
            "professionals": [],
            "error_message": f"No professionals found matching profession {profession.lower()} and location {location.lower()}."
        }

    return {
        "status": "success",
        "professionals": matching,
        "message": f"Found {len(matching)} professionals matching profession and location."
    }


# ----------------------
# TOOL 2: find_other_city
# ----------------------
def find_other_city(profession: str) -> list:
    """
    Suggest alternative cities where professionals of a given profession are available.

    Args:
        profession (str): The profession for which to suggest cities (e.g., 'plumber').

    Returns:
        dict: A dictionary with status and the cities (if successful) or an error message.
    """

    # Database query to find city fildered by the presence of the profession
    available_cities = getCities(profession)

    if not available_cities or len(available_cities) == 0:
        return {
            "status": "error",
            "error_message": f"No cities found matching profession {profession.lower()}."
        }

    return {
        "status": "success",
        "cities": available_cities,
    }




# ----------------------
# TOOL 3: find_nearest_cities
# ----------------------
def find_nearest_cities(params: dict) -> dict:
    """
    Find the nearest cities to the target city from a list of cities using geographic coordinates.

    Args:
        params (dict): A dictionary containing the following keys:
            - 'target_city' (str): The city to find the nearest cities to.
            - 'city_list' (list of str): A list of cities to compare distances.
            - 'top_n' (int, optional): The number of nearest cities to return (default is 5).
    
    Returns:
        dict: A dictionary with status and the nearest cities (if successful) or an error message.

    Example usage:
        find_nearest_cities({
            'target_city': 'Paris, France',
            'city_list': ['London, UK', 'Berlin, Germany'],
            'top_n': 3
        })
        # Output: {'status': 'success', 'nearest_cities': [('London, UK', 344.45), ('Berlin, Germany', 878.23)]}
    """

    # First fetch coordinates
    all_cities = [params['target_city']] + params['city_list']  # Corrected to use params['key']
    city_coordinates = fetch_coordinates_for_cities(all_cities, max_workers=5)

    # Error handling if target city is not found
    if params['target_city'] not in city_coordinates:
        return {
            "status": "error",
            "error_message": "City not found: " + params['target_city'],
        }

    target_coord = city_coordinates[params['target_city']]
    city_distances = []

    # Calculate distances to each city
    for city in params['city_list']:
        coord = city_coordinates.get(city)
        if coord:
            distance = haversine(target_coord, coord)
            city_distances.append((city, distance))

    # Sort by distance
    city_distances.sort(key=lambda x: x[1])

    # If more than 5 cities, limit to the top 5
    top_n = params.get('top_n', 5)  # Default to 5 if not provided
    city_distances = city_distances[:top_n]

    return {
        "status": "success",
        "nearest_cities": city_distances,
    }


    




