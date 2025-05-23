#!/usr/bin/env python3
"""
Test MongoDB Connection

Questo script verifica la connessione al database MongoDB e esegue alcune operazioni
di base per assicurarsi che il database funzioni correttamente con tutti gli agenti.
"""

import os
import sys
import getpass
import time
from pathlib import Path
from pymongo import MongoClient, errors as pymongo_errors
from dotenv import load_dotenv

# Aggiunta della directory radice al path per importare moduli dal progetto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import delle funzioni da testare
from database.utils import (
    get_mongodb_connection,
    getProfessionals,
    getCities,
    registerUser,
    loginUser,
    createUserSession
)

# Funzione per caricare le variabili d'ambiente e gestire i casi mancanti
def load_env_variables():
    """Carica le variabili d'ambiente e richiede input se mancanti."""
    # Carica le variabili d'ambiente dal file .env se presente
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Controlla se la password MongoDB è disponibile
    mongodb_password = os.getenv("MONGODB_PASSWORD")
    if not mongodb_password:
        print("⚠️ MONGODB_PASSWORD non trovata nel file .env")
        print("Per procedere, inserisci manualmente la password (non sarà salvata):")
        mongodb_password = getpass.getpass("Password MongoDB: ")
        os.environ["MONGODB_PASSWORD"] = mongodb_password
    
    return {
        "mongodb_password": mongodb_password
    }

# Funzione per testare la connessione al database
def test_mongodb_connection():
    """Testa la connessione al database MongoDB."""
    print(f"🔄 Tentativo di connessione a MongoDB con retry logic...")
    
    try:
        # Test della funzione di connessione con retry
        client, db = get_mongodb_connection(max_retries=3, retry_delay=1)
        print("✅ Connessione al database riuscita!")
        
        # Test delle collezioni
        collection_names = db.list_collection_names()
        print(f"📋 Collezioni disponibili: {', '.join(collection_names) if collection_names else 'Nessuna'}")
        
        # Test query professioni
        if "professionals" in collection_names:
            professionals_count = db.professionals.count_documents({})
            print(f"👨‍🔧 Numero di professionisti nel database: {professionals_count}")
            
            # Esempio di query: professionisti per tipologia
            professions = db.professionals.distinct("profession")
            print(f"🔍 Tipologie di professionisti: {', '.join(professions) if professions else 'Nessuna'}")
            
            # Esempio di query: città disponibili
            cities = db.professionals.distinct("location")
            print(f"🏙️ Città disponibili: {', '.join(cities[:5])}{'...' if len(cities) > 5 else ''}")
        
        # Test query utenti
        if "users" in collection_names:
            users_count = db.users.count_documents({})
            print(f"👥 Numero di utenti nel database: {users_count}")
        
        # Chiusura della connessione
        client.close()
        print("🔒 Connessione chiusa correttamente")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test di connessione MongoDB: {e}")
        return False

# Test delle principali funzioni utilizzate dagli agenti
def test_agent_functions():
    """Testa le funzioni utilizzate dagli vari agenti."""
    print("\n📋 Test delle funzioni utilizzate dagli agenti:")
    
    # Test 1: getProfessionals (utilizzato dal Matching Agent)
    print("\n🧪 TEST 1: getProfessionals (Matching Agent)")
    try:
        plumbers = getProfessionals(profession="Idraulico")
        print(f"  Risultato: {len(plumbers)} idraulici trovati")
        
        rome_professionals = getProfessionals(location="Milan")
        print(f"  Risultato: {len(rome_professionals)} professionisti trovati a Milano")
        
        plumbers_in_rome = getProfessionals(profession="Idraulico", location="Milano")
        print(f"  Risultato: {len(plumbers_in_rome)} idraulici trovati a Milano")
        
        if plumbers_in_rome:
            print(f"  Esempio: {plumbers_in_rome[0].get('name', 'N/A')} - {plumbers_in_rome[0].get('phone', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Errore durante il test di getProfessionals: {e}")

    # Test 2: getCities (utilizzato dal Matching Agent)
    print("\n🧪 TEST 2: getCities (Matching Agent)")
    try:
        all_cities = getCities()
        print(f"  Risultato: {len(all_cities)} città trovate")
        
        cities_with_electricians = getCities(profession="Elettricista")
        print(f"  Risultato: {len(cities_with_electricians)} città con elettricisti")
        
        if cities_with_electricians:
            print(f"  Esempi: {', '.join(cities_with_electricians[:3])}")
    except Exception as e:
        print(f"  ❌ Errore durante il test di getCities: {e}")

    # Test 3: registerUser & loginUser (utilizzati dal Client e Orchestrator)
    print("\n🧪 TEST 3: registerUser & loginUser (Client/Orchestrator)")
    try:
        # Genera un email univoco per il test
        test_email = f"test_{int(time.time())}@example.com"
        test_password = "password123"
        
        # Registra un utente di test
        reg_result = registerUser(
            name="Test User", 
            email=test_email, 
            password=test_password, 
            phone="+390123456789"
        )
        
        print(f"  Registrazione: {reg_result.get('success')}, {reg_result.get('message')}")
        
        if reg_result.get('success'):
            user_id = reg_result.get('user_id')
            print(f"  Utente creato con ID: {user_id}")
            
            # Prova ad effettuare il login con l'utente appena creato
            login_result = loginUser(test_email, test_password)
            print(f"  Login: {login_result.get('success')}, {login_result.get('message')}")
            
            if login_result.get('success'):
                # Prova a creare una sessione
                session_result = createUserSession(user_id)
                print(f"  Creazione sessione: {session_result.get('success')}")
                if session_result.get('success'):
                    print(f"  Session ID: {session_result.get('session_id')}")
    except Exception as e:
        print(f"  ❌ Errore durante il test di registerUser/loginUser: {e}")

# Funzione principale
def main():
    """Funzione principale per l'esecuzione dei test."""
    print("🔍 Test di connessione e integrazione del database MongoDB\n")
    
    # Carica le variabili d'ambiente necessarie
    env_vars = load_env_variables()
    
    # Test connessione base
    connection_success = test_mongodb_connection()
    
    # Se la connessione ha successo, esegui i test delle funzioni
    if connection_success:
        print("\n📊 Esecuzione dei test di integrazione per gli agenti...")
        test_agent_functions()
    
    print("\n🏁 Test completati")

if __name__ == "__main__":
    main() 