from pymongo import MongoClient

from config import get_settings

settings = get_settings()

client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
db = client[settings.db_name]

users_collection = db["users"]
sessions_collection = db["sessions"]
