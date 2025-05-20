from typing import List, Dict, Any
import math
from datetime import datetime

def get_time_decay(feedback_date: str) -> float:
    print("3. Getting time decay...")
    # Dummy time decay calculation based on the date of the feedback
    feedback_date = datetime.strptime(feedback_date, "%Y-%m-%d")
    current_date = datetime.now()
    days_difference = (current_date - feedback_date).days
    
    # Assuming a decay factor of 0.01 per day
    decay_factor = 0.01
    return math.exp(-decay_factor * days_difference)  # Exponential decay function


def get_rating_scoring(rating: int) -> float:
    print("1. Getting rating scoring...")
    return (rating - 1) / 4.0  # Assuming rating is between 1 and 5

def get_tag_scoring(num_positive_tags: int, num_negative_tags: int) -> float:
    print("2. Getting tag scoring...")
    # Scoring based on the number of positive and negative tags
    total_tags = num_positive_tags + num_negative_tags
    return (num_positive_tags - num_negative_tags) / total_tags if total_tags > 0 else 0.0

def get_time_decay(feedback_date: str) -> float:
    print("3. Getting time decay...")
    # Dummy time decay calculation based on the date of the feedback
    feedback_date = datetime.strptime(feedback_date, "%Y-%m-%d")
    current_date = datetime.now()
    days_difference = (current_date - feedback_date).days
    
    # Assuming a decay factor of 0.01 per day
    decay_factor = 0.01
    return math.exp(-decay_factor * days_difference)  # Exponential decay function

def get_sentiment_scoring(feedback_type: str, text_feedback: str) -> float:
    print("4. Getting sentiment scoring...")
    # Dummy sentiment scoring based on feedback type
    if feedback_type == "text" and text_feedback:
        # Placeholder for actual sentiment analysis
        return 0.8  # Assume positive sentiment
    else:
        return 0.5  # Neutral sentiment for non-text feedback

def get_trust_score(rating_scoring: float, tag_scoring: float, time_decay: float, semtiment_scoring: float) -> float:
    print("4. Getting trust score...")
    
    weights = {  # Can be audited via A/B testing or online learning
        "rating_scoring": 0.5,
        "tag_scoring": 0.2,
        "time_decay": 0.2,
        "sentiment_scoring": 0.1
    }
    
    return (
        weights["rating_scoring"] * rating_scoring +
        weights["tag_scoring"] * tag_scoring +
        weights["time_decay"] * time_decay +
        weights["sentiment_scoring"] * (semtiment_scoring - 0.5)  # Normalize to range [-0.5, 0.5]
    )

def update_professional_trust_score(professional_id: str, trust_score: float) -> float:
    print("5. Updating professional trust score...")
    
    # It should retrieve the professional's current trust score from the database
    # For this example, let's assume the current trust score is 0.5
    current_trust_score = 0.5
    alpha = 0.8  # Weight for the new trust score (can be tuned via A/B testing or online learning)
    
    return alpha * current_trust_score + (1 - alpha) * trust_score  # Weighted average


feedback_tools = [
  {
    "type": "function",
    "function": {
      "name": "get_rating_scoring",
      "description": "Convert a rating from 1-5 into a normalized score between 0.0 and 1.0",
      "parameters": {
        "type": "object",
        "properties": {
          "rating": {
            "type": "integer",
            "description": "Rating value between 1 and 5"
          }
        },
        "required": ["rating"]
      }
    }
  },
  {
    "type": "function",
    "function": {
        "name": "get_tag_scoring",
        "description": "Calculate a score based on the number of positive and negative tags. Returns a value between -1.0 and 1.0.",
        "parameters": {
        "type": "object",
        "properties": {
            "num_positive_tags": {
            "type": "integer",
            "description": "Number of positive tags"
            },
            "num_negative_tags": {
            "type": "integer",
            "description": "Number of negative tags"
            }
        },
        "required": ["num_positive_tags", "num_negative_tags"]
        }
    }
  },
  {
    "type": "function",
    "function": {
        "name": "get_time_decay",
        "description": "Calculate an exponential time decay score based on the feedback date. More recent dates result in higher scores.",
        "parameters": {
        "type": "object",
        "properties": {
            "feedback_date": {
            "type": "string",
            "description": "Date of the feedback in YYYY-MM-DD format"
            }
        },
        "required": ["feedback_date"]
        }
    }
  },
  {
        "type": "function",
        "function": {
            "name": "get_sentiment_scoring",
            "description": "Calculate a sentiment score based on the feedback type and text feedback.",
            "parameters": {
            "type": "object",
            "properties": {
                "feedback_type": {
                "type": "string",
                "description": "Type of feedback, either 'text' or 'chips'"
                },
                "text_feedback": {
                "type": "string",
                "description": "The text feedback provided by the user"
                }
            },
            "required": ["feedback_type", "text_feedback"]
            }
        }
    },
  {
    "type": "function",
    "function": {
        "name": "get_trust_score",
        "description": "Calculate a trust score combining rating, tags, time decay, and sentiment score with predefined weights.",
        "parameters": {
        "type": "object",
        "properties": {
            "rating_scoring": {
            "type": "number",
            "description": "Normalized rating score between 0.0 and 1.0"
            },
            "tag_scoring": {
            "type": "number",
            "description": "Score based on tags, between -1.0 and 1.0"
            },
            "time_decay": {
            "type": "number",
            "description": "Decay factor based on time since feedback, between 0.0 and 1.0"
            },
            "semtiment_scoring": {
            "type": "number",
            "description": "Sentiment score, assumed between 0.0 (negative) and 1.0 (positive)"
            }
        },
        "required": ["rating_scoring", "tag_scoring", "time_decay", "semtiment_scoring"]
        }
    }
  },
  {
    "type": "function",
    "function": {
        "name": "update_professional_trust_score",
        "description": "Update the trust score of a professional using a weighted average between the current and new trust score.",
        "parameters": {
        "type": "object",
        "properties": {
            "professional_id": {
            "type": "string",
            "description": "The unique identifier of the professional"
            },
            "trust_score": {
            "type": "number",
            "description": "The new calculated trust score to be merged with the existing one"
            }
        },
        "required": ["professional_id", "trust_score"]
        }
    }
  },
    
]

TOOL_MAPPING = {
    "get_rating_scoring": get_rating_scoring,
    "get_tag_scoring": get_tag_scoring,
    "get_sentiment_scoring": get_sentiment_scoring,
    "get_time_decay": get_time_decay,
    "get_trust_score": get_trust_score,
    "update_professional_trust_score": update_professional_trust_score,
}







