#!/usr/bin/env python3
"""
CLI MCP Client - Command-line interface for your MCP server
"""

import asyncio
import argparse
import json
import sys
import os
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client.enhanced_client import EnhancedMCPClient

class CLIMCPClient:
    """Command-line interface for MCP client."""

    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = None

    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            self.client = EnhancedMCPClient(self.server_url, "CLI MCP Client")
            return await self.client.initialize()
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.client:
            await self.client.disconnect()

    async def cmd_status(self) -> int:
        """Show server and client status."""
        try:
            print("🔍 MCP Client Status")
            print("=" * 40)

            # Client status
            session_info = self.client.get_session_info()
            print(f"Session ID: {session_info['session_id']}")
            print(f"Commands sent: {session_info['command_history_count']}")
            print(f"Connected: {session_info['connection_status']['connected']}")

            # Server status
            server_info = await self.client.get_server_info()
            print(f"Server status: {server_info.get('status', 'unknown')}")
            print(f"Modular system: {server_info.get('modular_system', 'unknown')}")

            return 0
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return 1

    async def cmd_agents(self) -> int:
        """List available agents."""
        try:
            print("🤖 Available Agents")
            print("=" * 40)

            agents_info = await self.client.get_agents()
            total_agents = agents_info.get('total_agents', 0)
            print(f"Total agents: {total_agents}")

            agents = agents_info.get('agents', {})
            for agent_id, agent_info in agents.items():
                print(f"\n• {agent_id}")
                print(f"  Name: {agent_info.get('name', 'Unknown')}")
                capabilities = agent_info.get('capabilities', [])
                if capabilities:
                    print(f"  Capabilities: {len(capabilities)}")
                    for cap in capabilities[:2]:  # Show first 2 capabilities
                        print(f"    - {cap.get('name', 'Unknown')}: {cap.get('description', 'No description')}")

            return 0
        except Exception as e:
            print(f"❌ Error getting agents: {e}")
            return 1

    async def cmd_send(self, command: str, file_path: str = None) -> int:
        """Send a command to the MCP server."""
        try:
            print(f"📤 Sending command: {command}")

            documents = []
            if file_path and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents = [await self.client.upload_document(
                    os.path.basename(file_path), content
                )]
                print(f"📁 Attached file: {file_path}")

            result = await self.client.send_command(command, documents, rag_mode=bool(documents))

            print("\n📥 Response:")
            print("=" * 40)
            print(f"Status: {result.get('status', 'unknown')}")

            if result.get('comprehensive_answer'):
                print(f"Answer: {result['comprehensive_answer']}")
            elif result.get('response'):
                print(f"Response: {result['response']}")
            elif result.get('message'):
                print(f"Message: {result['message']}")

            if result.get('agents_involved'):
                print(f"Agents involved: {', '.join(result['agents_involved'])}")

            return 0
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return 1

    async def cmd_test_analysis(self) -> int:
        """Test document analysis functionality."""
        try:
            print("🎯 Testing Document Analysis")
            print("=" * 40)

            result = await self.client.test_document_analysis()

            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Type: {result.get('type', 'unknown')}")

            if result.get('comprehensive_answer'):
                print(f"\nAnswer:\n{result['comprehensive_answer']}")
            elif result.get('message'):
                print(f"\nMessage:\n{result['message']}")

            if result.get('agents_involved'):
                print(f"\nAgents involved: {', '.join(result['agents_involved'])}")

            if result.get('processing_approach'):
                print(f"Processing approach: {result['processing_approach']}")

            return 0
        except Exception as e:
            print(f"❌ Error testing document analysis: {e}")
            return 1

    async def cmd_weather(self, location: str) -> int:
        """Get weather for a location."""
        try:
            print(f"🌤️ Getting weather for: {location}")

            result = await self.client.get_weather(location)

            print(f"Status: {result.get('status', 'unknown')}")
            if result.get('message'):
                print(f"Response: {result['message']}")

            return 0
        except Exception as e:
            print(f"❌ Error getting weather: {e}")
            return 1

    async def cmd_reload(self) -> int:
        """Reload agents on the server."""
        try:
            print("🔄 Reloading agents...")

            result = await self.client.reload_agents()

            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Message: {result.get('message', 'No message')}")
            if result.get('total_loaded'):
                print(f"Total loaded: {result['total_loaded']}")

            return 0
        except Exception as e:
            print(f"❌ Error reloading agents: {e}")
            return 1

    async def cmd_interactive(self) -> int:
        """Start interactive mode."""
        try:
            await self.client.interactive_mode()
            return 0
        except Exception as e:
            print(f"❌ Error in interactive mode: {e}")
            return 1

async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="MCP Client CLI")
    parser.add_argument("--server", default="http://localhost:8000",
                       help="MCP server URL (default: http://localhost:8000)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show server and client status")

    # Agents command
    subparsers.add_parser("agents", help="List available agents")

    # Send command
    send_parser = subparsers.add_parser("send", help="Send a command to the server")
    send_parser.add_argument("text", help="Command text to send")
    send_parser.add_argument("--file", help="Optional file to attach")

    # Test document analysis
    subparsers.add_parser("test-analysis", help="Test document analysis functionality")

    # Weather command
    weather_parser = subparsers.add_parser("weather", help="Get weather for a location")
    weather_parser.add_argument("location", help="Location to get weather for")

    # Reload command
    subparsers.add_parser("reload", help="Reload agents on the server")

    # Interactive command
    subparsers.add_parser("interactive", help="Start interactive mode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create client
    cli_client = CLIMCPClient(args.server)

    try:
        print(f"🔗 Connecting to MCP server at {args.server}...")
        if not await cli_client.connect():
            return 1

        print("✅ Connected successfully!")

        # Execute command
        if args.command == "status":
            return await cli_client.cmd_status()
        elif args.command == "agents":
            return await cli_client.cmd_agents()
        elif args.command == "send":
            return await cli_client.cmd_send(args.text, args.file)
        elif args.command == "test-analysis":
            return await cli_client.cmd_test_analysis()
        elif args.command == "weather":
            return await cli_client.cmd_weather(args.location)
        elif args.command == "reload":
            return await cli_client.cmd_reload()
        elif args.command == "interactive":
            return await cli_client.cmd_interactive()
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        await cli_client.disconnect()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
