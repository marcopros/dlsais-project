import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from dotenv import load_dotenv
import logging
import random
import uuid

# Load environment variables
load_dotenv()

# Configura il logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection settings
# Try loading from environment variables, otherwise use defaults
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DB_NAME", "appointment_db")

# Collections - allineate con i nomi definiti nei modelli Mongoose
USERS_COLLECTION = "users"  # Corrisponde a mongoose.model('User', userSchema)
PROFESSIONALS_COLLECTION = "professionals"  # Corrisponde a mongoose.model('Professional', ProfessionalSchema)
APPOINTMENTS_COLLECTION = "appointments"  # Corrisponde a mongoose.model('Appointment', appointmentSchema)
AVAILABILITY_COLLECTION = "availability"  # Non esiste un modello dedicato ma la usiamo per gestire le disponibilità

# In-memory database class for fallback
class InMemoryDB:
    def __init__(self):
        self.collections = {
            AVAILABILITY_COLLECTION: [],
            APPOINTMENTS_COLLECTION: [],
            USERS_COLLECTION: [],
            PROFESSIONALS_COLLECTION: []
        }
    
    def insert_one(self, collection_name, document):
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        self.collections[collection_name].append(document)
        return InsertOneResult(document["_id"])
    
    def find_one(self, collection_name, query):
        for doc in self.collections[collection_name]:
            if self._matches_query(doc, query):
                return doc
        return None
    
    def find(self, collection_name, query):
        return [doc for doc in self.collections[collection_name] if self._matches_query(doc, query)]
    
    def update_many(self, collection_name, query, update):
        modified_count = 0
        for doc in self.collections[collection_name]:
            if self._matches_query(doc, query):
                # Handle $pull operator
                if "$pull" in update:
                    for field, value in update["$pull"].items():
                        if field in doc and isinstance(doc[field], list):
                            if value in doc[field]:
                                doc[field].remove(value)
                                modified_count += 1
                # Add other update operators as needed
                
        return UpdateResult(modified_count)
    
    def _matches_query(self, doc, query):
        for key, value in query.items():
            if key not in doc:
                return False
            
            if isinstance(value, dict):
                # Handle operators like $exists, $gte, $lte
                for op, op_value in value.items():
                    if op == "$exists":
                        if op_value and key not in doc:
                            return False
                        if not op_value and key in doc:
                            return False
                    elif op == "$gte":
                        if doc[key] < op_value:
                            return False
                    elif op == "$lte":
                        if doc[key] > op_value:
                            return False
            else:
                # Direct value comparison
                if doc[key] != value:
                    return False
        
        return True

class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class UpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count

# Flag to track if we're using MongoDB or in-memory
using_mongodb = False

# Initialize database (MongoDB or in-memory)
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Verify connection
    client.admin.command('ping')
    db = client[DB_NAME]
    using_mongodb = True
    print("Connected to MongoDB successfully!")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"MongoDB Connection Error: {str(e)}")
    # Initialize in-memory database
    in_memory_db = InMemoryDB()
    db = {}
    for collection in [AVAILABILITY_COLLECTION, APPOINTMENTS_COLLECTION, USERS_COLLECTION, PROFESSIONALS_COLLECTION]:
        db[collection] = []
    print("Using in-memory database instead of MongoDB...")

