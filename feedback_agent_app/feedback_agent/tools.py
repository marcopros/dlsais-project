import datetime
from agents import function_tool
from typing import List, Dict, Any
import math

@function_tool
def get_rating_scoring(rating: int) -> float:
    print("1. Getting rating scoring...")
    return (rating - 1) / 4.0  # Assuming rating is between 1 and 5


@function_tool
def get_tag_scoring(num_positive_tags: int, num_negative_tags: int) -> float:
    print("2. Getting tag scoring...")
    # Scoring based on the number of positive and negative tags
    total_tags = num_positive_tags + num_negative_tags
    return (num_positive_tags - num_negative_tags) / total_tags if total_tags > 0 else 0.0

@function_tool
def get_time_decay(feedback_date: str) -> float:
    print("3. Getting time decay...")
    # Dummy time decay calculation based on the date of the feedback
    from datetime import datetime, timedelta
    
    feedback_date = datetime.strptime(feedback_date, "%Y-%m-%d")
    current_date = datetime.now()
    days_difference = (current_date - feedback_date).days
    
    # Assuming a decay factor of 0.01 per day
    decay_factor = 0.01
    return math.exp(-decay_factor * days_difference)  # Exponential decay function

@function_tool
def get_trust_score(rating_scoring: float, tag_scoring: float, time_decay: float, semtiment_scoring: float) -> float:
    print("4. Getting trust score...")
    
    weights = { #! can be audited via A/B testing or online learning
        "rating_scoring": 0.5,
        "tag_scoring": 0.2,
        "time_decay": 0.2,
        "sentiment_scoring": 0.1
    }
    
    return (
        weights["rating_scoring"] * rating_scoring +
        weights["tag_scoring"] * tag_scoring +
        weights["time_decay"] * time_decay +
        weights["sentiment_scoring"] * (semtiment_scoring - 0.5)  # Normalizing sentiment score to be between -0.5 and 0.5
    )
  
  
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from a .env file if present
load_dotenv()
# MongoDB connection
mongo_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongo_uri)
db = client["home_repair_assistant"]
professionals = db["professionals"]  # o il nome corretto della tua collection

  
@function_tool
def update_professional_trust_score(professional_id: str, new_score: float) -> float:
    print("5. Updating professional trust score...")

    # Recupera il professionista dal DB
    prof = professionals.find_one({"id": professional_id})

    if not prof:
        raise ValueError(f"Professional with id '{professional_id}' not found.")
    
    # Usa il valore attuale se esiste, altrimenti default 0.5
    current_score = prof.get("trust_score", 0.5)
    alpha = 0.8  # peso per lo score precedente

    # Calcolo nuova media pesata
    updated_score = alpha * current_score + (1 - alpha) * new_score
    
    try:
        # Aggiorna il documento nel DB
        res = professionals.update_one(
            {"id": professional_id},
            {
                "$set": {
                    "trust_score": updated_score,
                    "updatedAt": datetime.utcnow()  # opzionale: aggiorna anche updatedAt
                }
            }
        )
    
        #print(f"Matched count: {res.matched_count}")
        #print(f"Modified count: {res.modified_count}")
        print(f"Old score: {current_score:.4f}")
        print(f"New score: {updated_score:.4f}")
    except Exception as e:
        print(f"Error updating trust score: {e}")
        raise
        
    return updated_score
