#!/usr/bin/env python3
"""
User-Friendly MCP Interface
Easy-to-use interface for querying agents and checking outputs
"""

import requests
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))

class UserFriendlyMCP:
    """User-friendly interface for MCP system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session_history = []
        
    def check_system_status(self):
        """Check if the system is ready."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                return {
                    "ready": health.get('ready', False),
                    "mongodb_connected": health.get('mongodb_connected', False),
                    "agents_loaded": health.get('system', {}).get('loaded_agents', 0)
                }
            return {"ready": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"ready": False, "error": str(e)}
    
    def send_query(self, query):
        """Send a query to the MCP system."""
        try:
            response = requests.post(
                f"{self.base_url}/api/mcp/command",
                json={"command": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Store in session history
                self.session_history.append({
                    "timestamp": datetime.now(),
                    "query": query,
                    "result": result
                })
                
                return result
            else:
                return {
                    "status": "error",
                    "message": f"Server error: HTTP {response.status_code}",
                    "query": query
                }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Connection error: {str(e)}",
                "query": query
            }
    
    def format_output(self, result):
        """Format the output in a user-friendly way."""
        query = result.get('query', 'Unknown query')
        status = result.get('status', 'unknown')
        
        print(f"\n{'='*60}")
        print(f"📤 QUERY: {query}")
        print(f"{'='*60}")
        
        if status == "success":
            agent_used = result.get('agent_used', 'unknown')
            print(f"🤖 AGENT: {agent_used}")
            print(f"✅ STATUS: {status.upper()}")
            
            # Format different types of results
            if 'result' in result:
                # Math results
                math_result = result['result']
                if isinstance(math_result, (int, float)):
                    print(f"🔢 ANSWER: {math_result}")
                else:
                    print(f"📊 RESULT: {math_result}")
            
            elif 'city' in result and 'weather_data' in result:
                # Weather results
                weather = result['weather_data']
                city = result['city']
                country = result.get('country', '')
                
                print(f"🌍 LOCATION: {city}, {country}")
                print(f"🌡️ TEMPERATURE: {weather.get('temperature', 'N/A')}°C")
                print(f"☁️ CONDITIONS: {weather.get('description', 'N/A').title()}")
                print(f"💧 HUMIDITY: {weather.get('humidity', 'N/A')}%")
                print(f"💨 WIND: {weather.get('wind_speed', 'N/A')} m/s")
            
            elif 'processed_documents' in result:
                # Document results
                docs = result['processed_documents']
                total_docs = result.get('total_documents', 0)
                authors = result.get('authors_found', [])
                
                print(f"📄 DOCUMENTS PROCESSED: {total_docs}")
                if authors:
                    print(f"👤 AUTHORS FOUND: {', '.join(authors)}")
                
                for i, doc in enumerate(docs[:3], 1):  # Show first 3 docs
                    analysis = doc.get('analysis', {})
                    word_count = analysis.get('word_count', 0)
                    content_type = analysis.get('content_type', 'unknown')
                    print(f"   📋 Document {i}: {word_count} words ({content_type})")
            
            elif 'message' in result:
                # General message results
                print(f"💬 MESSAGE: {result['message']}")
            
            # MongoDB storage info
            stored = result.get('stored_in_mongodb', False)
            mongodb_id = result.get('mongodb_id')
            
            print(f"💾 MONGODB STORED: {'✅ Yes' if stored else '❌ No'}")
            if mongodb_id:
                print(f"🆔 STORAGE ID: {mongodb_id}")
        
        else:
            # Error results
            print(f"❌ STATUS: {status.upper()}")
            error_msg = result.get('message', 'Unknown error')
            print(f"🚨 ERROR: {error_msg}")
            
            # Show available agents if no agents found
            if 'available_agents' in result:
                agents = result['available_agents']
                print(f"🤖 AVAILABLE AGENTS: {', '.join(agents)}")
        
        print(f"🕐 TIME: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
    
    def show_help(self):
        """Show help information."""
        print(f"\n{'='*60}")
        print("📚 MCP SYSTEM - USER GUIDE")
        print(f"{'='*60}")
        
        print("\n🎯 WHAT YOU CAN ASK:")
        print("🔢 MATH CALCULATIONS:")
        print("   • Calculate 25 * 4")
        print("   • What is 100 + 50?")
        print("   • Compute 20% of 500")
        print("   • Solve 15 + 25 * 2")
        
        print("\n🌤️ WEATHER QUERIES:")
        print("   • What is the weather in Mumbai?")
        print("   • Mumbai weather")
        print("   • Temperature in Delhi")
        print("   • Weather forecast for Bangalore")
        
        print("\n📄 DOCUMENT ANALYSIS:")
        print("   • Analyze this text: Your text here")
        print("   • Process document content")
        print("   • Extract information from text")
        
        print("\n💡 TIPS:")
        print("   • Be specific in your queries")
        print("   • Use natural language")
        print("   • Check 'history' to see past queries")
        print("   • Type 'status' to check system health")
        print("   • Type 'help' to see this guide")
        print("   • Type 'quit' or 'exit' to leave")
        
        print(f"\n🌐 WEB INTERFACE: {self.base_url}")
        print(f"{'='*60}")
    
    def show_history(self):
        """Show session history."""
        if not self.session_history:
            print("\n📝 No queries in this session yet.")
            return
        
        print(f"\n{'='*60}")
        print("📝 SESSION HISTORY")
        print(f"{'='*60}")
        
        for i, entry in enumerate(self.session_history[-10:], 1):  # Last 10 queries
            timestamp = entry['timestamp'].strftime('%H:%M:%S')
            query = entry['query']
            result = entry['result']
            status = result.get('status', 'unknown')
            
            status_icon = "✅" if status == "success" else "❌"
            print(f"{i:2d}. [{timestamp}] {status_icon} {query}")
            
            if status == "success":
                agent = result.get('agent_used', 'unknown')
                print(f"     🤖 {agent}")
        
        print(f"{'='*60}")
    
    def show_status(self):
        """Show system status."""
        print(f"\n{'='*60}")
        print("📊 SYSTEM STATUS")
        print(f"{'='*60}")
        
        status = self.check_system_status()
        
        if status.get('ready'):
            print("✅ SYSTEM: Ready and operational")
            print(f"✅ MONGODB: {'Connected' if status.get('mongodb_connected') else 'Disconnected'}")
            print(f"✅ AGENTS: {status.get('agents_loaded', 0)} loaded")
            
            # Get agent details
            try:
                response = requests.get(f"{self.base_url}/api/agents", timeout=5)
                if response.status_code == 200:
                    agents_data = response.json()
                    agents = agents_data.get('agents', {})
                    
                    print(f"\n🤖 AGENT DETAILS:")
                    for agent_id, agent_info in agents.items():
                        agent_status = agent_info.get('status', 'unknown')
                        status_icon = "✅" if agent_status == "loaded" else "⚠️"
                        print(f"   {status_icon} {agent_id}: {agent_status}")
            except:
                pass
        else:
            print("❌ SYSTEM: Not ready")
            error = status.get('error', 'Unknown error')
            print(f"🚨 ERROR: {error}")
            print("\n💡 SOLUTION:")
            print("   Run: python production_mcp_server.py")
        
        print(f"🌐 WEB INTERFACE: {self.base_url}")
        print(f"{'='*60}")
    
    def interactive_mode(self):
        """Run interactive mode."""
        print("🚀 MCP SYSTEM - INTERACTIVE MODE")
        print("=" * 60)
        print("Welcome to the MCP Agent System!")
        print("Type your queries naturally and get instant responses.")
        print("Type 'help' for guidance, 'quit' to exit.")
        print("=" * 60)
        
        # Check system status
        status = self.check_system_status()
        if not status.get('ready'):
            print("❌ SYSTEM NOT READY!")
            print(f"Error: {status.get('error', 'Unknown error')}")
            print("\n💡 Please start the server first:")
            print("   python production_mcp_server.py")
            return
        
        print(f"✅ System ready with {status.get('agents_loaded', 0)} agents")
        print(f"✅ MongoDB: {'Connected' if status.get('mongodb_connected') else 'Disconnected'}")
        
        while True:
            try:
                print(f"\n{'─'*60}")
                query = input("🎯 Your Query: ").strip()
                
                if not query:
                    continue
                
                # Handle special commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Thanks for using MCP System!")
                    break
                elif query.lower() in ['help', 'h']:
                    self.show_help()
                    continue
                elif query.lower() in ['history', 'hist']:
                    self.show_history()
                    continue
                elif query.lower() in ['status', 'stat']:
                    self.show_status()
                    continue
                elif query.lower() in ['clear', 'cls']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                
                # Process the query
                print("⏳ Processing your query...")
                result = self.send_query(query)
                self.format_output(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using MCP System!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def single_query_mode(self, query):
        """Process a single query."""
        print("🚀 MCP SYSTEM - SINGLE QUERY MODE")
        print("=" * 60)
        
        # Check system status
        status = self.check_system_status()
        if not status.get('ready'):
            print("❌ SYSTEM NOT READY!")
            print(f"Error: {status.get('error', 'Unknown error')}")
            return False
        
        print("⏳ Processing your query...")
        result = self.send_query(query)
        self.format_output(result)
        return True

def main():
    """Main function."""
    interface = UserFriendlyMCP()
    
    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        interface.single_query_mode(query)
    else:
        # Interactive mode
        interface.interactive_mode()

if __name__ == "__main__":
    main()
