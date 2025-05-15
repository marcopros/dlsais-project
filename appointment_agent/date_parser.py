from datetime import datetime, timedelta
import re

def parse_natural_date(date_text):
    """
    Parse natural language date expressions into datetime objects.
    
    Args:
        date_text (str): Natural language date expression like "tomorrow" or "as soon as possible"
        
    Returns:
        tuple: (datetime_obj, end_datetime_obj, is_range, is_asap)
            - datetime_obj: The parsed date/time as a datetime object
            - end_datetime_obj: End date if it's a range, otherwise None
            - is_range: Boolean indicating if this is a date range
            - is_asap: Boolean indicating if "as soon as possible" was requested
    """
    date_text = date_text.lower().strip()
    
    # Default values
    now = datetime.now()
    is_range = False
    is_asap = False
    end_datetime = None
    
    # ASAP or first available
    if any(phrase in date_text for phrase in ["as soon as possible", "asap", "prima possibile", "appena possibile", "first available", "next available"]):
        is_asap = True
        # Set start to now and end to 14 days from now
        end_datetime = now + timedelta(days=14)
        return now, end_datetime, True, True
    
    # Today
    elif any(phrase in date_text for phrase in ["today", "oggi", "questa giornata"]):
        return now, None, False, False
    
    # Tomorrow
    elif any(phrase in date_text for phrase in ["tomorrow", "domani"]):
        tomorrow = now + timedelta(days=1)
        # Set to beginning of the day
        tomorrow = tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)
        return tomorrow, None, False, False
    
    # Day after tomorrow
    elif any(phrase in date_text for phrase in ["day after tomorrow", "dopodomani"]):
        day_after = now + timedelta(days=2)
        day_after = day_after.replace(hour=8, minute=0, second=0, microsecond=0)
        return day_after, None, False, False
    
    # This week
    elif any(phrase in date_text for phrase in ["this week", "questa settimana"]):
        # Calculate end of week (Sunday)
        days_until_sunday = 6 - now.weekday()  # weekday: 0=Monday, 6=Sunday
        end_of_week = now + timedelta(days=days_until_sunday)
        end_of_week = end_of_week.replace(hour=18, minute=0, second=0, microsecond=0)
        return now, end_of_week, True, False
    
    # Next week
    elif any(phrase in date_text for phrase in ["next week", "prossima settimana", "la settimana prossima"]):
        # Calculate start of next week (Monday)
        days_until_next_monday = 7 - now.weekday() if now.weekday() > 0 else 7
        next_monday = now + timedelta(days=days_until_next_monday)
        next_monday = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Calculate end of next week (Sunday)
        next_sunday = next_monday + timedelta(days=6)
        next_sunday = next_sunday.replace(hour=18, minute=0, second=0, microsecond=0)
        
        return next_monday, next_sunday, True, False
    
    # Weekend
    elif any(phrase in date_text for phrase in ["weekend", "fine settimana"]):
        # Calculate days until Saturday
        days_until_saturday = 5 - now.weekday() if now.weekday() < 5 else 12 - now.weekday()
        next_saturday = now + timedelta(days=days_until_saturday)
        next_saturday = next_saturday.replace(hour=9, minute=0, second=0, microsecond=0)
        
        next_sunday = next_saturday + timedelta(days=1) 
        next_sunday = next_sunday.replace(hour=18, minute=0, second=0, microsecond=0)
        
        return next_saturday, next_sunday, True, False
    
    # Try to parse standard date format
    try:
        # Try YYYY-MM-DD format
        parsed_date = datetime.strptime(date_text, '%Y-%m-%d')
        parsed_date = parsed_date.replace(hour=8, minute=0, second=0, microsecond=0)
        return parsed_date, None, False, False
    except ValueError:
        # Try other common formats
        try:
            # Try DD/MM/YYYY format
            parsed_date = datetime.strptime(date_text, '%d/%m/%Y')
            parsed_date = parsed_date.replace(hour=8, minute=0, second=0, microsecond=0)
            return parsed_date, None, False, False
        except ValueError:
            pass
    
    # If nothing matched, default to tomorrow
    tomorrow = now + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)
    return tomorrow, None, False, False

def format_date_for_api(date_obj):
    """
    Format a datetime object into the string format required by the API (YYYY-MM-DD).
    
    Args:
        date_obj (datetime): Datetime object to format
        
    Returns:
        str: Formatted date string in 'YYYY-MM-DD' format
    """
    return date_obj.strftime('%Y-%m-%d')

def format_datetime_for_api(date_obj):
    """
    Format a datetime object into the string format required by the API (YYYY-MM-DD HH:MM).
    
    Args:
        date_obj (datetime): Datetime object to format
        
    Returns:
        str: Formatted datetime string in 'YYYY-MM-DD HH:MM' format
    """
    return date_obj.strftime('%Y-%m-%d %H:%M')

def create_date_range_string(start_date, end_date):
    """
    Create a date range string for the API.
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        
    Returns:
        str: Date range string in 'YYYY-MM-DD to YYYY-MM-DD' format
    """
    start_str = format_date_for_api(start_date)
    end_str = format_date_for_api(end_date)
    return f"{start_str} to {end_str}" 