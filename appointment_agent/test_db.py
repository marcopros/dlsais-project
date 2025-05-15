#!/usr/bin/env python
"""
Test script per verificare la connessione al database MongoDB e le operazioni CRUD
per l'appointment agent.
"""

import sys
from datetime import datetime, timedelta
from bson.objectid import ObjectId

# Import delle funzioni di database dell'appointment agent
from appointment_agent.database import (
    client, db, 
    USERS_COLLECTION, PROFESSIONALS_COLLECTION, APPOINTMENTS_COLLECTION, AVAILABILITY_COLLECTION,
    get_user_availability, get_professional_availability, 
    create_appointment, update_availability_after_booking
)

def test_database_connection():
    """Test della connessione al database"""
    print("=== Test Connessione al Database ===")
    try:
        # Verifica che il client sia connesso
        client.admin.command('ping')
        print("✅ Connessione al server MongoDB riuscita")
        
        # Verifica che possiamo accedere al database
        db_names = client.list_database_names()
        print(f"Database disponibili: {', '.join(db_names)}")
        
        # Verifica che possiamo accedere alle collections
        collection_names = db.list_collection_names()
        print(f"Collections nel database '{db.name}': {', '.join(collection_names)}")
        
        # Verifica che le collections necessarie esistano
        required_collections = [USERS_COLLECTION, PROFESSIONALS_COLLECTION, APPOINTMENTS_COLLECTION]
        missing_collections = []
        
        for coll in required_collections:
            if coll not in collection_names:
                missing_collections.append(coll)
        
        if missing_collections:
            print(f"⚠️ Attenzione: Le seguenti collections sono mancanti: {', '.join(missing_collections)}")
        else:
            print("✅ Tutte le collections richieste sono presenti")
            
        return True
    except Exception as e:
        print(f"❌ Errore di connessione al database: {str(e)}")
        return False

def test_data_retrieval():
    """Test del recupero dei dati"""
    print("\n=== Test Recupero Dati ===")
    
    try:
        # Verifica che possiamo recuperare utenti
        user_count = db[USERS_COLLECTION].count_documents({})
        print(f"Trovati {user_count} utenti nel database")
        
        if user_count > 0:
            # Prendi il primo utente
            user = db[USERS_COLLECTION].find_one({})
            print(f"Esempio utente: ID={user['_id']}, Nome={user.get('name', 'N/A')}")
            user_id = str(user['_id'])
        else:
            print("⚠️ Nessun utente trovato nel database")
            user_id = None
            
        # Verifica che possiamo recuperare professionisti
        prof_count = db[PROFESSIONALS_COLLECTION].count_documents({})
        print(f"Trovati {prof_count} professionisti nel database")
        
        if prof_count > 0:
            # Prendi il primo professionista
            prof = db[PROFESSIONALS_COLLECTION].find_one({})
            print(f"Esempio professionista: ID={prof['_id']}, Nome={prof.get('name', 'N/A')}, Professione={prof.get('profession', 'N/A')}")
            prof_id = str(prof['_id'])
        else:
            print("⚠️ Nessun professionista trovato nel database")
            prof_id = None
        
        return user_id, prof_id
    except Exception as e:
        print(f"❌ Errore nel recupero dei dati: {str(e)}")
        return None, None

