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
    
@function_tool
def update_professional_trust_score(professional_id: str, trust_score: float) -> float:
    print("5. Updating professional trust score...")
    
    #it should retrieve the professional's current trust score from the database
    # For this example, let's assume the current trust score is 0.5
    current_trust_score = 0.5
    alpha = 0.8 # Weight for the new trust score #! can be audited via A/B testing or online learning
    
    return alpha * current_trust_score + (1 - alpha) * trust_score  # Weighted average of current and new trust score