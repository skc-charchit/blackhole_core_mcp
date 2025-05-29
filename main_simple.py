#!/usr/bin/env python3
"""
Main Server Entry Point - Redirects to Enhanced MCP Server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point that redirects to the enhanced MCP server."""
    print("🔄 Main.py → Enhanced MCP Server")
    print("=" * 50)
    print("🎯 Your project now uses the Enhanced MCP Server system")
    print("📁 Agents are auto-discovered from folders")
    print("🤖 Multiple client interfaces available")
    print("=" * 50)

    # Check if enhanced MCP server exists
    start_server_path = Path("start_mcp_server.py")
    mcp_server_path = Path("enhanced_mcp_server.py")

    if start_server_path.exists():
        print("✅ Found start_mcp_server.py - Using MCP startup script")
        print("🚀 Starting Enhanced MCP Server...")
        print("")

        # Run the MCP server startup script
        try:
            subprocess.run([sys.executable, "start_mcp_server.py"], check=True)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            print("💡 Try running directly: python start_mcp_server.py")

    elif mcp_server_path.exists():
        print("✅ Found enhanced_mcp_server.py - Using direct MCP server")
        print("🚀 Starting Enhanced MCP Server...")
        print("")

        # Run the MCP server directly
        try:
            subprocess.run([sys.executable, "enhanced_mcp_server.py"], check=True)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            print("💡 Try running directly: python enhanced_mcp_server.py")

    else:
        print("❌ Enhanced MCP Server not found!")
        print("")
        print("🔧 Available options:")
        print("   1. python start_mcp_server.py    # Recommended")
        print("   2. python enhanced_mcp_server.py  # Direct server")
        print("")
        print("📁 Your MCP system structure:")
        print("   • enhanced_mcp_server.py  → Main MCP server")
        print("   • start_mcp_server.py     → Server startup script")
        print("   • agents/                 → Auto-discovered agents")
        print("   • mcp_client/             → Client interfaces")
        print("")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
