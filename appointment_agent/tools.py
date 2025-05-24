from datetime import datetime, timedelta
import random
import uuid
from typing import Optional, Dict, List, Any
from appointment_agent.database import (
    get_user_availability,
    get_professional_availability,
    create_appointment,
    update_availability_after_booking,
    get_user_details # Import the new function
)
from database.utils import getProfessionals # Assuming this function exists and can get professional details by ID
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
# Helper function to get professional details (assuming getProfessionals can fetch by ID)
# ----------------------
def get_professional_details(professional_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve professional details from the database by ID.

    Args:
        professional_id (str): The ID of the professional.

    Returns:
        dict: The professional details, or None if not found.
    """
    # Assuming getProfessionals can filter by ID if passed None for profession and location
    professionals = getProfessionals(None, None, professional_id)
    if professionals and len(professionals) > 0:
        return professionals[0]
    return None


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
            - 'datetime': Date and time of the appointment (format: 'YYYY-MM-DD HH:MM') or natural language like "tomorrow" or "as soon as possible"
            - 'issue': Description of the issue to be addressed
            - 'notes': Additional notes (optional)

    Returns:
        dict: {
            'status': 'success' or 'error',
            'appointment_id': unique ID for the appointment (if successful),
            'appointment_details': dict with scheduled appointment info (if successful),
            'message': confirmation message or error message
        }
    """
    try:
        # Validate and use default values if needed
        if not appointment_details:
            return {
                "status": "error",
                "error_message": "Appointment details are missing.",
                "user_id": DEFAULT_USER_ID,
                "professional_id": DEFAULT_PROFESSIONAL_ID
            }

        # Use default IDs if not provided
        user_id = appointment_details.get('user_id', DEFAULT_USER_ID)
        professional_id = appointment_details.get('professional_id', DEFAULT_PROFESSIONAL_ID)
        datetime_value = appointment_details.get('datetime')
        issue = appointment_details.get('issue')
        notes = appointment_details.get('notes', '')

        # Validate required fields
        if not datetime_value or not issue:
             missing = []
             if not datetime_value: missing.append("'datetime'")
             if not issue: missing.append("'issue'")
             return {
                 "status": "error",
                 "error_message": f"Missing required fields: {', '.join(missing)}",
                 "user_id": user_id,
                 "professional_id": professional_id
             }

        # Handle natural language date/time or parse explicit format
        try:
            # Attempt to parse as explicit YYYY-MM-DD HH:MM first
            scheduled_time_str = datetime.strptime(datetime_value, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M')
        except ValueError:
            # If explicit parse fails, try natural language
            start_date, _, _, is_asap = parse_natural_date(datetime_value)

            if is_asap:
                 # For ASAP, we need to find the first available slot that matches both calendars
                 # We'll rely on the create_appointment function to handle the location/user details lookup
                 # and potentially the availability check if needed.
                 # For now, just pass the ASAP intent. The create_appointment logic in database.py
                 # needs to be robust enough to handle this, or we need a separate tool/step
                 # to find the *actual* first available slot before calling schedule_appointment.
                 # Given the instruction in agent.py step 5 mentions passing natural language dates,
                 # let's assume create_appointment (or a subsequent step) handles the lookup.
                 # However, the current create_appointment expects '%Y-%m-%d %H:%M'.
                 # Let's revise the flow based on the agent instructions: The agent should
                 # check availability *before* calling schedule_appointment and pass a concrete slot.
                 # The current agent instructions (step 5) say "You can use natural language dates like 'tomorrow' or 'next Monday' in the datetime field".
                 # This conflicts with the create_appointment function expecting a formatted string.
                 # Let's adjust schedule_appointment to handle natural language and find a slot here,
                 # or clarify the agent's role vs tool's role.

                 # Let's stick to the original plan: the agent extracts date/time, and the tool schedules.
                 # The agent should use check_user_availability and check_professional_availability first,
                 # find a matching slot, and *then* call schedule_appointment with a specific datetime string.
                 # The current agent instructions are slightly ambiguous on this.
                 # Let's assume the agent *will* provide a specific datetime string after checking availability.
                 # So, schedule_appointment expects a formatted string.

                 # If natural language was used, and it wasn't ASAP handled by finding the first available slot
                 # earlier in the agent's flow (which isn't fully implemented yet based on the current agent.py),
                 # we need a concrete time. Let's default to noon for non-ASAP natural language dates
                 # if the time isn't specified.
                 if start_date:
                      # Default to noon if no time was specified in natural language
                      scheduled_time_str = start_date.replace(hour=12, minute=0, second=0).strftime('%Y-%m-%d %H:%M')
                 else:
                      # Fallback if natural language parsing failed completely
                      tomorrow = datetime.now() + timedelta(days=1)
                      scheduled_time_str = tomorrow.strftime('%Y-%m-%d 12:00')

        # Now scheduled_time_str is guaranteed to be in 'YYYY-MM-DD HH:MM' format
        scheduled_time_obj = datetime.strptime(scheduled_time_str, '%Y-%m-%d %H:%M')

        # Create appointment in database
        # The create_appointment function in database.py now handles fetching user location
        appointment_id = create_appointment({
            "user_id": user_id,
            "professional_id": professional_id,
            "datetime": scheduled_time_str, # Pass the formatted string
            "issue": issue,
            "notes": notes,
        })

        if not appointment_id:
            return {
                "status": "error",
                "error_message": "Failed to create appointment in database. Please try again later.",
                "user_id": user_id,
                "professional_id": professional_id
            }

        # Update availability to remove the booked slot
        update_result = update_availability_after_booking(
            user_id,
            professional_id,
            scheduled_time_str # Pass the formatted string
        )

        # Get professional details for the confirmation message
        professional_details = get_professional_details(professional_id)
        professional_name = professional_details.get("name", "Unknown Professional") if professional_details else "Unknown Professional"


        # Get the created appointment details to return in the response
        # This assumes get_appointment is updated to fetch by the new schema ID
        # (which create_appointment now returns)
        created_appointment = get_appointment(appointment_id)
        # Format date and time for the message
        formatted_date = created_appointment['scheduled_time'].strftime('%A, %B %d, %Y') if created_appointment and 'scheduled_time' in created_appointment else 'Unknown Date'
        formatted_time = created_appointment['scheduled_time'].strftime('%I:%M %p') if created_appointment and 'scheduled_time' in created_appointment else 'Unknown Time'
        issue_summary = created_appointment.get('problem_summary', 'Unknown Issue') if created_appointment else 'Unknown Issue'
        location_summary = created_appointment.get('location', {}) if created_appointment else {}
        location_str = f"{location_summary.get('city', 'Unknown City')}, {location_summary.get('zipCode', '')}".strip() if location_summary else "Unknown Location"
        if location_str.endswith(','):
             location_str = location_str[:-1].strip()

        message = f"Appointment successfully scheduled with {professional_name} for {issue_summary} on {formatted_date} at {formatted_time} at {location_str}."

        if not update_result:
            message += " Warning: There was an issue updating the availability calendar. The appointment may conflict with existing bookings."

        return {
            "status": "success" if update_result else "warning",
            "appointment_id": appointment_id,
            "appointment_details": {
                "user_id": user_id,
                "professional_id": professional_id,
                "date": formatted_date,
                "time": formatted_time,
                "issue": issue_summary,
                "location": location_str,
                "professional_name": professional_name
            },
            "message": message,
            "user_id": user_id, # Include IDs in the tool response
            "professional_id": professional_id
        }

    except ValueError as ve:
        return {
            "status": "error",
            "error_message": f"Error parsing date/time: {str(ve)}. Please provide the date and time in a clear format.",
            "user_id": user_id,
            "professional_id": professional_id
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error scheduling appointment: {str(e)}",
            "user_id": user_id,
            "professional_id": professional_id
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