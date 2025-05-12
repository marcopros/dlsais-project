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
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DB_NAME", "appointment_db")

# Collections - allineate con i nomi definiti nei modelli Mongoose
USERS_COLLECTION = "users"  # Corrisponde a mongoose.model('User', userSchema)
PROFESSIONALS_COLLECTION = "professionals"  # Corrisponde a mongoose.model('Professional', ProfessionalSchema)
APPOINTMENTS_COLLECTION = "requests"  # Corrisponde a mongoose.model('Request', requestSchema)
AVAILABILITY_COLLECTION = "availability"  # Non esiste un modello dedicato ma la usiamo per gestire le disponibilità

# Initialize MongoDB client with a shorter timeout for quicker error detection
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Verify connection
    client.admin.command('ping')
    db = client[DB_NAME]
    print("Connected to MongoDB successfully!")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"MongoDB Connection Error: {str(e)}")
    # We still define client and db, but operations will fail
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

# In-memory database
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

# Initialize in-memory database
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
        
    Returns:
        str: ID of the created appointment, or None if failed
    """
    try:
        # Add timestamp for creation
        appointment_details["created_at"] = datetime.now()
        
        # Adatta i campi per corrispondere al modello Request
        request_data = {
            "_id": str(uuid.uuid4()),
            "userId": appointment_details["user_id"],
            "professionalId": appointment_details["professional_id"],
            "date": datetime.strptime(appointment_details["datetime"], '%Y-%m-%d %H:%M'),
            "status": "pending",  # Gli stati possibili sono: pending, accepted, rejected
            "description": appointment_details["issue"],
            # Manteniamo anche i campi aggiuntivi specifici dell'appointment
            "location": appointment_details.get("location", "Not specified"),
            "notes": appointment_details.get("notes", ""),
            "created_at": appointment_details["created_at"]
        }
        
        # Insert the appointment document
        db[APPOINTMENTS_COLLECTION].append(request_data)
        
        # Return the ID of the inserted document
        return request_data["_id"]
    
    except Exception as e:
        logger.error(f"Database error in create_appointment: {str(e)}")
        raise Exception(f"Error creating appointment: {str(e)}")

def get_appointment(appointment_id):
    """
    Retrieve an appointment by ID.
    
    Args:
        appointment_id (str): ID of the appointment
        
    Returns:
        dict: The appointment details, or None if not found
    """
    try:
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
        
        # If any update was successful
        return modified_count > 0
    
    except Exception as e:
        logger.error(f"Database error in update_availability_after_booking: {str(e)}")
        raise Exception(f"Error updating availability: {str(e)}") 