# Function to create availability entries for professionals if they don't exist
def ensure_professional_availability(professional_id):
    """
    Ensure a professional has availability slots. Create them if they don't exist.
    
    Args:
        professional_id (str): Professional ID
        
    Returns:
        bool: True if availability exists or was created, False otherwise
    """
    try:
        start_date = datetime.now()
        end_date = start_date + timedelta(days=14)  # Create availability for next 14 days
        
        # Check if availability exists
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        if using_mongodb:
            # MongoDB query to find availability
            query = {
                "entity_id": professional_id,
                "entity_type": "professional",
                "$or": [
                    {"date_range": {"$exists": True}},
                    {"date": {"$gte": start_str, "$lte": end_str}}
                ]
            }
            
            availability_docs = list(db[AVAILABILITY_COLLECTION].find(query))
            
            # Check if docs have slots
            has_slots = False
            for doc in availability_docs:
                if "slots" in doc and doc["slots"]:
                    has_slots = True
                    break
                
            # If no slots exist, create them
            if not has_slots:
                logger.info(f"No availability found for professional {professional_id}. Creating mock availability.")
                
                # Generate mock slots and insert into MongoDB
                current_date = start_date
                while current_date <= end_date:
                    # Generate slots for every day including weekends
                    if current_date.weekday() < 5:  # Monday to Friday
                        num_slots = random.randint(5, 8)  # More slots on weekdays
                    else:
                        num_slots = random.randint(3, 5)  # Fewer slots on weekends
                    
                    date_slots = []
                    for _ in range(num_slots):
                        hour = random.randint(8, 18)  # 8 AM to 6 PM
                        minute = random.choice([0, 30])  # Either on the hour or half hour
                        
                        slot_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        slot_str = slot_time.strftime('%Y-%m-%d %H:%M')
                        date_slots.append(slot_str)
                    
                    # Insert document for this day
                    date_str = current_date.strftime('%Y-%m-%d')
                    doc = {
                        "_id": str(uuid.uuid4()),
                        "entity_id": professional_id,
                        "entity_type": "professional",
                        "date": date_str,
                        "slots": date_slots
                    }
                    db[AVAILABILITY_COLLECTION].insert_one(doc)
                    
                    current_date += timedelta(days=1)
                
                logger.info(f"Created availability slots for professional {professional_id}")
                return True
        else:
            # In-memory database logic
            # First try finding the date range document
            availability = None
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == professional_id and 
                    doc.get("entity_type") == "professional" and
                    "date_range" in doc):
                    availability = doc
                    break
            
            # If no date range document exists, try finding individual day documents
            if not availability:
                day_docs = []
                for doc in db[AVAILABILITY_COLLECTION]:
                    if (doc.get("entity_id") == professional_id and 
                        doc.get("entity_type") == "professional" and
                        doc.get("date", "") >= start_str and
                        doc.get("date", "") <= end_str):
                        day_docs.append(doc)
                
                has_slots = False
                for doc in day_docs:
                    if "slots" in doc and doc["slots"]:
                        has_slots = True
                        break
                
                # If no slots exist, create them
                if not has_slots:
                    logger.info(f"No availability found for professional {professional_id}. Creating mock availability.")
                    
                    # Generate mock slots
                    current_date = start_date
                    while current_date <= end_date:
                        # Generate slots for every day including weekends
                        if current_date.weekday() < 5:  # Monday to Friday
                            num_slots = random.randint(5, 8)  # More slots on weekdays
                        else:
                            num_slots = random.randint(3, 5)  # Fewer slots on weekends
                        
                        date_slots = []
                        for _ in range(num_slots):
                            hour = random.randint(8, 18)  # 8 AM to 6 PM
                            minute = random.choice([0, 30])  # Either on the hour or half hour
                            
                            slot_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            slot_str = slot_time.strftime('%Y-%m-%d %H:%M')
                            date_slots.append(slot_str)
                        
                        # Insert document for this day
                        date_str = current_date.strftime('%Y-%m-%d')
                        doc = {
                            "_id": str(uuid.uuid4()),
                            "entity_id": professional_id,
                            "entity_type": "professional",
                            "date": date_str,
                            "slots": date_slots
                        }
                        db[AVAILABILITY_COLLECTION].append(doc)
                        
                        current_date += timedelta(days=1)
                    
                    logger.info(f"Created availability slots for professional {professional_id}")
                    return True
        
        return True
    
    except Exception as e:
        logger.error(f"Error ensuring professional availability: {str(e)}")
        return False

