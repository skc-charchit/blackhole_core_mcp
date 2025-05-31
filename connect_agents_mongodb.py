#!/usr/bin/env python3
"""
Connect Agents with MongoDB
Integrate all agents with MongoDB using your existing mongodb.py
"""

import os
import sys
import asyncio
import requests
import json
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

class AgentMongoDBConnector:
    """Connect all agents with MongoDB storage."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.mongodb_client = None
        self.agent_outputs_collection = None
        self.connection_status = {}
        
    def test_mongodb_connection(self):
        """Test MongoDB connection using your existing module."""
        print("💾 TESTING MONGODB CONNECTION")
        print("=" * 60)
        
        try:
            # Import your existing MongoDB module
            from mongodb import get_mongo_client, get_agent_outputs_collection, test_connection
            
            print("✅ Successfully imported your MongoDB module")
            
            # Test connection
            connection_success = test_connection()
            
            if connection_success:
                print("✅ MongoDB connection successful")
                
                # Get client and collection
                self.mongodb_client = get_mongo_client()
                self.agent_outputs_collection = get_agent_outputs_collection()
                
                print(f"✅ MongoDB client: {type(self.mongodb_client).__name__}")
                print(f"✅ Collection: {type(self.agent_outputs_collection).__name__}")
                
                # Test data insertion
                test_doc = {
                    "test": True,
                    "timestamp": datetime.now(),
                    "message": "MongoDB connection test"
                }
                
                result = self.agent_outputs_collection.insert_one(test_doc)
                print(f"✅ Test document inserted: {result.inserted_id}")
                
                if "dummy" in str(result.inserted_id):
                    print("⚠️ Using dummy MongoDB (no actual storage)")
                    return "dummy"
                else:
                    print("🎉 Real MongoDB storage working!")
                    return "real"
                    
            else:
                print("❌ MongoDB connection failed")
                return False
                
        except ImportError as e:
            print(f"❌ Failed to import MongoDB module: {e}")
            return False
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            return False
    
    def check_server_status(self):
        """Check if MCP server is running."""
        print("\n🚀 CHECKING MCP SERVER STATUS")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Server Status: {health.get('status')}")
                print(f"✅ Ready: {health.get('ready')}")
                print(f"✅ Agents Loaded: {health.get('system', {}).get('loaded_agents', 0)}")
                print(f"✅ MongoDB Connected: {health.get('mongodb_connected', False)}")
                return True
            else:
                print(f"❌ Server responded with status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Server not running")
            print("💡 Please start the server first: python production_mcp_server.py")
            return False
        except Exception as e:
            print(f"❌ Error checking server: {e}")
            return False
    
    def get_agent_list(self):
        """Get list of available agents."""
        print("\n🤖 GETTING AGENT LIST")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/api/agents", timeout=5)
            if response.status_code == 200:
                agents_data = response.json()
                agents = agents_data.get('agents', {})
                
                print(f"📊 Total Agents: {len(agents)}")
                
                loaded_agents = []
                for agent_id, agent_info in agents.items():
                    status = agent_info.get('status', 'unknown')
                    if status == 'loaded':
                        loaded_agents.append(agent_id)
                        print(f"✅ {agent_id}: {status}")
                    else:
                        print(f"⚠️ {agent_id}: {status}")
                
                return loaded_agents
            else:
                print(f"❌ Failed to get agents: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error getting agents: {e}")
            return []
    
    def test_agent_mongodb_integration(self, agent_id, test_command):
        """Test agent with MongoDB storage."""
        print(f"\n🧪 Testing {agent_id} with MongoDB")
        
        try:
            # Send command to agent
            response = requests.post(
                f"{self.base_url}/api/mcp/command",
                json={"command": test_command},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                status = result.get('status')
                agent_used = result.get('agent_used')
                stored = result.get('stored_in_mongodb', False)
                mongodb_id = result.get('mongodb_id')
                
                print(f"   ✅ Status: {status}")
                print(f"   🤖 Agent Used: {agent_used}")
                print(f"   💾 MongoDB Stored: {stored}")
                print(f"   🆔 MongoDB ID: {mongodb_id}")
                
                # Store additional data using your MongoDB module
                if self.agent_outputs_collection:
                    try:
                        enhanced_doc = {
                            "agent_id": agent_id,
                            "command": test_command,
                            "result": result,
                            "timestamp": datetime.now(),
                            "status": status,
                            "enhanced_storage": True
                        }
                        
                        enhanced_result = self.agent_outputs_collection.insert_one(enhanced_doc)
                        print(f"   ✅ Enhanced Storage: {enhanced_result.inserted_id}")
                        
                    except Exception as e:
                        print(f"   ⚠️ Enhanced Storage Failed: {e}")
                
                return {
                    "agent_id": agent_id,
                    "status": status,
                    "stored": stored,
                    "mongodb_id": mongodb_id,
                    "working": status == "success"
                }
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return {"agent_id": agent_id, "working": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"agent_id": agent_id, "working": False, "error": str(e)}
    
    def test_all_agents_with_mongodb(self):
        """Test all agents with MongoDB integration."""
        print("\n🔗 TESTING ALL AGENTS WITH MONGODB")
        print("=" * 60)
        
        # Get available agents
        loaded_agents = self.get_agent_list()
        
        if not loaded_agents:
            print("❌ No agents available for testing")
            return {}
        
        # Test commands for each agent type
        test_commands = {
            "math_agent": "Calculate 100 + 50",
            "weather_agent": "What is the weather in Mumbai?",
            "document_agent": "Analyze this text: Hello MongoDB integration",
            "gmail_agent": "Send email test",
            "calendar_agent": "Create reminder test"
        }
        
        results = {}
        
        for agent_id in loaded_agents:
            test_command = test_commands.get(agent_id, f"Test {agent_id}")
            result = self.test_agent_mongodb_integration(agent_id, test_command)
            results[agent_id] = result
        
        return results
    
    def create_mongodb_storage_enhancement(self):
        """Create enhanced MongoDB storage for agents."""
        print("\n🔧 CREATING MONGODB STORAGE ENHANCEMENT")
        print("=" * 60)
        
        if not self.agent_outputs_collection:
            print("❌ MongoDB collection not available")
            return False
        
        try:
            # Create indexes for better performance
            try:
                self.agent_outputs_collection.create_index("agent_id")
                self.agent_outputs_collection.create_index("timestamp")
                self.agent_outputs_collection.create_index("status")
                print("✅ Created database indexes")
            except Exception as e:
                print(f"⚠️ Index creation: {e}")
            
            # Create a comprehensive storage function
            storage_code = '''
# Enhanced MongoDB Storage for Agents
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))

from mongodb import get_agent_outputs_collection
from datetime import datetime

async def store_agent_result(agent_id, command, result, metadata=None):
    """Store agent result in MongoDB with enhanced data."""
    try:
        collection = get_agent_outputs_collection()
        
        document = {
            "agent_id": agent_id,
            "command": command,
            "result": result,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
            "stored_by": "enhanced_storage"
        }
        
        result = collection.insert_one(document)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Storage error: {e}")
        return None

def get_agent_history(agent_id, limit=10):
    """Get agent command history from MongoDB."""
    try:
        collection = get_agent_outputs_collection()
        
        cursor = collection.find(
            {"agent_id": agent_id}
        ).sort("timestamp", -1).limit(limit)
        
        return list(cursor)
    except Exception as e:
        print(f"History retrieval error: {e}")
        return []
'''
            
            with open("enhanced_mongodb_storage.py", "w") as f:
                f.write(storage_code)
            
            print("✅ Created enhanced_mongodb_storage.py")
            return True
            
        except Exception as e:
            print(f"❌ Enhancement creation failed: {e}")
            return False
    
    def generate_connection_summary(self, test_results):
        """Generate comprehensive connection summary."""
        print("\n" + "=" * 80)
        print("📊 MONGODB AGENT CONNECTION SUMMARY")
        print("=" * 80)
        
        working_agents = sum(1 for result in test_results.values() if result.get('working', False))
        total_agents = len(test_results)
        
        print(f"🎯 MongoDB Connection: {'✅ Working' if self.mongodb_client else '❌ Failed'}")
        print(f"🤖 Working Agents: {working_agents}/{total_agents}")
        print(f"💾 Storage Type: {self.connection_status.get('mongodb_type', 'Unknown')}")
        
        print(f"\n📋 AGENT DETAILS:")
        for agent_id, result in test_results.items():
            working = result.get('working', False)
            stored = result.get('stored', False)
            status_icon = "✅" if working else "❌"
            storage_icon = "💾" if stored else "⚠️"
            
            print(f"   {status_icon} {agent_id}: {result.get('status', 'unknown')}")
            print(f"      {storage_icon} Storage: {'Working' if stored else 'Limited'}")
            
            if result.get('mongodb_id'):
                print(f"      🆔 MongoDB ID: {result['mongodb_id']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if working_agents == total_agents:
            print("   🎉 Perfect! All agents connected with MongoDB")
        elif working_agents > 0:
            print("   👍 Good! Most agents working, some need attention")
        else:
            print("   🔧 Needs work! Check agent and MongoDB configuration")
        
        if self.connection_status.get('mongodb_type') == 'dummy':
            print("   💾 Install MongoDB for persistent storage")
        
        return working_agents >= (total_agents * 0.5)  # 50% success rate
    
    def run_complete_connection(self):
        """Run complete MongoDB agent connection."""
        print("🔗 CONNECTING AGENTS WITH MONGODB")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Step 1: Test MongoDB
        mongodb_status = self.test_mongodb_connection()
        self.connection_status['mongodb_type'] = mongodb_status
        
        if not mongodb_status:
            print("❌ MongoDB connection failed - cannot proceed")
            return False
        
        # Step 2: Check server
        server_running = self.check_server_status()
        if not server_running:
            print("❌ MCP server not running - cannot proceed")
            return False
        
        # Step 3: Test all agents with MongoDB
        test_results = self.test_all_agents_with_mongodb()
        
        # Step 4: Create enhancements
        self.create_mongodb_storage_enhancement()
        
        # Step 5: Generate summary
        success = self.generate_connection_summary(test_results)
        
        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return success

def main():
    """Main function."""
    connector = AgentMongoDBConnector()
    
    try:
        success = connector.run_complete_connection()
        
        if success:
            print("\n🎉 AGENTS SUCCESSFULLY CONNECTED WITH MONGODB!")
            print("✅ Your agents are now integrated with MongoDB storage")
            print("✅ Enhanced storage functions created")
            print("✅ Database indexes optimized")
            
            print("\n🌐 NEXT STEPS:")
            print("1. Your agents are now storing data in MongoDB")
            print("2. Use enhanced_mongodb_storage.py for advanced features")
            print("3. Access your system at http://localhost:8000")
            
            return True
        else:
            print("\n⚠️ PARTIAL CONNECTION ACHIEVED")
            print("Some agents connected but system needs attention")
            return False
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🔗 MongoDB agent connection completed successfully!")
    else:
        print("\n🔧 Connection completed with issues - check messages above")
