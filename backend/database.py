import logging

from pymongo import ASCENDING, DESCENDING, MongoClient

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
db = client[settings.db_name]

users_collection = db["users"]
sessions_collection = db["sessions"]


def ensure_indexes() -> None:
    """Create the indexes the query patterns rely on.

    Called during application startup. Failures are logged rather than raised so
    the API still boots when Mongo is briefly unreachable.
    """
    try:
        sessions_collection.create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
            name="user_recent_sessions",
        )
        users_collection.create_index([("email", ASCENDING)], unique=True, name="unique_email")
    except Exception:
        logger.warning("Could not ensure MongoDB indexes.", exc_info=True)
