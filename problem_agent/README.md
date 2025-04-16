# 🧩 `problem_agent` – Home Repair Assistant: Problem Handling Agents

This package is part of a modular AI system designed to help users resolve household issues through intelligent conversation and diagnostic steps. The `problem_agent` module includes the agents responsible for:

1. Understanding the user's problem  
2. Diagnosing possible DIY solutions  
3. Passing results to the orchestrator for further action

> 💡 This is **Step 1** of a larger system orchestrated by a central agent (`orchestrator_agent`), which coordinates all actions.

---

## 🔹 Agents in this module

### 👂 `Listener Agent`
**Purpose:** Understand the user's home issue in detail.  
**Behavior:**
- Gathers key info from the user (what, where, when, type of issue).
- Clarifies and confirms inputs.
- Passes a structured description to the next agent.

### 🔧 `DIY Agent`
**Purpose:** Determine if the issue can be solved with a DIY solution.  
**Behavior:**
- Searches a local knowledge base and/or uses **Google Search**.
- Returns a clear fix or recommends escalation.
> 🔍 This agent is tool-enabled using `google_search`.

---

## ⚙️ System Architecture (Brief)

This module is part of a broader agent system:

```
User ↔ Listener Agent → DIY Agent → Orchestrator Agent → [Professional Finder Agent]
```

---

## 📁 Folder Structure

```
problem_agent/
├── __init__.py             # Package initializer
├── agent.py                # Main agent definitions
├── diy_agent.py            # DIY troubleshooting agent
├── listener_agent.py       # Listener agent to capture the problem
├── .env                    # API key & settings
├── .gitignore              # Ignored files
└── README.md               # You're here!
```

---

## 🛠️ Setup

### 1. Set up Environment & Install ADK

```bash
python -m venv .venv
# Activate it:
# macOS/Linux
source .venv/bin/activate
# Windows CMD
.venv\Scripts\activate.bat
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the SDK:

```bash
pip install google-adk
```

---

### 2. Create `.env` File

Inside `problem_agent/`, create a `.env` file with the following:

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=PASTE_YOUR_ACTUAL_API_KEY_HERE
```

Replace the placeholder with your real [Google Generative AI API key](https://makersuite.google.com/app/apikey).

---

## ▶️ Run Your Agent

There are multiple ways to interact with your agent:

- 🌐 **Dev UI**: `adk web`  
- 🖥️ **Terminal**: `adk run`  
- ⚙️ **API Server**: `adk api_server`  

### 🚀 Launch the Dev UI

```bash
adk web
```

1. Open the URL provided in the terminal (usually `http://localhost:8000` or `http://127.0.0.1:8000`).
2. In the top-left corner, select your agent from the dropdown — choose **`problem_agent`**.

---

### 🛠️ Troubleshooting

If you don’t see `problem_agent` in the UI:

- Make sure you're running `adk web` from the **parent directory** of `problem_agent/` (e.g., the root of your project).
- Ensure your `agent.py` file is properly configured with an exported agent.

📚 For full details, see the official [Google ADK Quickstart Guide](https://google.github.io/adk-docs/get-started/quickstart/#run-your-agent).

---

## ✅ What’s Left to Implement

- 🧠 **Session Management**:  
  Implement logic to maintain conversational context, allowing agents to:
  - Share information between turns
  - Remember past interactions
  - Store user preferences (e.g., preferred language, location, skill level)
