#!/usr/bin/env python3
"""
Simple System Test
Test the MCP system and MongoDB storage
"""

import requests
import json
from datetime import datetime

def test_system():
    """Test the system."""
    base_url = "http://localhost:8000"
    
    print("🧪 SIMPLE SYSTEM TEST")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n🔍 Health Check")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Status: {health.get('status')}")
            print(f"   ✅ Ready: {health.get('ready')}")
            print(f"   ✅ MongoDB: {health.get('mongodb_connected')}")
            print(f"   ✅ Agents: {health.get('system', {}).get('loaded_agents', 0)}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Math Command
    print("\n🔢 Math Command Test")
    try:
        response = requests.post(
            f"{base_url}/api/mcp/command",
            json={"command": "Calculate 100 + 50"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Status: {result.get('status')}")
            print(f"   🤖 Agent: {result.get('agent_used')}")
            print(f"   📊 Result: {result.get('result')}")
            print(f"   💾 MongoDB Stored: {result.get('stored_in_mongodb', False)}")
            print(f"   🆔 MongoDB ID: {result.get('mongodb_id', 'None')}")
            print(f"   🔧 Storage Method: {result.get('storage_method', 'None')}")
            
            if result.get('stored_in_mongodb'):
                print("   🎉 MONGODB STORAGE IS WORKING!")
            else:
                print("   ⚠️ MongoDB storage not working")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Weather Command
    print("\n🌤️ Weather Command Test")
    try:
        response = requests.post(
            f"{base_url}/api/mcp/command",
            json={"command": "What is the weather in Mumbai?"},
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Status: {result.get('status')}")
            print(f"   🤖 Agent: {result.get('agent_used')}")
            print(f"   🌍 City: {result.get('city', 'N/A')}")
            print(f"   💾 MongoDB Stored: {result.get('stored_in_mongodb', False)}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ SYSTEM TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    test_system()
