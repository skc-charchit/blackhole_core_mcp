#!/usr/bin/env python3
"""
MongoDB Status Checker for MCP System
Comprehensive MongoDB connection and integration testing
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import pymongo
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

class MongoDBStatusChecker:
    """Comprehensive MongoDB status checker for MCP system."""
    
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI')
        self.db_name = os.getenv('MONGO_DB_NAME', 'blackhole_db')
        self.collection_name = os.getenv('MONGO_COLLECTION_NAME', 'agent_outputs')
        self.client = None
        self.db = None
        self.collection = None
        
    def check_dependencies(self) -> Dict[str, Any]:
        """Check if required dependencies are available."""
        return {
            "pymongo_available": PYMONGO_AVAILABLE,
            "pymongo_version": pymongo.__version__ if PYMONGO_AVAILABLE else None,
            "environment_variables": {
                "MONGO_URI": bool(os.getenv('MONGO_URI')),
                "MONGODB_URI": bool(os.getenv('MONGODB_URI')),
                "MONGO_DB_NAME": bool(os.getenv('MONGO_DB_NAME')),
                "MONGO_COLLECTION_NAME": bool(os.getenv('MONGO_COLLECTION_NAME'))
            }
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test MongoDB connection."""
        if not PYMONGO_AVAILABLE:
            return {
                "status": "error",
                "message": "PyMongo not available. Install with: pip install pymongo"
            }
        
        if not self.mongo_uri:
            return {
                "status": "error",
                "message": "MongoDB URI not found in environment variables"
            }
        
        try:
            # Create client with timeout
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection with ping
            ping_result = self.client.admin.command('ping')
            
            # Get server info
            server_info = self.client.server_info()
            
            # Get database list
            databases = self.client.list_database_names()
            
            return {
                "status": "connected",
                "ping_result": ping_result,
                "server_version": server_info.get('version', 'unknown'),
                "connection_type": "MongoDB Atlas" if "mongodb.net" in self.mongo_uri else "Local MongoDB",
                "databases": databases,
                "configured_database": self.db_name,
                "database_exists": self.db_name in databases
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__
            }
    
    def test_database_operations(self) -> Dict[str, Any]:
        """Test database operations."""
        if not self.client:
            return {"status": "error", "message": "No MongoDB connection"}
        
        try:
            # Get database and collection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Test operations
            results = {}
            
            # 1. List collections
            collections = self.db.list_collection_names()
            results["collections"] = collections
            results["target_collection_exists"] = self.collection_name in collections
            
            # 2. Test insert (with cleanup)
            test_doc = {
                "test": True,
                "timestamp": datetime.now(),
                "agent": "mongodb_status_checker",
                "message": "Test document for connection verification"
            }
            
            insert_result = self.collection.insert_one(test_doc)
            results["insert_test"] = {
                "success": True,
                "inserted_id": str(insert_result.inserted_id)
            }
            
            # 3. Test find
            found_doc = self.collection.find_one({"_id": insert_result.inserted_id})
            results["find_test"] = {
                "success": found_doc is not None,
                "document_found": found_doc is not None
            }
            
            # 4. Test count
            total_docs = self.collection.count_documents({})
            results["count_test"] = {
                "success": True,
                "total_documents": total_docs
            }
            
            # 5. Clean up test document
            delete_result = self.collection.delete_one({"_id": insert_result.inserted_id})
            results["cleanup"] = {
                "success": delete_result.deleted_count == 1,
                "deleted_count": delete_result.deleted_count
            }
            
            return {
                "status": "success",
                "database": self.db_name,
                "collection": self.collection_name,
                "operations": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.db:
            return {"status": "error", "message": "No database connection"}
        
        try:
            # Database stats
            db_stats = self.db.command("dbStats")
            
            # Collection stats
            collection_stats = {}
            for collection_name in self.db.list_collection_names():
                try:
                    stats = self.db.command("collStats", collection_name)
                    collection_stats[collection_name] = {
                        "count": stats.get("count", 0),
                        "size": stats.get("size", 0),
                        "avgObjSize": stats.get("avgObjSize", 0)
                    }
                except:
                    collection_stats[collection_name] = {"error": "Could not get stats"}
            
            return {
                "status": "success",
                "database_stats": {
                    "collections": db_stats.get("collections", 0),
                    "dataSize": db_stats.get("dataSize", 0),
                    "storageSize": db_stats.get("storageSize", 0),
                    "indexes": db_stats.get("indexes", 0)
                },
                "collection_stats": collection_stats
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__
            }
    
    def test_mcp_integration(self) -> Dict[str, Any]:
        """Test MCP-specific MongoDB integration."""
        if not self.collection:
            return {"status": "error", "message": "No collection connection"}
        
        try:
            # Look for MCP-related data
            results = {}
            
            # 1. Check for agent outputs
            agent_outputs = list(self.collection.find({"agent": {"$exists": True}}).limit(5))
            results["agent_outputs"] = {
                "count": len(agent_outputs),
                "sample": [
                    {
                        "agent": doc.get("agent", "unknown"),
                        "timestamp": doc.get("timestamp", doc.get("created_at", "unknown")),
                        "has_output": "output" in doc
                    }
                    for doc in agent_outputs
                ]
            }
            
            # 2. Check for different agent types
            agent_types = list(self.collection.distinct("agent"))
            results["agent_types"] = agent_types
            
            # 3. Check for recent activity (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(days=1)
            recent_docs = self.collection.count_documents({
                "$or": [
                    {"timestamp": {"$gte": yesterday}},
                    {"created_at": {"$gte": yesterday}}
                ]
            })
            results["recent_activity"] = {
                "last_24_hours": recent_docs
            }
            
            # 4. Check for document processing results
            doc_processing = self.collection.count_documents({
                "$or": [
                    {"agent": {"$regex": "document", "$options": "i"}},
                    {"agent": {"$regex": "pdf", "$options": "i"}},
                    {"agent": {"$regex": "ocr", "$options": "i"}}
                ]
            })
            results["document_processing"] = {
                "count": doc_processing
            }
            
            return {
                "status": "success",
                "mcp_integration": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__
            }
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run comprehensive MongoDB status check."""
        print("🔍 MongoDB Status Checker for MCP System")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "mongo_uri_configured": bool(self.mongo_uri),
                "database_name": self.db_name,
                "collection_name": self.collection_name
            }
        }
        
        # 1. Check dependencies
        print("\n1️⃣ Checking Dependencies...")
        deps = self.check_dependencies()
        results["dependencies"] = deps
        
        if deps["pymongo_available"]:
            print(f"   ✅ PyMongo available (v{deps['pymongo_version']})")
        else:
            print("   ❌ PyMongo not available")
            return results
        
        # 2. Test connection
        print("\n2️⃣ Testing Connection...")
        connection = self.test_connection()
        results["connection"] = connection
        
        if connection["status"] == "connected":
            print(f"   ✅ Connected to {connection['connection_type']}")
            print(f"   📊 Server version: {connection['server_version']}")
            print(f"   📁 Databases: {len(connection['databases'])}")
            print(f"   🎯 Target database exists: {connection['database_exists']}")
        else:
            print(f"   ❌ Connection failed: {connection['message']}")
            return results
        
        # 3. Test database operations
        print("\n3️⃣ Testing Database Operations...")
        operations = self.test_database_operations()
        results["operations"] = operations
        
        if operations["status"] == "success":
            ops = operations["operations"]
            print(f"   ✅ Collections: {len(ops['collections'])}")
            print(f"   ✅ Insert test: {ops['insert_test']['success']}")
            print(f"   ✅ Find test: {ops['find_test']['success']}")
            print(f"   ✅ Count test: {ops['count_test']['success']} ({ops['count_test']['total_documents']} docs)")
            print(f"   ✅ Cleanup: {ops['cleanup']['success']}")
        else:
            print(f"   ❌ Operations failed: {operations['message']}")
        
        # 4. Get database stats
        print("\n4️⃣ Getting Database Statistics...")
        stats = self.get_database_stats()
        results["statistics"] = stats
        
        if stats["status"] == "success":
            db_stats = stats["database_stats"]
            print(f"   📊 Collections: {db_stats['collections']}")
            print(f"   📊 Data size: {db_stats['dataSize']} bytes")
            print(f"   📊 Indexes: {db_stats['indexes']}")
        
        # 5. Test MCP integration
        print("\n5️⃣ Testing MCP Integration...")
        mcp = self.test_mcp_integration()
        results["mcp_integration"] = mcp
        
        if mcp["status"] == "success":
            integration = mcp["mcp_integration"]
            print(f"   🤖 Agent outputs: {integration['agent_outputs']['count']}")
            print(f"   🤖 Agent types: {len(integration['agent_types'])}")
            print(f"   🤖 Recent activity: {integration['recent_activity']['last_24_hours']} docs")
            print(f"   📄 Document processing: {integration['document_processing']['count']} docs")
            
            if integration['agent_types']:
                print(f"   🎯 Active agents: {', '.join(integration['agent_types'][:5])}")
        
        return results
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()

def main():
    """Main function to run MongoDB status check."""
    checker = MongoDBStatusChecker()
    
    try:
        results = checker.run_comprehensive_check()
        
        print("\n" + "=" * 60)
        print("📋 SUMMARY")
        print("=" * 60)
        
        # Overall status
        if results.get("connection", {}).get("status") == "connected":
            print("✅ MongoDB Status: CONNECTED")
            
            if results.get("operations", {}).get("status") == "success":
                print("✅ Database Operations: WORKING")
            else:
                print("⚠️ Database Operations: ISSUES DETECTED")
            
            if results.get("mcp_integration", {}).get("status") == "success":
                mcp_data = results["mcp_integration"]["mcp_integration"]
                if mcp_data["agent_outputs"]["count"] > 0:
                    print("✅ MCP Integration: ACTIVE WITH DATA")
                else:
                    print("⚠️ MCP Integration: CONNECTED BUT NO DATA")
            else:
                print("❌ MCP Integration: ISSUES DETECTED")
        else:
            print("❌ MongoDB Status: DISCONNECTED")
        
        print("\n🎯 MongoDB is ready for your MCP system!")
        
    except Exception as e:
        print(f"\n❌ Error during status check: {e}")
    finally:
        checker.close()

if __name__ == "__main__":
    main()
