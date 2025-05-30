import os
import uuid
import logging
import bcrypt
import time

from pymongo import MongoClient, errors as pymongo_errors
from dotenv import load_dotenv
from pathlib import Path
from bson import ObjectId
from typing import List


# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# MongoDB connection setup with retry logic
def get_mongodb_connection(max_retries=3, retry_delay=2):
    """
    Establish a connection to MongoDB with retry logic.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retry attempts in seconds
        
    Returns:
        tuple: (client, db) MongoDB client and database objects
        
    Raises:
        Exception: If connection fails after all retries
    """
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            # Try to get URI from environment variables in different formats
            MONGO_URI = os.getenv("MONGODB_URI")
            
            # If not available, try to construct it from components
            if not MONGO_URI:
                MONGO_USERNAME = os.getenv("MONGODB_USERNAME")
                MONGO_PASSWORD = os.getenv("MONGODB_PASSWORD")
                MONGO_HOST = os.getenv("MONGODB_HOST")
                
                if all([MONGO_USERNAME, MONGO_PASSWORD, MONGO_HOST]):
                    MONGO_URI = f'mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}/?retryWrites=true&w=majority'
                else:
                    # Fallback to hardcoded URI if necessary (for backward compatibility)
                    logger.warning("Variabili d'ambiente MongoDB non trovate. Utilizzo configurazione di fallback.")
                    MONGO_PASSWORD = os.getenv("MONGODB_PASSWORD", "unitn2025")
                    MONGO_URI = f'mongodb+srv://marco:{MONGO_PASSWORD}@dlsais-cluster.vkxu2tc.mongodb.net/?retryWrites=true&w=majority&appName=dlsais-cluster'
            
            DB_NAME = os.getenv("MONGODB_DB_NAME", "dev")
            
            # Connection with timeout to avoid blocking
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')  # Test connection
            db = client[DB_NAME]
            
            logger.info(f"Connessione MongoDB stabilita con successo al database: {DB_NAME}")
            return client, db
            
        except pymongo_errors.ServerSelectionTimeoutError as e:
            retry_count += 1
            last_error = e
            logger.warning(f"Tentativo {retry_count}/{max_retries} fallito: {e}")
            if retry_count < max_retries:
                time.sleep(retry_delay)
                
        except (pymongo_errors.ConnectionFailure, pymongo_errors.OperationFailure) as e:
            last_error = e
            logger.error(f"Errore di connessione MongoDB: {e}")
            break
    
    # If we've exhausted retries or hit a fatal error
    error_message = f"Impossibile connettersi a MongoDB dopo {retry_count} tentativi: {last_error}"
    logger.error(error_message)
    raise Exception(error_message)




# Try to establish the connection
try:
    mongo_client, db = get_mongodb_connection()
except Exception as e:
    logger.error(f"Errore fatale nella connessione al database: {e}")
    # Don't raise the exception here to allow the module to be imported 
    # Set db to None, individual functions will handle this case
    db = None




# ------------------------------------------ Professional ------------------------------------------------
# ----------------------
# FUNCTION: getProfessionals
# ----------------------
def getProfessionals(profession: str = None, city: str = None) -> List[dict]:
    """
    Retrieve professionals from the database, optionally filtering by profession and/or city.

    Args:
        profession (str): The profession to filter by (e.g., 'Electrician').
        city (str): The city name to filter by.

    Returns:
        list: A list of professionals matching the criteria.
    """
    try:
        # Verify db connection is available
        if db is None:
            logger.error("Database connection not available in getProfessionals")
            return []

        collection = db["professionals"]
        query = {}

        # Add profession filter if provided (case-insensitive exact match)
        if profession:
            query["profession"] = {"$regex": f"^{profession}$", "$options": "i"}

        # Add city filter if provided (search in location.city)
        if city:
            query["location.city"] = {"$regex": city, "$options": "i"}

        # Execute the query
        response = collection.find(query, {"password": 0})
        professionals = []

        for doc in response:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            professionals.append(doc)

        logger.debug(f"Found {len(professionals)} professionals - Profession: {profession}, City: {city}")
        return professionals

    except Exception as e:
        logger.error(f"Error retrieving professionals: {e}")
        return []




# ------------------------------------------ Location ----------------------------------------------------
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
    try:
        # Verify db connection is available
        if db is None:
            logger.error("Database connection not available in getCities")
            return []

        collection = db["professionals"]
        query = {}

        # Add profession filter if provided
        if profession:
            query["profession"] = {"$regex": f"^{profession}$", "$options": "i"}

        # Get all distinct 'location.city' values matching the query
        locations = collection.distinct("location.city", query)

        # Remove None or empty values
        unique_cities = list(set(city for city in locations if city))

        logger.debug(f"Found {len(unique_cities)} unique cities for profession: {profession}")
        return unique_cities

    except Exception as e:
        logger.error(f"Error in getCities: {e}")
        return []

