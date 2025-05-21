from dataclasses import asdict
from typing import List
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os
from agents import (
    function_tool
)
from typing import List, Literal
import aiohttp
from dotenv import load_dotenv
import os
import json
import asyncio

from session import SessionSettings
from pydantic import BaseModel


@function_tool
async def search_video_tutorial(query: str, hl: str, gl: str) -> List[str]:
    """ Searches YouTube for video tutorials matching the given query.
        Returns a list of YouTube watch URLs.
    Args:
        query (str): The search query for the video tutorial.
        hl (str): The language code for the search results (e.g., 'it' for Italian).
        gl (str): The country code for the search results (e.g., 'it' for Italy).
    """
    # Add the site filter to the query to search only for YouTube videos
    full_query = f"{query} site:youtube.com"
    url = "https://serpapi.com/search"
    params = {
        "q": full_query,
        "hl": hl,
        "gl": gl,
        "engine": "google",
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    # Extract video links from the response
    videos: List[str] = []
    for item in data.get("organic_results", []):
        link = item.get("link", "")
        if "youtube.com/watch" in link:
            videos.append(link)

    # Provide only the first 5 links
    return videos[:5]



# Load environment variables from a .env file if present
load_dotenv()
# MongoDB connection
mongo_uri = os.getenv("MONGODB_URI")

# Connessione al database
client = MongoClient(mongo_uri)
db = client["home_repair_assistant"]
user_collection = db["users"]

# Funzione per aggiornare le impostazioni
@function_tool
def update_user_settings(user_id: str, settings: SessionSettings) -> int:
    print("✨ Updating user settings... ✨")
    settings_dict = asdict(settings)
    result = user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"settings": settings_dict}},
        upsert=True
    )
    return result.modified_count
