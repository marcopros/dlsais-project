# Appointment Agent

## Overview

The Appointment Agent facilitates scheduling appointments between users and professionals for home repair interventions. It uses the A2A (Agent-to-Agent) protocol to manage communication and appointment scheduling.

## Functionality

The Appointment Agent performs the following key tasks:

1. Extracts user and professional information from the input query
2. Checks user availability for potential appointment times
3. Checks professional availability for potential appointment times
4. Finds matching time slots between the user and professional
5. Presents options to the user or suggests alternatives if no matches are found
6. Confirms and schedules the appointment once a time slot is selected

## Technical Details

- Implements the A2A protocol for agent communication
- Uses Google ADK (Agent Development Kit) for LLM functionality
- Provides both streaming and non-streaming response capabilities
- Manages session state to maintain context across interactions

## Tools

The agent includes the following tools:

1. `check_user_availability`: Retrieves available time slots for a user
2. `check_professional_availability`: Retrieves available time slots for a professional
3. `schedule_appointment`: Confirms and records the appointment details

## Running the Agent

To run the Appointment Agent:

1. Ensure you have the required dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Set the Google API key in your environment:

   ```
   export GOOGLE_API_KEY=your_api_key
   ```

3. Run the server:
   ```
   python -m appointment_agent.server
   ```

The agent will be available at http://localhost:8003/ by default.

## Example Usage

Example input:

```
I need to schedule an appointment with electrician John Smith (ID: 12345) to fix my broken circuit breaker. My user ID is 54321.
```

The agent will:

1. Extract the user ID (54321) and professional ID (12345)
2. Check availability for both parties
3. Present matching time slots or alternatives
4. Confirm the appointment once a time slot is selected
