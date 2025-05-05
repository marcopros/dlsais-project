# 🛠️ Feedback Analysis with OpenAI Agent

## ✅ Requirements

- Python 3.9+
- OpenAI API key

---

## 📦 1) Install dependencies

```bash
pip install -r requirements.txt
````

---

## 🔑 2) Set your OpenAI API key

Create a `.env` file in the root directory and add the following line:

```
OPENAI_API_KEY=sk-your-api-key
```

Make sure the key is valid and has access to GPT-4 (or GPT-4o).

---

## 🚀 3) Run the FastAPI server

```bash
uvicorn server_feedback:app --reload --host 0.0.0.0 --port 8001
```

This will start the backend API at:

```
http://localhost:8001/analyze
```

---

## 🌐 4) Open the HTML interface

Open the `feedback.html` file in your browser (included in this project or inside `feedback_page.zip`).

You can submit a star rating and either a written comment or select predefined feedback chips.
After submission, the AI agent's analysis will be displayed directly on the page.

---

## 🧪 Test the API directly (optional)

You can also send requests manually using tools like `curl` or Postman:

```bash
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"feedback": { ... }}'
```

---

## ✅ Example response from the agent

```json
{
  "rating_scoring": 0.8,
  "tag_scoring": 0.6,
  "time_decay": 0.97,
  "sentiment_scoring": 0.5,
  "updated_trust_score": 0.73,
  "jobTitle": "Electrical Repair",
  "professional": "Marco Bianchi, Electrician",
  "date": "2025-04-28"
}
```

---

🧠 Built with OpenAI + FastAPI + Tailwind CSS
