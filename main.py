#!/usr/bin/env python3
"""
Simple Main Server - Redirects to Enhanced MCP Server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point that redirects to the enhanced MCP server."""
    print("🔄 Redirecting to Enhanced MCP Server...")
    print("=" * 50)
    
    # Check if enhanced MCP server exists
    mcp_server_path = Path("enhanced_mcp_server.py")
    start_server_path = Path("start_mcp_server.py")
    
    if start_server_path.exists():
        print("✅ Found start_mcp_server.py - Using MCP startup script")
        print("🚀 Starting Enhanced MCP Server...")
        
        # Run the MCP server startup script
        try:
            subprocess.run([sys.executable, "start_mcp_server.py"], check=True)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            
    elif mcp_server_path.exists():
        print("✅ Found enhanced_mcp_server.py - Using direct MCP server")
        print("🚀 Starting Enhanced MCP Server...")
        
        # Run the MCP server directly
        try:
            subprocess.run([sys.executable, "enhanced_mcp_server.py"], check=True)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            
    else:
        print("❌ Enhanced MCP Server not found!")
        print("🔧 Please make sure enhanced_mcp_server.py exists")
        print("💡 Or use: python start_mcp_server.py")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
