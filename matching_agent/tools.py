from mock_database import professionals


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
    matching = []

    for pro in professionals:
        if (
            profession.lower() == pro.get("profession", "").lower() and
            location.lower() in pro.get("location", "").lower()
        ):
            matching.append(pro)

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
        list: A list of alternative cities where the searched profession is available.
    """

    # Filter professionals by profession
    matching_professionals = [p for p in professionals if p["profession"].lower() == profession.lower()]

    # Filter unique cities from the matching professionals
    available_cities = list({p["location"] for p in matching_professionals})

    return available_cities



