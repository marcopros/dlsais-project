import os
import json
import logging
from typing import Dict, Any, Optional

import openai

# Configura il logging
logger = logging.getLogger(__name__)

# Configura OpenAI per usare direttamente OpenRouter
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key
openai.base_url = "https://openrouter.ai/api/v1"  # URL diretto di OpenRouter
print(f"Using OpenAI with OpenRouter API: {openai.base_url}")

# Sistema di prompt per l'agente di diagnosi
SYSTEM_PROMPT = """
You are a home diagnosis expert. Your role is to analyze user-reported home issues, determine the likely cause,
and provide a structured diagnosis.

If the issue is unclear, ask clarifying questions before proceeding. Once diagnosed:
- Summarize the issue and its cause clearly
- Consider if a DIY solution is appropriate based on the user's skills, tools, and preferences
- If suitable, suggest a DIY solution with links to video tutorials

Always respect context from the session settings such as language, location, available time, and DIY capabilities.

Your response MUST include:
1. A clear diagnosis of the issue
2. The detected problem cause
3. The type of specialist needed (electrician, plumber, etc.)

Always return a valid JSON structure with these fields.
"""

def get_diagnosis_template():
    """Returns a template with default values for the diagnosis response"""
    return {
        "agent_response": "",          # summary of the diagnosis agent 
        "diagnosis": "Unable to determine",  # brief diagnosis (default provided)
        "detected_problem_cause": "Unknown",  # what caused the problem (default provided) 
        "type_specialist": "General handyman",  # type of specialist needed (default provided)
        "unlock_request_for_diy_solution": False,
        "diy_solution": None,
        "diy_links": None
    }

async def query_agent(user_message: str, session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Query the OpenAI model directly through OpenRouter.
    
    Args:
        user_message: The user's input
        session_data: Optional session context
    
    Returns:
        A dictionary with the structured diagnosis response
    """
    # Default session settings if none provided
    if not session_data:
        session_data = {
            "search_for_diy_solution": False,
            "user_location": "Unknown",
            "user_diy_skills": "beginner",
            "user_diy_tools": [],
            "home_type": "apartment",
            "solution_preferences": "professional",
            "time_available_for_repair": "limited",
            "favourite_language": "English"
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
            "X-Title": "DIY Home Diagnosis Agent" 
        }
        
        # Call the OpenAI API through OpenRouter directly (sync version)
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
        
        # Check if response is None
        if response is None:
            logger.error("Received None response from OpenRouter")
            return get_diagnosis_template()
            
        # Check if choices exists and is not empty
        if not hasattr(response, 'choices') or not response.choices:
            logger.error("Response does not have choices or choices is empty")
            return get_diagnosis_template()
            
        # Check if first choice exists
        if len(response.choices) == 0:
            logger.error("Response choices is empty")
            return get_diagnosis_template()
            
        # Check if message exists in first choice
        if not hasattr(response.choices[0], 'message'):
            logger.error("First choice does not have message")
            return get_diagnosis_template()
            
        # Check if content exists in message
        if not hasattr(response.choices[0].message, 'content') or response.choices[0].message.content is None:
            logger.error("Message does not have content or content is None")
            return get_diagnosis_template()
        
        # Extract the content from the response
        ai_message = response.choices[0].message.content
        logger.info(f"AI message content: {ai_message}")
        
        # Parse the JSON response
        try:
            diagnosis_data = json.loads(ai_message)
            logger.info(f"Parsed diagnosis data: {diagnosis_data}")
            
            # Ensure we have all required fields
            template = get_diagnosis_template()
            for key in template:
                if key not in diagnosis_data:
                    diagnosis_data[key] = template[key]
            
            # Set defaults for required fields if they are None
            if diagnosis_data["diagnosis"] is None:
                diagnosis_data["diagnosis"] = "Unable to determine"
                
            if diagnosis_data["detected_problem_cause"] is None:
                diagnosis_data["detected_problem_cause"] = "Unknown"
                
            if diagnosis_data["type_specialist"] is None:
                diagnosis_data["type_specialist"] = "General handyman"
            
            # Return the filled template
            return diagnosis_data
            
        except json.JSONDecodeError as e:
            # If the response isn't valid JSON, create a diagnostic error response
            logger.error(f"JSON decode error: {e}. Content: {ai_message}")
            template = get_diagnosis_template()
            template["agent_response"] = f"I'm sorry, I encountered an error processing your request. The response wasn't in the expected JSON format: {str(e)}"
            return template
            
    except Exception as e:
        # Handle any other errors
        logger.error(f"Error during OpenRouter query: {type(e).__name__} - {str(e)}")
        template = get_diagnosis_template()
        template["agent_response"] = f"An error occurred: {str(e)}"
        return template 