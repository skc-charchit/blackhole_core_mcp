#!/usr/bin/env python3
"""
Start MCP Client - Simple startup script for MCP client
"""

import asyncio
import sys
import os
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_client import EnhancedMCPClient

async def interactive_client(server_url: str):
    """Start interactive MCP client."""
    print("🤖 Starting Enhanced MCP Client")
    print("🎯 Interactive Mode for Model Context Protocol")
    print("=" * 50)

    try:
        client = EnhancedMCPClient(server_url, "Interactive MCP Client")

        print(f"🔗 Connecting to MCP server at {server_url}...")
        if await client.initialize():
            print("✅ Connected successfully!")
            print("🎯 Starting interactive mode...")
            await client.interactive_mode()
        else:
            print("❌ Failed to connect to MCP server")
            print("🔧 Make sure the server is running:")
            print(f"   python start_mcp_server.py")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        if 'client' in locals():
            await client.disconnect()

    return 0

async def test_client(server_url: str):
    """Test MCP client functionality."""
    print("🧪 Testing MCP Client")
    print("=" * 30)

    try:
        from test_mcp_client import run_comprehensive_client_test
        success = await run_comprehensive_client_test()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test error: {e}")
        return 1

def show_usage():
    """Show usage information."""
    print("🤖 MCP Client Usage")
    print("=" * 40)
    print("Available interfaces:")
    print("")
    print("1. 🐍 Python Interactive:")
    print("   python start_mcp_client.py")
    print("   python start_mcp_client.py --server http://localhost:8000")
    print("")
    print("2. 💻 Command Line Interface:")
    print("   python mcp_client/cli_client.py status")
    print("   python mcp_client/cli_client.py agents")
    print("   python mcp_client/cli_client.py send \"hello world\"")
    print("   python mcp_client/cli_client.py test-analysis")
    print("   python mcp_client/cli_client.py interactive")
    print("")
    print("3. 🌐 Web Interface:")
    print("   Open mcp_client/web_client.html in your browser")
    print("")
    print("4. 🧪 Test Suite:")
    print("   python start_mcp_client.py --test")
    print("   python test_mcp_client.py")
    print("")
    print("🎯 Make sure your MCP server is running:")
    print("   python start_mcp_server.py")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="MCP Client Startup")
    parser.add_argument("--server", default="http://localhost:8000",
                       help="MCP server URL (default: http://localhost:8000)")
    parser.add_argument("--test", action="store_true",
                       help="Run client test suite")
    parser.add_argument("--usage", action="store_true",
                       help="Show usage information")

    args = parser.parse_args()

    if args.usage:
        show_usage()
        return 0

    if args.test:
        return asyncio.run(test_client(args.server))
    else:
        return asyncio.run(interactive_client(args.server))

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
