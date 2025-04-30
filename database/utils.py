from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os

# Load the .env file from the parent directory (adjust as needed)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# MongoDB connection URI and database name
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = "test"

# Create MongoDB client and access the database
client = MongoClient(MONGO_URI)
db = client[DB_NAME]


# ----------------------
# FUNCTION: getProfessionals
# ----------------------
def getProfessionals(profession: str = None, location: str = None) -> list:
    """
    Retrieve professionals from the database, optionally filtering by profession and/or location.

    Args:
        profession (str): The profession to filter by (e.g., 'Electrician').
        location (str): The location or city to filter by.

    Returns:
        list: A list of professionals matching the criteria.
        
    """
    collection = db["professionals"]
    query = {}

    # Add profession filter if provided
    if profession:
        query["profession"] = {"$regex": f"^{profession}$", "$options": "i"}

    # Add location filter if provided
    if location:
        query["location"] = {"$regex": f".*{location}.*", "$options": "i"}

    # Execute the query
    response = collection.find(query)
    professionals = []

    for doc in response:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        professionals.append(doc)

    return professionals


# ----------------------
# FUNCTION: getCities
# ----------------------
def getCities(profession: str = None) -> list:
    """
    Retrieve a list of unique cities where professionals are available,
    optionally filtered by profession.

    Args:
        profession (str, optional): Filter by this profession.

    Returns:
        list: A list of unique city names.
    """
    collection = db["professionals"]
    query = {}

    if profession:
        query["profession"] = {"$regex": f"^{profession}$", "$options": "i"}

    cities = collection.distinct("location", query)
    return cities


      