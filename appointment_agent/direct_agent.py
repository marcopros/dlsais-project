import os
import json
import logging
from typing import Dict, Any, Optional
import datetime

import os
import json
import logging
from typing import Dict, Any, Optional
import datetime

# Import Google Generative AI SDK
import google.generativeai as genai

# Configura il logging
logger = logging.getLogger(__name__)

# The SYSTEM_PROMPT is now primarily managed by the LlmAgent in agent.py
# However, keeping a consistent prompt here might be useful for direct testing or fallback.
# This prompt should ideally match the 'instruction' in agent.py.
SYSTEM_PROMPT = """
You are the Appointment Agent, specialized in scheduling home repair appointments.

**Main Steps:**
1. From the user input, extract:
   - The issue that needs to be resolved.
   - The user_id and professional_id which are included at the beginning of the message in the format:
     "user_id:XXXX professional_id:YYYY [actual message]"
   - Note: DO NOT ask the user for their ID or the professional's ID as they are already included in the message.

2. **Confirm Appointment Details:**
   - Inform the user that you are ready to schedule an appointment with the selected professional (mention professional ID if name is not available, otherwise use name if you can retrieve it using a tool).
   - State the issue that needs to be resolved.
   - Ask the user to confirm if they wish to proceed with scheduling this appointment.

3. **If User Confirms:**
   - Ask the user for their preferred date and time for the appointment. Accept natural language inputs (e.g., "tomorrow afternoon", "next Monday at 10 AM", "as soon as possible").

4. **Interpret Date and Time:**
   - Use the user's response to determine the desired date and time.

5. **Schedule Appointment:**
   - Use the 'schedule_appointment' tool with the following details:
     - `user_id`: Extracted from the initial message.
     - `professional_id`: Extracted from the initial message.
     - `datetime`: The date and time interpreted from the user's response (format 'YYYY-MM-DD HH:MM'). If the user requested "as soon as possible", pass this phrase to the tool to handle.
     - `issue`: Extracted from the initial message.
     - `notes`: Include any relevant notes from the conversation.

6. **After the appointment is successfully scheduled (based on the tool's response):**
   - Provide the user with a confirmation summary including:
     - The date and time of the appointment.
     - The professional's name (if available from the tool response).
     - The issue to be addressed.
     - The appointment ID for reference.
   - IMPORTANT: End your response with a confirmation line in this format:
     "APPOINTMENT_CONFIRMED: <appointment_id> USER: <user_id> PROFESSIONAL: <professional_id>"
   - This format is crucial for the orchestrator to process the appointment correctly.

**Important Notes:**
- ALWAYS extract and use the user_id and professional_id from the message - never ask the user for these.
- Message format: "user_id:XXXX professional_id:YYYY [actual message]".
- Accept natural language date and time inputs.
- If the date/time is ambiguous, ask for clarification.
- Always confirm all details with the user before finalizing the appointment.
- After booking, always provide a summary of the scheduled appointment.
- Always include the structured confirmation line at the end of successful bookings.

**Tone:**
- Friendly and professional.
- Be clear and concise.
- Confirm all details with the user before finalizing the appointment.
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
    Query the Google Generative AI model directly.

    Args:
        user_message: The user's input
        session_data: Optional session context (currently not directly used in this simplified query)

    Returns:
        A dictionary with a simple text response from the model.
        Note: This direct query bypasses ADK's tool orchestration and structured response handling.
        It's primarily for basic text generation based on the prompt.
    """
    try:
        # Ensure genai is configured (should be done in server.py, but a check here is safe)
        if not genai.get_client().api_key:
             # This might happen if query_agent is called directly without server initialization
             logger.error("Google Generative AI SDK not configured. Cannot query model.")
             template = get_appointment_template()
             template["agent_response"] = "Error: Google API key not configured."
             return template

        # Get the generative model
        # Use the model specified in agent.py or a default
        # For direct query, we'll use a default model name compatible with genai
        model_name = "gemini-1.5-flash-latest" # Or match the model in agent.py if accessible

        model = genai.GenerativeModel(model_name)

        # Build the prompt including system instructions and user message
        # Note: Direct querying might not handle multi-turn conversation or session state
        # as effectively as the ADK Runner. This is a simplified interaction.
        prompt_parts = [
            SYSTEM_PROMPT,
            f"User: {user_message}",
            "Agent:" # Prompt the model to generate the agent's response
        ]

        # Generate content from the model
        response = await model.generate_content_async(prompt_parts)

        # Extract the text response
        if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            # Assuming the response is text
            agent_response_text = "".join([part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')])
            logger.info(f"Agent response text: {agent_response_text}")

            # For compatibility with the calling code (task_manager.py process_task before ADK integration),
            # we return a dictionary, even though the response isn't structured JSON from the model here.
            # The Task Manager's updated process_task (using ADK runner) will handle structured data.
            # This direct_agent query is now a simplified path.
            template = get_appointment_template()
            template["agent_response"] = agent_response_text
            # We cannot reliably extract structured data (appointment_scheduled, etc.) from a freeform text response here
            # This part of the return is less meaningful when bypassing ADK/tools.
            return template

        else:
            logger.warning("Model generated no content.")
            template = get_appointment_template()
            template["agent_response"] = "No response generated by the model."
            return template

    except Exception as e:
        logger.error(f"Error during Google Generative AI query: {type(e).__name__} - {str(e)}")
        template = get_appointment_template()
        template["agent_response"] = f"An error occurred during model query: {str(e)}"
        return template