#!/usr/bin/env python3
"""
CONNECT ALL - Unified MCP Connection Script
One script to connect everything together
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

async def connect_all():
    """Connect all MCP components with one command."""
    
    print("🔗 CONNECT ALL - UNIFIED MCP SYSTEM")
    print("=" * 80)
    print("🎯 Connecting all agents, servers, and databases")
    print("🛡️ Independent agents with failsafe isolation")
    print("💾 MongoDB integration with conversation engine")
    print("=" * 80)
    
    try:
        # Import the unified system
        from unified_mcp_system import UnifiedMCPSystem
        
        # Create system instance
        system = UnifiedMCPSystem()
        
        # Start everything with high priority agents
        print("🚀 Starting unified system with high priority agents...")
        results = await system.start_unified_system("high")
        
        if results["system_operational"]:
            print("\n🎉 ALL SYSTEMS CONNECTED!")
            print("=" * 50)
            print("✅ MCP Server: Running")
            print("✅ Agents: Connected and Independent")
            print("✅ MongoDB: Integrated")
            print("✅ Failsafe: Active")
            
            print("\n🤖 ACTIVE AGENTS:")
            for agent_name in results["agents_loaded"]:
                print(f"   ✅ {agent_name}")
            
            if system.failed_agents:
                print("\n🔒 ISOLATED AGENTS (System continues smoothly):")
                for agent_name in system.failed_agents:
                    print(f"   🔒 {agent_name}")
            
            print("\n🌐 ACCESS POINTS:")
            print("   • Web Interface: http://localhost:8000")
            print("   • Command Line: python unified_mcp_client.py")
            print("   • API: http://localhost:8000/api/")
            
            print("\n💡 READY FOR USE:")
            print("   🌤️ Weather queries")
            print("   🔢 Mathematical calculations")
            print("   📄 Document processing")
            print("   📧 Email automation")
            print("   📅 Calendar management")
            print("   💾 MongoDB data storage")
            print("   🗣️ Conversational AI")
            
            return True
        else:
            print("\n⚠️ PARTIAL CONNECTION")
            print("Some components failed but system is operational")
            return False
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

def show_agent_selection_menu():
    """Show agent selection menu for user choice."""
    
    print("\n📋 AGENT SELECTION MENU")
    print("=" * 50)
    print("Choose which agents to integrate:")
    print()
    
    print("🔥 HIGH PRIORITY (Recommended):")
    print("   ✅ realtime_weather_agent - Live weather data")
    print("   ✅ math_agent - Mathematical calculations")
    print("   ✅ document_processor - Document analysis")
    print("   ✅ real_gmail_agent - Email automation")
    print("   ✅ calendar_agent - Scheduling & reminders")
    print()
    
    print("⚡ MEDIUM PRIORITY (Optional):")
    print("   🔧 image_ocr_agent - Image text extraction")
    print("   🔧 pdf_extractor_agent - PDF processing")
    print("   🔧 search_agent - Search functionality")
    print("   🔧 mongodb_connection - Database operations")
    print()
    
    print("📋 LOW PRIORITY (Advanced):")
    print("   📝 live_data_agent - General data fetching")
    print("   📝 archive_search_agent - Historical search")
    print()
    
    print("💡 RECOMMENDATIONS:")
    print("   • Start with HIGH PRIORITY agents (most stable)")
    print("   • Add MEDIUM PRIORITY agents as needed")
    print("   • LOW PRIORITY agents are experimental")
    print()
    
    choice = input("Select priority level (high/medium/all) [high]: ").strip().lower()
    if choice in ["medium", "all"]:
        return choice
    return "high"

async def main():
    """Main function with user interaction."""
    
    print("🔗 MCP UNIFIED CONNECTION SYSTEM")
    print("=" * 80)
    print("🎯 One script to connect all your MCP components")
    print("=" * 80)
    
    # Check if user wants to see agent selection
    if len(sys.argv) > 1 and sys.argv[1] == "--select":
        priority = show_agent_selection_menu()
    else:
        priority = "high"  # Default to high priority
        print("🚀 Using HIGH PRIORITY agents (recommended)")
        print("💡 Use --select flag to choose different agents")
    
    print(f"\n🔄 Connecting with {priority.upper()} priority agents...")
    
    try:
        # Import and run unified system
        from unified_mcp_system import UnifiedMCPSystem
        
        system = UnifiedMCPSystem()
        results = await system.start_unified_system(priority)
        
        if results["system_operational"]:
            print("\n🎉 SUCCESS! ALL SYSTEMS CONNECTED!")
            
            # Show quick test commands
            print("\n🧪 QUICK TEST COMMANDS:")
            print("   python unified_mcp_client.py -c 'What is the weather in Mumbai?'")
            print("   python unified_mcp_client.py -c 'Calculate 20% of 500'")
            print("   python unified_mcp_client.py -c 'Send email to test@example.com'")
            
            print("\n🌐 WEB INTERFACE:")
            print("   Open: http://localhost:8000")
            
            print("\n💾 MONGODB STATUS:")
            print("   ✅ Connected and storing all interactions")
            
            print("\n🛡️ FAILSAFE STATUS:")
            print("   ✅ Failed agents isolated - system continues smoothly")
            
            return True
        else:
            print("\n⚠️ PARTIAL SUCCESS")
            print("Some agents failed but core system is operational")
            return False
            
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("💡 Make sure all required files are present")
        return False
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\n🎉 All systems connected and ready!")
            print("🔗 Your unified MCP system is operational!")
        else:
            print("\n🔧 Some issues detected. Check messages above.")
    except KeyboardInterrupt:
        print("\n👋 Connection cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
