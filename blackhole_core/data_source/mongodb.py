import os
import sys
import time
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, InvalidURI, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Import our custom logger
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(handler)

# Load environment variables
load_dotenv()

# Cache the client instance so it reuses connections
_client = None
_max_retry_attempts = 3
_retry_delay_seconds = 2

def get_mongo_client():
    """
    Establish and return a cached MongoDB client with fallback to local MongoDB.

    Returns:
        MongoClient: A MongoDB client instance (or DummyMongoClient if all connections fail)

    This function attempts to connect to the cloud MongoDB first, then falls back to
    local MongoDB if that fails, and finally uses an in-memory dummy client if both fail.
    """
    global _client
    if _client is None:
        # Try cloud MongoDB first
        for attempt in range(1, _max_retry_attempts + 1):
            try:
                uri = os.getenv("MONGO_URI")
                if not uri:
                    logger.warning("MONGO_URI not found in environment variables. Trying local MongoDB...")
                    raise ValueError("MONGO_URI not found")

                # Fix URI format if needed
                uri = uri.replace('\\x3a', ':')  # Fix encoding issues

                # Validate URI format
                if not (uri.startswith('mongodb://') or uri.startswith('mongodb+srv://')):
                    logger.warning(f"Invalid MongoDB URI format: {uri}")
                    # Try to fix common issues
                    if 'mongodb+srv' in uri:
                        uri = 'mongodb+srv://' + uri.split('mongodb+srv')[1]
                        logger.info(f"Attempted to fix URI format: {uri}")
                    else:
                        raise InvalidURI("Invalid URI scheme: URI must begin with 'mongodb://' or 'mongodb+srv://'")

                logger.info(f"Connecting to cloud MongoDB (attempt {attempt}/{_max_retry_attempts})...")
                _client = MongoClient(uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)
                # Test connection
                _client.admin.command('ping')
                logger.info("[SUCCESS] Connected to cloud MongoDB successfully!")
                return _client

            except (ConnectionFailure, InvalidURI, ValueError, ServerSelectionTimeoutError) as e:
                logger.warning(f"[WARNING] Could not connect to cloud MongoDB (attempt {attempt}/{_max_retry_attempts}): {e}")
                if attempt < _max_retry_attempts:
                    logger.info(f"Retrying in {_retry_delay_seconds} seconds...")
                    time.sleep(_retry_delay_seconds)
                else:
                    logger.warning("[WARNING] All cloud MongoDB connection attempts failed. Falling back to local MongoDB...")
                    break

        # Try local MongoDB as fallback
        for attempt in range(1, _max_retry_attempts + 1):
            try:
                local_uri = os.getenv("MONGO_URI_LOCAL", "mongodb://localhost:27017/")
                logger.info(f"Connecting to local MongoDB (attempt {attempt}/{_max_retry_attempts})...")
                _client = MongoClient(local_uri, serverSelectionTimeoutMS=5000)
                _client.admin.command('ping')
                logger.info("[SUCCESS] Connected to local MongoDB successfully!")
                return _client

            except Exception as local_e:
                logger.warning(f"[WARNING] Could not connect to local MongoDB (attempt {attempt}/{_max_retry_attempts}): {local_e}")
                if attempt < _max_retry_attempts:
                    logger.info(f"Retrying in {_retry_delay_seconds} seconds...")
                    time.sleep(_retry_delay_seconds)
                else:
                    logger.error("[ERROR] All MongoDB connection attempts failed. Using in-memory mode (data will not be persisted)")
                    # Return a dummy client that won't actually connect but won't crash the app
                    _client = DummyMongoClient()
                    return _client

    return _client

class DummyMongoClient:
    """
    A dummy MongoDB client that doesn't actually connect to a database.
    Used as a fallback when no MongoDB connection is available.
    """
    def __getitem__(self, db_name):
        logger.debug(f"[DUMMY MODE] Accessing database: {db_name}")
        return DummyDatabase(db_name)

    def admin(self):
        return DummyAdminDB()

class DummyAdminDB:
    """A dummy admin database for the dummy client."""
    def command(self, command_name):
        logger.debug(f"[DUMMY MODE] Executing admin command: {command_name}")
        return {"ok": 1.0, "dummy": True}

class DummyDatabase:
    """A dummy database that doesn't actually store data."""
    def __init__(self, db_name):
        self.db_name = db_name

    def __getitem__(self, collection_name):
        logger.debug(f"[DUMMY MODE] Accessing collection: {collection_name} in database: {self.db_name}")
        return DummyCollection(self.db_name, collection_name)

class DummyCollection:
    """A dummy collection that doesn't actually store data."""
    def __init__(self, db_name, collection_name):
        self.db_name = db_name
        self.collection_name = collection_name

    def insert_one(self, document):
        logger.warning(f"[DUMMY MODE] Would have inserted document into {self.db_name}.{self.collection_name}")
        logger.debug(f"[DUMMY MODE] Document content: {document}")
        return DummyInsertResult()

    def insert_many(self, documents):
        logger.warning(f"[DUMMY MODE] Would have inserted {len(documents)} documents into {self.db_name}.{self.collection_name}")
        return DummyInsertManyResult(len(documents))

    def find(self, query=None):
        logger.warning(f"[DUMMY MODE] Would have queried {self.db_name}.{self.collection_name}")
        if query:
            logger.debug(f"[DUMMY MODE] Query: {query}")
        return []

    def find_one(self, query=None):
        logger.warning(f"[DUMMY MODE] Would have queried for one document in {self.db_name}.{self.collection_name}")
        if query:
            logger.debug(f"[DUMMY MODE] Query: {query}")
        return None

class DummyInsertResult:
    """A dummy result for insert_one operations."""
    @property
    def inserted_id(self):
        return "dummy_id"

class DummyInsertManyResult:
    """A dummy result for insert_many operations."""
    def __init__(self, count):
        self.inserted_ids = ["dummy_id_" + str(i) for i in range(count)]

def get_agent_outputs_collection():
    """
    Return the agent_outputs collection from MongoDB.

    Returns:
        Collection: A MongoDB collection object for storing agent outputs.

    This function uses the database and collection names specified in the
    environment variables MONGO_DB_NAME and MONGO_COLLECTION_NAME.
    """
    client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "blackhole_db")
    collection_name = os.getenv("MONGO_COLLECTION_NAME", "agent_outputs")
    logger.debug(f"Accessing collection {collection_name} in database {db_name}")
    db = client[db_name]
    return db[collection_name]

def test_connection():
    """
    Test the MongoDB connection and print the status.

    Returns:
        bool: True if connection was successful, False otherwise.
    """
    try:
        client = get_mongo_client()
        # If we get here, we're connected to either cloud or local MongoDB
        # or using the dummy client
        if isinstance(client, DummyMongoClient):
            logger.warning("Using dummy MongoDB client - no actual database connection")
            return False
        else:
            logger.info("MongoDB connection test successful!")
            return True
    except Exception as e:
        logger.error(f"❌ Error during connection test: {e}")
        return False

# Test connection if run directly
if __name__ == "__main__":
    logger.info("Testing MongoDB connection...")
    success = test_connection()
    if success:
        logger.info("✅ MongoDB connection is working properly.")
    else:
        logger.warning("⚠️ MongoDB connection is not available. Using dummy mode.")

    # Test the agent outputs collection
    try:
        collection = get_agent_outputs_collection()
        logger.info(f"✅ Successfully accessed the agent outputs collection.")
    except Exception as e:
        logger.error(f"❌ Error accessing agent outputs collection: {e}")
