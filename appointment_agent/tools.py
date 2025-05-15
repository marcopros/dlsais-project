from datetime import datetime, timedelta
import random
import uuid
from typing import Optional, Dict, List, Any
from appointment_agent.database import (
    get_user_availability,
    get_professional_availability,
    create_appointment,
    update_availability_after_booking
)
from appointment_agent.utils import format_datetime
from appointment_agent.date_parser import (
    parse_natural_date,
    create_date_range_string,
    format_datetime_for_api
)

# Default IDs when not provided
DEFAULT_USER_ID = "user_123456"
DEFAULT_PROFESSIONAL_ID = "pro_123456"  # Luca Bianchi ID

# ----------------------
# TOOL 1: check_user_availability
# ----------------------
def check_user_availability(user_id: str, date_range: Optional[str] = None, date_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Check the availability of a user for a given date or date range.

    Args:
        user_id (str): The ID of the user.
        date_range (str, optional): The date range to check (e.g., "2023-12-01 to 2023-12-10").
        date_text (str, optional): Natural language date like "tomorrow" or "as soon as possible".
                                   If provided, this will override date_range.

    Returns:
        dict: {
            'status': 'success' or 'error',
            'available_slots': list of available time slots,
            'message': description of what was done or error message
        }
    """
    try:
        # If no user_id provided, use default
        if not user_id or user_id.strip() == "":
            user_id = DEFAULT_USER_ID
        
        if date_text:
            # Parse natural language date
            start_date, end_date, is_range, is_asap = parse_natural_date(date_text)
            
            if is_range:
                # Create formatted date range string
                date_range = create_date_range_string(start_date, end_date)
                
                # For ASAP, we'll want to flag this for getting the first available slot
                is_asap_flag = is_asap
            else:
                # Single date - use the date but include full day
                end_date = start_date.replace(hour=23, minute=59, second=59)
                date_range = create_date_range_string(start_date, end_date)
                is_asap_flag = False
        
        # Parse date range or use default (next 7 days)
        if date_range:
            try:
                start_date_str, end_date_str = date_range.split(' to ')
                start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d')
            except:
                return {
                    "status": "error",
                    "error_message": "Invalid date range format. Please use 'YYYY-MM-DD to YYYY-MM-DD'.",
                    "user_id": user_id  # Always include user_id in response
                }
        else:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
        
        # Get availability from database
        available_slots = get_user_availability(user_id, start_date, end_date)
        
        if not available_slots:
            return {
                "status": "error",
                "error_message": f"No availability found for user {user_id} in the specified date range. Please check the user ID or choose a different date range.",
                "user_id": user_id  # Always include user_id in response
            }
        
        # Sort the slots chronologically
        available_slots.sort()
        
        # If ASAP requested, prioritize first available slot
        if date_text and ('asap' in date_text.lower() or 'prima possibile' in date_text.lower()):
            return {
                "status": "success",
                "available_slots": available_slots,
                "first_available": available_slots[0] if available_slots else None,
                "message": f"Found {len(available_slots)} available time slots for user {user_id}. First available: {available_slots[0] if available_slots else 'None'}",
                "user_id": user_id  # Always include user_id in response
            }
        
        return {
            "status": "success",
            "available_slots": available_slots,
            "message": f"Found {len(available_slots)} available time slots for user {user_id}.",
            "user_id": user_id  # Always include user_id in response
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Database error checking user availability: {str(e)}",
            "user_id": user_id if user_id else DEFAULT_USER_ID  # Always include user_id in response
        }


# ----------------------
# TOOL 2: check_professional_availability
# ----------------------
def check_professional_availability(professional_id: str, date_range: Optional[str] = None, date_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Check the availability of a professional for a given date range.

    Args:
        professional_id (str): The ID of the professional.
        date_range (str, optional): The date range to check (e.g., "2023-12-01 to 2023-12-10").
        date_text (str, optional): Natural language date like "tomorrow" or "as soon as possible".
                                   If provided, this will override date_range.

    Returns:
        dict: {
            'status': 'success' or 'error',
            'available_slots': list of available time slots,
            'message': description of what was done or error message
        }
    """
    try:
        # If no professional_id provided, use default (Luca Bianchi)
        if not professional_id or professional_id.strip() == "":
            professional_id = DEFAULT_PROFESSIONAL_ID
        
        if date_text:
            # Parse natural language date
            start_date, end_date, is_range, is_asap = parse_natural_date(date_text)
            
            if is_range:
                # Create formatted date range string
                date_range = create_date_range_string(start_date, end_date)
                
                # For ASAP, we'll want to flag this for getting the first available slot
                is_asap_flag = is_asap
            else:
                # Single date - use the date but include full day
                end_date = start_date.replace(hour=23, minute=59, second=59)
                date_range = create_date_range_string(start_date, end_date)
                is_asap_flag = False
        
        # Parse date range or use default (next 7 days)
        if date_range:
            try:
                start_date_str, end_date_str = date_range.split(' to ')
                start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d')
            except:
                return {
                    "status": "error",
                    "error_message": "Invalid date range format. Please use 'YYYY-MM-DD to YYYY-MM-DD'.",
                    "professional_id": professional_id  # Always include professional_id in response
                }
        else:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
        
        # Get availability from database
        available_slots = get_professional_availability(professional_id, start_date, end_date)
        
        if not available_slots:
            return {
                "status": "error",
                "error_message": f"No availability found for professional {professional_id} in the specified date range. Please check the professional ID or choose a different date range.",
                "professional_id": professional_id  # Always include professional_id in response
            }
        
        # Sort the slots chronologically
        available_slots.sort()
        
        # If ASAP requested, prioritize first available slot
        if date_text and ('asap' in date_text.lower() or 'prima possibile' in date_text.lower()):
            return {
                "status": "success",
                "available_slots": available_slots,
                "first_available": available_slots[0] if available_slots else None,
                "message": f"Found {len(available_slots)} available time slots for professional {professional_id}. First available: {available_slots[0] if available_slots else 'None'}",
                "professional_id": professional_id  # Always include professional_id in response
            }
        
        return {
            "status": "success",
            "available_slots": available_slots,
            "message": f"Found {len(available_slots)} available time slots for professional {professional_id}.",
            "professional_id": professional_id  # Always include professional_id in response
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Database error checking professional availability: {str(e)}",
            "professional_id": professional_id if professional_id else DEFAULT_PROFESSIONAL_ID  # Always include professional_id in response
        }


# ----------------------
# TOOL 3: schedule_appointment
# ----------------------
def schedule_appointment(appointment_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule an appointment between a user and a professional.

    Args:
        appointment_details (dict): A dictionary containing:
            - 'user_id': ID of the user
            - 'professional_id': ID of the professional
            - 'datetime': Date and time of the appointment (format: 'YYYY-MM-DD HH:MM') or natural language like "tomorrow"
            - 'issue': Description of the issue to be addressed
            - 'location': Location of the appointment (optional)
            - 'notes': Additional notes (optional)

    Returns:
        dict: {
            'status': 'success' or 'error',
            'appointment_id': unique ID for the appointment (if successful),
            'message': confirmation message or error message
        }
    """
    try:
        # Validate and use default values if needed
        if not appointment_details:
            appointment_details = {}
            
        # Use default IDs if not provided
        if 'user_id' not in appointment_details or not appointment_details['user_id']:
            appointment_details['user_id'] = DEFAULT_USER_ID
            
        if 'professional_id' not in appointment_details or not appointment_details['professional_id']:
            appointment_details['professional_id'] = DEFAULT_PROFESSIONAL_ID
            
        # Validate required fields
        required_fields = ['datetime', 'issue']
        missing_fields = [field for field in required_fields if field not in appointment_details]
        
        if missing_fields:
            # Generate default datetime if not provided (tomorrow at noon)
            if 'datetime' in missing_fields:
                tomorrow = datetime.now() + timedelta(days=1)
                appointment_details['datetime'] = tomorrow.strftime('%Y-%m-%d 12:00')
                missing_fields.remove('datetime')
                
            # Generate default issue if not provided
            if 'issue' in missing_fields:
                appointment_details['issue'] = "General maintenance"
                missing_fields.remove('issue')
                
            # If we still have missing fields, return error
            if missing_fields:
                return {
                    "status": "error",
                    "error_message": f"Missing required fields: {', '.join(missing_fields)}",
                    "user_id": appointment_details.get('user_id', DEFAULT_USER_ID),
                    "professional_id": appointment_details.get('professional_id', DEFAULT_PROFESSIONAL_ID)
                }
        
        # Check if datetime is a natural language string
        datetime_value = appointment_details['datetime']
        if not isinstance(datetime_value, str) or ' ' not in datetime_value or not any(c.isdigit() for c in datetime_value):
            # Handle natural language date
            start_date, _, _, is_asap = parse_natural_date(datetime_value)
            
            if is_asap:
                # For ASAP, we need to find the first available slot that matches both calendars
                # Check professional availability
                prof_result = check_professional_availability(
                    appointment_details['professional_id'],
                    date_text="as soon as possible"
                )
                
                if prof_result["status"] == "success" and "first_available" in prof_result:
                    # Use the first available slot
                    appointment_details['datetime'] = prof_result["first_available"]
                else:
                    # Default to tomorrow at noon if no match
                    tomorrow = datetime.now() + timedelta(days=1)
                    appointment_details['datetime'] = tomorrow.strftime('%Y-%m-%d 12:00')
            else:
                # For other natural language dates, use noon as default time
                start_date = start_date.replace(hour=12, minute=0, second=0)
                appointment_details['datetime'] = format_datetime_for_api(start_date)
        
        # Format datetime for readability
        datetime_obj = datetime.strptime(appointment_details['datetime'], '%Y-%m-%d %H:%M')
        formatted_date, formatted_time = format_datetime(appointment_details['datetime'])
        
        # Create appointment in database
        appointment_id = create_appointment({
            "user_id": appointment_details['user_id'],
            "professional_id": appointment_details['professional_id'],
            "datetime": appointment_details['datetime'],
            "datetime_obj": datetime_obj,
            "formatted_date": formatted_date,
            "formatted_time": formatted_time,
            "issue": appointment_details['issue'],
            "location": appointment_details.get('location', 'Not specified'),
            "notes": appointment_details.get('notes', ''),
            "status": "confirmed"
        })
        
        if not appointment_id:
            return {
                "status": "error",
                "error_message": "Failed to create appointment in database. Please try again later.",
                "user_id": appointment_details['user_id'],
                "professional_id": appointment_details['professional_id']
            }
        
        # Update availability to remove the booked slot
        update_result = update_availability_after_booking(
            appointment_details['user_id'],
            appointment_details['professional_id'],
            appointment_details['datetime']
        )
        
        if not update_result:
            return {
                "status": "warning",
                "appointment_id": appointment_id,
                "appointment_details": {
                    "user_id": appointment_details['user_id'],
                    "professional_id": appointment_details['professional_id'],
                    "date": formatted_date,
                    "time": formatted_time,
                    "issue": appointment_details['issue'],
                    "location": appointment_details.get('location', 'Not specified')
                },
                "message": f"Appointment created successfully, but there was an issue updating the availability calendar. The appointment may conflict with existing bookings.",
                "user_id": appointment_details['user_id'],
                "professional_id": appointment_details['professional_id']
            }
        
        return {
            "status": "success",
            "appointment_id": appointment_id,
            "appointment_details": {
                "user_id": appointment_details['user_id'],
                "professional_id": appointment_details['professional_id'],
                "date": formatted_date,
                "time": formatted_time,
                "issue": appointment_details['issue'],
                "location": appointment_details.get('location', 'Not specified')
            },
            "message": f"Appointment successfully scheduled for {formatted_date} at {formatted_time}.",
            "user_id": appointment_details['user_id'],
            "professional_id": appointment_details['professional_id']
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error scheduling appointment: {str(e)}",
            "user_id": appointment_details.get('user_id', DEFAULT_USER_ID) if appointment_details else DEFAULT_USER_ID,
            "professional_id": appointment_details.get('professional_id', DEFAULT_PROFESSIONAL_ID) if appointment_details else DEFAULT_PROFESSIONAL_ID
        }


# ----------------------
# Mock data generation for testing
# ----------------------

def _generate_mock_user_slots(start_date, end_date):
    """Generate mock availability slots for a user"""
    slots = []
    current_date = start_date
    while current_date <= end_date:
        # Skip some days randomly to simulate unavailability
        if random.random() > 0.3:  # 70% chance of having availability on a given day
            # Generate 3-6 slots per day
            num_slots = random.randint(3, 6)
            for _ in range(num_slots):
                hour = random.randint(9, 20)  # 9 AM to 8 PM
                minute = random.choice([0, 30])  # Either on the hour or half hour
                
                slot_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # Only add future slots
                if slot_time > datetime.now():
                    slot_str = slot_time.strftime('%Y-%m-%d %H:%M')
                    slots.append(slot_str)
        
        current_date += timedelta(days=1)
    
    return slots

def _generate_mock_professional_slots(start_date, end_date):
    """Generate mock availability slots for a professional"""
    slots = []
    current_date = start_date
    while current_date <= end_date:
        # Only generate slots for weekdays
        if current_date.weekday() < 5:  # Monday to Friday
            # Generate 5-8 slots per day
            num_slots = random.randint(5, 8)
            for _ in range(num_slots):
                hour = random.randint(8, 18)  # 8 AM to 6 PM
                minute = random.choice([0, 30])  # Either on the hour or half hour
                
                slot_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # Only add future slots
                if slot_time > datetime.now():
                    slot_str = slot_time.strftime('%Y-%m-%d %H:%M')
                    slots.append(slot_str)
        
        current_date += timedelta(days=1)
    
    return slots 