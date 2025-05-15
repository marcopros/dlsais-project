#!/usr/bin/env python
"""
Demonstration script for the improved human-readable logging in the orchestrator.
This script simulates the conversation flow we saw in the example with clearer output.
"""

import asyncio
import sys
import os

# Add the parent directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.logging import human_readable_logger

async def simulate_conversation():
    """Simulate the conversation flow with human-readable logging."""
    # First user query - asking about a leaking sink in Italian
    user_query = "il lavandino perde acqua tantissimo"
    human_readable_logger.log_user_message(user_query)
    
    # System processes the request
    human_readable_logger.log_system_message("Processing your request...")
    
    # Diagnosis Agent call
    human_readable_logger.log_agent_call("Diagnosis Agent", user_query)
    
    # Diagnosis Agent response - simulated
    diagnosis_response = {
        "result": {
            "artifacts": [
                {
                    "parts": [
                        {
                            "data": {
                                "diagnosis": "The sink is leaking water excessively.",
                                "cause": "The most likely cause of the excessive water leaking is a worn out or damaged faucet or a loose connection in the plumbing under the sink.",
                                "specialist_needed": "Plumber",
                                "agent_response": "",
                                "detected_problem_cause": "Unknown",
                                "type_specialist": "General handyman",
                                "unlock_request_for_diy_solution": False,
                                "diy_solution": None,
                                "diy_links": None
                            }
                        }
                    ]
                }
            ]
        }
    }
    human_readable_logger.log_agent_response("Diagnosis Agent", diagnosis_response)
    
    # Validate diagnosis
    human_readable_logger.log_system_message("Diagnosis validation: ✅ Valid")
    
    # System message to user
    human_readable_logger.log_system_message("The diagnosis is valid and the agent suggests a `General handyman`.")
    human_readable_logger.log_system_message("Do you want to proceed with finding a `General handyman`?")
    
    # User responds yes
    human_readable_logger.log_user_message("si")
    
    # Matching Agent call
    human_readable_logger.log_agent_call("Matching Agent", "Find a General handyman")
    
    # Matching Agent response - needs more info
    matching_response_1 = {
        "result": {
            "status": {
                "message": {
                    "parts": [
                        {
                            "text": "Could you please provide the location (city or area) where you need the handyman service? Also, can you describe the issue you need help with? This will help me find the best match for you."
                        }
                    ]
                }
            }
        }
    }
    human_readable_logger.log_agent_response("Matching Agent", matching_response_1)
    
    # System asks for location
    human_readable_logger.log_system_message("The Matching Agent needs more information. Please provide the location (city or area) where you need the handyman service and describe the issue.")
    
    # User provides vague location
    human_readable_logger.log_user_message("any area")
    
    # Matching Agent call with updated info
    human_readable_logger.log_agent_call("Matching Agent", "Find a General handyman in any area. The sink is leaking water excessively.")
    
    # Matching Agent response - still needs specific location
    matching_response_2 = {
        "result": {
            "status": {
                "message": {
                    "parts": [
                        {
                            "text": "I need a location to find a handyman. Please provide one."
                        }
                    ]
                }
            }
        }
    }
    human_readable_logger.log_agent_response("Matching Agent", matching_response_2)
    
    # System asks for specific location
    human_readable_logger.log_system_message("The Matching Agent requires a location. Please provide the city or area where you need the handyman service.")
    
    # User provides specific location
    human_readable_logger.log_user_message("Milan")
    
    # Matching Agent call with specific location
    human_readable_logger.log_agent_call("Matching Agent", "Find a General handyman in Milan. The sink is leaking water excessively.")
    
    # Matching Agent final response - no handymen found
    matching_response_3 = {
        "result": {
            "status": {
                "message": {
                    "parts": [
                        {
                            "text": "I am very sorry, but it seems I am unable to find any cities with General handymen in my database. I recommend trying again with a different profession."
                        }
                    ]
                }
            }
        }
    }
    human_readable_logger.log_agent_response("Matching Agent", matching_response_3)
    
    # Final system message
    human_readable_logger.log_system_message("I am very sorry, but it seems I am unable to find any cities with General handymen in my database. I recommend trying again with a different profession.")

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" "*30 + "ORCHESTRATOR DEMO")
    print("="*80 + "\n")
    print("This is a demonstration of the new human-readable output format\n")
    
    asyncio.run(simulate_conversation())
    
    print("\n" + "="*80)
    print(" "*20 + "End of conversation simulation")
    print("="*80 + "\n") 