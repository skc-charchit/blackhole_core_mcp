#!/usr/bin/env python3
"""
Test Gmail Integration and All Production Agents
Comprehensive testing of the cleaned up MCP system
"""

import requests
import json
from datetime import datetime

def test_server_health():
    """Test if the MCP server is running."""
    print("🔍 TESTING SERVER HEALTH")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server Status: {result.get('status', 'unknown')}")
            print(f"📊 Server Type: {result.get('mcp_server', 'unknown')}")
            print(f"⏰ Timestamp: {result.get('timestamp', 'unknown')}")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_loaded_agents():
    """Test what agents are currently loaded."""
    print("\n🤖 TESTING LOADED AGENTS")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/mcp/agents", timeout=5)
        if response.status_code == 200:
            result = response.json()
            agents = result.get("agents", {})
            
            print(f"📊 Total Loaded Agents: {len(agents)}")
            print()
            
            # Expected production agents
            expected_agents = [
                "realtime_weather_agent",
                "math_agent", 
                "calendar_agent",
                "real_gmail_agent",
                "document_processor"
            ]
            
            print("🎯 EXPECTED PRODUCTION AGENTS:")
            for agent in expected_agents:
                if agent in agents:
                    print(f"   ✅ {agent}")
                else:
                    print(f"   ❌ {agent} (not loaded)")
            
            print("\n📋 ALL LOADED AGENTS:")
            for name, info in agents.items():
                desc = info.get("description", "No description")
                print(f"   • {name}: {desc}")
            
            return agents
        else:
            print(f"❌ Failed to get agents: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Error getting agents: {e}")
        return {}

def test_weather_functionality():
    """Test weather functionality."""
    print("\n🌤️ TESTING WEATHER FUNCTIONALITY")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": "What is the weather in Mumbai?"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                print("✅ Weather query successful!")
                city = result.get("city", "Unknown")
                weather_data = result.get("weather_data", {})
                temp = weather_data.get("temperature", "N/A")
                desc = weather_data.get("description", "N/A")
                agent = result.get("agent_used", "unknown")
                
                print(f"   🏙️ City: {city}")
                print(f"   🌡️ Temperature: {temp}°C")
                print(f"   ☁️ Conditions: {desc}")
                print(f"   🤖 Agent: {agent}")
                return True
            else:
                print(f"❌ Weather query failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Weather test error: {e}")
        return False

def test_math_functionality():
    """Test math functionality."""
    print("\n🔢 TESTING MATH FUNCTIONALITY")
    print("=" * 50)
    
    math_queries = [
        "What is 15% of 200?",
        "Calculate 2 + 3 * 4",
        "What is the square root of 16?"
    ]
    
    success_count = 0
    
    for query in math_queries:
        print(f"🧮 Testing: {query}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": query},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "success":
                    math_result = result.get("result", result.get("formatted_result", "N/A"))
                    agent = result.get("agent_used", "unknown")
                    print(f"   ✅ Result: {math_result} (Agent: {agent})")
                    success_count += 1
                else:
                    print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Math tests passed: {success_count}/{len(math_queries)}")
    return success_count > 0

def test_gmail_functionality():
    """Test Gmail functionality."""
    print("\n📧 TESTING GMAIL FUNCTIONALITY")
    print("=" * 50)
    
    email_commands = [
        "Send email to shreekumarchandancharchit@gmail.com about test message",
        "Email shreekumarchandancharchit@gmail.com with project update",
        "Mail to shreekumarchandancharchit@gmail.com about system status"
    ]
    
    success_count = 0
    
    for command in email_commands:
        print(f"📧 Testing: {command}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": command},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "success":
                    email_sent = result.get("email_sent", False)
                    agent = result.get("agent_used", "unknown")
                    to_email = result.get("to_email", "N/A")
                    
                    print(f"   ✅ Email processed!")
                    print(f"   📧 To: {to_email}")
                    print(f"   📤 Sent: {email_sent}")
                    print(f"   🤖 Agent: {agent}")
                    
                    if email_sent:
                        success_count += 1
                        print(f"   🎉 EMAIL SUCCESSFULLY SENT!")
                    else:
                        print(f"   ⚠️ Email processed but not sent (demo mode)")
                else:
                    print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print(f"📊 Gmail tests processed: {len(email_commands)}")
    print(f"📤 Emails sent: {success_count}")
    return success_count > 0

