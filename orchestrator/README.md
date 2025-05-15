# Orchestrator with Human-Readable Logging

This component adds human-readable logging to the orchestrator, making it easier to understand the conversation flow between users and the different agents in the system.

## Overview

The orchestrator in this system is responsible for coordinating conversations between:

1. **Diagnosis Agent** - understands problems and determines if DIY or professional help is needed
2. **Matching Agent** - finds appropriate professionals when needed
3. **Appointment Agent** - schedules appointments with matched professionals

The standard output from the orchestrator can be difficult to follow due to its technical nature. The human-readable logging system transforms this output into a clear, conversational format that's easy to understand.

## Features

- 👤 **Clear User Messages** - Shows what the user said
- 🔄 **Agent Call Tracking** - Shows when each agent is called and what data is sent
- ✅ **Agent Response Display** - Shows responses from agents in a readable format
- 🤖 **System Messages** - Shows orchestrator decisions and instructions to the user

## How to Use

### In Code

Import and use the human-readable logger in your code:

```python
from orchestrator.logging import human_readable_logger

# Log a user message
human_readable_logger.log_user_message("My sink is leaking")

# Log an agent call
human_readable_logger.log_agent_call("Diagnosis Agent", "My sink is leaking")

# Log an agent response
human_readable_logger.log_agent_response("Diagnosis Agent", response_object)

# Log a system message
human_readable_logger.log_system_message("The diagnosis is valid")
```

### Demo

You can run the included demo to see the human-readable output in action:

```bash
python -m orchestrator.demo
```

## Output Format

The human-readable output uses this format:

```
[HH:MM:SS] 👤 User: <user message>

[HH:MM:SS] 🔄 Calling <agent>: "<message>"

[HH:MM:SS] ✅ <agent>: "<agent response>"
or
[HH:MM:SS] ✅ <agent> response: <JSON data>

[HH:MM:SS] 🤖 System: <system message>
```

## Example Conversation

```
[15:29:01] 👤 User: il lavandino perde acqua tantissimo

[15:29:01] 🤖 System: Processing your request...

[15:29:01] 🔄 Calling Diagnosis Agent: "il lavandino perde acqua tantissimo"

[15:29:01] ✅ Diagnosis Agent response: {
  "diagnosis": "The sink is leaking water excessively.",
  "cause": "The most likely cause of the excessive water leaking is a worn out or damaged faucet or a loose connection in the plumbing under the sink.",
  "specialist_needed": "Plumber",
  "agent_response": "",
  "detected_problem_cause": "Unknown",
  "type_specialist": "General handyman",
  "unlock_request_for_diy_solution": false,
  "diy_solution": null,
  "diy_links": null
}

[15:29:01] 🤖 System: Diagnosis validation: ✅ Valid

[15:29:01] 🤖 System: The diagnosis is valid and the agent suggests a `General handyman`.

[15:29:01] 🤖 System: Do you want to proceed with finding a `General handyman`?

[15:29:02] 👤 User: si

[15:29:02] 🔄 Calling Matching Agent: "Find a General handyman"

...
```

## How It Works

The system uses a custom formatter for logging that transforms the raw API responses and function calls into a human-readable format. The formatter:

1. Extracts relevant information from complex response objects
2. Formats messages with appropriate timestamps and icons
3. Structures the output to clearly show the conversation flow
