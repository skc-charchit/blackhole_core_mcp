#!/usr/bin/env python3
"""
Unified MCP Client
Connects to multiple MCP servers and routes commands intelligently
"""

import asyncio
import requests
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

class UnifiedMCPClient:
    """Client that can connect to multiple MCP servers."""
    
    def __init__(self):
        self.servers = {
            "main": "http://localhost:8000",
            "core": "http://localhost:8001", 
            "mongodb": "http://localhost:8003"
        }
        self.primary_server = "main"
        self.fallback_servers = ["core", "mongodb"]
    
    async def check_server_availability(self) -> Dict[str, bool]:
        """Check which servers are available."""
        availability = {}
        
        for server_name, url in self.servers.items():
            try:
                response = requests.get(f"{url}/api/health", timeout=3)
                availability[server_name] = response.status_code == 200
            except:
                availability[server_name] = False
        
        return availability
    
    async def send_command(self, command: str, preferred_server: str = None) -> Dict[str, Any]:
        """Send command to MCP servers with intelligent routing."""
        
        # Determine server priority
        server_priority = [preferred_server] if preferred_server else [self.primary_server]
        server_priority.extend([s for s in self.fallback_servers if s not in server_priority])
        
        # Check availability
        availability = await self.check_server_availability()
        
        # Try servers in priority order
        for server_name in server_priority:
            if server_name in self.servers and availability.get(server_name, False):
                try:
                    url = self.servers[server_name]
                    response = requests.post(
                        f"{url}/api/mcp/command",
                        json={"command": command},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        result["server_used"] = server_name
                        result["server_url"] = url
                        return result
                    
                except Exception as e:
                    print(f"⚠️ Error with {server_name}: {e}")
                    continue
        
        return {
            "status": "error",
            "message": "No available MCP servers",
            "available_servers": availability
        }
    
    async def interactive_mode(self):
        """Interactive command mode."""
        print("🤖 UNIFIED MCP CLIENT - INTERACTIVE MODE")
        print("=" * 60)
        print("💡 Type 'help' for commands, 'quit' to exit")
        print("🔗 Connecting to multiple MCP servers...")
        
        # Check initial availability
        availability = await self.check_server_availability()
        available_count = sum(availability.values())
        
        print(f"📊 Available servers: {available_count}/{len(self.servers)}")
        for server, available in availability.items():
            status = "✅ Online" if available else "❌ Offline"
            print(f"   • {server}: {status}")
        
        if available_count == 0:
            print("❌ No MCP servers available. Please start servers first.")
            return
        
        print("\n🎯 Ready for commands!")
        print("=" * 60)
        
        while True:
            try:
                command = input("\nMCP> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif command.lower() == 'help':
                    self.show_help()
                    continue
                
                elif command.lower() == 'status':
                    await self.show_status()
                    continue
                
                elif command.lower().startswith('server '):
                    server_name = command[7:].strip()
                    if server_name in self.servers:
                        self.primary_server = server_name
                        print(f"🔄 Switched to {server_name} as primary server")
                    else:
                        print(f"❌ Unknown server: {server_name}")
                        print(f"Available: {', '.join(self.servers.keys())}")
                    continue
                
                elif not command:
                    continue
                
                # Send command to servers
                print(f"🔄 Processing: {command}")
                result = await self.send_command(command)
                
                # Display result
                self.display_result(result)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_help(self):
        """Show help information."""
        print("\n📚 UNIFIED MCP CLIENT HELP")
        print("=" * 40)
        print("🤖 Commands:")
        print("   help          - Show this help")
        print("   status        - Show server status")
        print("   server <name> - Switch primary server")
        print("   quit/exit/q   - Exit client")
        print("\n🌤️ Weather Examples:")
        print("   What is the weather in Mumbai?")
        print("   Mumbai weather forecast")
        print("\n🔢 Math Examples:")
        print("   Calculate 20% of 500")
        print("   What is 15 * 25?")
        print("\n📧 Email Examples:")
        print("   Send email to john@example.com about weather")
        print("\n🔗 Available Servers:")
        for name, url in self.servers.items():
            print(f"   • {name}: {url}")
    
    async def show_status(self):
        """Show current status of all servers."""
        print("\n📊 SERVER STATUS")
        print("=" * 40)
        
        availability = await self.check_server_availability()
        
        for server_name, url in self.servers.items():
            available = availability.get(server_name, False)
            status = "✅ Online" if available else "❌ Offline"
            primary = "⭐ Primary" if server_name == self.primary_server else ""
            
            print(f"   • {server_name}: {status} {primary}")
            print(f"     URL: {url}")
            
            if available:
                try:
                    response = requests.get(f"{url}/api/health", timeout=3)
                    if response.status_code == 200:
                        health = response.json()
                        agents = health.get("agents_loaded", 0)
                        mongodb = health.get("mongodb_connected", False)
                        print(f"     Agents: {agents}, MongoDB: {'✅' if mongodb else '❌'}")
                except:
                    pass
            print()
    
    def display_result(self, result: Dict[str, Any]):
        """Display command result in a formatted way."""
        print("\n" + "=" * 60)
        print("📊 MCP COMMAND RESPONSE")
        print("=" * 60)
        
        status = result.get("status", "unknown")
        if status == "success":
            print("✅ Status: SUCCESS")
        else:
            print("❌ Status: ERROR")
        
        # Show message
        message = result.get("message", "No message")
        print(f"💬 Message: {message}")
        
        # Show server info
        server_used = result.get("server_used", "unknown")
        print(f"🔗 Server: {server_used}")
        
        # Show agent info
        agent_used = result.get("agent_used", "unknown")
        if agent_used != "unknown":
            print(f"🤖 Agent: {agent_used}")
        
        # Show specific response types
        if "weather_response" in result:
            print(f"🌤️ Weather: {result['weather_response']}")
            
            weather_data = result.get("weather_data", {})
            if weather_data:
                temp = weather_data.get("temperature", "N/A")
                desc = weather_data.get("description", "N/A")
                print(f"   🌡️ Temperature: {temp}°C")
                print(f"   ☁️ Conditions: {desc}")
        
        if "math_response" in result:
            print(f"🔢 Math: {result['math_response']}")
            if "result" in result:
                print(f"   📊 Result: {result['result']}")
        
        if "email_response" in result:
            print(f"📧 Email: {result['email_response']}")
            if "to_email" in result:
                print(f"   📬 To: {result['to_email']}")
            if "email_sent" in result:
                sent = "✅ Sent" if result["email_sent"] else "⚠️ Prepared"
                print(f"   📤 Status: {sent}")
        
        # Show suggestions if available
        if "suggestions" in result and result["suggestions"]:
            print("\n💡 Suggestions:")
            for suggestion in result["suggestions"][:3]:
                print(f"   • {suggestion}")
        
        # Show examples if available
        if "examples" in result and result["examples"]:
            print("\n📝 Examples:")
            for example in result["examples"][:3]:
                print(f"   • {example}")
        
        # Show timestamp
        timestamp = result.get("timestamp", datetime.now().isoformat())
        print(f"\n⏰ Timestamp: {timestamp}")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified MCP Client")
    parser.add_argument("-c", "--command", help="Single command to execute")
    parser.add_argument("-s", "--server", help="Preferred server (main, core, mongodb)")
    parser.add_argument("--status", action="store_true", help="Show server status")
    
    args = parser.parse_args()
    
    client = UnifiedMCPClient()
    
    if args.status:
        await client.show_status()
        return
    
    if args.command:
        # Single command mode
        print("🤖 UNIFIED MCP CLIENT - COMMAND MODE")
        print("=" * 60)
        print(f"🔄 Processing: {args.command}")
        
        result = await client.send_command(args.command, args.server)
        client.display_result(result)
    else:
        # Interactive mode
        await client.interactive_mode()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Client terminated by user")
    except Exception as e:
        print(f"\n❌ Client error: {e}")
        import traceback
        traceback.print_exc()
