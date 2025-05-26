# Appointment Agent

## Overview

The Appointment Agent is a specialized agent that facilitates scheduling appointments between users and professionals for home repair interventions. It leverages the A2A (Agent-to-Agent) protocol for communication and interaction within the larger home repair assistant system.

## Functionality

The Appointment Agent now follows a refined workflow to schedule appointments:

1.  **Receive Initial Request:** Receives a request, typically from an orchestrator agent, including the user ID, the selected professional's ID, and a summary of the problem.
2.  **Confirm Details:** Presents the professional's details (name, profession, etc. - retrieved using an internal helper function) and the problem summary to the user, asking for confirmation to proceed with scheduling.
3.  **Request Date and Time:** If the user confirms, asks for their preferred date and time for the appointment, accepting natural language input.
4.  **Interpret Date and Time:** Parses the user's response to determine the specific date and time.
5.  **Schedule Appointment:** Uses the `schedule_appointment` tool to create the appointment entry in the database, incorporating the user's location (retrieved using an internal helper function), the professional's ID, the scheduled time, and the problem summary.
6.  **Confirm Completion:** Provides a confirmation summary to the user and signals completion to the orchestrator with a structured message.

## Technical Details

- Implements the A2A protocol for agent-to-agent communication.
- Uses Google ADK (Agent Development Kit) for managing the LLM's interaction flow and tool usage.
- Utilizes OpenRouter for accessing LLM models (configured in `direct_agent.py` and `server.py`).
- Provides streaming response capabilities via the Task Manager.
- Manages session state to maintain context across the conversation with the user.
- Interacts with a MongoDB database (or an in-memory fallback) for storing appointments and retrieving user/professional details and availability. The appointment data is stored in the `appointments` collection, following the schema defined in `database/models/Appointment.js`.

## Tools

The agent interacts with the following tools and internal helper functions:

1.  `check_user_availability`:

    - **Description:** Retrieves available time slots for a specific user.
    - **Input:**
      - `user_id` (string): The ID of the user.
      - `date_range` (string, optional): A date range to check (e.g., "YYYY-MM-DD to YYYY-MM-DD").
      - `date_text` (string, optional): Natural language date preference (e.g., "tomorrow", "as soon as possible"). Overrides `date_range` if provided.
    - **Output:**
      - `dict`: Contains `status` ('success' or 'error'), `available_slots` (list of strings, format 'YYYY-MM-DD HH:MM'), `message` (string), and the `user_id`. May also include `first_available` (string) if "as soon as possible" was requested.

2.  `check_professional_availability`:

    - **Description:** Retrieves available time slots for a specific professional.
    - **Input:**
      - `professional_id` (string): The ID of the professional.
      - `date_range` (string, optional): A date range to check (e.g., "YYYY-MM-DD to YYYY-MM-DD").
      - `date_text` (string, optional): Natural language date preference (e.g., "tomorrow", "as soon as possible"). Overrides `date_range` if provided.
    - **Output:**
      - `dict`: Contains `status` ('success' or 'error'), `available_slots` (list of strings, format 'YYYY-MM-DD HH:MM'), `message` (string), and the `professional_id`. May also include `first_available` (string) if "as soon as possible" was requested.

3.  `schedule_appointment`:
    - **Description:** Creates a new appointment entry in the database and updates availability.
    - **Input:**
      - `appointment_details` (dict): A dictionary containing:
        - `user_id` (string): ID of the user.
        - `professional_id` (string): ID of the professional.
        - `datetime` (string): The scheduled date and time (format 'YYYY-MM-DD HH:MM') or natural language ("as soon as possible").
        - `issue` (string): Description of the problem.
        - `notes` (string, optional): Additional notes.
    - **Output:**
      - `dict`: Contains `status` ('success', 'warning', or 'error'), `appointment_id` (string, if successful/warning), `appointment_details` (dict with scheduled info, if successful/warning), `message` (string), `user_id` (string), and `professional_id` (string).

### Internal Helper Functions (used by the agent/tools)

- `get_user_details`:

  - **Description:** Retrieves detailed information about a user from the database.
  - **Input:**
    - `user_id` (string): The ID of the user.
  - **Output:**
    - `dict` or `None`: A dictionary containing user details (e.g., `_id`, `location` as `{city, zipCode}`, etc.) or `None` if not found.

- `get_professional_details`:
  - **Description:** Retrieves detailed information about a professional from the database.
  - **Input:**
    - `professional_id` (string): The ID of the professional.
  - **Output:**
    - `dict` or `None`: A dictionary containing professional details (e.g., `_id`, `name`, `profession`, etc.) or `None` if not found.

## Database Schema Reference

The appointment data is stored in the `appointments` collection and conforms to the schema defined in [`database/models/Appointment.js`](database/models/Appointment.js):

```javascript
const mongoose = require("mongoose");

const appointmentSchema = new mongoose.Schema({
  user_id: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  professional_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "Professional",
  },
  location: {
    city: String,
    zipCode: String,
  },
  scheduled_time: Date,
  confermation_dead_line: Date,
  problem_summary: String,
  status: String,
});
```

## Running the Agent

To run the Appointment Agent:

1.  Ensure you have the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2.  Set the OpenRouter API key in your environment:

    ```bash
    export OPENROUTER_API_KEY=your_api_key
    ```

    (Note: You may also need to configure MongoDB connection details via `MONGODB_URI` and `DB_NAME` environment variables if not using the default in-memory database).

3.  Run the server:

    ```bash
    python -m appointment_agent.server
    ```

    The agent will be available at `http://localhost:8003/` by default.

## Example Usage

Example input (typically from an orchestrator):

```
user_id:USER_ID_HERE professional_id:PROF_ID_HERE I need help to fix my broken circuit breaker.
```

The agent will then engage in a conversation with the user:

1.  **Agent:** "Okay, sono pronto a schedulare un appuntamento con [Professional Name] per risolvere il problema: 'fix my broken circuit breaker'. Confermi di voler procedere?"
2.  **User:** "Sì, confermo."
3.  **Agent:** "Ottimo. Qual è la data e l'ora che preferisci per l'intervento?"
4.  **User:** "Domani pomeriggio alle 15:30"
5.  **Agent:** (Interprets date/time, uses `schedule_appointment` tool, and provides confirmation)
    "Appuntamento schedulato con successo con [Professional Name] per 'fix my broken circuit breaker' il [Formatted Date] alle [Formatted Time] a [User Location]. L'ID dell'appuntamento è [Appointment ID]. APPOINTMENT_CONFIRMED: [Appointment ID] USER: [User ID] PROFESSIONAL: [Professional ID]"