# Function to create availability entries for users if they don't exist
def ensure_user_availability(user_id):
    """
    Ensure a user has availability slots. Create them if they don't exist.
    
    Args:
        user_id (str): User ID
        
    Returns:
        bool: True if availability exists or was created, False otherwise
    """
    try:
        start_date = datetime.now()
        end_date = start_date + timedelta(days=14)  # Create availability for next 14 days
        
        # Check if availability exists
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        if using_mongodb:
            # MongoDB query to find availability
            query = {
                "entity_id": user_id,
                "entity_type": "user",
                "$or": [
                    {"date_range": {"$exists": True}},
                    {"date": {"$gte": start_str, "$lte": end_str}}
                ]
            }
            
            availability_docs = list(db[AVAILABILITY_COLLECTION].find(query))
            
            # Check if docs have slots
            has_slots = False
            for doc in availability_docs:
                if "slots" in doc and doc["slots"]:
                    has_slots = True
                    break
                
            # If no slots exist, create them
            if not has_slots:
                logger.info(f"No availability found for user {user_id}. Creating mock availability.")
                
                # Generate mock slots and insert into MongoDB
                current_date = start_date
                while current_date <= end_date:
                    # Skip weekends in this example
                    if current_date.weekday() < 5:  # Monday to Friday
                        # Generate slots for weekdays
                        num_slots = random.randint(4, 6)
                        
                        date_slots = []
                        for _ in range(num_slots):
                            hour = random.randint(9, 19)  # 9 AM to 7 PM
                            minute = random.choice([0, 30])  # Either on the hour or half hour
                            
                            slot_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            slot_str = slot_time.strftime('%Y-%m-%d %H:%M')
                            date_slots.append(slot_str)
                        
                        # Insert document for this day
                        date_str = current_date.strftime('%Y-%m-%d')
                        doc = {
                            "_id": str(uuid.uuid4()),
                            "entity_id": user_id,
                            "entity_type": "user",
                            "date": date_str,
                            "slots": date_slots
                        }
                        db[AVAILABILITY_COLLECTION].insert_one(doc)
                    
                    current_date += timedelta(days=1)
                
                logger.info(f"Created availability slots for user {user_id}")
                return True
        else:
            # In-memory database logic
            # First try finding the date range document
            availability = None
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == user_id and 
                    doc.get("entity_type") == "user" and
                    "date_range" in doc):
                    availability = doc
                    break
            
            # If no date range document exists, try finding individual day documents
            if not availability:
                day_docs = []
                for doc in db[AVAILABILITY_COLLECTION]:
                    if (doc.get("entity_id") == user_id and 
                        doc.get("entity_type") == "user" and
                        doc.get("date", "") >= start_str and
                        doc.get("date", "") <= end_str):
                        day_docs.append(doc)
                
                has_slots = False
                for doc in day_docs:
                    if "slots" in doc and doc["slots"]:
                        has_slots = True
                        break
                
                # If no slots exist, create them
                if not has_slots:
                    logger.info(f"No availability found for user {user_id}. Creating mock availability.")
                    
                    # Generate mock slots
                    current_date = start_date
                    while current_date <= end_date:
                        # Skip weekends in this example
                        if current_date.weekday() < 5:  # Monday to Friday
                            # Generate slots for weekdays
                            num_slots = random.randint(4, 6)
                            
                            date_slots = []
                            for _ in range(num_slots):
                                hour = random.randint(9, 19)  # 9 AM to 7 PM
                                minute = random.choice([0, 30])  # Either on the hour or half hour
                                
                                slot_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                slot_str = slot_time.strftime('%Y-%m-%d %H:%M')
                                date_slots.append(slot_str)
                            
                            # Insert document for this day
                            date_str = current_date.strftime('%Y-%m-%d')
                            doc = {
                                "_id": str(uuid.uuid4()),
                                "entity_id": user_id,
                                "entity_type": "user",
                                "date": date_str,
                                "slots": date_slots
                            }
                            db[AVAILABILITY_COLLECTION].append(doc)
                        
                        current_date += timedelta(days=1)
                    
                    logger.info(f"Created availability slots for user {user_id}")
                    return True
                
        return True
    
    except Exception as e:
        logger.error(f"Error ensuring user availability: {str(e)}")
        return False

