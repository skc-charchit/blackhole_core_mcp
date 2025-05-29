#!/usr/bin/env python3
"""
MCP Production Client
Command-line interface for the Model Context Protocol server
"""

import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List

class MCPClient:
    """Production MCP client for command-line interaction."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def send_command(self, command: str) -> Dict[str, Any]:
        """Send a command to the MCP server."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/mcp/command",
                json={"command": command}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def analyze_document(self, filename: str, content: str, query: str) -> Dict[str, Any]:
        """Analyze a document."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/mcp/analyze",
                json={
                    "documents": [
                        {
                            "filename": filename,
                            "content": content,
                            "type": "text"
                        }
                    ],
                    "query": query,
                    "rag_mode": True
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def execute_workflow(self, documents: List[Dict], query: str) -> Dict[str, Any]:
        """Execute an automated workflow."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/mcp/workflow",
                json={
                    "documents": documents,
                    "query": query,
                    "rag_mode": True
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_agents(self) -> Dict[str, Any]:
        """Get available agents."""
        try:
            response = self.session.get(f"{self.base_url}/api/mcp/agents")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

def print_response(response: Dict[str, Any], command_type: str = "command"):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"📊 MCP {command_type.upper()} RESPONSE")
    print(f"{'='*60}")
    
    if response.get("status") == "success":
        print("✅ Status: SUCCESS")
        
        # Weather response
        if "weather_response" in response:
            print(f"\n🌤️ WEATHER DATA:")
            print(f"🏙️ City: {response.get('city', 'Unknown')}")
            print(f"🌍 Country: {response.get('country', 'Unknown')}")
            print(f"📡 Source: {response.get('data_source', 'Unknown')}")
            print(f"\n{response['weather_response']}")
        
        # Workflow response
        elif "workflow_description" in response:
            print(f"\n🔄 WORKFLOW EXECUTED:")
            print(f"📋 Description: {response['workflow_description']}")
            print(f"⏱️ Execution time: {response.get('execution_time', 0):.3f}s")
            print(f"🆔 Workflow ID: {response.get('workflow_id', 'Unknown')}")
            
            if "comprehensive_answer" in response:
                print(f"\n📝 RESULTS:")
                print(response['comprehensive_answer'])
        
        # Document analysis response
        elif "comprehensive_answer" in response:
            print(f"\n📄 DOCUMENT ANALYSIS:")
            print(response['comprehensive_answer'])
        
        # General response
        elif "message" in response:
            print(f"\n💬 MESSAGE:")
            print(response['message'])
        
        # Agents list
        elif "agents" in response:
            agents = response['agents']
            print(f"\n🤖 AVAILABLE AGENTS ({len(agents)}):")
            for agent_id, agent_info in agents.items():
                print(f"  • {agent_id}: {agent_info.get('description', 'No description')}")
    
    else:
        print("❌ Status: ERROR")
        print(f"💬 Message: {response.get('message', 'Unknown error')}")
        
        if "suggestions" in response:
            print(f"\n💡 Suggestions:")
            for suggestion in response['suggestions']:
                print(f"  • {suggestion}")
        
        if "examples" in response:
            print(f"\n📝 Examples:")
            for example in response['examples']:
                print(f"  • {example}")
    
    print(f"\n⏰ Timestamp: {response.get('timestamp', datetime.now().isoformat())}")
    print(f"{'='*60}")

def interactive_mode(client: MCPClient):
    """Run interactive mode."""
    print("🤖 MCP INTERACTIVE MODE")
    print("=" * 40)
    print("💬 Type your commands or 'quit' to exit")
    print("🌤️ Try: 'What is the weather in Mumbai?'")
    print("📄 Try: 'help' for more examples")
    print("=" * 40)
    
    while True:
        try:
            command = input("\n🎯 MCP> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if command.lower() == 'help':
                print("\n📚 EXAMPLE COMMANDS:")
                print("🌤️ Weather: 'What is the weather in Mumbai?'")
                print("🌤️ Weather: 'Delhi weather'")
                print("🌤️ Weather: 'Temperature in New York'")
                print("🤖 Agents: 'agents' - List available agents")
                print("🔍 Health: 'health' - Check server health")
                print("❌ Exit: 'quit' or 'exit'")
                continue
            
            if command.lower() == 'agents':
                response = client.get_agents()
                print_response(response, "agents")
                continue
            
            if command.lower() == 'health':
                response = client.health_check()
                print_response(response, "health")
                continue
            
            if not command:
                continue
            
            # Send command
            response = client.send_command(command)
            print_response(response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="MCP Production Client")
    parser.add_argument("--server", default="http://localhost:8000", help="MCP server URL")
    parser.add_argument("--command", "-c", help="Single command to execute")
    parser.add_argument("--file", "-f", help="File to analyze")
    parser.add_argument("--query", "-q", help="Query for file analysis")
    parser.add_argument("--health", action="store_true", help="Check server health")
    parser.add_argument("--agents", action="store_true", help="List available agents")
    
    args = parser.parse_args()
    
    # Create client
    client = MCPClient(args.server)
    
    # Health check
    if args.health:
        response = client.health_check()
        print_response(response, "health")
        return
    
    # List agents
    if args.agents:
        response = client.get_agents()
        print_response(response, "agents")
        return
    
    # File analysis
    if args.file and args.query:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            response = client.analyze_document(args.file, content, args.query)
            print_response(response, "analyze")
            return
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
    
    # Single command
    if args.command:
        response = client.send_command(args.command)
        print_response(response)
        return
    
    # Interactive mode
    interactive_mode(client)

if __name__ == "__main__":
    main()
