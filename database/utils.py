import os
import uuid
import bcrypt

from pymongo import MongoClient, errors as pymongo_errors
from dotenv import load_dotenv
from pathlib import Path
from bson import ObjectId
from bson.errors import InvalidId


# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# MongoDB connection setup
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = "test"

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')  # Test connection
    db = client[DB_NAME]
except pymongo_errors.ConnectionFailure as e:
    raise RuntimeError(f"Failed to connect to MongoDB: {e}") from e


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


# ----------------------
# FUNCTION: registerUser
# ----------------------
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


# ----------------------
# FUNCTION: loginUser
# ----------------------
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
    
    except errors.PyMongoError as e:
        return {"success": False, "message": f"Database error: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}