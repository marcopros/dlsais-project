import logging

from database.utils import getProfessionals, getCities, getCity
from matching_agent_app.utils import haversine, fetch_coordinates_for_cities

# Setup basic logging to help debug and trace execution flow
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# ----------------------
# TOOL 1: find_professionals
# ----------------------
def find_professionals(profession: str, city: str) -> dict:
    """
    Find professionals based on profession and location match.

    Args:
        profession (str): The required profession (e.g., 'Electrician').
        city (str): The required city or area.

    Returns:
        dict: {
            'status': 'success' or 'no_results',
            'professionals': list of matching professional dicts,
            'message': description of what was done
        }
    """
    # Query database to find professionals by profession and city
    matching = getProfessionals(profession, city)

    if not matching:
        # FALLBACK 1: If no match in this city, check which other cities have this profession
        cities_with_profession = getCities(profession)
        nearest_cities_result = find_nearest_cities(city, cities_with_profession)
        logger.debug(f'Nearest Cities: {nearest_cities_result}')

        if nearest_cities_result.get('status') == 'success':
            return {
                "status": "cities_found",
                "professionals": [],
                "cities": nearest_cities_result.get('nearest_cities'),
                "message": f"No '{profession}' found in {city}. However, '{profession}' is available in these cities: {nearest_cities_result.get('nearest_cities')}."
            }

        # FALLBACK 2: If no such professionals exist elsewhere, look for any professionals in the same city
        any_professionals = getProfessionals(None, city)

        if any_professionals:
            # Found other types of professionals in the same city
            professions_available = set(p["profession"] for p in any_professionals)
            return {
                "status": "alternate_found",
                "professionals": any_professionals,
                "alternate_professions": list(professions_available),
                "message": f"No '{profession}' found in {city}, but here are other available professions: {', '.join(professions_available)}."
            }

        # No results at all
        return {
            "status": "error",
            "professionals": [],
            "error_message": f"No professionals found matching profession '{profession.lower()}' and city '{city.lower()}'."
        }

    return {
        "status": "success",
        "professionals": matching,
        "message": f"Found {len(matching)} professionals matching '{profession}' in '{city}'."
    }

    
def find_nearest_cities(target_city: str, city_candidates: list, top_n: int = 3):
    """
    Find the closest cities from a given target city based on real geographical coordinates.

    Args:
        target_city (str): The city to compare others against.
        city_candidates (list): List of other candidate cities to compare.
        top_n (int): Number of nearest cities to return.

    Returns:
        dict: {
            'status': 'success' or 'error',
            'nearest_cities': list of (city, distance_km) tuples
        }
    """
    # Combine all unique cities to fetch coordinates at once
    all_cities = list(set([target_city] + city_candidates))
    
    # Fetch coordinates for all involved cities
    coords = fetch_coordinates_for_cities(all_cities)

    # Check if we have the target city's coordinates
    if target_city not in coords:
        return {
            "status": "error",
            "error_message": f"Could not retrieve coordinates for target city: {target_city}"
        }

    target_coord = coords[target_city]

    # Calculate distances
    city_distances = []
    for city in city_candidates:
        if city == target_city:
            continue
        coord = coords.get(city)
        if coord:
            distance = haversine(target_coord, coord)
            city_distances.append((city, round(distance, 2)))

    # Sort by distance
    city_distances.sort(key=lambda x: x[1])

    return {
        "status": "success",
        "nearest_cities": city_distances[:top_n]
    }




# ----------------------
# TOOL 2: get_user_cities
# ----------------------
def get_user_city(user_id: str):
    '''
    Fine the city of one user 

    Args:
        user_id (str): The id of the user 

    Returns:
        city (str): The city of the user
    '''
    return getCity(user_id)

