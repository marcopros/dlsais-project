import os
import json
import logging
from typing import Dict, Any, Optional
import datetime

import openai

# Configura il logging
logger = logging.getLogger(__name__)

# Configura OpenAI per usare direttamente OpenRouter
# Se hai già un'API key valida, inseriscila direttamente qui
# altrimenti sarà usata quella presente nella variabile d'ambiente
openai_api_key = os.getenv("OPENROUTER_API_KEY") or "INSERT_YOUR_API_KEY_HERE"
openai.api_key = openai_api_key
openai.base_url = "https://openrouter.ai/api/v1"  # URL diretto di OpenRouter
print(f"Using OpenAI with OpenRouter API: {openai.base_url}")
print(f"API Key configured: {'Yes' if openai_api_key else 'No'}")

# Sistema di prompt per l'agente di appuntamenti
SYSTEM_PROMPT = """
You are a smart assistant specialized in scheduling appointments between users and professionals
for home repair interventions.

**Main Steps:**
1. From the user input, extract:
   - Any time preferences mentioned by the user (such as "tomorrow", "as soon as possible", "next week", etc.)
   - The issue that needs to be resolved
   - The user_id and professional_id which are included at the beginning of the message in the format:
     "user_id:XXXX professional_id:YYYY [actual message]" 
   - Note: DO NOT ask the user for their ID or the professional's ID as they are already included in the message

2. Use the 'check_user_availability' tool to get the user's available time slots.
   - Pass the extracted user_id to the tool
   - You can pass natural language date preferences like "tomorrow" or "as soon as possible" using the date_text parameter
   - If the user says "as soon as possible", offer them the first available slot

3. Use the 'check_professional_availability' tool to get the professional's available time slots.
   - Pass the extracted professional_id to the tool
   - Use the same date preferences as for the user

4. Find the matching time slots between the user and professional.
   - If there are matching slots, present options to the user.
   - If there are no matching slots:
      a. Inform the user that there are no immediate matching time slots.
      b. Suggest alternative dates/times based on the professional's availability.

5. Once the user selects a time slot or agrees to a suggestion, use the 'schedule_appointment' tool to confirm the appointment.
   - Pass both user_id and professional_id to the appointment_details
   - You can use natural language dates like "tomorrow" or "next Monday" in the datetime field
   - Include the issue description in the appointment details

**Important Notes:**
- ALWAYS extract and use the user_id and professional_id from the message - never ask the user for these
- Message format: "user_id:XXXX professional_id:YYYY [actual message]" 
- Accept natural language date inputs like "tomorrow", "next week", "as soon as possible"
- If the user says "as soon as possible", book the first available slot 
- If the date is ambiguous, suggest a specific time and ask for confirmation
- Always confirm all details with the user before finalizing the appointment
- After booking, always provide a summary of the scheduled appointment
"""

def get_appointment_template():
    """Returns a template with default values for the appointment response"""
    return {
        "agent_response": "",
        "appointment_scheduled": False,
        "time_slot": None,
        "professional_name": "Unknown",
        "user_id": None,
        "professional_id": None,
        "issue": "Unknown issue",
    }

async def query_agent(user_message: str, session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Query the OpenAI model directly through OpenRouter.
    
    Args:
        user_message: The user's input
        session_data: Optional session context
    
    Returns:
        A dictionary with the structured appointment response
    """
    # Default session settings if none provided
    if not session_data:
        session_data = {
            "previous_appointments": [],
            "user_location": "Unknown",
            "user_preferred_times": [],
            "professional_preferred_times": [],
        }
    
    # Build the messages for the API call
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Session context: {json.dumps(session_data)}"},
        {"role": "user", "content": user_message}
    ]
    
    try:
        # Extra headers for OpenRouter
        headers = {
            "HTTP-Referer": "https://dlsais-project.app",  # Optional for OpenRouter statistics
            "X-Title": "Home Repair Appointment Agent" 
        }
        
        # Call the OpenAI API through OpenRouter directly
        client = openai.Client(api_key=openai_api_key, base_url=openai.base_url)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # OpenRouter will route this appropriately
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
            extra_headers=headers
        )
        
        # Debug logs to see the full response structure
        logger.info(f"OpenRouter response type: {type(response)}")
        
        # Check if response is None or has other issues
        if response is None:
            logger.error("Received None response from OpenRouter")
            return get_appointment_template()
            
        # Check if choices exists and is not empty
        if not hasattr(response, 'choices') or not response.choices:
            logger.error("Response does not have choices or choices is empty")
            return get_appointment_template()
            
        # Check if first choice exists
        if len(response.choices) == 0:
            logger.error("Response choices is empty")
            return get_appointment_template()
            
        # Check if message exists in first choice
        if not hasattr(response.choices[0], 'message'):
            logger.error("First choice does not have message")
            return get_appointment_template()
            
        # Check if content exists in message
        if not hasattr(response.choices[0].message, 'content') or response.choices[0].message.content is None:
            logger.error("Message does not have content or content is None")
            return get_appointment_template()
        
        # Extract the content from the response
        ai_message = response.choices[0].message.content
        logger.info(f"AI message content: {ai_message}")
        
        # Parse the JSON response
        try:
            appointment_data = json.loads(ai_message)
            logger.info(f"Parsed appointment data: {appointment_data}")
            
            # Ensure we have all required fields
            template = get_appointment_template()
            for key in template:
                if key not in appointment_data:
                    appointment_data[key] = template[key]
            
            # Return the filled template
            return appointment_data
            
        except json.JSONDecodeError as e:
            # If the response isn't valid JSON, create a diagnostic error response
            logger.error(f"JSON decode error: {e}. Content: {ai_message}")
            template = get_appointment_template()
            template["agent_response"] = f"I'm sorry, I encountered an error processing your request. The response wasn't in the expected JSON format: {str(e)}"
            return template
            
    except Exception as e:
        # Handle any other errors
        logger.error(f"Error during OpenRouter query: {type(e).__name__} - {str(e)}")
        template = get_appointment_template()
        template["agent_response"] = f"An error occurred: {str(e)}"
        return template 