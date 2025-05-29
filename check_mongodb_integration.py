#!/usr/bin/env python3
"""
Check MongoDB Integration Status
Verify if MongoDB is storing data and interacting with all agents
"""

import os
import sys
import requests
import json
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

def check_mongodb_connection():
    """Check if MongoDB is connected and accessible."""
    print("🔍 CHECKING MONGODB CONNECTION")
    print("=" * 50)
    
    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        print(f"📡 MongoDB URI: {mongo_uri}")
        
        # Try to connect
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # List databases
        db_names = client.list_database_names()
        print(f"📊 Available databases: {len(db_names)}")
        for db_name in db_names:
            if not db_name.startswith('admin') and not db_name.startswith('config') and not db_name.startswith('local'):
                print(f"   • {db_name}")
        
        # Check MCP database
        mcp_db_names = [name for name in db_names if 'mcp' in name.lower() or 'blackhole' in name.lower()]
        if mcp_db_names:
            print(f"🎯 MCP-related databases found: {mcp_db_names}")
            
            for db_name in mcp_db_names:
                db = client[db_name]
                collections = db.list_collection_names()
                print(f"   📁 {db_name} collections: {collections}")
                
                # Check collection sizes
                for collection_name in collections:
                    collection = db[collection_name]
                    count = collection.count_documents({})
                    print(f"      • {collection_name}: {count} documents")
        else:
            print("⚠️ No MCP-related databases found")
        
        client.close()
        return True, mcp_db_names
        
    except ImportError:
        print("❌ PyMongo not installed")
        return False, []
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False, []

def check_mcp_mongodb_integration():
    """Check if MCP MongoDB integration is working."""
    print("\n🔗 CHECKING MCP MONGODB INTEGRATION")
    print("=" * 50)
    
    try:
        # Check if integration file exists
        integration_file = Path("mcp_mongodb_integration.py")
        if not integration_file.exists():
            print("❌ mcp_mongodb_integration.py not found")
            return False
        
        print("✅ MCP MongoDB integration file found")
        
        # Try to import and test
        from mcp_mongodb_integration import MCPMongoDBIntegration
        
        integration = MCPMongoDBIntegration()
        print("✅ MCPMongoDBIntegration class imported successfully")
        
        # Test connection
        import asyncio
        
        async def test_connection():
            connected = await integration.connect()
            if connected:
                print("✅ MCP MongoDB integration connected")
                
                # Test basic operations
                test_data = {
                    "test_type": "connection_test",
                    "timestamp": datetime.now().isoformat(),
                    "message": "Testing MongoDB integration"
                }
                
                result = await integration.store_interaction("test_agent", "test_command", test_data)
                if result:
                    print("✅ Test data storage successful")
                else:
                    print("⚠️ Test data storage failed")
                
                return True
            else:
                print("❌ MCP MongoDB integration connection failed")
                return False
        
        return asyncio.run(test_connection())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def check_agent_mongodb_usage():
    """Check if agents are using MongoDB for storage."""
    print("\n🤖 CHECKING AGENT MONGODB USAGE")
    print("=" * 50)
    
    agent_files = [
        "agents/specialized/math_agent.py",
        "agents/data/realtime_weather_agent.py",
        "agents/communication/real_gmail_agent.py",
        "agents/specialized/calendar_agent.py",
        "agents/core/document_processor.py"
    ]
    
    mongodb_usage = {}
    
    for agent_file in agent_files:
        agent_path = Path(agent_file)
        agent_name = agent_path.stem
        
        print(f"\n🔍 Checking {agent_name}...")
        
        if not agent_path.exists():
            print(f"   ❌ File not found: {agent_file}")
            mongodb_usage[agent_name] = "file_not_found"
            continue
        
        try:
            with open(agent_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for MongoDB-related imports and usage
            mongodb_indicators = [
                'pymongo',
                'MongoClient',
                'mongodb',
                'mongo',
                'store_interaction',
                'save_to_database',
                'database',
                'collection'
            ]
            
            found_indicators = []
            for indicator in mongodb_indicators:
                if indicator.lower() in content.lower():
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"   ✅ MongoDB usage found: {', '.join(found_indicators)}")
                mongodb_usage[agent_name] = "mongodb_integrated"
            else:
                print(f"   ⚠️ No MongoDB usage detected")
                mongodb_usage[agent_name] = "no_mongodb"
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            mongodb_usage[agent_name] = "read_error"
    
    return mongodb_usage

