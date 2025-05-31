#!/usr/bin/env python3
"""
Connection Status Summary
Quick summary of all MCP system connections
"""

import requests
import sys
from datetime import datetime

def check_connection_status():
    """Check and display connection status."""
    print("🔍 MCP SYSTEM CONNECTION STATUS")
    print("=" * 60)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Server Health
    print("\n🚀 SERVER STATUS:")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Status: {health.get('status', 'unknown').upper()}")
            print(f"   ✅ Ready: {health.get('ready', False)}")
            print(f"   ✅ Agents Loaded: {health.get('system', {}).get('loaded_agents', 0)}")
            print(f"   ✅ MongoDB Connected: {health.get('mongodb_connected', False)}")
            server_ok = True
        else:
            print(f"   ❌ Server Error: HTTP {response.status_code}")
            server_ok = False
    except Exception as e:
        print(f"   ❌ Server Not Running: {e}")
        server_ok = False
    
    # 2. MongoDB Connection
    print("\n💾 MONGODB STATUS:")
    try:
        sys.path.insert(0, "blackhole_core/data_source")
        from mongodb import test_connection, get_agent_outputs_collection
        
        if test_connection():
            collection = get_agent_outputs_collection()
            doc_count = collection.count_documents({})
            print(f"   ✅ Connection: Working")
            print(f"   ✅ Documents Stored: {doc_count}")
            mongodb_ok = True
        else:
            print(f"   ❌ Connection: Failed")
            mongodb_ok = False
    except Exception as e:
        print(f"   ❌ MongoDB Error: {e}")
        mongodb_ok = False
    
    # 3. Agent Functionality
    print("\n🤖 AGENT FUNCTIONALITY:")
    if server_ok:
        test_queries = [
            ("Calculate 5 + 5", "Math Agent"),
            ("What is the weather in Mumbai?", "Weather Agent"),
            ("Analyze this text: test", "Document Agent")
        ]
        
        working_agents = 0
        
        for query, agent_name in test_queries:
            try:
                response = requests.post(
                    "http://localhost:8000/api/mcp/command",
                    json={"command": query},
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        print(f"   ✅ {agent_name}: Working")
                        working_agents += 1
                    else:
                        print(f"   ❌ {agent_name}: Failed")
                else:
                    print(f"   ❌ {agent_name}: HTTP Error")
            except Exception as e:
                print(f"   ❌ {agent_name}: Error")
        
        agents_ok = working_agents >= 2
        print(f"   📊 Working Agents: {working_agents}/3")
    else:
        print("   ⚠️ Cannot test agents - server not running")
        agents_ok = False
    
    # 4. Web Interface
    print("\n🌐 WEB INTERFACE:")
    if server_ok:
        try:
            response = requests.get("http://localhost:8000", timeout=5)
            if response.status_code == 200:
                content = response.text
                interactive = all(element in content for element in [
                    'id="queryInput"', 'sendQuery()', 'class="example"'
                ])
                
                if interactive:
                    print("   ✅ Interactive Interface: Working")
                    print("   ✅ All Elements: Present")
                    interface_ok = True
                else:
                    print("   ⚠️ Interface: Partially Working")
                    interface_ok = False
            else:
                print(f"   ❌ Interface: HTTP {response.status_code}")
                interface_ok = False
        except Exception as e:
            print(f"   ❌ Interface Error: {e}")
            interface_ok = False
    else:
        print("   ⚠️ Cannot test interface - server not running")
        interface_ok = False
    
    # 5. Overall Status
    print("\n" + "=" * 60)
    print("📊 OVERALL CONNECTION STATUS")
    print("=" * 60)
    
    components = [
        ("Server", server_ok),
        ("MongoDB", mongodb_ok),
        ("Agents", agents_ok),
        ("Web Interface", interface_ok)
    ]
    
    working = sum(1 for _, status in components if status)
    total = len(components)
    health_score = (working / total) * 100
    
    for name, status in components:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {'Working' if status else 'Issues'}")
    
    print(f"\n🎯 System Health: {health_score:.0f}% ({working}/{total} components)")
    
    if health_score >= 90:
        print("🎉 EXCELLENT! All connections working perfectly!")
        status_msg = "PERFECT"
    elif health_score >= 75:
        print("👍 GOOD! Most connections working well!")
        status_msg = "GOOD"
    elif health_score >= 50:
        print("⚠️ FAIR! System partially functional!")
        status_msg = "PARTIAL"
    else:
        print("❌ POOR! Major connection issues!")
        status_msg = "ISSUES"
    
    print(f"\n🌐 ACCESS YOUR SYSTEM:")
    if server_ok:
        print("🚀 Web Interface: http://localhost:8000")
        print("📊 Health Check: http://localhost:8000/api/health")
        print("🤖 Agent Status: http://localhost:8000/api/agents")
        
        print(f"\n💬 TRY THESE QUERIES:")
        print("🔢 Calculate 25 * 4")
        print("🌤️ What is the weather in Mumbai?")
        print("📄 Analyze this text: Hello world")
    else:
        print("⚠️ Start server first: python production_mcp_server.py")
    
    return status_msg, health_score

def main():
    """Main function."""
    try:
        status, score = check_connection_status()
        
        print(f"\n🎯 FINAL STATUS: {status} ({score:.0f}%)")
        
        if score >= 75:
            print("✅ Your MCP system connections are working fine!")
            return True
        else:
            print("⚠️ Some connection issues detected - check details above")
            return False
            
    except Exception as e:
        print(f"\n❌ Connection check failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Connection check completed - all good!")
    else:
        print("\n🔧 Connection check completed - some issues found")
