#!/usr/bin/env python3
"""
MongoDB Manager
Centralized MongoDB operations for MCP system
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MCPMongoDBManager:
    """Centralized MongoDB manager for MCP system."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = {}
        self.logger = logging.getLogger("mongodb_manager")
        
        # Configuration
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('MONGO_DB_NAME', 'blackhole_mcp')
        self.connection_timeout = 30
        
        # Collection names
        self.collection_names = {
            'conversations': 'conversation_history',
            'agent_logs': 'agent_execution_logs',
            'extracted_data': 'extracted_text_data',
            'query_cache': 'query_response_cache',
            'user_sessions': 'user_sessions',
            'agent_performance': 'agent_performance_metrics'
        }
        
        self.logger.info("MongoDB Manager initialized")
    
    async def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.logger.info(f"Connecting to MongoDB: {self.db_name}")
            
            # Create client with configuration
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=self.connection_timeout * 1000,
                connectTimeoutMS=self.connection_timeout * 1000,
                maxPoolSize=100,
                retryWrites=True
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[self.db_name]
            
            # Initialize collections
            await self._initialize_collections()
            
            self.logger.info("MongoDB connected successfully")
            return True
            
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"MongoDB connection error: {e}")
            return False
    
    async def _initialize_collections(self):
        """Initialize collections with indexes."""
        try:
            for key, collection_name in self.collection_names.items():
                collection = self.db[collection_name]
                self.collections[key] = collection
                
                # Create indexes based on collection type
                if key == 'conversations':
                    collection.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
                    collection.create_index([("session_id", ASCENDING)])
                    collection.create_index([("query", "text")])
                
                elif key == 'agent_logs':
                    collection.create_index([("agent_id", ASCENDING), ("timestamp", DESCENDING)])
                    collection.create_index([("status", ASCENDING)])
                    collection.create_index([("execution_time", DESCENDING)])
                
                elif key == 'extracted_data':
                    collection.create_index([("source_type", ASCENDING), ("timestamp", DESCENDING)])
                    collection.create_index([("extracted_text", "text")])
                    collection.create_index([("agent_id", ASCENDING)])
                
                elif key == 'query_cache':
                    collection.create_index([("query_hash", ASCENDING)], unique=True)
                    collection.create_index([("timestamp", ASCENDING)], expireAfterSeconds=3600)  # 1 hour TTL
                
                self.logger.info(f"Initialized collection: {collection_name}")
                
        except Exception as e:
            self.logger.error(f"Error initializing collections: {e}")
    
    # Conversation Management
    async def store_conversation(self, user_id: str, session_id: str, query: str, 
                               response: str, agent_used: str = None, 
                               metadata: Dict = None) -> str:
        """Store conversation in MongoDB."""
        try:
            conversation_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "response": response,
                "agent_used": agent_used,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow(),
                "query_length": len(query),
                "response_length": len(response)
            }
            
            result = self.collections['conversations'].insert_one(conversation_doc)
            self.logger.info(f"Stored conversation: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Error storing conversation: {e}")
            return None
    
    async def search_conversations(self, query: str, user_id: str = None, 
                                 limit: int = 10) -> List[Dict]:
        """Search conversations by text."""
        try:
            search_filter = {"$text": {"$search": query}}
            
            if user_id:
                search_filter["user_id"] = user_id
            
            conversations = list(
                self.collections['conversations']
                .find(search_filter)
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
            
            self.logger.info(f"Found {len(conversations)} conversations for query: {query}")
            return conversations
            
        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []
    
    async def get_conversation_history(self, user_id: str, session_id: str = None, 
                                     limit: int = 50) -> List[Dict]:
        """Get conversation history for a user/session."""
        try:
            filter_query = {"user_id": user_id}
            if session_id:
                filter_query["session_id"] = session_id
            
            history = list(
                self.collections['conversations']
                .find(filter_query)
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
    
    # Agent Logging
    async def log_agent_execution(self, agent_id: str, query: str, response: Dict,
                                execution_time: float, status: str = "success",
                                error_message: str = None) -> str:
        """Log agent execution details."""
        try:
            log_doc = {
                "agent_id": agent_id,
                "query": query,
                "response": response,
                "execution_time": execution_time,
                "status": status,
                "error_message": error_message,
                "timestamp": datetime.utcnow(),
                "response_size": len(str(response))
            }
            
            result = self.collections['agent_logs'].insert_one(log_doc)
            self.logger.info(f"Logged agent execution: {agent_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Error logging agent execution: {e}")
            return None
    
    async def get_agent_performance(self, agent_id: str = None, 
                                  hours: int = 24) -> Dict:
        """Get agent performance metrics."""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            filter_query = {"timestamp": {"$gte": since}}
            
            if agent_id:
                filter_query["agent_id"] = agent_id
            
            # Aggregation pipeline for performance metrics
            pipeline = [
                {"$match": filter_query},
                {"$group": {
                    "_id": "$agent_id",
                    "total_executions": {"$sum": 1},
                    "successful_executions": {
                        "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                    },
                    "avg_execution_time": {"$avg": "$execution_time"},
                    "max_execution_time": {"$max": "$execution_time"},
                    "min_execution_time": {"$min": "$execution_time"}
                }},
                {"$addFields": {
                    "success_rate": {
                        "$divide": ["$successful_executions", "$total_executions"]
                    }
                }}
            ]
            
            performance = list(self.collections['agent_logs'].aggregate(pipeline))
            return {agent["_id"]: agent for agent in performance}
            
        except Exception as e:
            self.logger.error(f"Error getting agent performance: {e}")
            return {}
    
    # Extracted Data Management
    async def store_extracted_data(self, agent_id: str, source_file: str,
                                 source_type: str, extracted_text: str,
                                 metadata: Dict = None) -> str:
        """Store extracted data (OCR, document analysis, etc.)."""
        try:
            data_doc = {
                "agent_id": agent_id,
                "source_file": source_file,
                "source_type": source_type,
                "extracted_text": extracted_text,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow(),
                "text_length": len(extracted_text),
                "word_count": len(extracted_text.split())
            }
            
            result = self.collections['extracted_data'].insert_one(data_doc)
            self.logger.info(f"Stored extracted data: {source_file}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Error storing extracted data: {e}")
            return None
    
    async def search_extracted_data(self, query: str, source_type: str = None,
                                  limit: int = 10) -> List[Dict]:
        """Search extracted data by text content."""
        try:
            search_filter = {"$text": {"$search": query}}
            
            if source_type:
                search_filter["source_type"] = source_type
            
            results = list(
                self.collections['extracted_data']
                .find(search_filter)
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
            
            self.logger.info(f"Found {len(results)} extracted data results for: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching extracted data: {e}")
            return []
    
    # Query Caching
    async def cache_query_response(self, query_hash: str, query: str,
                                 response: Dict, agent_used: str) -> bool:
        """Cache query response for faster retrieval."""
        try:
            cache_doc = {
                "query_hash": query_hash,
                "query": query,
                "response": response,
                "agent_used": agent_used,
                "timestamp": datetime.utcnow(),
                "access_count": 1
            }
            
            # Upsert to handle duplicates
            self.collections['query_cache'].replace_one(
                {"query_hash": query_hash},
                cache_doc,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching query response: {e}")
            return False
    
    async def get_cached_response(self, query_hash: str) -> Optional[Dict]:
        """Get cached response for a query."""
        try:
            cached = self.collections['query_cache'].find_one({"query_hash": query_hash})
            
            if cached:
                # Update access count
                self.collections['query_cache'].update_one(
                    {"query_hash": query_hash},
                    {"$inc": {"access_count": 1}}
                )
                
                self.logger.info(f"Retrieved cached response for query hash: {query_hash}")
                return cached
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached response: {e}")
            return None
    
    # Utility Methods
    async def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            stats = {}
            
            for key, collection in self.collections.items():
                count = collection.count_documents({})
                stats[key] = {
                    "document_count": count,
                    "collection_name": collection.name
                }
            
            # Database size
            db_stats = self.db.command("dbStats")
            stats["database"] = {
                "size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2),
                "storage_mb": round(db_stats.get("storageSize", 0) / (1024 * 1024), 2),
                "indexes": db_stats.get("indexes", 0)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days: int = 30) -> Dict:
        """Clean up old data from collections."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cleanup_results = {}
            
            # Clean old conversations (keep recent ones)
            conv_result = self.collections['conversations'].delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            cleanup_results["conversations"] = conv_result.deleted_count
            
            # Clean old agent logs
            logs_result = self.collections['agent_logs'].delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            cleanup_results["agent_logs"] = logs_result.deleted_count
            
            self.logger.info(f"Cleaned up old data: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")

# Global instance
mongodb_manager = MCPMongoDBManager()
