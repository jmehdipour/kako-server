import pymongo
from pydantic import BaseSettings


class Database(BaseSettings):
    DATABASE_URL: str = "mongodb://localhost:27017/"
    DATABASE_NAME: str = "kako_app_server"
    USERS_COLLECTION: str = "users"
    PARTNER_REQUESTS_COLLECTION: str = "partner_requests"
    LIKES_COLLECTION: str = "likes"
    ACTIVITIES_COLLECTION: str = "activities"
    DIRECT_MESSAGES_COLLECTION: str = "direct_messages"
    GROUP_MESSAGES_COLLECTION: str = "group_messages"


database_settings = Database()

db_client = pymongo.MongoClient(database_settings.DATABASE_URL)

database = db_client.get_database(database_settings.DATABASE_NAME)
users_collection = database[database_settings.USERS_COLLECTION]
partner_requests_collection = database[database_settings.PARTNER_REQUESTS_COLLECTION]
likes_collection = database[database_settings.LIKES_COLLECTION]
activities_collection = database[database_settings.ACTIVITIES_COLLECTION]
direct_messages_collection = database[database_settings.DIRECT_MESSAGES_COLLECTION]
group_messages_collection = database[database_settings.GROUP_MESSAGES_COLLECTION]
# channel_chat_collection = database[database_settings.CHANNEL_CHAT_COLLECTION]


likes_collection.create_index([("user_id", pymongo.ASCENDING), ("partner_request", pymongo.ASCENDING)], unique=True)
users_collection.create_index([("email", pymongo.ASCENDING)], unique=True)
users_collection.create_index([("username", pymongo.ASCENDING)], unique=True)

users_collection.create_index([("loc", pymongo.GEO2D)])
partner_requests_collection.create_index([("loc", pymongo.GEO2D)])
