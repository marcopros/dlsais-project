import uvicorn

uvicorn.run("server_feedback:app", host="0.0.0.0", port=8009, reload=True)