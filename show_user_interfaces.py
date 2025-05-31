#!/usr/bin/env python3
"""
Show User Interfaces
Demonstrate where users can ask queries
"""

import webbrowser
import time
import requests
from datetime import datetime

def show_all_interfaces():
    """Show all user interfaces and where to ask queries."""
    print("🎯 WHERE USERS CAN ASK QUERIES")
    print("=" * 80)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        server_running = response.status_code == 200
    except:
        server_running = False
    
    if not server_running:
        print("❌ SERVER NOT RUNNING!")
        print("💡 Please start: python production_mcp_server.py")
        print("=" * 80)
        return False
    
    print("✅ SERVER IS RUNNING - All interfaces available!")
    print("=" * 80)
    
    # Interface 1: Web Interface
    print("\n🌐 INTERFACE 1: WEB INTERFACE (RECOMMENDED)")
    print("-" * 60)
    print("📍 WHERE: http://localhost:8000")
    print("🎯 USER INPUT LOCATION:")
    print("   ┌─────────────────────────────────────────────────────┐")
    print("   │  💬 Ask Your Question                               │")
    print("   │  ┌─────────────────────────────────────────────────┐ │")
    print("   │  │ Type your question here... ← USER TYPES HERE   │ │")
    print("   │  └─────────────────────────────────────────────────┘ │")
    print("   │  [🚀 Send Query] [🗑️ Clear] [📝 History]            │")
    print("   └─────────────────────────────────────────────────────┘")
    print("💡 FEATURES:")
    print("   • Large input text box")
    print("   • Click-to-fill example queries")
    print("   • Real-time status monitoring")
    print("   • Formatted response display")
    print("   • Query history tracking")
    print("   • Mobile-friendly design")
    
    # Interface 2: Interactive Command Line
    print("\n💻 INTERFACE 2: INTERACTIVE COMMAND LINE")
    print("-" * 60)
    print("📍 WHERE: python user_friendly_interface.py")
    print("🎯 USER INPUT LOCATION:")
    print("   ────────────────────────────────────────────────────────")
    print("   🎯 Your Query: [USER TYPES HERE] ← USER INPUT PROMPT")
    print("   ────────────────────────────────────────────────────────")
    print("💡 FEATURES:")
    print("   • Natural conversation interface")
    print("   • Help system (type 'help')")
    print("   • Status monitoring (type 'status')")
    print("   • Query history (type 'history')")
    print("   • Special commands available")
    
    # Interface 3: Quick Query Tool
    print("\n⚡ INTERFACE 3: QUICK QUERY TOOL")
    print("-" * 60)
    print("📍 WHERE: python quick_query.py \"Your question\"")
    print("🎯 USER INPUT LOCATION:")
    print("   python quick_query.py \"USER TYPES QUESTION HERE\"")
    print("                          ↑")
    print("                    QUESTION IN QUOTES")
    print("💡 FEATURES:")
    print("   • One-shot queries")
    print("   • Perfect for automation")
    print("   • Instant formatted results")
    print("   • Command-line friendly")
    
    # Interface 4: API Endpoint
    print("\n🔌 INTERFACE 4: API ENDPOINT (FOR DEVELOPERS)")
    print("-" * 60)
    print("📍 WHERE: POST http://localhost:8000/api/mcp/command")
    print("🎯 USER INPUT LOCATION:")
    print("   JSON Body: {\"command\": \"USER QUESTION HERE\"}")
    print("                         ↑")
    print("                   QUESTION IN JSON")
    print("💡 FEATURES:")
    print("   • Direct API access")
    print("   • Integration-friendly")
    print("   • JSON request/response")
    print("   • Programmatic access")
    
    # Example queries
    print("\n💬 EXAMPLE QUERIES USERS CAN ASK:")
    print("-" * 60)
    
    examples = [
        ("🔢 Math", "Calculate 25 * 4"),
        ("🔢 Math", "What is 20% of 500?"),
        ("🌤️ Weather", "What is the weather in Mumbai?"),
        ("🌤️ Weather", "Temperature in Delhi"),
        ("📄 Document", "Analyze this text: Hello world"),
        ("📄 Document", "Process this content: Sample text here")
    ]
    
    for category, query in examples:
        print(f"   {category}: \"{query}\"")
    
    # Live demonstration
    print(f"\n🧪 LIVE DEMONSTRATION:")
    print("-" * 60)
    
    test_queries = [
        "Calculate 10 + 15",
        "What is the weather in Mumbai?",
        "Analyze this text: User interface demonstration"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: \"{query}\"")
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": query},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                agent = result.get('agent_used')
                
                print(f"   ✅ Status: {status}")
                print(f"   🤖 Agent: {agent}")
                
                if 'result' in result:
                    print(f"   🔢 Answer: {result['result']}")
                elif 'city' in result:
                    print(f"   🌍 Location: {result['city']}")
                elif 'total_documents' in result:
                    print(f"   📄 Documents: {result['total_documents']} processed")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)
    
    # Open web interface
    print(f"\n🌐 OPENING WEB INTERFACE...")
    print("-" * 60)
    print("Opening http://localhost:8000 in your browser...")
    print("You can now see the main user interface!")
    
    try:
        webbrowser.open("http://localhost:8000")
        print("✅ Web interface opened successfully!")
    except:
        print("⚠️ Could not auto-open browser")
        print("💡 Manually open: http://localhost:8000")
    
    # Final summary
    print(f"\n" + "=" * 80)
    print("🎯 SUMMARY: WHERE USERS ASK QUERIES")
    print("=" * 80)
    
    print("✅ PRIMARY USER INPUT LOCATIONS:")
    print("1. 🌐 Web Interface Input Box - http://localhost:8000")
    print("   • Main text input field (most user-friendly)")
    print("   • Click-to-fill example buttons")
    print("   • Enter key or Send button to submit")
    
    print("\n2. 💻 Interactive Terminal Prompt")
    print("   • Run: python user_friendly_interface.py")
    print("   • Type at 'Your Query:' prompt")
    print("   • Press Enter to submit")
    
    print("\n3. ⚡ Command Line Arguments")
    print("   • Run: python quick_query.py \"Your question\"")
    print("   • Question in quotes after script name")
    
    print("\n4. 🔌 API Endpoint")
    print("   • POST to: http://localhost:8000/api/mcp/command")
    print("   • JSON body: {\"command\": \"Your question\"}")
    
    print(f"\n🎉 USERS HAVE 4 CONVENIENT WAYS TO ASK QUESTIONS!")
    print("The web interface is the most user-friendly option.")
    print("=" * 80)
    
    return True

def main():
    """Main function."""
    success = show_all_interfaces()
    
    if success:
        print("\n✅ All user interfaces demonstrated successfully!")
        print("🌐 Users can now easily ask questions through multiple channels!")
    else:
        print("\n❌ Please start the server first:")
        print("   python production_mcp_server.py")

if __name__ == "__main__":
    main()