def check_server_mongodb_integration():
    """Check if the MCP server is using MongoDB."""
    print("\n🚀 CHECKING SERVER MONGODB INTEGRATION")
    print("=" * 50)
    
    server_files = [
        "mcp_server.py",
        "simple_mcp_server.py",
        "embedded_mcp_server.py"
    ]
    
    for server_file in server_files:
        server_path = Path(server_file)
        
        if not server_path.exists():
            continue
            
        print(f"\n🔍 Checking {server_file}...")
        
        try:
            with open(server_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for MongoDB integration
            mongodb_indicators = [
                'mongodb_integration',
                'MCPMongoDBIntegration',
                'pymongo',
                'store_interaction',
                'database'
            ]
            
            found_indicators = []
            for indicator in mongodb_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"   ✅ MongoDB integration found: {', '.join(found_indicators)}")
            else:
                print(f"   ⚠️ No MongoDB integration detected")
                
        except Exception as e:
            print(f"   ❌ Error reading {server_file}: {e}")

def test_data_storage_retrieval():
    """Test if data is being stored and retrieved from MongoDB."""
    print("\n🧪 TESTING DATA STORAGE & RETRIEVAL")
    print("=" * 50)
    
    # Test commands that should store data
    test_commands = [
        "Calculate 20% of 500",
        "What is the weather in Mumbai?",
        "Send email to test@example.com",
        "Create reminder for tomorrow"
    ]
    
    print("🔄 Sending test commands to check data storage...")
    
    for command in test_commands:
        print(f"\n📤 Testing: {command}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": command},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                agent_used = result.get("agent_used", "unknown")
                
                # Check if response indicates data storage
                storage_indicators = [
                    'stored', 'saved', 'database', 'mongodb', 
                    'logged', 'recorded', 'persisted'
                ]
                
                response_text = json.dumps(result).lower()
                storage_found = any(indicator in response_text for indicator in storage_indicators)
                
                if storage_found:
                    print(f"   ✅ {agent_used}: Data storage indicated")
                else:
                    print(f"   ⚠️ {agent_used}: No storage indication")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main function to check MongoDB integration."""
    print("💾 MONGODB INTEGRATION STATUS CHECK")
    print("=" * 80)
    print("🎯 Checking if MongoDB is storing data and interacting with agents")
    print("=" * 80)
    
    # 1. Check MongoDB connection
    mongodb_connected, mcp_databases = check_mongodb_connection()
    
    # 2. Check MCP MongoDB integration
    integration_working = check_mcp_mongodb_integration()
    
    # 3. Check agent MongoDB usage
    agent_usage = check_agent_mongodb_usage()
    
    # 4. Check server MongoDB integration
    check_server_mongodb_integration()
    
    # 5. Test data storage and retrieval
    if mongodb_connected:
        test_data_storage_retrieval()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 MONGODB INTEGRATION SUMMARY")
    print("=" * 80)
    
    print(f"💾 MongoDB Connection: {'✅ Connected' if mongodb_connected else '❌ Not Connected'}")
    print(f"🔗 MCP Integration: {'✅ Working' if integration_working else '❌ Not Working'}")
    print(f"🎯 MCP Databases: {len(mcp_databases)} found")
    
    # Agent usage summary
    mongodb_agents = len([a for a in agent_usage.values() if a == "mongodb_integrated"])
    total_agents = len(agent_usage)
    
    print(f"🤖 Agent Integration: {mongodb_agents}/{total_agents} agents using MongoDB")
    
    for agent, status in agent_usage.items():
        if status == "mongodb_integrated":
            print(f"   ✅ {agent}: MongoDB integrated")
        elif status == "no_mongodb":
            print(f"   ⚠️ {agent}: No MongoDB usage")
        else:
            print(f"   ❌ {agent}: {status}")
    
    # Overall assessment
    if mongodb_connected and integration_working and mongodb_agents > 0:
        print(f"\n⚡ Overall Status: ✅ MONGODB FULLY INTEGRATED")
        print(f"🎉 MongoDB is storing data and interacting with agents!")
    elif mongodb_connected and integration_working:
        print(f"\n⚡ Overall Status: ⚡ MONGODB PARTIALLY INTEGRATED")
        print(f"🔧 MongoDB connected but agents need integration")
    elif mongodb_connected:
        print(f"\n⚡ Overall Status: ⚠️ MONGODB AVAILABLE BUT NOT INTEGRATED")
        print(f"🔧 MongoDB running but MCP integration needs setup")
    else:
        print(f"\n⚡ Overall Status: ❌ MONGODB NOT INTEGRATED")
        print(f"🔧 MongoDB needs to be set up and integrated")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if not mongodb_connected:
        print(f"   1. Start MongoDB service")
        print(f"   2. Check MONGO_URI in .env file")
    if not integration_working:
        print(f"   3. Set up MCP MongoDB integration")
    if mongodb_agents == 0:
        print(f"   4. Add MongoDB storage to agents")
    
    print(f"\n🔄 To check again: python check_mongodb_integration.py")

if __name__ == "__main__":
    main()
