#!/usr/bin/env python3
"""
Enhanced MCP Client - Full-featured client for your MCP server
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client.base_client import BaseMCPClient, MCPResponse

class EnhancedMCPClient(BaseMCPClient):
    """Enhanced MCP client with advanced features."""

    def __init__(self, server_url: str = "http://localhost:8000", client_name: str = "Enhanced MCP Client"):
        super().__init__(server_url, client_name)

        # Enhanced capabilities
        self.capabilities.update({
            "document_processing": True,
            "agent_collaboration": True,
            "file_upload": True,
            "session_management": True
        })

        # Session management
        self.session_id = f"client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.command_history = []
        self.agent_cache = {}

    async def initialize(self) -> bool:
        """Initialize the client with server handshake."""
        if not await self.connect():
            return False

        try:
            # Get server info
            server_info = await self.get_server_info()
            self.logger.info(f"Connected to: {server_info.get('status', 'Unknown server')}")

            # Cache available agents
            agents_info = await self.get_agents()
            self.agent_cache = agents_info.get("agents", {})
            self.logger.info(f"Available agents: {len(self.agent_cache)}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            return False

    async def send_command(self, command: str, documents: List[Dict[str, Any]] = None,
                          rag_mode: bool = False) -> Dict[str, Any]:
        """Send a command with optional document context."""
        params = {
            "session_id": self.session_id,
            "rag_mode": rag_mode
        }

        if documents:
            params["documents_context"] = documents

        # Store in history
        self.command_history.append({
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "documents_count": len(documents) if documents else 0
        })

        response = await self.process_command(command, **params)

        # Log response
        if response.get("status") == "success":
            self.logger.info(f"Command processed successfully: {command[:50]}...")
        else:
            self.logger.warning(f"Command failed: {response.get('message', 'Unknown error')}")

        return response

    async def upload_document(self, filename: str, content: str, doc_type: str = "text") -> Dict[str, Any]:
        """Upload a document for processing."""
        document = {
            "filename": filename,
            "content": content,
            "type": doc_type,
            "uploaded_at": datetime.now().isoformat()
        }

        return document

    async def analyze_document(self, filename: str, content: str,
                             query: str = "analyze this document") -> Dict[str, Any]:
        """Analyze a document with a specific query."""
        document = await self.upload_document(filename, content)
        return await self.send_command(query, documents=[document], rag_mode=True)

    async def ask_about_author(self, filename: str, content: str) -> Dict[str, Any]:
        """Ask about the author of a document."""
        return await self.analyze_document(filename, content, "who is the author and what is the summary")

    async def get_weather(self, location: str) -> Dict[str, Any]:
        """Get weather information for a location."""
        return await self.send_command(f"get weather for {location}")

    async def search_documents(self, query: str) -> Dict[str, Any]:
        """Search for documents."""
        return await self.send_command(f"search for {query}")

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get detailed agent status from server."""
        try:
            response = await self.send_request("mcp/agents/status")
            return response.result or response.error
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def reload_agents(self) -> Dict[str, Any]:
        """Reload agents on the server."""
        try:
            endpoint = f"{self.server_url}/api/mcp/agents/reload"
            async with self.session.post(endpoint) as response:
                if response.status == 200:
                    result = await response.json()
                    # Update agent cache
                    agents_info = await self.get_agents()
                    self.agent_cache = agents_info.get("agents", {})
                    return result
                else:
                    return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_document_analysis(self) -> Dict[str, Any]:
        """Test general document analysis functionality."""
        sample_content = '''
        Sample Document Content

        Content Type: Text Document
        Processing Confidence: 95%

        Text Content:
        "This is a sample document for testing the analysis capabilities of the MCP system."

        Additional Context:
        This document demonstrates the system's ability to process and analyze various types of content,
        extract meaningful information, and provide comprehensive responses through agent collaboration.
        '''

        return await self.analyze_document("sample_document.txt", sample_content, "analyze this document")

    async def batch_process_documents(self, documents: List[Dict[str, Any]],
                                    query: str = "analyze these documents") -> List[Dict[str, Any]]:
        """Process multiple documents in batch."""
        results = []

        for doc in documents:
            try:
                result = await self.analyze_document(
                    doc.get("filename", "unknown"),
                    doc.get("content", ""),
                    query
                )
                results.append({
                    "document": doc.get("filename", "unknown"),
                    "result": result,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "document": doc.get("filename", "unknown"),
                    "error": str(e),
                    "status": "error"
                })

        return results

    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        return {
            "session_id": self.session_id,
            "command_history_count": len(self.command_history),
            "cached_agents": len(self.agent_cache),
            "connection_status": self.get_connection_status(),
            "recent_commands": self.command_history[-5:] if self.command_history else []
        }

    async def interactive_mode(self):
        """Start interactive mode for testing."""
        print(f"🤖 {self.client_name} - Interactive Mode")
        print("=" * 50)
        print("Commands:")
        print("  help - Show this help")
        print("  status - Show connection status")
        print("  agents - Show available agents")
        print("  test - Test document analysis")
        print("  weather <location> - Get weather")
        print("  quit - Exit interactive mode")
        print("=" * 50)

        while True:
            try:
                command = input("\n> ").strip()

                if command.lower() in ['quit', 'exit', 'q']:
                    break
                elif command.lower() == 'help':
                    print("Available commands: help, status, agents, test, weather <location>, quit")
                elif command.lower() == 'status':
                    status = self.get_session_info()
                    print(f"Session: {status['session_id']}")
                    print(f"Commands sent: {status['command_history_count']}")
                    print(f"Connected: {status['connection_status']['connected']}")
                elif command.lower() == 'agents':
                    agents = await self.get_agents()
                    print(f"Available agents: {agents.get('total_agents', 0)}")
                    for agent_id, agent_info in agents.get('agents', {}).items():
                        print(f"  • {agent_id}: {agent_info.get('name', 'Unknown')}")
                elif command.lower() == 'test':
                    print("Testing document analysis...")
                    result = await self.test_document_analysis()
                    print(f"Result: {result.get('status', 'unknown')}")
                    if 'comprehensive_answer' in result:
                        print(f"Answer: {result['comprehensive_answer'][:100]}...")
                    elif 'message' in result:
                        print(f"Message: {result['message'][:100]}...")
                elif command.lower().startswith('weather '):
                    location = command[8:].strip()
                    if location:
                        result = await self.get_weather(location)
                        print(f"Weather result: {result.get('status', 'unknown')}")
                else:
                    # Send as general command
                    result = await self.send_command(command)
                    print(f"Response: {result.get('status', 'unknown')}")
                    if result.get('message'):
                        print(f"Message: {result['message']}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        print("\n👋 Goodbye!")

# Convenience function
async def create_client(server_url: str = "http://localhost:8000") -> EnhancedMCPClient:
    """Create and initialize an enhanced MCP client."""
    client = EnhancedMCPClient(server_url)
    if await client.initialize():
        return client
    else:
        raise ConnectionError(f"Failed to connect to MCP server at {server_url}")

if __name__ == "__main__":
    async def main():
        try:
            client = await create_client()
            await client.interactive_mode()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if 'client' in locals():
                await client.disconnect()

    asyncio.run(main())
