#!/usr/bin/env python3
"""
Check Agent Status - Comprehensive status report
"""

import requests
import json
from datetime import datetime

def check_server_health():
    """Check server health and basic info."""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def check_agents_list():
    """Get detailed agent list."""
    try:
        response = requests.get("http://localhost:8000/api/agents", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def test_individual_agent(command, agent_name):
    """Test individual agent functionality."""
    try:
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": command},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": result.get("status", "unknown"),
                "agent_used": result.get("agent_used", "none"),
                "message": result.get("message", ""),
                "result": result.get("result", ""),
                "city": result.get("city", ""),
                "email_sent": result.get("email_sent", False),
                "reminder": result.get("reminder", {}),
                "weather_data": result.get("weather_data", {}),
                "raw_response": result
            }
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main status check function."""
    print("📊 COMPREHENSIVE AGENT STATUS REPORT")
    print("=" * 80)
    print(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. Server Health Check
    print("\n🔍 SERVER HEALTH CHECK")
    print("-" * 50)
    
    health = check_server_health()
    if "error" in health:
        print(f"❌ Server Error: {health['error']}")
        print("💡 Try running: python connect_everything.py")
        return
    
    print(f"✅ Server Status: {health.get('status', 'unknown')}")
    print(f"🚀 Server Type: {health.get('server', 'unknown')}")
    print(f"⚡ Ready: {health.get('ready', False)}")
    print(f"🤖 Agents Loaded: {health.get('agents_loaded', 0)}")
    print(f"📋 Available Agents: {', '.join(health.get('available_agents', []))}")
    print(f"⏰ Timestamp: {health.get('timestamp', 'unknown')}")
    
    # 2. Detailed Agent Information
    print("\n🤖 DETAILED AGENT INFORMATION")
    print("-" * 50)
    
    agents_info = check_agents_list()
    if "error" in agents_info:
        print(f"❌ Agents List Error: {agents_info['error']}")
    else:
        agents = agents_info.get("agents", {})
        total_agents = agents_info.get("total_agents", 0)
        
        print(f"📊 Total Agents: {total_agents}")
        
        for agent_id, agent_data in agents.items():
            print(f"\n   🔹 {agent_id.upper()}")
            print(f"      Status: {agent_data.get('status', 'unknown')}")
            print(f"      Class: {agent_data.get('class_name', 'unknown')}")
            print(f"      Keywords: {', '.join(agent_data.get('keywords', []))}")
    
    # 3. Individual Agent Testing
    print("\n🧪 INDIVIDUAL AGENT TESTING")
    print("-" * 50)
    
    test_cases = [
        ("Calculate 20% of 500", "Math Agent"),
        ("What is the weather in Mumbai?", "Weather Agent"),
        ("Send email to test@example.com", "Gmail Agent"),
        ("Create reminder for tomorrow", "Calendar Agent"),
        ("Analyze this text: Hello world", "Document Agent")
    ]
    
    working_agents = 0
    total_tests = len(test_cases)
    
    for command, agent_name in test_cases:
        print(f"\n🔍 Testing {agent_name}")
        print(f"   Command: {command}")
        
        result = test_individual_agent(command, agent_name)
        
        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            status = result.get("status", "unknown")
            agent_used = result.get("agent_used", "none")
            
            if status == "success":
                print(f"   ✅ Status: SUCCESS")
                print(f"   🤖 Agent Used: {agent_used}")
                working_agents += 1
                
                # Show specific results
                if result.get("result"):
                    print(f"   📊 Result: {result['result']}")
                if result.get("city"):
                    print(f"   🌍 City: {result['city']}")
                    weather = result.get("weather_data", {})
                    if weather:
                        temp = weather.get("temperature", "N/A")
                        desc = weather.get("description", "N/A")
                        print(f"   🌡️ Weather: {temp}°C, {desc}")
                if result.get("reminder"):
                    print(f"   📅 Reminder: Created")
                if "email" in result.get("message", "").lower():
                    print(f"   📧 Email: Prepared")
            else:
                print(f"   ⚠️ Status: {status}")
                print(f"   💬 Message: {result.get('message', 'No message')}")
    
    # 4. Summary
    print("\n" + "=" * 80)
    print("📈 FINAL STATUS SUMMARY")
    print("=" * 80)
    
    success_rate = (working_agents / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"🔧 Server: {'✅ Running' if health.get('status') == 'ok' else '❌ Issues'}")
    print(f"🤖 Total Agents: {health.get('agents_loaded', 0)}")
    print(f"✅ Working Agents: {working_agents}/{total_tests}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print(f"⚡ Overall Status: ✅ EXCELLENT")
        print(f"🎉 Your MCP system is performing excellently!")
    elif success_rate >= 60:
        print(f"⚡ Overall Status: ⚡ GOOD")
        print(f"👍 Your MCP system is working well!")
    elif success_rate >= 40:
        print(f"⚡ Overall Status: ⚠️ FAIR")
        print(f"🔧 Some agents need attention")
    else:
        print(f"⚡ Overall Status: ❌ NEEDS ATTENTION")
        print(f"🔧 Multiple agents require troubleshooting")
    
    print(f"\n🌐 Access Points:")
    print(f"   • Web Interface: http://localhost:8000")
    print(f"   • API Documentation: http://localhost:8000/docs")
    print(f"   • Health Check: http://localhost:8000/api/health")
    
    print(f"\n🔄 To restart system: python connect_everything.py")

if __name__ == "__main__":
    main()
