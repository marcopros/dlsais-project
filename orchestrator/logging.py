import logging
import json
from datetime import datetime

# Configure standard logger
def setup_logger():
    logger = logging.getLogger("orchestrator")
    logger.setLevel(logging.INFO)
    
    # Console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create standard formatter
    standard_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(standard_formatter)
    logger.addHandler(console_handler)
    
    return logger

# Human-readable logger for conversation flow
class HumanReadableLogger:
    def __init__(self):
        self.logger = logging.getLogger("orchestrator.human_readable")
        self.logger.setLevel(logging.INFO)
        
        # Console handler with custom formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create a human-readable formatter
        human_formatter = HumanReadableFormatter()
        console_handler.setFormatter(human_formatter)
        self.logger.addHandler(console_handler)
    
    def log_user_message(self, message):
        self.logger.info({"type": "user_message", "content": message})
    
    def log_agent_call(self, agent_name, message):
        self.logger.info({"type": "agent_call", "agent": agent_name, "message": message})
    
    def log_agent_response(self, agent_name, response):
        self.logger.info({"type": "agent_response", "agent": agent_name, "response": response})
    
    def log_system_message(self, message):
        self.logger.info({"type": "system_message", "content": message})

class HumanReadableFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "msg") or not isinstance(record.msg, dict):
            return super().format(record)
        
        log_entry = record.msg
        log_type = log_entry.get("type", "")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if log_type == "user_message":
            return f"\n[{timestamp}] 👤 User: {log_entry.get('content', '')}"
        
        elif log_type == "agent_call":
            agent = log_entry.get("agent", "")
            message = log_entry.get("message", "")
            return f"\n[{timestamp}] 🔄 Calling {agent}: \"{message}\""
        
        elif log_type == "agent_response":
            agent = log_entry.get("agent", "")
            response = log_entry.get("response", "")
            
            # Handle different response formats
            if isinstance(response, dict):
                # Extract the most relevant information from complex responses
                if "result" in response and isinstance(response["result"], dict):
                    result = response["result"]
                    if "artifacts" in result and result["artifacts"]:
                        # Extract data from artifacts
                        try:
                            artifact_data = result["artifacts"][0]["parts"][0]["data"]
                            return f"\n[{timestamp}] ✅ {agent} response: {json.dumps(artifact_data, indent=2)}"
                        except (KeyError, IndexError):
                            pass
                    
                    # Extract text message if available
                    if "message" in result.get("status", {}):
                        try:
                            message_text = result["status"]["message"]["parts"][0]["text"]
                            if message_text:
                                return f"\n[{timestamp}] ✅ {agent}: \"{message_text}\""
                        except (KeyError, IndexError):
                            pass
            
            # Fallback to simple string representation
            return f"\n[{timestamp}] ✅ {agent} responded"
        
        elif log_type == "system_message":
            return f"\n[{timestamp}] 🤖 System: {log_entry.get('content', '')}"
        
        return super().format(record)

# Create singleton instance
human_readable_logger = HumanReadableLogger() 