def getCity(user_id: str) -> str:
    '''
    Retrieve the city of the specified user from the database.

    Args:
        user_id (str): The ID of the user whose city is to be retrieved.

    Returns:
        str: The name of the city if found, otherwise an empty string.
    '''
    try:
        # Verify db connection is available
        if db is None:
            logger.error("Database connection not available in getCity")
            return ""

        collection = db["users"]

        # Find the user by ID (case-insensitive regex match)
        user = collection.find_one(
            {"_id": ObjectId(user_id)},
            {"location": 1}
        )

        if not user:
            logger.info(f"No user found for {user_id}")
            return "No city founded in the database"
        
        if "location" not in user:
            logger.info(f"No location found for user {user_id}")
            return "No city founded in the database"

        city = user["location"].get("city")
        if not city:
            logger.info(f"Location exists, but 'city' is missing for user {user_id}")

        logger.info(f"{city} is the city of user {user_id}")
        return city

    except Exception as e:
        logger.error(f"Error in getCity: {e}", exc_info=True)
        return "Error, no city founded in the database"




# ------------------------------------------ User ----------------------------------------------------
# ----------------------
# FUNCTION: getUSer
# ----------------------
def getUser(user_id: str, fields: list = None) -> dict:
    """
    Fetch a user by ID with optional field filtering and population of trust network.

    Args:
        user_id (str): ID of the user to fetch.
        fields (list, optional): List of fields to include in the result. Defaults to None (all fields).

    Returns:
        dict: User document with optional population, or None if not found.
    """
    # Verify db connection is available
    if db is None:
        logger.error("Database connection not available in getCity")
        return ""
    
    logger.info(f'Requested field: {fields}')

    collection = db["users"]

    query = {"_id": ObjectId(user_id)}
    projection = {field: 1 for field in fields} if fields else None

    user = collection.find_one(query, projection)

    logger.info(f"Raw DB result for user {user_id}: {user}")

    if not user:
        logger.warning(f"No user found with ID: {user_id}")
        return None

    return user


# ----------------------
# FUNCTION: registerUser
# ----------------------
def registerUser(
    name: str,
    email: str,
    password: str,
    phone: str,
    city: str = None,
    zipCode: str = None,
    diy_skills: list = None,
    diy_tools: list = None
) -> dict:
    """
    Register a new user in the database with extended profile fields.

    Returns:
        dict: Result of the registration (success/failure + message).
    """
    try:
        # Verify db connection is available
        if db is None:
            logger.error("Database connection not available in registerUser")
            return {"success": False, "message": "Database connection error"}
            
        collection = db["users"]

        if collection.find_one({"email": email}):
            return {"success": False, "message": "Email already registered"}

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_data = {
            "name": name,
            "email": email,
            "password": hashed_pw,
            "phone": phone,
            "location": {
                "city": city or "",
                "zipCode": zipCode or ""
            },
            "diy_preference": {
                "diy_skills": diy_skills or [],
                "diy_tools": diy_tools or []
            },
            "trusted_professionals": [],  # Initialize empty
            "trusted_users": [],          # Initialize empty
            "feedbacks": [],              # Initialize empty
            "sessions": []                # Already existing field
        }

        result = collection.insert_one(user_data)
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": str(result.inserted_id)
        }
    
    except pymongo_errors.PyMongoError as e:
        logger.error(f"Database error during user registration: {e}")
        return {"success": False, "message": f"Database error: {e}"}
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {e}")
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
        # Verify db connection is available
        if db is None:
            logger.error("Database connection not available in loginUser")
            return {"success": False, "message": "Database connection error"}
            
        collection = db["users"]
        user = collection.find_one({"email": email})

        if not user:
            return {"success": False, "message": "Invalid email or password"}

        # Ensure user has a sessions array
        if "sessions" not in user:
            collection.update_one({"_id": user["_id"]}, {"$set": {"sessions": []}})
            user["sessions"] = []

        if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            user_data = {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "phone": user["phone"],
                "sessions": user.get("sessions", [])
            }
            return {"success": True, "message": "Login successful", "user": user_data}
        else:
            return {"success": False, "message": "Invalid email or password"}
    except pymongo_errors.PyMongoError as e:
        logger.error(f"Errore database durante il login: {e}")
        return {"success": False, "message": f"Database error: {e}"}
    except Exception as e:
        logger.error(f"Errore imprevisto durante il login: {e}")
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
        # Verify db connection is available
        if db is None:
            logger.error("Database connection not available in createUserSession")
            return {"success": False, "message": "Database connection error"}
            
        # Validate user_id as a MongoDB ObjectId
        if not ObjectId.is_valid(user_id):
            logger.error(f"ID utente non valido: {user_id}")
            return {"success": False, "message": "Invalid user ID format"}

        collection = db["users"]
        session_id = str(uuid.uuid4())

        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"sessions": session_id}}
        )

        if result.matched_count == 0:
            logger.error(f"Utente non trovato con ID: {user_id}")
            return {"success": False, "message": "User not found"}

        return {"success": True, "session_id": session_id}
    
    except pymongo_errors.PyMongoError as e:
        logger.error(f"Errore database durante la creazione della sessione: {e}")
        return {"success": False, "message": f"Database error: {e}"}
    except Exception as e:
        logger.error(f"Errore imprevisto durante la creazione della sessione: {e}")
        return {"success": False, "message": f"Unexpected error: {e}"}