def get_user_availability(user_id, start_date, end_date):
    """
    Get user availability from the database.
    
    Args:
        user_id (str): User ID
        start_date (datetime): Start date for availability check
        end_date (datetime): End date for availability check
        
    Returns:
        list: List of available datetime slots
    """
    try:
        # Ensure user has availability data
        ensure_user_availability(user_id)
        
        # Convert dates to string format for query
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        if using_mongodb:
            # MongoDB query for date range document
            range_query = {
                "entity_id": user_id,
                "entity_type": "user",
                "date_range": {"$exists": True}
            }
            
            date_range_doc = db[AVAILABILITY_COLLECTION].find_one(range_query)
            
            if date_range_doc and "slots" in date_range_doc:
                # Filter slots that are within our date range
                filtered_slots = [
                    slot for slot in date_range_doc["slots"] 
                    if slot >= f"{start_str} 00:00" and slot <= f"{end_str} 23:59"
                ]
                return filtered_slots
            
            # If no date range document, try finding individual day documents
            day_query = {
                "entity_id": user_id,
                "entity_type": "user",
                "date": {"$gte": start_str, "$lte": end_str}
            }
            
            day_docs = list(db[AVAILABILITY_COLLECTION].find(day_query))
            
            all_slots = []
            for doc in day_docs:
                if "slots" in doc:
                    all_slots.extend(doc["slots"])
            
            return all_slots
        
        else:
            # In-memory database logic
            # First try finding the date range document
            availability = None
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == user_id and 
                    doc.get("entity_type") == "user" and
                    "date_range" in doc):
                    availability = doc
                    break
            
            if availability and "slots" in availability:
                # Filter slots that are within our date range
                filtered_slots = [
                    slot for slot in availability["slots"] 
                    if slot >= f"{start_str} 00:00" and slot <= f"{end_str} 23:59"
                ]
                return filtered_slots
            
            # If no date range document, try finding individual day documents
            all_slots = []
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == user_id and 
                    doc.get("entity_type") == "user" and
                    doc.get("date", "") >= start_str and
                    doc.get("date", "") <= end_str and
                    "slots" in doc):
                    all_slots.extend(doc["slots"])
            
            return all_slots
    
    except Exception as e:
        logger.error(f"Database error in get_user_availability: {str(e)}")
        raise Exception(f"Error retrieving user availability: {str(e)}")

def get_professional_availability(professional_id, start_date, end_date):
    """
    Get professional availability from the database.
    
    Args:
        professional_id (str): Professional ID
        start_date (datetime): Start date for availability check
        end_date (datetime): End date for availability check
        
    Returns:
        list: List of available datetime slots
    """
    try:
        # Ensure professional has availability data
        ensure_professional_availability(professional_id)
        
        # Convert dates to string format for query
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        if using_mongodb:
            # MongoDB query for date range document
            range_query = {
                "entity_id": professional_id,
                "entity_type": "professional",
                "date_range": {"$exists": True}
            }
            
            date_range_doc = db[AVAILABILITY_COLLECTION].find_one(range_query)
            
            if date_range_doc and "slots" in date_range_doc:
                # Filter slots that are within our date range
                filtered_slots = [
                    slot for slot in date_range_doc["slots"] 
                    if slot >= f"{start_str} 00:00" and slot <= f"{end_str} 23:59"
                ]
                return filtered_slots
            
            # If no date range document, try finding individual day documents
            day_query = {
                "entity_id": professional_id,
                "entity_type": "professional",
                "date": {"$gte": start_str, "$lte": end_str}
            }
            
            day_docs = list(db[AVAILABILITY_COLLECTION].find(day_query))
            
            all_slots = []
            for doc in day_docs:
                if "slots" in doc:
                    all_slots.extend(doc["slots"])
            
            return all_slots
        
        else:
            # In-memory database logic
            # First try finding the date range document
            availability = None
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == professional_id and 
                    doc.get("entity_type") == "professional" and
                    "date_range" in doc):
                    availability = doc
                    break
            
            if availability and "slots" in availability:
                # Filter slots that are within our date range
                filtered_slots = [
                    slot for slot in availability["slots"] 
                    if slot >= f"{start_str} 00:00" and slot <= f"{end_str} 23:59"
                ]
                return filtered_slots
            
            # If no date range document, try finding individual day documents
            all_slots = []
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == professional_id and 
                    doc.get("entity_type") == "professional" and
                    doc.get("date", "") >= start_str and
                    doc.get("date", "") <= end_str and
                    "slots" in doc):
                    all_slots.extend(doc["slots"])
            
            return all_slots
    
    except Exception as e:
        logger.error(f"Database error in get_professional_availability: {str(e)}")
        raise Exception(f"Error retrieving professional availability: {str(e)}")

