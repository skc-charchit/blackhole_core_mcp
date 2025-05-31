#!/usr/bin/env python3
"""
Quick Query Tool
Simple command-line tool for single queries
"""

import requests
import sys
from datetime import datetime

def quick_query(query):
    """Send a quick query and display results."""
    print("🚀 MCP QUICK QUERY")
    print("=" * 50)
    print(f"📤 Query: {query}")
    print("=" * 50)
    
    try:
        # Check if server is running
        health_response = requests.get("http://localhost:8000/api/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server not running!")
            print("💡 Start server: python production_mcp_server.py")
            return False
        
        health = health_response.json()
        print(f"✅ Server: Ready")
        print(f"✅ MongoDB: {'Connected' if health.get('mongodb_connected') else 'Disconnected'}")
        print(f"✅ Agents: {health.get('system', {}).get('loaded_agents', 0)} loaded")
        print()
        
        # Send query
        print("⏳ Processing...")
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": query},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("📊 RESULT:")
            print("-" * 30)
            print(f"🤖 Agent: {result.get('agent_used', 'Unknown')}")
            print(f"✅ Status: {result.get('status', 'Unknown').upper()}")
            
            if result.get('status') == 'success':
                # Math results
                if 'result' in result:
                    print(f"🔢 Answer: {result['result']}")
                
                # Weather results
                elif 'city' in result and 'weather_data' in result:
                    weather = result['weather_data']
                    print(f"🌍 Location: {result['city']}, {result.get('country', '')}")
                    print(f"🌡️ Temperature: {weather.get('temperature', 'N/A')}°C")
                    print(f"☁️ Conditions: {weather.get('description', 'N/A')}")
                    print(f"💧 Humidity: {weather.get('humidity', 'N/A')}%")
                    print(f"💨 Wind: {weather.get('wind_speed', 'N/A')} m/s")
                
                # Document results
                elif 'total_documents' in result:
                    print(f"📄 Documents: {result['total_documents']} processed")
                    if result.get('authors_found'):
                        print(f"👤 Authors: {', '.join(result['authors_found'])}")
                
                # General message
                elif 'message' in result:
                    print(f"💬 Message: {result['message']}")
            
            else:
                print(f"❌ Error: {result.get('message', 'Unknown error')}")
            
            print(f"💾 MongoDB: {'✅ Stored' if result.get('stored_in_mongodb') else '❌ Not Stored'}")
            print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
            
            return True
        else:
            print(f"❌ Server error: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("💡 Start server: python production_mcp_server.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("🚀 MCP QUICK QUERY TOOL")
        print("=" * 50)
        print("Usage: python quick_query.py \"Your question here\"")
        print()
        print("Examples:")
        print("  python quick_query.py \"Calculate 25 * 4\"")
        print("  python quick_query.py \"What is the weather in Mumbai?\"")
        print("  python quick_query.py \"Analyze this text: Hello world\"")
        print()
        print("💡 For interactive mode: python user_friendly_interface.py")
        print("🌐 For web interface: http://localhost:8000")
        return
    
    query = " ".join(sys.argv[1:])
    success = quick_query(query)
    
    if success:
        print("\n✅ Query completed successfully!")
    else:
        print("\n❌ Query failed!")

if __name__ == "__main__":
    main()
