#!/usr/bin/env python3
"""
MCP System Launcher - Quick start for your MCP ecosystem
"""

import asyncio
import sys
import os
import subprocess
import webbrowser
import time
import requests
from pathlib import Path

def quick_start():
    """Quick start the entire MCP system."""
    print("🚀 MCP SYSTEM QUICK LAUNCHER")
    print("=" * 50)
    print("🎯 Starting your complete MCP ecosystem...")
    print("")
    
    # Start server
    print("1️⃣ Starting MCP Server...")
    server_process = None
    
    try:
        if Path("start_mcp_server.py").exists():
            server_process = subprocess.Popen(
                [sys.executable, "start_mcp_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        elif Path("enhanced_mcp_server.py").exists():
            server_process = subprocess.Popen(
                [sys.executable, "enhanced_mcp_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            print("❌ MCP Server not found!")
            return
        
        print("   ⏳ Waiting for server to start...")
        time.sleep(5)
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ MCP Server running!")
            else:
                print("   ⚠️ Server started but not fully ready")
        except:
            print("   ⚠️ Server starting (may take a moment)")
        
        # Open web interfaces
        print("\n2️⃣ Opening Web Interfaces...")
        
        # Main server interface
        try:
            webbrowser.open("http://localhost:8000")
            print("   ✅ Main Interface: http://localhost:8000")
        except:
            print("   ⚠️ Could not open main interface")
        
        # Client interface
        client_path = Path("mcp_client/web_client.html")
        if client_path.exists():
            try:
                client_url = f"file:///{client_path.absolute()}"
                webbrowser.open(client_url)
                print("   ✅ Client Interface opened")
            except:
                print("   ⚠️ Could not open client interface")
        
        print("\n3️⃣ System Ready!")
        print("=" * 50)
        print("🌐 Web Interfaces:")
        print("   • Main Server: http://localhost:8000")
        print("   • API Docs: http://localhost:8000/docs")
        print("   • Client Interface: mcp_client/web_client.html")
        print("")
        print("💻 Command Line:")
        print("   • CLI Client: python mcp_client/cli_client.py")
        print("   • Interactive: python start_mcp_client.py")
        print("   • Test System: python test_mcp_system.py")
        print("")
        print("📁 Agents:")
        print("   • Drop agents in: agents/custom/")
        print("   • Templates in: agents/templates/")
        print("")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping MCP Server...")
            if server_process:
                server_process.terminate()
                server_process.wait()
            print("✅ MCP System stopped")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if server_process:
            server_process.terminate()

if __name__ == "__main__":
    quick_start()
