import streamlit as st
import asyncio
from app import ask_agent  # your async function that returns the agent reply

# Initialize Streamlit UI
st.set_page_config(page_title="Feedback Agent Chat", layout="centered")
st.title("🤖 Feedback Agent")

# --- Session State Setup ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# --- On First Load: Let the agent start the conversation ---
if not st.session_state.initialized:
    # You can customize the prompt the agent sees on startup:
    startup_prompt = "Ciao! Come posso aiutarti oggi?"
    # Run the async agent call
    agent_reply = asyncio.run(ask_agent(startup_prompt))
    # Store it in the chat history
    st.session_state.messages.append({"role": "assistant", "content": agent_reply})
    st.session_state.initialized = True

# --- Display chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User input ---
prompt = st.chat_input("Scrivi qui...")

if prompt:
    # Show the user's message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Placeholder for the agent's response
    response_area = st.chat_message("assistant")
    with response_area:
        response_text = st.empty()
        response_text.markdown("Thinking...")

    # Call ask_agent asynchronously and update the UI
    agent_reply = asyncio.run(ask_agent(prompt))
    response_text.markdown(agent_reply)
    st.session_state.messages.append({"role": "assistant", "content": agent_reply})
