import os
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = "mongodb+srv://marco:unitn2025@dlsais-cluster.vkxu2tc.mongodb.net/?retryWrites=true&w=majority&appName=dlsais-cluster"
DB_NAME = "test"  # Stesso nome usato in database/utils.py

# Collections - allineate con i nomi definiti nei modelli Mongoose
USERS_COLLECTION = "users"  # Corrisponde a mongoose.model('User', userSchema)
PROFESSIONALS_COLLECTION = "professionals"  # Corrisponde a mongoose.model('Professional', ProfessionalSchema)
APPOINTMENTS_COLLECTION = "requests"  # Corrisponde a mongoose.model('Request', requestSchema)
AVAILABILITY_COLLECTION = "availability"  # Non esiste un modello dedicato ma la usiamo per gestire le disponibilità

# Initialize MongoDB client with a shorter timeout for quicker error detection
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Verify connection
    client.admin.command('ping')
    db = client[DB_NAME]
    print("Connected to MongoDB successfully!")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"MongoDB Connection Error: {str(e)}")
    # We still define client and db, but operations will fail
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]

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
        # Convert dates to string format for query
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # First try finding the date range document
        availability = db[AVAILABILITY_COLLECTION].find_one(
            {
                "entity_id": user_id,
                "entity_type": "user",
                "date_range": {"$exists": True}
            }
        )
        
        if availability and "slots" in availability:
            # Filter slots that are within our date range
            filtered_slots = [
                slot for slot in availability["slots"] 
                if slot >= f"{start_str} 00:00" and slot <= f"{end_str} 23:59"
            ]
            return filtered_slots
        
        # If no date range document, try finding individual day documents
        cursor = db[AVAILABILITY_COLLECTION].find(
            {
                "entity_id": user_id,
                "entity_type": "user",
                "date": {"$gte": start_str, "$lte": end_str}
            }
        )
        
        all_slots = []
        for doc in cursor:
            if "slots" in doc:
                all_slots.extend(doc["slots"])
        
        return all_slots
    
    except ServerSelectionTimeoutError:
        print("Error: Cannot connect to MongoDB server. Please check the connection.")
        raise Exception("Database connection error. Cannot retrieve user availability.")
    except OperationFailure as e:
        print(f"MongoDB operation failed: {str(e)}")
        raise Exception(f"Database operation error: {str(e)}")
    except Exception as e:
        print(f"Database error in get_user_availability: {str(e)}")
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
        # Convert dates to string format for query
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # First try finding the date range document
        availability = db[AVAILABILITY_COLLECTION].find_one(
            {
                "entity_id": professional_id,
                "entity_type": "professional",
                "date_range": {"$exists": True}
            }
        )
        
        if availability and "slots" in availability:
            # Filter slots that are within our date range
            filtered_slots = [
                slot for slot in availability["slots"] 
                if slot >= f"{start_str} 00:00" and slot <= f"{end_str} 23:59"
            ]
            return filtered_slots
        
        # If no date range document, try finding individual day documents
        cursor = db[AVAILABILITY_COLLECTION].find(
            {
                "entity_id": professional_id,
                "entity_type": "professional",
                "date": {"$gte": start_str, "$lte": end_str}
            }
        )
        
        all_slots = []
        for doc in cursor:
            if "slots" in doc:
                all_slots.extend(doc["slots"])
        
        return all_slots
    
    except ServerSelectionTimeoutError:
        print("Error: Cannot connect to MongoDB server. Please check the connection.")
        raise Exception("Database connection error. Cannot retrieve professional availability.")
    except OperationFailure as e:
        print(f"MongoDB operation failed: {str(e)}")
        raise Exception(f"Database operation error: {str(e)}")
    except Exception as e:
        print(f"Database error in get_professional_availability: {str(e)}")
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
        result = db[APPOINTMENTS_COLLECTION].insert_one(request_data)
        
        # Return the ID of the inserted document
        return str(result.inserted_id)
    
    except ServerSelectionTimeoutError:
        print("Error: Cannot connect to MongoDB server. Please check the connection.")
        raise Exception("Database connection error. Cannot create appointment.")
    except OperationFailure as e:
        print(f"MongoDB operation failed: {str(e)}")
        raise Exception(f"Database operation error: {str(e)}")
    except Exception as e:
        print(f"Database error in create_appointment: {str(e)}")
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
        from bson.objectid import ObjectId
        
        # Query the appointments collection
        appointment = db[APPOINTMENTS_COLLECTION].find_one({"_id": ObjectId(appointment_id)})
        
        if not appointment:
            raise Exception(f"Appointment with ID {appointment_id} not found.")
            
        return appointment
    
    except ServerSelectionTimeoutError:
        print("Error: Cannot connect to MongoDB server. Please check the connection.")
        raise Exception("Database connection error. Cannot retrieve appointment.")
    except OperationFailure as e:
        print(f"MongoDB operation failed: {str(e)}")
        raise Exception(f"Database operation error: {str(e)}")
    except Exception as e:
        print(f"Database error in get_appointment: {str(e)}")
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
        # Remove the booked slot from both user and professional availability
        # First check date range documents
        result1 = db[AVAILABILITY_COLLECTION].update_many(
            {"entity_id": user_id, "entity_type": "user", "date_range": {"$exists": True}},
            {"$pull": {"slots": booked_slot}}
        )
        
        result2 = db[AVAILABILITY_COLLECTION].update_many(
            {"entity_id": professional_id, "entity_type": "professional", "date_range": {"$exists": True}},
            {"$pull": {"slots": booked_slot}}
        )
        
        # Also update individual day documents
        slot_date = booked_slot.split(" ")[0]  # Extract just the date part
        
        result3 = db[AVAILABILITY_COLLECTION].update_many(
            {"entity_id": user_id, "entity_type": "user", "date": slot_date},
            {"$pull": {"slots": booked_slot}}
        )
        
        result4 = db[AVAILABILITY_COLLECTION].update_many(
            {"entity_id": professional_id, "entity_type": "professional", "date": slot_date},
            {"$pull": {"slots": booked_slot}}
        )
        
        # If any update was successful
        return result1.modified_count > 0 or result2.modified_count > 0 or result3.modified_count > 0 or result4.modified_count > 0
    
    except ServerSelectionTimeoutError:
        print("Error: Cannot connect to MongoDB server. Please check the connection.")
        raise Exception("Database connection error. Cannot update availability.")
    except OperationFailure as e:
        print(f"MongoDB operation failed: {str(e)}")
        raise Exception(f"Database operation error: {str(e)}")
    except Exception as e:
        print(f"Database error in update_availability_after_booking: {str(e)}")
        raise Exception(f"Error updating availability: {str(e)}") 