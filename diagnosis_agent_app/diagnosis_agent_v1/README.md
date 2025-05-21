Sure! Here's the **README.md** in **English**, polished and ready for your repository.

---

### 📄 `README.md`

````markdown
# 🛠️ Home-Repair Multi-Agent API

A FastAPI-based backend powered by AI agents that help users diagnose home repair issues and suggest DIY or professional solutions.

---

## 🚀 Quick Start

### 1. Clone the project
```bash
git clone https://github.com/your-username/home-repair-ai.git
cd home-repair-ai
````

### 2. Install dependencies

Make sure you have **Python 3.10+** installed, then run:

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root with your credentials (e.g., API keys):

```env
# .env
OPENAI_API_KEY=sk-...
SERPAPI_API_KEY=...
```

### 4. Run the server

```bash
uvicorn server:app --reload
```

The API will be available at:
📡 `http://localhost:8000`


### 5. UI
Open the file index.html in your browser to access the UI for interacting with the API.

```bash
open index.html   [for macOS]
start index.html  [for Windows]
```

---

## 🧪 Swagger UI

FastAPI provides two built-in documentation UIs:

* 📘 Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* 📕 ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Use these to test the endpoints interactively.

---

## 🧩 Main Endpoints

### `POST /start`

Start a new session by submitting user preferences (e.g. language, location, tools, etc.).

### `POST /message`

Send a message (e.g. a home issue description) and get a response from the current AI agent.

---

## 📁 Project Structure

```
.
├── server.py            # FastAPI entry point
├── agents/              # Contains agent logic and tools
├── agent.py             # Agent definitions and tool setup
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (not committed)
```

---

## ✅ Requirements

* Python 3.10+
* Packages in `requirements.txt`, including:

  * `fastapi`
  * `uvicorn`
  * `pydantic`
  * `openai`
  * `python-dotenv`
  * (and any agent-related libraries)

---