def create_appointment(appointment_details):
    """
    Create a new appointment in the database.

    Args:
        appointment_details (dict): Details of the appointment
                                    Expected keys: 'user_id', 'professional_id', 'datetime', 'issue', 'notes' (optional)

    Returns:
        str: ID of the created appointment, or None if failed
    """
    try:
        # Get user details to retrieve location
        user_id = appointment_details.get("user_id")
        user = get_user_details(user_id)

        location_data = {"city": "Unknown", "zipCode": "Unknown"}
        if user and "location" in user and isinstance(user["location"], dict):
             location_data = {
                 "city": user["location"].get("city", "Unknown"),
                 "zipCode": user["location"].get("zipCode", "Unknown")
             }
        elif user and "location" in user and isinstance(user["location"], str):
             # Handle case where location is a string, try to parse city/zip
             # This is a basic attempt; more robust parsing might be needed
             location_str = user["location"]
             city = location_str.split(',')[0].strip() if ',' in location_str else location_str.strip()
             zip_code = "" # Cannot reliably extract zip from a simple string without more context
             location_data = {"city": city, "zipCode": zip_code}


        # Convert datetime string to datetime object
        scheduled_time_obj = datetime.strptime(appointment_details["datetime"], '%Y-%m-%d %H:%M')

        # Calculate confirmation deadline (e.g., 24 hours before scheduled time)
        # This is an example; adjust logic as needed
        confermation_dead_line_obj = scheduled_time_obj - timedelta(hours=24)

        # Prepare data according to Appointment.js schema
        appointment_data = {
            "user_id": user_id,
            "professional_id": appointment_details["professional_id"],
            "location": location_data,
            "scheduled_time": scheduled_time_obj,
            "confermation_dead_line": confermation_dead_line_obj,
            "problem_summary": appointment_details["issue"],
            "status": "pending",  # Initial status
            # Add any other fields from the schema if necessary, e.g., createdAt
            # For simplicity, we use the default _id generation
        }

        # Add notes if provided
        if "notes" in appointment_details:
            appointment_data["notes"] = appointment_details["notes"]


        if using_mongodb:
            # Insert using MongoDB
            result = db[APPOINTMENTS_COLLECTION].insert_one(appointment_data)
            logger.info(f"Appointment created in MongoDB with ID: {result.inserted_id}")
            return str(result.inserted_id)
        else:
            # Insert using in-memory database
            appointment_data["_id"] = str(uuid.uuid4()) # Generate ID for in-memory
            db[APPOINTMENTS_COLLECTION].append(appointment_data)
            logger.info(f"Appointment created in in-memory DB with ID: {appointment_data['_id']}")
            return appointment_data["_id"]

    except ValueError as ve:
        logger.error(f"ValueError in create_appointment (datetime parsing): {str(ve)}")
        raise ValueError(f"Invalid datetime format provided: {appointment_details.get('datetime')}. Expected 'YYYY-MM-DD HH:MM'.")
    except Exception as e:
        logger.error(f"Database error in create_appointment: {str(e)}")
        raise Exception(f"Error creating appointment: {str(e)}")

def get_user_details(user_id):
    """
    Retrieve user details from the database.

    Args:
        user_id (str): User ID

    Returns:
        dict: The user details, or None if not found
    """
    try:
        if using_mongodb:
            # Use MongoDB find_one
            user = db[USERS_COLLECTION].find_one({"_id": user_id})
            if not user:
                logger.warning(f"User with ID {user_id} not found.")
                return None
            return user
        else:
            # Use in-memory search
            for user in db[USERS_COLLECTION]:
                if user.get("_id") == user_id:
                    return user
            logger.warning(f"User with ID {user_id} not found in in-memory DB.")
            return None

    except Exception as e:
        logger.error(f"Database error in get_user_details: {str(e)}")
        raise Exception(f"Error retrieving user details: {str(e)}")

