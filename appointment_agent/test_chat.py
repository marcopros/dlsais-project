#!/usr/bin/env python
"""
Script di test per simulare una chat con l'appointment agent.
Questo script crea un'interfaccia a riga di comando per interagire con l'agent.
"""

import requests
import json
import uuid
import sys
import os
from datetime import datetime

# Configurazione dell'endpoint
AGENT_URL = "http://localhost:8003/"
SESSION_ID = str(uuid.uuid4())[:10]  # Crea un ID sessione casuale

def clear_screen():
    """Pulisce lo schermo del terminale"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_welcome():
    """Stampa un messaggio di benvenuto"""
    clear_screen()
    print("\n" + "=" * 80)
    print(" " * 25 + "APPOINTMENT AGENT CHAT TEST")
    print("=" * 80)
    print("\nBenvenuto nella chat di test con l'Appointment Agent.")
    print("Questo agente ti aiuta a pianificare appuntamenti tra utenti e professionisti.")
    print("\nSuggermenti:")
    print(" - Puoi richiedere un appuntamento specificando utente, professionista e problema")
    print(" - Usa gli ID utente e professionista del database di test")
    print(" - Scrivi 'exit' o 'quit' per uscire")
    print(" - Scrivi 'clear' per pulire lo schermo")
    print("\nID utente di esempio:       681e685a8c9d17d973875c31")
    print("ID professionista esempio: 6810f7d1cad59974220357b0")
    print("-" * 80 + "\n")

def send_message(text):
    """
    Invia un messaggio all'agent usando il protocollo A2A
    
    Args:
        text (str): Il testo del messaggio da inviare
        
    Returns:
        str: La risposta dell'agent o None in caso di errore
    """
    # Crea un ID univoco per questa richiesta
    task_id = f"task-{str(uuid.uuid4())[:8]}"
    
    # Costruisci la richiesta A2A
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tasks/send",
        "params": {
            "id": task_id,
            "sessionId": SESSION_ID,
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        }
    }
    
    try:
        # Invia la richiesta all'agent
        response = requests.post(
            AGENT_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60  # Timeout più lungo per dare tempo all'agent di rispondere
        )
        
        # Verifica se la richiesta ha avuto successo
        if response.status_code == 200:
            # Analizza la risposta JSON
            response_data = response.json()
            
            # Estrai la risposta dell'agent
            if "result" in response_data and response_data["result"]:
                result = response_data["result"]
                if "status" in result and "message" in result["status"]:
                    # Cerca la parte di testo nella risposta
                    message = result["status"]["message"]
                    for part in message.get("parts", []):
                        if part.get("type") == "text":
                            return part.get("text", "")
            
            # Se non troviamo il testo, restituiamo la risposta come JSON formattato
            return f"Risposta ricevuta, ma in formato non previsto:\n{json.dumps(response_data, indent=2)}"
        else:
            return f"Errore nella richiesta: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Errore nella comunicazione con l'agent: {str(e)}"

def chat_loop():
    """Loop principale della chat"""
    print_welcome()
    
    try:
        while True:
            # Input dell'utente
            user_input = input("\n\033[94mTu:\033[0m ")
            
            # Comandi speciali
            if user_input.lower() in ['exit', 'quit']:
                print("\nGrazie per aver usato l'Appointment Agent Test. Arrivederci!")
                break
            elif user_input.lower() == 'clear':
                clear_screen()
                continue
            elif not user_input.strip():
                continue
            
            # Stampa un indicatore di attesa
            print("\n\033[93mAttendere risposta...\033[0m")
            
            # Invia il messaggio all'agent
            response = send_message(user_input)
            
            # Visualizza la risposta dell'agent
            print(f"\n\033[92mAppointment Agent:\033[0m {response}\n")
            print("-" * 80)
            
    except KeyboardInterrupt:
        print("\n\nChat interrotta dall'utente. Arrivederci!")
    except Exception as e:
        print(f"\n\nErrore imprevisto: {str(e)}")

if __name__ == "__main__":
    chat_loop() 