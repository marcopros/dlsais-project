from datetime import datetime

def format_datetime(datetime_str: str) -> tuple:
    """
    Format a datetime string into a more readable format.
    
    Args:
        datetime_str (str): Datetime string in 'YYYY-MM-DD HH:MM' format
        
    Returns:
        tuple: (formatted_date, formatted_time)
    """
    try:
        dt_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        formatted_date = dt_obj.strftime('%A, %B %d, %Y')
        formatted_time = dt_obj.strftime('%I:%M %p')
        return formatted_date, formatted_time
    except ValueError:
        return datetime_str, ""

def find_matching_slots(user_slots: list, professional_slots: list) -> list:
    """
    Find matching time slots between user and professional.
    
    Args:
        user_slots (list): List of datetime strings for user availability
        professional_slots (list): List of datetime strings for professional availability
        
    Returns:
        list: List of matching datetime strings
    """
    # Convert to sets for efficient intersection
    user_set = set(user_slots)
    professional_set = set(professional_slots)
    
    # Find matching slots
    matching_slots = user_set.intersection(professional_set)
    
    # Convert back to sorted list
    return sorted(list(matching_slots))

def suggest_alternatives(user_slots: list, professional_slots: list, max_suggestions: int = 5) -> list:
    """
    Suggest alternative slots when no exact matches are found.
    This function finds the closest professional slots to each user slot.
    
    Args:
        user_slots (list): List of datetime strings for user availability
        professional_slots (list): List of datetime strings for professional availability
        max_suggestions (int): Maximum number of suggestions to return
        
    Returns:
        list: List of suggested datetime strings from professional slots
    """
    if not user_slots or not professional_slots:
        return []
    
    # Convert strings to datetime objects
    user_datetimes = [datetime.strptime(slot, '%Y-%m-%d %H:%M') for slot in user_slots]
    prof_datetimes = [datetime.strptime(slot, '%Y-%m-%d %H:%M') for slot in professional_slots]
    
    # Create a mapping of professional datetime to original string
    prof_map = {dt: slot for dt, slot in zip(prof_datetimes, professional_slots)}
    
    # Find closest slots
    suggestions = []
    for user_dt in user_datetimes:
        # Calculate time difference in minutes for each professional slot
        differences = [(abs((prof_dt - user_dt).total_seconds() / 60), prof_dt) 
                       for prof_dt in prof_datetimes]
        
        # Sort by smallest time difference
        differences.sort()
        
        # Take the closest few slots
        for _, prof_dt in differences[:3]:  # Take up to 3 closest options per user slot
            if len(suggestions) < max_suggestions:
                suggestions.append(prof_map[prof_dt])
            else:
                break
        
        if len(suggestions) >= max_suggestions:
            break
    
    # Remove duplicates and sort
    return sorted(list(set(suggestions))) 