def get_appointment(appointment_id):
    """
    Retrieve an appointment by ID.

    Args:
        appointment_id (str): ID of the appointment

    Returns:
        dict: The appointment details, or None if not found
    """
    try:
        if using_mongodb:
            # Use MongoDB find_one
            appointment = db[APPOINTMENTS_COLLECTION].find_one({"_id": appointment_id})
            if not appointment:
                raise Exception(f"Appointment with ID {appointment_id} not found.")
            return appointment
        else:
            # Use in-memory search
            for appointment in db[APPOINTMENTS_COLLECTION]:
                if appointment.get("_id") == appointment_id:
                    return appointment

            raise Exception(f"Appointment with ID {appointment_id} not found.")

    except Exception as e:
        logger.error(f"Database error in get_appointment: {str(e)}")
        raise Exception(f"Error retrieving appointment: {str(e)}")

def update_availability_after_booking(user_id, professional_id, booked_slot):
    """
    Update availability after a slot is booked.
    
    Args:
        user_id (str): User ID
        professional_id (str): Professional ID
        booked_slot (str): The slot that was booked
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if using_mongodb:
            # Update MongoDB collections
            modified_count = 0
            
            # Update date range documents
            range_query = {
                "$or": [
                    {"entity_id": user_id, "entity_type": "user", "date_range": {"$exists": True}},
                    {"entity_id": professional_id, "entity_type": "professional", "date_range": {"$exists": True}}
                ]
            }
            update = {"$pull": {"slots": booked_slot}}
            
            result = db[AVAILABILITY_COLLECTION].update_many(range_query, update)
            modified_count += result.modified_count
            
            # Update day documents
            slot_date = booked_slot.split(" ")[0]  # Extract just the date part
            
            day_query = {
                "$or": [
                    {"entity_id": user_id, "entity_type": "user", "date": slot_date},
                    {"entity_id": professional_id, "entity_type": "professional", "date": slot_date}
                ]
            }
            
            result = db[AVAILABILITY_COLLECTION].update_many(day_query, update)
            modified_count += result.modified_count
            
            return modified_count > 0
        else:
            # In-memory database implementation
            modified_count = 0
            
            # Remove the booked slot from both user and professional availability in date range documents
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == user_id and 
                    doc.get("entity_type") == "user" and
                    "date_range" in doc and
                    "slots" in doc and
                    booked_slot in doc["slots"]):
                    doc["slots"].remove(booked_slot)
                    modified_count += 1
                
                if (doc.get("entity_id") == professional_id and 
                    doc.get("entity_type") == "professional" and
                    "date_range" in doc and
                    "slots" in doc and
                    booked_slot in doc["slots"]):
                    doc["slots"].remove(booked_slot)
                    modified_count += 1
            
            # Also update individual day documents
            slot_date = booked_slot.split(" ")[0]  # Extract just the date part
            
            for doc in db[AVAILABILITY_COLLECTION]:
                if (doc.get("entity_id") == user_id and 
                    doc.get("entity_type") == "user" and
                    doc.get("date") == slot_date and
                    "slots" in doc and
                    booked_slot in doc["slots"]):
                    doc["slots"].remove(booked_slot)
                    modified_count += 1
                
                if (doc.get("entity_id") == professional_id and 
                    doc.get("entity_type") == "professional" and
                    doc.get("date") == slot_date and
                    "slots" in doc and
                    booked_slot in doc["slots"]):
                    doc["slots"].remove(booked_slot)
                    modified_count += 1
            
            return modified_count > 0
    
    except Exception as e:
        logger.error(f"Database error in update_availability_after_booking: {str(e)}")
        raise Exception(f"Error updating availability: {str(e)}") 