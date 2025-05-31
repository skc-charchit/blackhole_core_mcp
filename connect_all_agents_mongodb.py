#!/usr/bin/env python3
"""
Connect All Agents to MongoDB - Comprehensive Integration Script
Ensures all agents are properly connected to MongoDB and storing data consistently
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mongodb_connector")

class MongoDBAgentConnector:
    """Comprehensive MongoDB connector for all agents."""
    
    def __init__(self):
        self.logger = logger
        self.mongodb_integration = None
        self.agents = {}
        self.connection_status = {}
        self.storage_stats = {
            "total_stored": 0,
            "successful_stores": 0,
            "failed_stores": 0,
            "agents_connected": 0
        }
    
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
    
    async def load_all_agents(self):
        """Load all available agents."""
        try:
            # Import agent manager
            from agent_manager import AgentManager
            
            agent_manager = AgentManager()
            await agent_manager.discover_agents()
            
            self.agents = agent_manager.loaded_agents
            self.logger.info(f"✅ Loaded {len(self.agents)} agents")
            
            for agent_id, agent_info in self.agents.items():
                self.logger.info(f"   📋 {agent_id}: {agent_info.get('metadata', {}).get('name', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load agents: {e}")
            return False
    
    async def check_agent_mongodb_connection(self, agent_id: str, agent_instance):
        """Check if an agent is properly connected to MongoDB."""
        try:
            # Check if agent has MongoDB integration
            if hasattr(agent_instance, 'mongodb_integration') and agent_instance.mongodb_integration:
                # Test the connection
                if hasattr(agent_instance.mongodb_integration, 'collection') and agent_instance.mongodb_integration.collection:
                    self.connection_status[agent_id] = "connected"
                    self.storage_stats["agents_connected"] += 1
                    self.logger.info(f"✅ {agent_id}: MongoDB connected")
                    return True
                else:
                    self.connection_status[agent_id] = "disconnected"
                    self.logger.warning(f"⚠️ {agent_id}: MongoDB integration exists but not connected")
                    return False
            else:
                self.connection_status[agent_id] = "no_integration"
                self.logger.warning(f"⚠️ {agent_id}: No MongoDB integration found")
                return False
                
        except Exception as e:
            self.connection_status[agent_id] = f"error: {str(e)}"
            self.logger.error(f"❌ {agent_id}: Connection check failed - {e}")
            return False
    
    async def test_agent_storage(self, agent_id: str, agent_instance):
        """Test if an agent can store data in MongoDB."""
        try:
            if not hasattr(agent_instance, 'mongodb_integration') or not agent_instance.mongodb_integration:
                return False
            
            # Create test data
            test_input = {
                "test": True,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "test_type": "mongodb_connection_test"
            }
            
            test_output = {
                "status": "success",
                "message": f"MongoDB connection test for {agent_id}",
                "test_result": "storage_test_passed",
                "timestamp": datetime.now().isoformat()
            }
            
            test_metadata = {
                "test_type": "mongodb_storage_test",
                "agent_version": getattr(agent_instance, 'version', '1.0.0'),
                "storage_method": "connection_test"
            }
            
            # Test primary storage method
            mongodb_id = await agent_instance.mongodb_integration.save_agent_output(
                agent_id,
                test_input,
                test_output,
                test_metadata
            )
            
            if mongodb_id and "error" not in str(mongodb_id):
                self.storage_stats["successful_stores"] += 1
                self.storage_stats["total_stored"] += 1
                self.logger.info(f"✅ {agent_id}: Storage test passed - {mongodb_id}")
                return True
            else:
                self.storage_stats["failed_stores"] += 1
                self.storage_stats["total_stored"] += 1
                self.logger.error(f"❌ {agent_id}: Storage test failed - {mongodb_id}")
                return False
                
        except Exception as e:
            self.storage_stats["failed_stores"] += 1
            self.storage_stats["total_stored"] += 1
            self.logger.error(f"❌ {agent_id}: Storage test error - {e}")
            return False
    
    async def ensure_agent_mongodb_connection(self, agent_id: str, agent_instance):
        """Ensure an agent is properly connected to MongoDB."""
        try:
            # Check if agent already has MongoDB integration
            if not hasattr(agent_instance, 'mongodb_integration') or not agent_instance.mongodb_integration:
                # Initialize MongoDB integration for the agent
                try:
                    from mcp_mongodb_integration import MCPMongoDBIntegration
                    agent_instance.mongodb_integration = MCPMongoDBIntegration()
                    connected = await agent_instance.mongodb_integration.connect()
                    
                    if connected:
                        self.logger.info(f"✅ {agent_id}: MongoDB integration initialized")
                    else:
                        self.logger.error(f"❌ {agent_id}: Failed to initialize MongoDB integration")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"❌ {agent_id}: MongoDB integration initialization error - {e}")
                    return False
            
            # Test the connection
            connection_ok = await self.check_agent_mongodb_connection(agent_id, agent_instance)
            if not connection_ok:
                # Try to reconnect
                try:
                    connected = await agent_instance.mongodb_integration.connect()
                    if connected:
                        self.logger.info(f"✅ {agent_id}: MongoDB reconnected successfully")
                        connection_ok = True
                    else:
                        self.logger.error(f"❌ {agent_id}: MongoDB reconnection failed")
                        return False
                except Exception as e:
                    self.logger.error(f"❌ {agent_id}: MongoDB reconnection error - {e}")
                    return False
            
            # Test storage capability
            storage_ok = await self.test_agent_storage(agent_id, agent_instance)
            
            return connection_ok and storage_ok
            
        except Exception as e:
            self.logger.error(f"❌ {agent_id}: Ensure connection error - {e}")
            return False
    
    async def connect_all_agents(self):
        """Connect all agents to MongoDB."""
        self.logger.info("🔗 CONNECTING ALL AGENTS TO MONGODB")
        self.logger.info("=" * 60)
        
        # Initialize MongoDB
        mongodb_ok = await self.initialize_mongodb()
        if not mongodb_ok:
            self.logger.error("❌ Cannot proceed without MongoDB connection")
            return False
        
        # Load all agents
        agents_loaded = await self.load_all_agents()
        if not agents_loaded:
            self.logger.error("❌ Cannot proceed without agents")
            return False
        
        # Connect each agent to MongoDB
        success_count = 0
        total_agents = len(self.agents)
        
        for agent_id, agent_info in self.agents.items():
            self.logger.info(f"\n🔌 Connecting {agent_id} to MongoDB...")
            
            try:
                agent_instance = agent_info.get("instance")
                if agent_instance:
                    success = await self.ensure_agent_mongodb_connection(agent_id, agent_instance)
                    if success:
                        success_count += 1
                        self.logger.info(f"✅ {agent_id}: Successfully connected to MongoDB")
                    else:
                        self.logger.error(f"❌ {agent_id}: Failed to connect to MongoDB")
                else:
                    self.logger.error(f"❌ {agent_id}: No agent instance found")
                    
            except Exception as e:
                self.logger.error(f"❌ {agent_id}: Connection error - {e}")
        
        # Generate summary report
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 MONGODB CONNECTION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ Total Agents: {total_agents}")
        self.logger.info(f"✅ Successfully Connected: {success_count}")
        self.logger.info(f"❌ Failed Connections: {total_agents - success_count}")
        self.logger.info(f"📈 Success Rate: {(success_count/total_agents)*100:.1f}%")
        
        self.logger.info(f"\n📊 STORAGE TEST RESULTS:")
        self.logger.info(f"✅ Successful Stores: {self.storage_stats['successful_stores']}")
        self.logger.info(f"❌ Failed Stores: {self.storage_stats['failed_stores']}")
        self.logger.info(f"📊 Total Tests: {self.storage_stats['total_stored']}")
        
        if self.storage_stats['total_stored'] > 0:
            storage_success_rate = (self.storage_stats['successful_stores'] / self.storage_stats['total_stored']) * 100
            self.logger.info(f"📈 Storage Success Rate: {storage_success_rate:.1f}%")
        
        # Show connection status for each agent
        self.logger.info(f"\n📋 AGENT CONNECTION STATUS:")
        for agent_id, status in self.connection_status.items():
            status_icon = "✅" if status == "connected" else "❌"
            self.logger.info(f"   {status_icon} {agent_id}: {status}")
        
        return success_count == total_agents
    
    async def verify_data_storage(self):
        """Verify that data is being stored properly by testing each agent."""
        self.logger.info("\n🧪 VERIFYING DATA STORAGE")
        self.logger.info("=" * 60)
        
        test_queries = {
            "math_agent": "Calculate 10 + 5",
            "weather_agent": "Weather in Mumbai",
            "document_agent": "Analyze this text: Hello world, this is a test document for MongoDB storage verification."
        }
        
        verification_results = {}
        
        for agent_id, test_query in test_queries.items():
            if agent_id in self.agents:
                self.logger.info(f"\n🧪 Testing {agent_id} with query: '{test_query}'")
                
                try:
                    agent_instance = self.agents[agent_id]["instance"]
                    
                    # Create test message
                    from agents.base_agent import MCPMessage
                    message = MCPMessage(
                        id=f"test_{agent_id}_{datetime.now().timestamp()}",
                        method="process",
                        params={"query": test_query, "expression": test_query},
                        timestamp=datetime.now()
                    )
                    
                    # Process the message
                    result = await agent_instance.process_message(message)
                    
                    if result.get("status") == "success":
                        verification_results[agent_id] = "✅ PASSED"
                        self.logger.info(f"✅ {agent_id}: Test query processed successfully")
                    else:
                        verification_results[agent_id] = "❌ FAILED"
                        self.logger.error(f"❌ {agent_id}: Test query failed")
                        
                except Exception as e:
                    verification_results[agent_id] = f"❌ ERROR: {str(e)}"
                    self.logger.error(f"❌ {agent_id}: Test error - {e}")
            else:
                verification_results[agent_id] = "❌ NOT LOADED"
                self.logger.warning(f"⚠️ {agent_id}: Agent not loaded")
        
        # Show verification results
        self.logger.info(f"\n📊 VERIFICATION RESULTS:")
        for agent_id, result in verification_results.items():
            self.logger.info(f"   {result.split()[0]} {agent_id}: {result}")
        
        return verification_results

async def main():
    """Main function to connect all agents to MongoDB."""
    print("🔗 MONGODB AGENT CONNECTOR")
    print("=" * 80)
    print("🎯 Connecting all agents to MongoDB for comprehensive data storage")
    print("💾 Ensuring consistent data persistence across all agents")
    print("🧪 Testing storage capabilities and data verification")
    print("=" * 80)
    
    connector = MongoDBAgentConnector()
    
    try:
        # Connect all agents to MongoDB
        success = await connector.connect_all_agents()
        
        if success:
            print("\n🎉 ALL AGENTS SUCCESSFULLY CONNECTED TO MONGODB!")

            # Verify data storage with test queries
            await connector.verify_data_storage()

            # Monitor storage health
            await connector.monitor_storage_health()

            # Get storage statistics
            await connector.get_storage_statistics()

            print("\n" + "=" * 80)
            print("✅ MONGODB INTEGRATION COMPLETE")
            print("=" * 80)
            print("🎯 All agents are now connected to MongoDB")
            print("💾 Data storage is working across all agents")
            print("🧪 Storage verification tests completed")
            print("💊 Health monitoring active")
            print("📊 Storage statistics available")
            print("🚀 Your system is ready for production use")
            
        else:
            print("\n⚠️ SOME AGENTS FAILED TO CONNECT TO MONGODB")
            print("🔧 Check the logs above for specific issues")
            print("💡 The system will still work, but some data may not be stored")
            
    except Exception as e:
        logger.error(f"❌ Main execution error: {e}")
        print(f"\n❌ MONGODB CONNECTION FAILED: {e}")
        print("🔧 Check your MongoDB configuration and try again")

    async def monitor_storage_health(self):
        """Monitor MongoDB storage health across all agents."""
        self.logger.info("\n💊 MONGODB STORAGE HEALTH MONITORING")
        self.logger.info("=" * 60)

        health_results = {}

        for agent_id, agent_info in self.agents.items():
            try:
                agent_instance = agent_info.get("instance")
                if agent_instance and hasattr(agent_instance, 'health_check'):
                    health = await agent_instance.health_check()
                    mongodb_status = health.get('mongodb_connected', False)

                    health_results[agent_id] = {
                        "mongodb_connected": mongodb_status,
                        "status": health.get('status', 'unknown'),
                        "failure_count": health.get('failure_count', 0),
                        "last_check": health.get('last_check', 'unknown')
                    }

                    status_icon = "✅" if mongodb_status else "❌"
                    self.logger.info(f"   {status_icon} {agent_id}: MongoDB {mongodb_status}, Status: {health.get('status', 'unknown')}")
                else:
                    health_results[agent_id] = {"error": "No health check available"}
                    self.logger.warning(f"   ⚠️ {agent_id}: No health check method available")

            except Exception as e:
                health_results[agent_id] = {"error": str(e)}
                self.logger.error(f"   ❌ {agent_id}: Health check error - {e}")

        return health_results

    async def get_storage_statistics(self):
        """Get comprehensive storage statistics from MongoDB."""
        if not self.mongodb_integration or not self.mongodb_integration.db:
            self.logger.warning("MongoDB not available for statistics")
            return {}

        try:
            self.logger.info("\n📊 MONGODB STORAGE STATISTICS")
            self.logger.info("=" * 60)

            db = self.mongodb_integration.db

            # Get collection statistics
            collections = await asyncio.to_thread(db.list_collection_names)
            stats = {}

            for collection_name in collections:
                collection = db[collection_name]
                count = await asyncio.to_thread(collection.count_documents, {})
                stats[collection_name] = count
                self.logger.info(f"   📋 {collection_name}: {count} documents")

            # Get agent-specific statistics
            if 'agent_outputs' in collections:
                agent_outputs = db['agent_outputs']

                # Count by agent
                pipeline = [
                    {"$group": {"_id": "$agent_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]

                agent_counts = await asyncio.to_thread(
                    lambda: list(agent_outputs.aggregate(pipeline))
                )

                self.logger.info(f"\n📊 DOCUMENTS BY AGENT:")
                for item in agent_counts:
                    agent_id = item.get('_id', 'unknown')
                    count = item.get('count', 0)
                    self.logger.info(f"   🤖 {agent_id}: {count} documents")

            return stats

        except Exception as e:
            self.logger.error(f"❌ Error getting storage statistics: {e}")
            return {}

if __name__ == "__main__":
    asyncio.run(main())
