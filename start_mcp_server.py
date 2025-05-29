#!/usr/bin/env python3
"""
Start MCP Server - Proper startup script for your modular MCP server
"""

import uvicorn
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start the Enhanced MCP Server with proper agent loading."""
    print("🚀 Starting Enhanced MCP Server with Modular Agent System")
    print("🎯 True Model Context Protocol with Auto-Discovery")
    print("🤖 Drop agents in folders and they auto-connect!")
    print("📁 Folder structure:")
    print("   agents/core/        - Core agents")
    print("   agents/specialized/ - Specialized agents")
    print("   agents/custom/      - Your custom agents")
    print("   agents/templates/   - Agent templates")
    print("=" * 60)
    
    try:
        # Import and run the enhanced MCP server
        from enhanced_mcp_server import app
        
        # Test agent discovery
        print("\n🔍 Testing Agent Discovery...")
        try:
            from agents import discover_agents
            discovered = discover_agents()
            print(f"✅ Discovered {len(discovered)} agents:")
            for agent_id, info in discovered.items():
                print(f"   • {agent_id}: {info['name']} ({info['category']})")
        except Exception as e:
            print(f"⚠️ Agent discovery issue: {e}")
        
        print("\n🌐 Starting FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Make sure all required files are present:")
        print("   - enhanced_mcp_server.py")
        print("   - agents/__init__.py")
        print("   - agents/base_agent.py")
        print("   - agents/agent_loader.py")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("🔧 Check the error details above and try again.")

if __name__ == "__main__":
    main()
