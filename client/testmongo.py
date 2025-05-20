from calendar import c
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri)
db = client["home_repair_assistant"]
professionals = db["professionals"]  # o il nome corretto della tua collection


print(client.list_database_names())
print(db.professionals.find_one({ "id": "pro-1" })
)

