#!/usr/bin/env python3
"""
Test All Agents - Verify that all agents are working
"""

import requests
import json
from datetime import datetime

def test_agent(command, description):
    """Test a single agent command."""
    print(f"\n🔍 Testing: {description}")
    print(f"Command: {command}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": command},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            
            if status == "success":
                print(f"✅ SUCCESS")
                
                # Show specific results
                if "result" in result:
                    print(f"   Result: {result['result']}")
                if "formatted_result" in result:
                    print(f"   Formatted: {result['formatted_result']}")
                if "weather_data" in result:
                    weather = result["weather_data"]
                    print(f"   Weather: {weather.get('temperature', 'N/A')}°C, {weather.get('description', 'N/A')}")
                if "city" in result:
                    print(f"   City: {result['city']}")
                if "email_sent" in result:
                    print(f"   Email: {'Sent' if result['email_sent'] else 'Prepared'}")
                if "reminder" in result:
                    print(f"   Reminder: {result['reminder']}")
                
                agent_used = result.get("agent_used", "unknown")
                print(f"   Agent: {agent_used}")
                
                return True
            else:
                print(f"❌ FAILED: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def main():
    """Test all agents."""
    print("🧪 TESTING ALL AGENTS")
    print("=" * 80)
    
    # Check server health first
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server Status: {health.get('status', 'unknown')}")
            print(f"📊 Agents Loaded: {health.get('agents_loaded', 0)}")
            print(f"🤖 Available Agents: {health.get('available_agents', [])}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test commands
    test_cases = [
        ("Calculate 20% of 500", "Math Agent - Percentage calculation"),
        ("What is 15 * 25?", "Math Agent - Multiplication"),
        ("Analyze this text: Hello world", "Document Agent - Text analysis"),
        ("Send email to test@example.com", "Gmail Agent - Email sending"),
        ("Create reminder for tomorrow", "Calendar Agent - Reminder creation"),
        ("What is the weather in Mumbai?", "Weather Agent - Live weather data"),
        ("Mumbai weather", "Weather Agent - Simple weather query"),
        ("Temperature in Delhi", "Weather Agent - Temperature query")
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for command, description in test_cases:
        success = test_agent(command, description)
        if success:
            successful_tests += 1
    
    # Final results
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - successful_tests}/{total_tests}")
    print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("\n🎉 ALL AGENTS WORKING PERFECTLY!")
        print("✅ Your unified MCP system is fully operational!")
    elif successful_tests > 0:
        print(f"\n⚡ PARTIAL SUCCESS!")
        print(f"✅ {successful_tests} agents working correctly")
        print("🔧 Some agents may need attention")
    else:
        print("\n❌ NO AGENTS WORKING")
        print("🔧 System needs troubleshooting")
    
    print(f"\n🌐 Access your system at: http://localhost:8000")
    print(f"📚 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
