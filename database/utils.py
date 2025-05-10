from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
import bcrypt

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



# ----------------------
# FUNCTION: registerUser
# ----------------------
def registerUser(name: str, email: str, password: str, phone: str) -> dict:
    """
    Register a new user in the database.

    Args:
        name (str): Full name of the user.
        email (str): Email address (must be unique).
        password (str): Plaintext password (will be hashed).
        phone (str): Phone number.

    Returns:
        dict: Result of the registration (success/failure + message).
    """
    collection = db["users"]

    # Check for existing email
    if collection.find_one({"email": email}):
        return {"success": False, "message": "Email already registered"}

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user_data = {
        "name": name,
        "email": email,
        "password": hashed_pw,
        "phone": phone
    }

    try:
        collection.insert_one(user_data)
        return {"success": True, "message": "User registered successfully"}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}


# ----------------------
# FUNCTION: loginUser
# ----------------------
def loginUser(email: str, password: str) -> dict:
    """
    Authenticate a user by email and password.

    Args:
        email (str): The user's email address.
        password (str): The plaintext password provided at login.

    Returns:
        dict: Result of the login (success/failure, message, and optionally user data).
    """
    collection = db["users"]

    # Fetch user by email
    user = collection.find_one({"email": email})
    if not user:
        return {"success": False, "message": "Invalid email or password"}

    # Verify password
    if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        user_data = {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"]
        }
        return {"success": True, "message": "Login successful", "user": user_data}
    else:
        return {"success": False, "message": "Invalid email or password"}
