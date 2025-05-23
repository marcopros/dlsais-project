# Diagnosis Agent README

A modular and intelligent diagnosis agent designed to identify user problems and suggest either DIY solutions or forward tasks to appropriate agents. This project integrates with a DIY agent for handling self-help queries using web search and video tutorials.

---
## 🔧 Tools Used

### Diagnosis Agent:
- **DIY Agent**: Sub-agent responsible for retrieving DIY solutions

### DIY Agent:
- **WebSearchTool()**: Searches the web for relevant solutions
- **search_video_tutorial()**: Finds YouTube video tutorials based on the query

---

## 📁 Directory Structure
```bash
├── /carloImplementation        # Alternative implementation using OpenRoute 
├── /oldImplementation          # Original implementation
├── a2a_agent_card.json         # A2A card definition for the agent
├── server.py                   # Starts the A2A server for the Diagnosis Agent
├── session.py                  # Experimental session manager (currently not working)
├── task_manager.py             # Task manager for handling A2A workflows
├── test.py                     # Test client to interact with the agent
```


## ▶️ How to Run
1. **Start the A2A Server**
   ```bash
   python -m diagnosis_agent_app.server
   ```

2. **Run the Test Client**
   ```bash
   python -m diagnosis_agent_app.test
   ```

3. **Chat with the Agent**
   - Once both server and client are running, you can begin chatting in the terminal.
   - The agent will diagnose your issue and respond accordingly.

---

## 📝 Notes

- `session.py` was an early attempt at managing conversation sessions but currently isn't functional.
- The system follows the **Agent-to-Agent (A2A)** communication model.