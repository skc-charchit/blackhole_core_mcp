#!/usr/bin/env python3
"""
Base MCP Client - Foundation for MCP client implementations
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_client")

@dataclass
class MCPRequest:
    """Represents an MCP request."""
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None
    jsonrpc: str = "2.0"

@dataclass
class MCPResponse:
    """Represents an MCP response."""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    jsonrpc: str = "2.0"

class BaseMCPClient(ABC):
    """Base class for MCP clients."""

    def __init__(self, server_url: str, client_name: str = "MCP Client"):
        self.server_url = server_url.rstrip('/')
        self.client_name = client_name
        self.session = None
        self.connected = False
        self.logger = logging.getLogger(f"mcp_client.{client_name.lower().replace(' ', '_')}")

        # Client capabilities
        self.capabilities = {
            "experimental": {},
            "roots": {
                "listChanged": True
            },
            "sampling": {}
        }

        # Connection info
        self.connection_info = {
            "connected_at": None,
            "last_request_at": None,
            "total_requests": 0,
            "failed_requests": 0
        }

    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            self.session = aiohttp.ClientSession()

            # Test connection with health check
            health_response = await self.health_check()
            if health_response.get("status") == "ok":
                self.connected = True
                self.connection_info["connected_at"] = datetime.now().isoformat()
                self.logger.info(f"Connected to MCP server at {self.server_url}")
                return True
            else:
                self.logger.error(f"MCP server health check failed: {health_response}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        self.logger.info("Disconnected from MCP server")

    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        try:
            async with self.session.get(f"{self.server_url}/api/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def send_request(self, method: str, params: Dict[str, Any] = None) -> MCPResponse:
        """Send a request to the MCP server."""
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")

        request = MCPRequest(
            method=method,
            params=params or {},
            id=f"req_{self.connection_info['total_requests'] + 1}"
        )

        try:
            self.connection_info["total_requests"] += 1
            self.connection_info["last_request_at"] = datetime.now().isoformat()

            # Send request based on method type
            if method.startswith("mcp/"):
                response_data = await self._send_mcp_request(request)
            else:
                response_data = await self._send_api_request(request)

            return MCPResponse(
                result=response_data,
                id=request.id
            )

        except Exception as e:
            self.connection_info["failed_requests"] += 1
            self.logger.error(f"Request failed: {e}")
            return MCPResponse(
                error={"code": -1, "message": str(e)},
                id=request.id
            )

    async def _send_mcp_request(self, request: MCPRequest) -> Dict[str, Any]:
        """Send MCP protocol request."""
        endpoint = f"{self.server_url}/api/mcp/command"

        payload = {
            "command": request.params.get("command", ""),
            "session_id": request.params.get("session_id"),
            "documents_context": request.params.get("documents_context"),
            "rag_mode": request.params.get("rag_mode", False)
        }

        async with self.session.post(endpoint, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")

    async def _send_api_request(self, request: MCPRequest) -> Dict[str, Any]:
        """Send API request."""
        endpoint = f"{self.server_url}/api/{request.method}"

        async with self.session.get(endpoint, params=request.params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")

    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        response = await self.send_request("health")
        return response.result or response.error

    async def get_agents(self) -> Dict[str, Any]:
        """Get available agents from server."""
        try:
            async with self.session.get(f"{self.server_url}/api/mcp/agents") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "code": response.status}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def process_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Process a command through the MCP server."""
        try:
            payload = {
                "command": command,
                **kwargs
            }

            async with self.session.post(f"{self.server_url}/api/mcp/command", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"status": "error", "code": response.status, "message": error_text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_connection_status(self) -> Dict[str, Any]:
        """Get client connection status."""
        return {
            "connected": self.connected,
            "server_url": self.server_url,
            "client_name": self.client_name,
            "connection_info": self.connection_info,
            "capabilities": self.capabilities
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    def __str__(self):
        return f"{self.client_name} -> {self.server_url}"

    def __repr__(self):
        return f"BaseMCPClient(server_url='{self.server_url}', client_name='{self.client_name}')"
