import streamlit as st

def collect_star_rating_widget(prompt: str) -> int:
    """
    Displays a star rating widget using Streamlit's slider.

    Args:
        prompt (str): The prompt to display above the star rating widget.

    Returns:
        int: The selected star rating (1-5), or None if not selected.
    """
    rating = st.slider(prompt, 1, 5, 3)
    return rating

def collect_category_ratings_widget(categories: list) -> dict:
    """
    Displays a set of sliders for rating different categories.

    Args:
        categories (list): A list of category names (e.g., ["Speed", "Competence", ...]).

    Returns:
        dict: A dictionary where keys are category names and values are the ratings (1-5).
    """
    ratings = {}
    for category in categories:
        ratings[category] = st.slider(category, 1, 5, 3)
    return ratings