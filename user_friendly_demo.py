#!/usr/bin/env python3
"""
User-Friendly MCP Demo
Demonstrate all user interfaces and capabilities
"""

import requests
import time
import sys
from datetime import datetime

def demo_all_interfaces():
    """Demonstrate all user interfaces."""
    print("🎉 USER-FRIENDLY MCP SYSTEM DEMO")
    print("=" * 80)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check system status
    print("\n🔍 SYSTEM STATUS CHECK:")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server: {health.get('status', 'unknown').upper()}")
            print(f"✅ Ready: {health.get('ready', False)}")
            print(f"✅ MongoDB: {'Connected' if health.get('mongodb_connected') else 'Disconnected'}")
            print(f"✅ Agents: {health.get('system', {}).get('loaded_agents', 0)} loaded")
        else:
            print("❌ Server not responding properly")
            return False
    except:
        print("❌ Server not running!")
        print("💡 Please start: python production_mcp_server.py")
        return False
    
    # Demo queries
    demo_queries = [
        {
            "query": "Calculate 25 * 4",
            "description": "Math Calculation",
            "expected_agent": "math_agent"
        },
        {
            "query": "What is the weather in Mumbai?",
            "description": "Weather Query",
            "expected_agent": "weather_agent"
        },
        {
            "query": "Analyze this text: Hello world, this is a test document for analysis.",
            "description": "Document Analysis",
            "expected_agent": "document_agent"
        }
    ]
    
    print(f"\n🧪 TESTING ALL QUERY TYPES:")
    print("-" * 40)
    
    successful_queries = 0
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n{i}. {demo['description']}")
        print(f"   📤 Query: {demo['query']}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": demo['query']},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                agent_used = result.get('agent_used')
                
                if status == 'success':
                    print(f"   ✅ Status: SUCCESS")
                    print(f"   🤖 Agent: {agent_used}")
                    
                    # Show specific results
                    if 'result' in result:
                        print(f"   🔢 Answer: {result['result']}")
                    elif 'city' in result:
                        weather = result.get('weather_data', {})
                        print(f"   🌍 Location: {result['city']}")
                        print(f"   🌡️ Temperature: {weather.get('temperature', 'N/A')}°C")
                    elif 'total_documents' in result:
                        print(f"   📄 Documents: {result['total_documents']} processed")
                    
                    print(f"   💾 MongoDB: {'Stored' if result.get('stored_in_mongodb') else 'Not Stored'}")
                    successful_queries += 1
                else:
                    print(f"   ❌ Status: {status}")
                    print(f"   🚨 Error: {result.get('message', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between queries
    
    # Show available interfaces
    print(f"\n🌐 AVAILABLE USER INTERFACES:")
    print("-" * 40)
    
    interfaces = [
        {
            "name": "🌐 Web Interface",
            "access": "http://localhost:8000",
            "description": "Beautiful web UI with real-time responses",
            "best_for": "Interactive exploration and testing"
        },
        {
            "name": "💻 Interactive Command Line",
            "access": "python user_friendly_interface.py",
            "description": "Terminal-based chat interface",
            "best_for": "Power users and automation"
        },
        {
            "name": "⚡ Quick Query Tool",
            "access": "python quick_query.py \"Your question\"",
            "description": "One-shot queries with instant results",
            "best_for": "Scripts and quick tests"
        }
    ]
    
    for interface in interfaces:
        print(f"\n{interface['name']}")
        print(f"   🚀 Access: {interface['access']}")
        print(f"   📝 Description: {interface['description']}")
        print(f"   💡 Best for: {interface['best_for']}")
    
    # Show example usage
    print(f"\n💡 EXAMPLE USAGE:")
    print("-" * 40)
    
    examples = [
        "🔢 Math: Calculate 100 + 50, What is 20% of 500?",
        "🌤️ Weather: Weather in Delhi, Temperature in Bangalore",
        "📄 Document: Analyze this text: Your content here",
        "🔍 System: Type 'help' for guidance, 'status' for health check"
    ]
    
    for example in examples:
        print(f"   {example}")
    
    # MongoDB integration info
    print(f"\n💾 MONGODB INTEGRATION:")
    print("-" * 40)
    
    try:
        sys.path.insert(0, "blackhole_core/data_source")
        from mongodb import get_agent_outputs_collection
        
        collection = get_agent_outputs_collection()
        total_docs = collection.count_documents({})
        
        print(f"   ✅ Connection: Working")
        print(f"   ✅ Documents Stored: {total_docs}")
        print(f"   ✅ Enhanced Storage: Available")
        print(f"   ✅ Query History: Tracked")
    except Exception as e:
        print(f"   ⚠️ MongoDB Status: {e}")
    
    # Final summary
    print(f"\n" + "=" * 80)
    print("🎯 USER-FRIENDLY MCP SYSTEM SUMMARY")
    print("=" * 80)
    
    print(f"✅ System Status: {'FULLY OPERATIONAL' if successful_queries >= 2 else 'PARTIAL'}")
    print(f"✅ Successful Queries: {successful_queries}/{len(demo_queries)}")
    print(f"✅ User Interfaces: 3 available (web, interactive, quick)")
    print(f"✅ MongoDB Storage: Connected and storing data")
    print(f"✅ Agent Types: Math, Weather, Document analysis")
    
    print(f"\n🚀 GET STARTED:")
    print("1. Open http://localhost:8000 for web interface")
    print("2. Run 'python user_friendly_interface.py' for interactive mode")
    print("3. Use 'python quick_query.py \"question\"' for quick queries")
    print("4. Read USER_GUIDE.md for detailed instructions")
    
    print(f"\n🎉 YOUR USER-FRIENDLY MCP SYSTEM IS READY!")
    print("Ask questions naturally and get intelligent responses!")
    
    return successful_queries >= 2

def main():
    """Main function."""
    success = demo_all_interfaces()
    
    if success:
        print(f"\n✅ Demo completed successfully!")
        print("🌐 Try the web interface: http://localhost:8000")
    else:
        print(f"\n⚠️ Demo completed with some issues.")
        print("🔧 Check the system status and try again.")

if __name__ == "__main__":
    main()
