# Matching Agent
Until now the ADK Agent is able to make search on google using the ADK tool: google_search.

## References
- **[Google AI Studio](https://google.github.io/adk-docs/)**
- **[A Guide to Google’s Agent Development Kit (ADK)](https://ai.plainenglish.io/building-intelligent-agents-made-easy-a-guide-to-googles-agent-development-kit-adk-f583425bde8d)**


## Features
- Command-line interface for real-time user interaction.
- In-memory session management to maintain conversation context.
- Integration with Google search engine


## Installation
1. **Install Dependencies**: in an virtual enviroments install the dependecies: 
```bash 
pip install -r requirements.txt
```

2. **Create a .env file** in the directory and add the following:
```bash 
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=false 
```
**NB**: To get the GOOGLE_API_KEY use this link: **[Google AI Studio](https://aistudio.google.com/apikey)**

3. **Run the application** ( to terminate the conversation type 'quit' )
```bash 
python app.py
```
