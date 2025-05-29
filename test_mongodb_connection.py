#!/usr/bin/env python3
"""
Test MongoDB Connection
Test the existing MongoDB module and integration
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))

def test_mongodb_integration():
    """Test the MongoDB integration."""
    print("🧪 TESTING MONGODB INTEGRATION")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test 1: Import MongoDB module
    print("\n🔍 Test 1: Import MongoDB Module")
    try:
        from mongodb import get_mongo_client, get_agent_outputs_collection, test_connection
        print("   ✅ Successfully imported MongoDB module")
    except ImportError as e:
        print(f"   ❌ Failed to import MongoDB module: {e}")
        return False
    
    # Test 2: Test MongoDB connection
    print("\n🔍 Test 2: Test MongoDB Connection")
    try:
        connection_success = test_connection()
        if connection_success:
            print("   ✅ MongoDB connection successful")
        else:
            print("   ⚠️ MongoDB connection failed - using dummy mode")
    except Exception as e:
        print(f"   ❌ MongoDB connection test error: {e}")
        connection_success = False
    
    # Test 3: Get MongoDB client
    print("\n🔍 Test 3: Get MongoDB Client")
    try:
        client = get_mongo_client()
        print(f"   ✅ MongoDB client obtained: {type(client).__name__}")
        
        # Check if it's a dummy client
        if "Dummy" in type(client).__name__:
            print("   ⚠️ Using dummy MongoDB client (no actual database)")
        else:
            print("   ✅ Using real MongoDB client")
    except Exception as e:
        print(f"   ❌ Failed to get MongoDB client: {e}")
        client = None
    
    # Test 4: Get agent outputs collection
    print("\n🔍 Test 4: Get Agent Outputs Collection")
    try:
        collection = get_agent_outputs_collection()
        print(f"   ✅ Agent outputs collection obtained: {type(collection).__name__}")
        
        # Check if it's a dummy collection
        if "Dummy" in type(collection).__name__:
            print("   ⚠️ Using dummy collection (no actual storage)")
        else:
            print("   ✅ Using real MongoDB collection")
    except Exception as e:
        print(f"   ❌ Failed to get agent outputs collection: {e}")
        collection = None
    
    # Test 5: Test data insertion
    print("\n🔍 Test 5: Test Data Insertion")
    try:
        if collection:
            test_document = {
                "agent_id": "test_agent",
                "command": "test command",
                "result": "test result",
                "timestamp": datetime.now(),
                "test": True
            }
            
            result = collection.insert_one(test_document)
            print(f"   ✅ Document inserted with ID: {result.inserted_id}")
            
            if "dummy" in str(result.inserted_id):
                print("   ⚠️ Dummy insertion (not actually stored)")
            else:
                print("   ✅ Real insertion (actually stored in MongoDB)")
        else:
            print("   ❌ No collection available for testing")
    except Exception as e:
        print(f"   ❌ Data insertion test error: {e}")
    
    # Test 6: Environment variables
    print("\n🔍 Test 6: Environment Variables")
    env_vars = [
        "MONGODB_URI",
        "MONGO_URI", 
        "MONGO_URI_LOCAL",
        "MONGO_DB_NAME",
        "MONGO_COLLECTION_NAME"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive parts of URI
            if "URI" in var and value:
                masked_value = value[:20] + "..." + value[-10:] if len(value) > 30 else value
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️ {var}: Not set")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MONGODB INTEGRATION SUMMARY")
    print("=" * 60)
    
    if connection_success:
        print("🎉 MONGODB INTEGRATION WORKING!")
        print("   ✅ Connection successful")
        print("   ✅ Data storage available")
        print("   ✅ Ready for production use")
    else:
        print("⚠️ MONGODB INTEGRATION IN DUMMY MODE")
        print("   ❌ No real database connection")
        print("   ⚠️ Data will not be persisted")
        print("   💡 Install MongoDB or check connection settings")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return connection_success

def show_mongodb_setup_instructions():
    """Show MongoDB setup instructions."""
    print("\n💡 MONGODB SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("🔧 Option 1: Install MongoDB Locally")
    print("   1. Download MongoDB Community Server")
    print("   2. Install with default settings")
    print("   3. Start MongoDB service")
    print("   4. Set MONGO_URI_LOCAL=mongodb://localhost:27017/")
    
    print("\n🐳 Option 2: Use Docker")
    print("   1. docker run -d -p 27017:27017 --name mongodb mongo")
    print("   2. Set MONGO_URI_LOCAL=mongodb://localhost:27017/")
    
    print("\n☁️ Option 3: Use Cloud MongoDB")
    print("   1. Create MongoDB Atlas account")
    print("   2. Create cluster and get connection string")
    print("   3. Set MONGODB_URI=your_connection_string")
    
    print("\n📝 Environment Variables (.env file):")
    print("   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/")
    print("   MONGO_URI_LOCAL=mongodb://localhost:27017/")
    print("   MONGO_DB_NAME=mcp_production")
    print("   MONGO_COLLECTION_NAME=agent_outputs")

def main():
    """Main function."""
    success = test_mongodb_integration()
    
    if not success:
        show_mongodb_setup_instructions()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
