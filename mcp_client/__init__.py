#!/usr/bin/env python3
"""
MCP Client Package - Client implementations for Model Context Protocol
"""

from .base_client import BaseMCPClient, MCPRequest, MCPResponse
from .enhanced_client import EnhancedMCPClient, create_client

__version__ = "1.0.0"
__author__ = "MCP System"
__description__ = "Client implementations for Model Context Protocol"

# Export main classes
__all__ = [
    "BaseMCPClient",
    "EnhancedMCPClient", 
    "MCPRequest",
    "MCPResponse",
    "create_client"
]

# Package metadata
PACKAGE_INFO = {
    "name": "mcp_client",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "components": [
        "base_client.py - Base MCP client implementation",
        "enhanced_client.py - Full-featured MCP client",
        "cli_client.py - Command-line interface",
        "web_client.html - Web interface"
    ]
}
