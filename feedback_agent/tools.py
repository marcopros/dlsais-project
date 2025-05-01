# @title Define the get_weather Tool
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, Optional

def update_professional_trust_score(
    professional_id: str,
    trust_score_contribution: float
) -> None:
    """
    Updates the trust score of a professional in the database.

    Args:
        professional_id (str): The ID of the professional whose score is to be updated.
        trust_score_contribution (float): The calculated trust score contribution.

    Returns:
        None: This function does not return a value but updates the database.
    """
    # Placeholder for database update logic
    # Example: db.update_professional_score(professional_id, trust_score_contribution)
    print(f"UPDATED professional {professional_id} trust score by {trust_score_contribution:.2f}.")


def calculate_trust_contribution(
    feedback_json: Dict[str, Any],
    agent1_result: Optional[Dict[str, Any]], # Output JSON from Agent 1, or None if feedbackType is 'chips'
    agent2_result: Dict[str, Any],      # Output JSON from Agent 2
    agent3_result: Dict[str, Any]       # Output JSON from Agent 3
) -> float:
    """
    Calculates the trust score contribution of a feedback based on original data
    and analysis results from specialized agents.

    Args:
        feedback_json: The original feedback JSON object.
        agent1_result: The output JSON from Agent 1 (Text Analysis), or None
                       if the original feedback type was not 'text'.
                       Expected keys: 'sentiment' (str), 'extractedFeatures' (list of str).
        agent2_result: The output JSON from Agent 2 (Fakeness Detection).
                       Expected keys: 'fakeConfidence' (float).
        agent3_result: The output JSON from Agent 3 (Information Level).
                       Expected keys: 'informationLevel' (str, 'Low', 'Medium', 'High').

    Returns:
        float: The calculated trust score contribution value (can be negative).

    Raises:
        ValueError: If essential input data (feedback_json, agent2_result, agent3_result)
                    is missing or malformed.
    """

    # --- Input Validation ---
    if not isinstance(feedback_json, dict) or not isinstance(agent2_result, dict) or not isinstance(agent3_result, dict):
         raise ValueError("Missing or invalid input dictionaries.")
    if 'rating' not in feedback_json or 'feedbackType' not in feedback_json:
         raise ValueError("feedback_json is missing essential keys ('rating' or 'feedbackType').")
    if 'fakeConfidence' not in agent2_result:
         raise ValueError("agent2_result is missing 'fakeConfidence' key.")
    if 'informationLevel' not in agent3_result:
         raise ValueError("agent3_result is missing 'informationLevel' key.")
    if feedback_json.get('feedbackType') == 'text' and not isinstance(agent1_result, dict):
         # Agent 1 result is required if feedback type is text
         # Allow empty or minimal agent1_result if text was truly empty/uninformative
         # but require the dict structure if feedbackType is 'text'
         pass # The calculation logic below handles missing optional keys within agent1_result


    # --- Data Extraction with Fallbacks ---
    rating = feedback_json.get('rating', 2.5) # Default to neutral if somehow missing after validation
    feedback_type = feedback_json.get('feedbackType', 'unknown')
    selected_tags = feedback_json.get('selectedTags', [])

    fake_confidence = agent2_result.get('fakeConfidence', 0.0)
    information_level = agent3_result.get('informationLevel', 'Medium')

    # 1. Calculate ratingScore
    rating_score = float(rating) - 2.5 # Ensure float arithmetic

    # 2. Calculate contentScore
    content_score = 0.0
    if feedback_type == 'chips':
        chip_values = {'positive': 1.0, 'negative': -1.0}
        # Safely get category, default to '' to avoid errors on malformed tags
        chips_sum = sum(chip_values.get(tag.get('category', ''), 0.0) for tag in selected_tags if isinstance(tag, dict))
        content_score = chips_sum
    elif feedback_type == 'text' and agent1_result:
        sentiment = agent1_result.get('sentiment', 'Neutro')
        extracted_features = agent1_result.get('extractedFeatures', [])

        # Sentiment Base Value
        sentiment_base_value_map = {
            'Positivo': 5.0, 'Negativo': -5.0, 'Misto': 0.0, 'Neutro': 0.0,
            'Positive': 5.0, 'Negative': -5.0, 'Mixed': 0.0, 'Neutral': 0.0
        }
        sentiment_base_value = sentiment_base_value_map.get(sentiment, 0.0)

        # Feature Adjustment (simplified logic - needs careful consideration in production)
        # Using the same keyword lists as before for consistency
        positive_keywords = ["professionale", "puntuale", "onesto", "pulito", "cortese", "accurato", "comunicazione", "veloce", "efficiente", "competente", "flessibile"]
        negative_keywords = ["ritardo", "costoso", "scarsa", "incompleto", "poco professionale", "inadeguata", "impreciso", "sicurezza", "disordine", "lento", "non duraturo", "interventi"]

        feature_adjustment = 0.0
        if isinstance(extracted_features, list): # Ensure extracted_features is a list
            for feature in extracted_features:
                if isinstance(feature, str): # Ensure feature is a string
                    lower_feature = feature.lower()
                    is_negated = "non " in lower_feature or "poco " in lower_feature

                    is_positive_mention = any(kw in lower_feature for kw in positive_keywords)
                    is_negative_mention = any(kw in lower_feature for kw in negative_keywords)

                    if is_negative_mention and not is_negated:
                         feature_adjustment -= 1.0
                    elif is_positive_mention and not is_negated:
                         feature_adjustment += 1.0
                    elif is_negative_mention and is_negated:
                         feature_adjustment += 1.0
                    elif is_positive_mention and is_negated:
                         feature_adjustment -= 1.0

        content_score = sentiment_base_value + feature_adjustment

    # If feedback_type is text but agent1_result was None, content_score remains 0.0

    # 3. Calculate informationMultiplier
    information_multiplier_map = {
        'Low': 0.5,
        'Medium': 1.0,
        'High': 1.5
    }
    # Default to Medium multiplier if information_level is missing or unknown
    information_multiplier = information_multiplier_map.get(information_level, 1.0)

    # 4. Calculate fakenessMultiplier
    # Ensure fake_confidence is treated as a float and clamped between 0 and 1
    fake_confidence_clamped = max(0.0, min(1.0, float(fake_confidence)))
    fakeness_multiplier = 1.0 - fake_confidence_clamped

    # 5. Calculate rawContribution and final trustScoreContribution
    # Apply a weight to contentScore relative to ratingScore base (-2.5 to +2.5)
    weighted_content_score = content_score * 0.5 # Suggestion: adjust this weight based on tuning

    raw_contribution = (rating_score + weighted_content_score) * information_multiplier

    trust_score_contribution = raw_contribution * fakeness_multiplier

    return trust_score_contribution