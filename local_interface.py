#!/usr/bin/env python3
"""
Complete Local Interface for MCP System
Unified interface to run your entire MCP ecosystem locally
"""

import asyncio
import sys
import os
import subprocess
import webbrowser
import time
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MCPLocalInterface:
    """Complete local interface for MCP system."""
    
    def __init__(self):
        self.server_url = "http://localhost:8000"
        self.server_process = None
        self.server_running = False
        
    def print_header(self):
        """Print interface header."""
        print("🌐 MCP SYSTEM - COMPLETE LOCAL INTERFACE")
        print("=" * 60)
        print("🎯 Your Enhanced Model Context Protocol Ecosystem")
        print("📁 Modular agents with auto-discovery")
        print("🤖 Multiple client interfaces")
        print("📧 Gmail integration ready")
        print("=" * 60)
    
    def check_server_status(self):
        """Check if MCP server is running."""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                return health_data.get('status') == 'ok'
        except:
            pass
        return False
    
    def start_server(self):
        """Start the MCP server."""
        if self.check_server_status():
            print("✅ MCP Server already running!")
            self.server_running = True
            return True
        
        print("🚀 Starting MCP Server...")
        
        # Check for server files
        start_server_path = Path("start_mcp_server.py")
        mcp_server_path = Path("enhanced_mcp_server.py")
        
        if start_server_path.exists():
            print("   Using start_mcp_server.py")
            try:
                self.server_process = subprocess.Popen(
                    [sys.executable, "start_mcp_server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait a moment for server to start
                time.sleep(3)
                
                if self.check_server_status():
                    print("✅ MCP Server started successfully!")
                    self.server_running = True
                    return True
                else:
                    print("⚠️ Server started but not responding yet...")
                    self.server_running = True
                    return True
                    
            except Exception as e:
                print(f"❌ Error starting server: {e}")
                return False
                
        elif mcp_server_path.exists():
            print("   Using enhanced_mcp_server.py")
            try:
                self.server_process = subprocess.Popen(
                    [sys.executable, "enhanced_mcp_server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                time.sleep(3)
                
                if self.check_server_status():
                    print("✅ MCP Server started successfully!")
                    self.server_running = True
                    return True
                else:
                    print("⚠️ Server started but not responding yet...")
                    self.server_running = True
                    return True
                    
            except Exception as e:
                print(f"❌ Error starting server: {e}")
                return False
        else:
            print("❌ MCP Server files not found!")
            return False
    
    def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            print("🛑 Stopping MCP Server...")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_running = False
            print("✅ MCP Server stopped")
    
    def open_web_interface(self):
        """Open web interface in browser."""
        if not self.server_running:
            print("❌ Server not running. Please start server first.")
            return
        
        print("🌐 Opening Web Interface...")
        
        # Try to open main server interface
        try:
            webbrowser.open(f"{self.server_url}")
            print(f"✅ Opened: {self.server_url}")
        except Exception as e:
            print(f"⚠️ Could not open browser: {e}")
            print(f"   Please manually open: {self.server_url}")
        
        # Also mention client interface
        client_path = Path("mcp_client/web_client.html")
        if client_path.exists():
            try:
                client_url = f"file:///{client_path.absolute()}"
                print(f"🤖 Client Interface: {client_url}")
                webbrowser.open(client_url)
            except Exception as e:
                print(f"   Client interface available at: {client_path}")
    
    def run_cli_client(self):
        """Run CLI client."""
        if not self.server_running:
            print("❌ Server not running. Please start server first.")
            return
        
        print("💻 Starting CLI Client...")
        cli_path = Path("mcp_client/cli_client.py")
        
        if cli_path.exists():
            try:
                subprocess.run([sys.executable, str(cli_path), "interactive"], check=True)
            except KeyboardInterrupt:
                print("\n✅ CLI Client closed")
            except Exception as e:
                print(f"❌ Error running CLI client: {e}")
        else:
            print("❌ CLI client not found")
    
    def run_interactive_client(self):
        """Run interactive Python client."""
        if not self.server_running:
            print("❌ Server not running. Please start server first.")
            return
        
        print("🐍 Starting Interactive Python Client...")
        client_script = Path("start_mcp_client.py")
        
        if client_script.exists():
            try:
                subprocess.run([sys.executable, str(client_script)], check=True)
            except KeyboardInterrupt:
                print("\n✅ Interactive client closed")
            except Exception as e:
                print(f"❌ Error running interactive client: {e}")
        else:
            print("❌ Interactive client not found")
    
    def run_system_test(self):
        """Run comprehensive system test."""
        print("🧪 Running System Test...")
        test_script = Path("test_mcp_system.py")
        
        if test_script.exists():
            try:
                subprocess.run([sys.executable, str(test_script)], check=True)
            except KeyboardInterrupt:
                print("\n🛑 Test cancelled")
            except Exception as e:
                print(f"❌ Error running test: {e}")
        else:
            print("❌ Test script not found")
    
    def show_system_status(self):
        """Show current system status."""
        print("\n📊 SYSTEM STATUS")
        print("-" * 40)
        
        # Server status
        server_status = self.check_server_status()
        print(f"🖥️ MCP Server: {'✅ Running' if server_status else '❌ Stopped'}")
        
        if server_status:
            try:
                response = requests.get(f"{self.server_url}/api/mcp/agents", timeout=5)
                if response.status_code == 200:
                    agents_data = response.json()
                    total_agents = agents_data.get('total_agents', 0)
                    print(f"🤖 Agents Loaded: {total_agents}")
                    
                    if 'agents' in agents_data:
                        for agent_id, agent_info in agents_data['agents'].items():
                            print(f"   • {agent_id}: {agent_info.get('name', 'Unknown')}")
                else:
                    print("🤖 Agents: Unable to fetch")
            except:
                print("🤖 Agents: Unable to connect")
        
        # File status
        files_to_check = [
            ("enhanced_mcp_server.py", "🖥️ MCP Server"),
            ("start_mcp_server.py", "🚀 Server Startup"),
            ("mcp_client/web_client.html", "🌐 Web Client"),
            ("mcp_client/cli_client.py", "💻 CLI Client"),
            ("start_mcp_client.py", "🐍 Interactive Client"),
            ("test_mcp_system.py", "🧪 System Test")
        ]
        
        print("\n📁 Files Status:")
        for file_path, description in files_to_check:
            exists = Path(file_path).exists()
            status = "✅" if exists else "❌"
            print(f"   {status} {description}")
    
    def show_menu(self):
        """Show main menu."""
        print("\n🎯 MAIN MENU")
        print("-" * 30)
        print("1. 🚀 Start MCP Server")
        print("2. 🌐 Open Web Interface")
        print("3. 💻 Run CLI Client")
        print("4. 🐍 Run Interactive Client")
        print("5. 🧪 Run System Test")
        print("6. 📊 Show System Status")
        print("7. 🛑 Stop Server")
        print("8. ❌ Exit")
        print("-" * 30)
    
    def run(self):
        """Run the complete local interface."""
        self.print_header()
        
        try:
            while True:
                self.show_menu()
                choice = input("\n🎯 Choose an option (1-8): ").strip()
                
                if choice == "1":
                    self.start_server()
                elif choice == "2":
                    self.open_web_interface()
                elif choice == "3":
                    self.run_cli_client()
                elif choice == "4":
                    self.run_interactive_client()
                elif choice == "5":
                    self.run_system_test()
                elif choice == "6":
                    self.show_system_status()
                elif choice == "7":
                    self.stop_server()
                elif choice == "8":
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                
                input("\n⏸️ Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n🛑 Interface interrupted by user")
        finally:
            if self.server_running:
                self.stop_server()

def main():
    """Main entry point."""
    interface = MCPLocalInterface()
    interface.run()

if __name__ == "__main__":
    main()
