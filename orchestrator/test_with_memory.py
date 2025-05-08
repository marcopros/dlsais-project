from datetime import datetime
import asyncio
import uuid

from A2A.client import A2ACardResolver, A2AClient
from google.adk.sessions import Session

# for persistent memory management
from persistent_memory import MongoMemoryService

memory_service = MongoMemoryService()


async def ask_agent_with_a2a(agent_url: str, session_id: str, user_text: str):
    try:
        # Recupera memoria utente
        memory = memory_service.search_memory(user_id=session_id, app_name="dlsais-app")
        if memory:
            print("\n--- [MEMORIA UTENTE] ---")
            for e in memory:
                print(f"{e['author']}: {e['text']}")
            print("--- FINE MEMORIA ---\n")

        # Setup A2A
        card_resolver = A2ACardResolver(agent_url)
        agent_card = card_resolver.get_agent_card()
        print(f"[DEBUG] Agent Card caricata per {agent_url}")
        client = A2AClient(agent_card=agent_card)
        task_id = str(uuid.uuid4())
        streaming = agent_card.capabilities.streaming
        timestamp_ms = int(datetime.now().timestamp() * 1000)
        payload = {
            "id": task_id,
            "sessionId": session_id,
            "acceptedOutputModes": ["text"],
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": user_text}],
                "id": str(uuid.uuid4()),
                "timestamp": timestamp_ms
            }
        }

        # Ricezione risposta
        full_response = ""
        if streaming:
            print(f"[AGENT]: ", end="", flush=True)
            response_stream = client.send_task_streaming(payload)
            async for result in response_stream:
                text = result.result.status.message.parts[0].text
                print(text, end="", flush=True)
                full_response += text
            print()
        else:
            taskResult = await client.send_task(payload)
            full_response = taskResult.result.status.message.parts[0].text
            print(f'[AGENT]: {full_response}')

        # Salva la sessione su MongoDB - Creazione diretta dell'oggetto Session
        now = datetime.now().timestamp()
        
        # Creiamo direttamente l'oggetto Session invece di usare from_dict
        # Rimozione del campo "type" che causa errori di validazione
        session = Session(
            id=session_id,
            user_id=session_id,
            app_name="dlsais-app",
            events=[
                {
                    "author": "user",
                    "content": {"parts": [{"text": user_text}]},  # Rimosso il campo "type"
                    "timestamp": now
                },
                {
                    "author": "agent",
                    "content": {"parts": [{"text": full_response}]},  # Rimosso il campo "type"
                    "timestamp": now
                }
            ],
            state={}
        )
        
        memory_service.add_session_to_memory(session)
    except Exception as e:
        print(f"[ERRORE]: {type(e).__name__} - {e}")


async def main():
    url = "http://localhost:8000/"
    session_id = str(uuid.uuid4())

    print("Chat Client A2A with Memory Started")
    print(f"\tSession ID: {session_id}")
    print(f"\tConnected to: {url}")
    print("Type 'quit' or ':q' to exit.")

    while True:
        try:
            user_input = input("[User]: ")
            if user_input.strip().lower() in ("quit", ":q"):
                print("Terminated chat.")
                break
            await ask_agent_with_a2a(url, session_id, user_input)
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            break


if __name__ == "__main__":
    asyncio.run(main())