def test_availability():
    """Test delle funzioni di disponibilità"""
    print("\n=== Test Disponibilità ===")
    
    try:
        # Verifica se la collection delle disponibilità esiste
        collection_names = db.list_collection_names()
        if AVAILABILITY_COLLECTION not in collection_names:
            print(f"⚠️ Collection {AVAILABILITY_COLLECTION} non esiste ancora - creandola ora")
            
            # Crea alcuni dati di esempio per la disponibilità
            user_id = "user_test_1"
            prof_id = "prof_test_1"
            
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
            
            # Crea slot di esempio
            slots = []
            current_date = start_date
            while current_date <= end_date:
                for hour in [9, 11, 14, 16]:
                    slot = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    slots.append(slot.strftime('%Y-%m-%d %H:%M'))
                current_date += timedelta(days=1)
            
            # Crea documenti di disponibilità
            db[AVAILABILITY_COLLECTION].insert_one({
                "entity_id": user_id,
                "entity_type": "user",
                "date_range": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "slots": slots
            })
            
            db[AVAILABILITY_COLLECTION].insert_one({
                "entity_id": prof_id,
                "entity_type": "professional",
                "date_range": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "slots": slots
            })
            
            print(f"✅ Creati dati di test per disponibilità")
        else:
            print(f"✅ Collection {AVAILABILITY_COLLECTION} esiste")
            
        # Verifica che possiamo recuperare le disponibilità
        try:
            # Usa i dati creati o cerca un documento esistente
            availability_doc = db[AVAILABILITY_COLLECTION].find_one({})
            
            if availability_doc:
                entity_id = availability_doc.get("entity_id", "user_test_1")
                entity_type = availability_doc.get("entity_type", "user")
                
                start_date = datetime.now()
                end_date = start_date + timedelta(days=7)
                
                if entity_type == "user":
                    slots = get_user_availability(entity_id, start_date, end_date)
                    print(f"✅ Recuperate {len(slots)} disponibilità per l'utente {entity_id}")
                else:
                    slots = get_professional_availability(entity_id, start_date, end_date)
                    print(f"✅ Recuperate {len(slots)} disponibilità per il professionista {entity_id}")
                
                return entity_id, "prof_test_1" if entity_type == "user" else "user_test_1", slots
            else:
                print("⚠️ Nessun documento di disponibilità trovato")
                return None, None, []
        except Exception as e:
            print(f"❌ Errore nel recupero delle disponibilità: {str(e)}")
            return None, None, []
    except Exception as e:
        print(f"❌ Errore nel test di disponibilità: {str(e)}")
        return None, None, []

def test_appointment_creation(user_id, prof_id, slot=None):
    """Test della creazione di un appuntamento"""
    print("\n=== Test Creazione Appuntamento ===")
    
    if not user_id or not prof_id:
        print("❌ Impossibile creare un appuntamento senza ID utente e professionista")
        return None
    
    try:
        # Se non abbiamo uno slot, ne creiamo uno fittizio
        if not slot:
            tomorrow = datetime.now() + timedelta(days=1)
            slot = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
        
        # Crea i dettagli dell'appuntamento
        appointment_details = {
            "user_id": user_id,
            "professional_id": prof_id,
            "datetime": slot,
            "issue": "Test problem for database verification",
            "location": "Remote test",
            "notes": "This is a test appointment"
        }
        
        # Crea l'appuntamento
        appointment_id = create_appointment(appointment_details)
        
        if appointment_id:
            print(f"✅ Appuntamento creato con successo con ID: {appointment_id}")
            
            # Verifica che l'appuntamento sia stato creato nel database
            try:
                appointment = db[APPOINTMENTS_COLLECTION].find_one({"_id": ObjectId(appointment_id)})
                if appointment:
                    print(f"✅ Appuntamento trovato nel database")
                    
                    # Controlla che i campi siano corretti
                    expected_fields = ["userId", "professionalId", "date", "description", "status"]
                    missing_fields = []
                    
                    for field in expected_fields:
                        if field not in appointment:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"⚠️ Campi mancanti nell'appuntamento: {', '.join(missing_fields)}")
                    else:
                        print(f"✅ Tutti i campi richiesti sono presenti nell'appuntamento")
                else:
                    print(f"❌ Appuntamento con ID {appointment_id} non trovato nel database")
            except Exception as e:
                print(f"❌ Errore nel recupero dell'appuntamento creato: {str(e)}")
            
            return appointment_id
        else:
            print("❌ Errore nella creazione dell'appuntamento")
            return None
    except Exception as e:
        print(f"❌ Errore nel test di creazione appuntamento: {str(e)}")
        return None

