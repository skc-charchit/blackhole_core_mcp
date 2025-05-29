"""
Tests for the MongoDB connection module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from blackhole_core.data_source.mongodb import (
    get_mongo_client,
    get_agent_outputs_collection,
    test_connection,
    DummyMongoClient
)

class TestMongoDB(unittest.TestCase):
    """Test cases for the MongoDB connection module."""

    @patch('blackhole_core.data_source.mongodb.os.getenv')
    @patch('blackhole_core.data_source.mongodb.MongoClient')
    def test_get_mongo_client_success(self, mock_mongo_client, mock_getenv):
        """Test successful MongoDB connection."""
        # Setup mocks
        mock_instance = MagicMock()
        mock_mongo_client.return_value = mock_instance
        mock_instance.admin.command.return_value = {'ok': 1}

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            'MONGO_URI': 'mongodb://localhost:27017/',
            'MONGO_URI_LOCAL': 'mongodb://localhost:27017/'
        }.get(key, default)

        # Reset the cached client
        import blackhole_core.data_source.mongodb
        blackhole_core.data_source.mongodb._client = None

        # Call the function
        client = get_mongo_client()

        # Assertions
        self.assertEqual(client, mock_instance)
        mock_instance.admin.command.assert_called_with('ping')

    @patch('blackhole_core.data_source.mongodb.MongoClient')
    def test_get_mongo_client_failure(self, mock_mongo_client):
        """Test MongoDB connection failure."""
        # Setup mock to raise an exception
        mock_mongo_client.side_effect = Exception("Connection failed")

        # Call the function
        client = get_mongo_client()

        # Assertions
        self.assertIsInstance(client, DummyMongoClient)

    @patch('blackhole_core.data_source.mongodb.get_mongo_client')
    def test_get_agent_outputs_collection(self, mock_get_client):
        """Test getting the agent outputs collection."""
        # Setup mock
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_get_client.return_value = mock_client

        # Call the function
        collection = get_agent_outputs_collection()

        # Assertions
        self.assertEqual(collection, mock_collection)
        mock_get_client.assert_called_once()

    def test_dummy_mongo_client(self):
        """Test the DummyMongoClient class."""
        # Create a dummy client
        dummy_client = DummyMongoClient()

        # Test accessing a database
        dummy_db = dummy_client['test_db']

        # Test accessing a collection
        dummy_collection = dummy_db['test_collection']

        # Test insert_one
        result = dummy_collection.insert_one({'test': 'data'})
        self.assertEqual(result.inserted_id, 'dummy_id')

        # Test find
        results = list(dummy_collection.find({'query': 'test'}))
        self.assertEqual(results, [])

        # Test find_one
        result = dummy_collection.find_one({'query': 'test'})
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
