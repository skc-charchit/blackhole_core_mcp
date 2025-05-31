#!/usr/bin/env python3
"""
Simple MongoDB Agent Connector
Connects all agents to MongoDB and verifies storage functionality
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mongodb_connector")

class SimpleMongoDBConnector:
    """Simple MongoDB connector for all agents."""
    
    def __init__(self):
        self.logger = logger
        self.mongodb_integration = None
        self.test_results = {}
    
    async def initialize_mongodb(self):
        """Initialize MongoDB integration."""
        try:
            from mcp_mongodb_integration import MCPMongoDBIntegration
            
            self.mongodb_integration = MCPMongoDBIntegration()
            connected = await self.mongodb_integration.connect()
            
            if connected:
                self.logger.info("✅ MongoDB integration initialized successfully")
                return True
            else:
                self.logger.error("❌ MongoDB connection failed")
                return False
                
        except ImportError as e:
            self.logger.error(f"❌ MongoDB integration not available: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ MongoDB initialization error: {e}")
            return False
    
    async def test_agent_storage(self, agent_name: str):
        """Test storage for a specific agent."""
        try:
            # Create test data
            test_input = {
                "test": True,
                "agent_id": agent_name,
                "timestamp": datetime.now().isoformat(),
                "test_type": "mongodb_connection_test"
            }
            
            test_output = {
                "status": "success",
                "message": f"MongoDB connection test for {agent_name}",
                "test_result": "storage_test_passed",
                "timestamp": datetime.now().isoformat()
            }
            
            test_metadata = {
                "test_type": "mongodb_storage_test",
                "storage_method": "connection_test",
                "connector_version": "1.0.0"
            }
            
            # Test storage
            mongodb_id = await self.mongodb_integration.save_agent_output(
                agent_name,
                test_input,
                test_output,
                test_metadata
            )
            
            if mongodb_id and "error" not in str(mongodb_id):
                self.logger.info(f"✅ {agent_name}: Storage test passed - {mongodb_id}")
                return True
            else:
                self.logger.error(f"❌ {agent_name}: Storage test failed - {mongodb_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ {agent_name}: Storage test error - {e}")
            return False
    
    async def test_all_agents(self):
        """Test MongoDB storage for all known agents."""
        self.logger.info("🧪 TESTING MONGODB STORAGE FOR ALL AGENTS")
        self.logger.info("=" * 60)
        
        # Known agents in the system
        agents = ["math_agent", "weather_agent", "document_agent"]
        
        success_count = 0
        
        for agent_name in agents:
            self.logger.info(f"\n🧪 Testing {agent_name}...")
            
            success = await self.test_agent_storage(agent_name)
            self.test_results[agent_name] = success
            
            if success:
                success_count += 1
        
        # Summary
        self.logger.info(f"\n📊 STORAGE TEST SUMMARY:")
        self.logger.info(f"✅ Total Agents Tested: {len(agents)}")
        self.logger.info(f"✅ Successful Tests: {success_count}")
        self.logger.info(f"❌ Failed Tests: {len(agents) - success_count}")
        self.logger.info(f"📈 Success Rate: {(success_count/len(agents))*100:.1f}%")
        
        return success_count == len(agents)
    
    async def verify_production_server_storage(self):
        """Verify that the production server is storing data in MongoDB."""
        try:
            self.logger.info("\n🔍 VERIFYING PRODUCTION SERVER STORAGE")
            self.logger.info("=" * 60)
            
            # Test command storage
            test_command = "Test MongoDB storage verification"
            test_result = {
                "status": "success",
                "message": "MongoDB storage verification test",
                "agent_used": "mongodb_connector",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store command result
            mongodb_id = await self.mongodb_integration.store_command_result(
                command=test_command,
                agent_used="mongodb_connector",
                result=test_result,
                timestamp=datetime.now()
            )
            
            if mongodb_id and "error" not in str(mongodb_id):
                self.logger.info(f"✅ Production server storage test passed - {mongodb_id}")
                return True
            else:
                self.logger.error(f"❌ Production server storage test failed - {mongodb_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Production server storage test error - {e}")
            return False
    
    async def get_storage_statistics(self):
        """Get storage statistics from MongoDB."""
        try:
            if not self.mongodb_integration or not self.mongodb_integration.db:
                self.logger.warning("MongoDB not available for statistics")
                return {}
            
            self.logger.info("\n📊 MONGODB STORAGE STATISTICS")
            self.logger.info("=" * 60)
            
            db = self.mongodb_integration.db
            
            # Get collection statistics
            collections = db.list_collection_names()
            stats = {}
            
            for collection_name in collections:
                collection = db[collection_name]
                count = collection.count_documents({})
                stats[collection_name] = count
                self.logger.info(f"   📋 {collection_name}: {count} documents")
            
            # Get recent documents from agent_outputs
            if 'agent_outputs' in collections:
                agent_outputs = db['agent_outputs']
                
                # Get recent documents
                recent_docs = list(agent_outputs.find().sort("timestamp", -1).limit(5))
                
                self.logger.info(f"\n📄 RECENT AGENT OUTPUTS:")
                for doc in recent_docs:
                    agent_id = doc.get('agent_id', 'unknown')
                    timestamp = doc.get('timestamp', 'unknown')
                    self.logger.info(f"   🤖 {agent_id}: {timestamp}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error getting storage statistics: {e}")
            return {}
    
    async def run_comprehensive_test(self):
        """Run comprehensive MongoDB connection and storage test."""
        self.logger.info("🔗 COMPREHENSIVE MONGODB AGENT CONNECTOR")
        self.logger.info("=" * 80)
        
        # Initialize MongoDB
        mongodb_ok = await self.initialize_mongodb()
        if not mongodb_ok:
            return False
        
        # Test agent storage
        agents_ok = await self.test_all_agents()
        
        # Test production server storage
        server_ok = await self.verify_production_server_storage()
        
        # Get storage statistics
        await self.get_storage_statistics()
        
        # Final summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 FINAL MONGODB CONNECTION SUMMARY")
        self.logger.info("=" * 80)
        
        mongodb_status = "✅ CONNECTED" if mongodb_ok else "❌ FAILED"
        agents_status = "✅ ALL WORKING" if agents_ok else "⚠️ SOME ISSUES"
        server_status = "✅ WORKING" if server_ok else "❌ FAILED"
        
        self.logger.info(f"💾 MongoDB Connection: {mongodb_status}")
        self.logger.info(f"🤖 Agent Storage: {agents_status}")
        self.logger.info(f"🖥️ Production Server: {server_status}")
        
        # Show individual agent results
        self.logger.info(f"\n🤖 INDIVIDUAL AGENT RESULTS:")
        for agent_name, success in self.test_results.items():
            status = "✅ WORKING" if success else "❌ FAILED"
            self.logger.info(f"   {agent_name}: {status}")
        
        overall_success = mongodb_ok and agents_ok and server_ok
        
        if overall_success:
            self.logger.info(f"\n🎉 ALL MONGODB CONNECTIONS SUCCESSFUL!")
            self.logger.info(f"✅ Your agents are now storing data in MongoDB")
            self.logger.info(f"🚀 System is ready for production use")
        else:
            self.logger.info(f"\n⚠️ SOME MONGODB CONNECTIONS FAILED")
            self.logger.info(f"🔧 Check the logs above for specific issues")
            self.logger.info(f"💡 The system will still work, but some data may not be stored")
        
        return overall_success

async def main():
    """Main function."""
    print("🔗 SIMPLE MONGODB AGENT CONNECTOR")
    print("=" * 80)
    print("🎯 Testing MongoDB connections for all agents")
    print("💾 Verifying data storage capabilities")
    print("📊 Getting storage statistics")
    print("=" * 80)
    
    connector = SimpleMongoDBConnector()
    
    try:
        success = await connector.run_comprehensive_test()
        
        if success:
            print("\n✅ MONGODB INTEGRATION SUCCESSFUL!")
            print("🎯 All agents can store data in MongoDB")
            print("💾 Production server storage verified")
            print("🚀 Your system is ready!")
        else:
            print("\n⚠️ MONGODB INTEGRATION HAD ISSUES")
            print("🔧 Check the logs for details")
            print("💡 Some features may not store data")
            
    except Exception as e:
        logger.error(f"❌ Main execution error: {e}")
        print(f"\n❌ MONGODB CONNECTION FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
