import requests
import math
import time
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


# Get latitude and longitude for a city name using OpenStreetMap Nominatim API.
def get_city_coordinates(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': city_name,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'HomeRepairAssistant/1.0 (matteo.grisenti@studenti.unitn.it)'  # You should add your contact info
    }
    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    else:
        raise Exception(f"City not found: {city_name}")



#Calculate the great-circle distance between two points (latitude, longitude).
def haversine(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Radius of Earth in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi/2) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in kilometers


# Fetch coordinates for a list of cities in parallel using threading.
def fetch_coordinates_for_cities(city_list, max_workers=5):
    coordinates = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_city = {executor.submit(get_city_coordinates, city): city for city in city_list}

        for future in as_completed(future_to_city):
            city = future_to_city[future]
            coord = future.result()
            if coord:
                coordinates[city] = coord
            else:
                print(f"Coordinates not found for {city}")
    
    return coordinates


def extract_final_response(final_response_text:str):
    # Step 1: Extract JSON block from the response
    json_match = re.search(r"```json\s*(\[.*?\])\s*```", final_response_text, re.DOTALL)

    if json_match:
        try:
            professionals = json.loads(json_match.group(1).strip())  # structured list
        except json.JSONDecodeError as e:
            professionals = []
            # Log or handle the parsing error
    else:
        professionals = []

    # Step 2: Extract the summary (everything before the JSON block)
    if json_match:
        summary = final_response_text.split("```json")[0].strip()
    else:
        summary = final_response_text

    # Step 3: Prepare and return a structured response
    structured_response = {
        "summary": summary,
        "professionals": professionals
    }

    return structured_response