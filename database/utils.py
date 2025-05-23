import os
import uuid
import bcrypt

from pymongo import MongoClient, errors as pymongo_errors
from dotenv import load_dotenv
from pathlib import Path
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# MongoDB connection setup
# MONGO_URI = os.getenv("MONGODB_URI")      # NON MI VA BOH (matteo) # perchè usa MONGO_URI (gian)

# Leggi direttamente la connessione completa
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("⚠️ MONGO_URI non trovata nel file .env: assicurati di avere MONGO_URI nel .env alla root.")

# Imposta il nome del database (opzionale: puoi spostarlo in env come DB_NAME)
DB_NAME = os.getenv("MONGO_DB_NAME", "test")

# Connessione a MongoDB
try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')  # Test connection
    db = client[DB_NAME]
except pymongo_errors.PyMongoError as e:
    raise RuntimeError(f"Failed to connect to MongoDB: {e}") from e





# -----------------------------------------------------------------------------------------------------------
# PROFESSIONAL DATABASE FUNCTIONS
# -----------------------------------------------------------------------------------------------------------
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




# ---------------------------------------------------------------------------------------------------------
# USER DATABASE FUNCTIONS
# ---------------------------------------------------------------------------------------------------------
def registerUser(name: str, email: str, password: str, phone: str) -> dict:
    """
    Register a new user in the database.

    Returns:
        dict: Result of the registration (success/failure + message).
    """
    try:
        collection = db["users"]

        if collection.find_one({"email": email}):
            return {"success": False, "message": "Email already registered"}

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_data = {
            "name": name,
            "email": email,
            "password": hashed_pw,
            "phone": phone
        }

        result = collection.insert_one(user_data)
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": str(result.inserted_id)
        }
    except pymongo_errors.PyMongoError as e:
        return {"success": False, "message": f"Database error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


def loginUser(email: str, password: str) -> dict:
    """
    Authenticate a user by email and password.

    Returns:
        dict: Result of the login (success/failure, message, and optionally user data).
    """
    try:
        collection = db["users"]
        user = collection.find_one({"email": email})

        if not user:
            return {"success": False, "message": "Invalid email or password"}

        if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            user_data = {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "phone": user["phone"],
                "sessions": user["sessions"]
            }
            return {"success": True, "message": "Login successful", "user": user_data}
        else:
            return {"success": False, "message": "Invalid email or password"}
    except pymongo_errors.PyMongoError as e:
        return {"success": False, "message": f"Database error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


# ----------------------
# FUNCTION: createUserSession
# ----------------------
def createUserSession(user_id: str) -> dict:
    """
    Generate and store a new session ID for a user.

    Returns:
        dict: Includes success status, session ID, and optional message.
    """
    try:
        # Validate user_id as a MongoDB ObjectId
        if not ObjectId.is_valid(user_id):
            return {"success": False, "message": "Invalid user ID format"}

        collection = db["users"]
        session_id = str(uuid.uuid4())

        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"sessions": session_id}}
        )

        if result.matched_count == 0:
            return {"success": False, "message": "User not found"}

        return {"success": True, "session_id": session_id}
    
    except pymongo_errors.PyMongoError as e:
        return {"success": False, "message": f"Database error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}
    



# ---------------------------------------------------------------------------------------------------------
# SESSIONS DATABASE FUNCTIONS
# ---------------------------------------------------------------------------------------------------------
def get_mongo_collection(collection_name: str = "sessions") -> MongoClient:
    db = client[DB_NAME]
    collection = db[collection_name]

    # Ensure index on _id for fast access
    collection.create_index([("_id", 1)], name="session_id_index")

    return collection


def create_session_in_db(
    session_id: str,
    app_name: str,
    user_id: str,
    state: dict,
) -> dict:
    collection = get_mongo_collection("sessions")
    now = datetime.now(timezone.utc).timestamp()

    session_data = {
        "_id": session_id,
        "app_name": app_name,
        "user_id": user_id,
        "state": state,
        "events": [],
        "created_at": now,
        "updated_at": now
    }

    collection.insert_one(session_data)
    return session_data


def get_session_from_db(
    session_id: str,
    app_name: str,
    user_id: str,
    num_recent_events: Optional[int] = None,
) -> Optional[dict]:
    collection = get_mongo_collection("sessions")
    doc = collection.find_one({"_id": session_id})
    if not doc or doc["app_name"] != app_name or doc["user_id"] != user_id:
        return None

    if num_recent_events:
        doc["events"] = doc.get("events", [])[-num_recent_events:]

    return doc


def list_sessions_for_user(app_name: str, user_id: str) -> List[dict]:
    collection = get_mongo_collection("sessions")
    docs = collection.find({
        "app_name": app_name,
        "user_id": user_id
    })
    return list(docs)


def delete_session_from_db(session_id: str, app_name: str, user_id: str):
    collection = get_mongo_collection("sessions")
    collection.delete_one({
        "_id": session_id,
        "app_name": app_name,
        "user_id": user_id
    })


def list_events_from_db(session_id: str, app_name: str, user_id: str) -> List[Dict[str, Any]]:
    collection = get_mongo_collection("sessions")
    doc = collection.find_one({
        "_id": session_id,
        "app_name": app_name,
        "user_id": user_id
    })

    return doc.get("events", []) if doc else []


def append_event_to_db(session_id: str, event: dict, updated_state: dict):
    collection = get_mongo_collection("sessions")
    sanitized_event = sanitize_mongo_input(event)

    collection.update_one(
        {"_id": session_id},
        {
            "$push": {"events": sanitized_event},
            "$set": {
                "state": updated_state,
                "updated_at": datetime.now(timezone.utc).timestamp()
            }
        }
    )


def sanitize_mongo_input(data):
    """
    Recursively converts unsupported types to MongoDB-compatible ones.
    - Converts sets to lists
    - Removes None values from dicts (optional)
    """
    if isinstance(data, dict):
        return {
            key: sanitize_mongo_input(value)
            for key, value in data.items()
            if value is not None
        }
    elif isinstance(data, list):
        return [sanitize_mongo_input(item) for item in data]
    elif isinstance(data, set):
        return [sanitize_mongo_input(item) for item in data]
    else:
        return data