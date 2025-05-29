#!/usr/bin/env python3
"""
Test Current MCP System
Simple tests to verify what's working
"""

import requests
import json
from datetime import datetime

def test_server_health():
    """Test if server is running."""
    print("🔍 TESTING SERVER HEALTH")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server Status: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure to run: python core/mcp_server.py")
        return False

def test_simple_weather():
    """Test simple weather query."""
    print("\n🌤️ TESTING SIMPLE WEATHER QUERY")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": "What is the weather in Mumbai?"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Message: {result.get('message', 'No message')}")
            print(f"Agent: {result.get('agent_used', 'unknown')}")
            
            if result.get('status') == 'success':
                print("✅ Weather query successful!")
                return True
            else:
                print("❌ Weather query failed")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Weather test error: {e}")
        return False

def test_simple_math():
    """Test simple math query."""
    print("\n🔢 TESTING SIMPLE MATH QUERY")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": "Calculate 20% of 500"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Message: {result.get('message', 'No message')}")
            print(f"Agent: {result.get('agent_used', 'unknown')}")
            
            if result.get('status') == 'success':
                print("✅ Math query successful!")
                return True
            else:
                print("❌ Math query failed")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Math test error: {e}")
        return False

def test_available_agents():
    """Test what agents are available."""
    print("\n🤖 TESTING AVAILABLE AGENTS")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/mcp/agents", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            agents = result.get("agents", {})
            
            print(f"Total agents: {len(agents)}")
            for name, info in agents.items():
                desc = info.get("description", "No description")
                print(f"  • {name}: {desc}")
            
            return len(agents) > 0
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Agent list error: {e}")
        return False

def test_conversation_engine():
    """Test if conversation engine is working."""
    print("\n🗣️ TESTING CONVERSATION ENGINE")
    print("=" * 50)
    
    try:
        # Test with a simple query
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": "Hello, are you working?"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Message: {result.get('message', 'No message')[:100]}...")
            
            return result.get('status') == 'success'
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Conversation test error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 CURRENT SYSTEM TEST")
    print("=" * 80)
    print("🎯 Testing what's currently working in your MCP system")
    print("=" * 80)
    
    tests = [
        ("Server Health", test_server_health),
        ("Available Agents", test_available_agents),
        ("Simple Weather", test_simple_weather),
        ("Simple Math", test_simple_math),
        ("Conversation Engine", test_conversation_engine)
    ]
    
    passed_tests = 0
    
    for test_name, test_function in tests:
        try:
            if test_function():
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
        
        print()
    
    print("=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    print(f"✅ Passed: {passed_tests}/{len(tests)}")
    print(f"📈 Success rate: {(passed_tests/len(tests))*100:.1f}%")
    
    if passed_tests >= 3:
        print("\n🎉 SYSTEM IS MOSTLY WORKING!")
        print("💡 Try these working commands:")
        print("   🌤️ MCP> What is the weather in Mumbai?")
        print("   🔢 MCP> Calculate 20% of 500")
        print("   🗣️ MCP> Hello, how are you?")
        
        print("\n🔧 FOR COMPLEX QUERIES:")
        print("   Break them into separate commands:")
        print("   1. MCP> What is the weather in Mumbai?")
        print("   2. MCP> Calculate 20% discount on 500 rupees")
        print("   3. MCP> Extract text from image")
        print("   4. MCP> Create a story about weather and savings")
        
    else:
        print("\n🔧 SYSTEM NEEDS ATTENTION")
        print("💡 Check if the MCP server is running:")
        print("   python core/mcp_server.py")
    
    return passed_tests >= 3

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 System test completed!")
        else:
            print("\n🔧 System needs fixes.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
