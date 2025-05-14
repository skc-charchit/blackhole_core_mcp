import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

# Cache the client instance so it reuses connections
_client = None

def get_mongo_client():
    """Establish and return a cached MongoDB client."""
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("MONGO_URI not found in environment variables.")
        _client = MongoClient(uri, server_api=ServerApi('1'))
    return _client

def get_agent_outputs_collection():
    """Return the agent_outputs collection from MongoDB."""
    client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "blackhole_db")
    collection_name = os.getenv("MONGO_COLLECTION_NAME", "agent_outputs")
    db = client[db_name]
    return db[collection_name]

# Test connection if run directly
if __name__ == "__main__":
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error: {e}")