def test_availability_update(user_id, prof_id, slot):
    """Test dell'aggiornamento della disponibilità dopo una prenotazione"""
    print("\n=== Test Aggiornamento Disponibilità ===")
    
    if not user_id or not prof_id or not slot:
        print("❌ Impossibile testare l'aggiornamento senza ID utente, professionista e slot")
        return False
    
    try:
        # Verifica che lo slot sia disponibile prima dell'aggiornamento
        start_date = datetime.strptime(slot, '%Y-%m-%d %H:%M') - timedelta(hours=1)
        end_date = start_date + timedelta(days=1)
        
        available_before = False
        
        try:
            user_slots_before = get_user_availability(user_id, start_date, end_date)
            prof_slots_before = get_professional_availability(prof_id, start_date, end_date)
            
            available_before = (slot in user_slots_before) or (slot in prof_slots_before)
            
            if available_before:
                print(f"✅ Slot {slot} trovato nelle disponibilità prima dell'aggiornamento")
            else:
                print(f"⚠️ Slot {slot} non trovato nelle disponibilità prima dell'aggiornamento - ne creiamo uno")
                
                # Aggiungi lo slot alle disponibilità per testare la rimozione
                db[AVAILABILITY_COLLECTION].update_one(
                    {"entity_id": user_id, "entity_type": "user", "date_range": {"$exists": True}},
                    {"$addToSet": {"slots": slot}},
                    upsert=True
                )
                
                db[AVAILABILITY_COLLECTION].update_one(
                    {"entity_id": prof_id, "entity_type": "professional", "date_range": {"$exists": True}},
                    {"$addToSet": {"slots": slot}},
                    upsert=True
                )
                
                print(f"✅ Slot {slot} aggiunto alle disponibilità per il test")
                available_before = True
        except Exception as e:
            print(f"⚠️ Errore nel recupero delle disponibilità prima dell'aggiornamento: {str(e)}")
        
        # Aggiorna la disponibilità
        update_success = update_availability_after_booking(user_id, prof_id, slot)
        
        if update_success:
            print(f"✅ Aggiornamento disponibilità completato con successo")
            
            # Verifica che lo slot non sia più disponibile
            try:
                user_slots_after = get_user_availability(user_id, start_date, end_date)
                prof_slots_after = get_professional_availability(prof_id, start_date, end_date)
                
                if slot in user_slots_after or slot in prof_slots_after:
                    print(f"❌ Slot {slot} ancora presente nelle disponibilità dopo l'aggiornamento")
                    return False
                else:
                    print(f"✅ Slot {slot} rimosso correttamente dalle disponibilità")
                    return True
            except Exception as e:
                print(f"❌ Errore nel recupero delle disponibilità dopo l'aggiornamento: {str(e)}")
                return False
        else:
            print(f"❌ Aggiornamento disponibilità fallito")
            return False
    except Exception as e:
        print(f"❌ Errore nel test di aggiornamento disponibilità: {str(e)}")
        return False

def main():
    """Funzione principale che esegue tutti i test"""
    print("🔍 INIZIA VERIFICA DATABASE PER APPOINTMENT AGENT")
    print("================================================\n")
    
    # Test 1: Verifica connessione al database
    if not test_database_connection():
        print("\n❌ Test fallito: impossibile connettersi al database")
        sys.exit(1)
    
    # Test 2: Verifica recupero dati
    user_id, prof_id = test_data_retrieval()
    
    # Test 3: Verifica funzioni di disponibilità
    if user_id is None or prof_id is None:
        print("\n⚠️ Utilizzando ID di test per il resto dei test")
        user_id = "user_test_1"
        prof_id = "prof_test_1"
    
    avail_user_id, avail_prof_id, slots = test_availability()
    
    # Usa gli ID della disponibilità se disponibili
    if avail_user_id and avail_prof_id:
        user_id = avail_user_id
        prof_id = avail_prof_id
    
    # Test 4: Verifica creazione appuntamento
    slot = slots[0] if slots else None
    appointment_id = test_appointment_creation(user_id, prof_id, slot)
    
    # Test 5: Verifica aggiornamento disponibilità
    if slot:
        test_availability_update(user_id, prof_id, slot)
    
    print("\n================================================")
    print("🏁 VERIFICA DATABASE COMPLETATA")

if __name__ == "__main__":
    main() 