def test_conditional_scenario():
    """Test the specific conditional scenario."""
    print("\n🧠 TESTING CONDITIONAL SCENARIO")
    print("=" * 50)
    
    scenario = "If it rains today after 4pm then remind me and send email to shreekumarchandancharchit@gmail.com to not come to office and submit work on Monday EOD"
    
    print(f"📝 Scenario: {scenario}")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": scenario},
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Status: {result.get('status', 'unknown')}")
            print(f"💬 Message: {result.get('message', 'No message')}")
            print(f"🤖 Agent: {result.get('agent_used', 'unknown')}")
            
            # Check if it's processed as weather or email
            if "weather" in result.get("message", "").lower():
                print("🌤️ Processed as weather query")
            elif "email" in result.get("message", "").lower():
                print("📧 Processed as email query")
            else:
                print("🤖 Processed as general command")
            
            return result.get("status") == "success"
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Scenario test error: {e}")
        return False

def show_gmail_credentials():
    """Show Gmail credentials status."""
    print("\n🔐 GMAIL CREDENTIALS STATUS")
    print("=" * 50)
    
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    gmail_email = os.getenv('GMAIL_EMAIL', '').strip()
    gmail_password = os.getenv('GMAIL_APP_PASSWORD', '').strip()
    
    if gmail_email and gmail_password:
        print(f"✅ Gmail Email: {gmail_email}")
        print(f"✅ App Password: {'*' * len(gmail_password)} ({len(gmail_password)} chars)")
        
        if gmail_email != 'your-email@gmail.com' and gmail_password != 'your-app-password':
            print("🎉 Real Gmail credentials configured!")
            return True
        else:
            print("⚠️ Using placeholder credentials")
            return False
    else:
        print("❌ Gmail credentials not found")
        return False

def main():
    """Main test function."""
    print("🧪 COMPREHENSIVE MCP SYSTEM TEST")
    print("=" * 80)
    print("🎯 Testing cleaned up system with Gmail integration")
    print("📧 Target email: shreekumarchandancharchit@gmail.com")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: Server Health
    test_results["server_health"] = test_server_health()
    
    # Test 2: Gmail Credentials
    test_results["gmail_credentials"] = show_gmail_credentials()
    
    # Test 3: Loaded Agents
    agents = test_loaded_agents()
    test_results["agents_loaded"] = len(agents) > 0
    
    # Test 4: Weather Functionality
    test_results["weather"] = test_weather_functionality()
    
    # Test 5: Math Functionality
    test_results["math"] = test_math_functionality()
    
    # Test 6: Gmail Functionality
    test_results["gmail"] = test_gmail_functionality()
    
    # Test 7: Conditional Scenario
    test_results["conditional"] = test_conditional_scenario()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n📈 Overall Score: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 MCP system is fully operational with Gmail integration!")
        print("\n💡 READY FOR USE:")
        print("   📧 Gmail integration working")
        print("   🌤️ Weather data live")
        print("   🔢 Math calculations working")
        print("   🤖 All agents operational")
        
    elif passed_tests >= total_tests * 0.7:
        print("\n🎯 MOSTLY SUCCESSFUL!")
        print("🔧 Minor issues but system is functional")
        
    else:
        print("\n⚠️ SYSTEM NEEDS ATTENTION")
        print("🔧 Several components need fixing")
    
    return passed_tests >= total_tests * 0.7

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 System test completed successfully!")
        else:
            print("\n🔧 System needs attention. Check failed tests above.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("💡 Make sure the MCP server is running: python mcp_server.py")
