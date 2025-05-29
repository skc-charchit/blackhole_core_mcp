#!/usr/bin/env python3
"""
Unified Connection Manager
Manages all database connections for the MCP system
"""

import os
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ConnectionManager:
    """Unified connection manager for all database connections."""
    
    _instance = None
    _connections = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the connection manager."""
        self.logger = logging.getLogger("connection_manager")
        self.logger.setLevel(logging.INFO)
        
        # MongoDB configuration
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.mongo_db_name = os.getenv('MONGO_DB_NAME', 'blackhole_mcp')
        self.mongo_connection_timeout = 30
        
        # Connection pool configuration
        self.max_pool_size = 100
        self.retry_writes = True
        self.auto_reconnect = True
        
        self.logger.info("Connection Manager initialized")
    
    async def get_mongodb_connection(self) -> Optional[MongoClient]:
        """Get or create MongoDB connection."""
        if 'mongodb' not in self._connections:
            try:
                self.logger.info(f"Connecting to MongoDB: {self.mongo_db_name}")
                
                # Create client with configuration
                client = MongoClient(
                    self.mongo_uri,
                    serverSelectionTimeoutMS=self.mongo_connection_timeout * 1000,
                    connectTimeoutMS=self.mongo_connection_timeout * 1000,
                    maxPoolSize=self.max_pool_size,
                    retryWrites=self.retry_writes
                )
                
                # Test connection
                client.admin.command('ping')
                
                # Store connection
                self._connections['mongodb'] = {
                    'client': client,
                    'db': client[self.mongo_db_name]
                }
                
                self.logger.info("MongoDB connected successfully")
                
            except ConnectionFailure as e:
                self.logger.error(f"MongoDB connection failed: {e}")
                return None
            except Exception as e:
                self.logger.error(f"MongoDB connection error: {e}")
                return None
        
        return self._connections['mongodb']['client']
    
    def get_mongodb_database(self):
        """Get MongoDB database instance."""
        if 'mongodb' in self._connections:
            return self._connections['mongodb']['db']
        return None
    
    async def close_all_connections(self):
        """Close all database connections."""
        for conn_name, conn_data in self._connections.items():
            try:
                if 'client' in conn_data:
                    conn_data['client'].close()
                    self.logger.info(f"Closed {conn_name} connection")
            except Exception as e:
                self.logger.error(f"Error closing {conn_name} connection: {e}")
        
        self._connections.clear()
        self.logger.info("All connections closed")

# Global instance
connection_manager = ConnectionManager() 