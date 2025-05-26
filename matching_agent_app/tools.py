from dataclasses import field
import logging
import pprint

from database.utils import getProfessionals, getCities, getCity, getUser
from matching_agent_app.utils import haversine, fetch_coordinates_for_cities

# Setup basic logging to help debug and trace execution flow
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# ----------------------
# TOOL 1: find_professionals
# ----------------------
def find_professionals(profession: str, city: str, user_id: str) -> dict:
    """
    Find professionals based on profession and location match, including trust network insights.

    Args:
        profession (str): The required profession (e.g., 'Electrician').
        city (str): The required city or area.
        user_id (str): The ID of the user performing the search.

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
    
    # Get the trust network fot he user
    user_data = getUser(user_id, fields=['trusted_professionals', 'trusted_users'])
    #DEBUG logger.info(f'user_data: {user_data}')

    trusted_professionals_ids = user_data['trusted_professionals']
    trusted_users_ids = user_data['trusted_users']
    #DEBUG logger.info(f'trusted professionals: {trusted_professionals_ids}')
    #DEBUG logger.info(f'trusted users: {trusted_users_ids}')

    # Update the founded matching with the information of the trust network
    matching = annotate_network_trust(matching, trusted_professionals_ids, trusted_users_ids)

    return {
        "status": "success",
        "professionals": matching,
        "message": f"Found {len(matching)} professionals matching '{profession}' in '{city}'."
    }


def annotate_network_trust(pro_list, trusted_professionals_ids, trusted_users_ids):
    """
    Annotates a list of professionals (`pro_list`) with trust information based on the network of trusted users.

    Specifically:
    - Marks if the current user trusts the professional (`trusted_by_you`).
    - Lists other users who trust that professional (`trusted_by`).

    Parameters:
        pro_list (list): List of professional dictionaries (each with at least '_id').
        trusted_professionals_ids (set or list): IDs of professionals trusted by the current user.
        trusted_users_ids (list): IDs of users whose trust relationships we should consider.

    Returns:
        list: Updated `pro_list` with `trusted_by_you` and `trusted_by` fields added where applicable.
    """

    # Dictionary mapping each professional ID (as string) to a list of users who trust them
    # Format: { "prof_id": [ {"user_id": "...", "name": "..."}, ... ] }
    trusted_by_map = {}

    # Iterate through all trusted users to build the trust map
    for trusted_user_id in trusted_users_ids:
        # Fetch basic info about this trusted user, including their list of trusted professionals
        trusted_user_data = getUser(trusted_user_id, fields=['name', 'trusted_professionals'])

        # Extract the list of professional IDs trusted by this user
        trusted_professionals_ids_by_trusted_user = trusted_user_data.get('trusted_professionals')
        
        # For each professional trusted by this user, record that this user trusts them
        for tp in trusted_professionals_ids_by_trusted_user:
            tp_id = str(tp)
            if tp_id not in trusted_by_map:
                trusted_by_map[tp_id] = []
            trusted_by_map[tp_id].append({
                "name": trusted_user_data['name']
            })

    # Annotate each professional in the input list with trust information
    for prof in pro_list:
        prof_id = str(prof['_id'])

        # Check if the current user trusts this professional
        if prof_id in trusted_professionals_ids:
            prof["trusted_by_you"] = True
        else:
            prof["trusted_by_you"] = False

        # Check if any other users trust this professional
        if prof_id in trusted_by_map:
            prof["trusted_by"] =  trusted_by_map.get(prof_id, [])
        else:
            prof["trusted_by"] = []

    return pro_list

    
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

