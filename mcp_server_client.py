#!/usr/bin/env python3
"""
Advanced MCP Server Client
Professional-grade client for Model Context Protocol server communication
"""

import asyncio
import aiohttp
import json
import sys
import os
import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

class MessageType(Enum):
    """Message type enumeration."""
    COMMAND = "command"
    QUERY = "query"
    DOCUMENT_ANALYSIS = "document_analysis"
    AGENT_CALL = "agent_call"
    SYSTEM_CONTROL = "system_control"

@dataclass
class MCPRequest:
    """MCP request data structure."""
    id: str
    type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    timeout: int = 30
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class MCPResponse:
    """MCP response data structure."""
    id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime
    processing_time: float
    error: Optional[str] = None

@dataclass
class ConnectionConfig:
    """Connection configuration."""
    server_url: str = "http://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    keepalive_interval: int = 30
    auto_reconnect: bool = True
    connection_pool_size: int = 10

class MCPServerClient:
    """Advanced MCP Server Client with professional features."""

    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}
        self.active_requests: Dict[str, MCPRequest] = {}
        self.connection_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "connection_uptime": 0.0,
            "last_error": None
        }

        # Event handlers
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_message: Optional[Callable] = None

        # Background tasks
        self._keepalive_task: Optional[asyncio.Task] = None
        self._request_processor_task: Optional[asyncio.Task] = None
        self._connection_monitor_task: Optional[asyncio.Task] = None

        # Setup logging
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the client."""
        logger = logging.getLogger(f"MCPClient-{id(self)}")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        if self.connection_state == ConnectionState.CONNECTED:
            self.logger.info("Already connected to MCP server")
            return True

        self.connection_state = ConnectionState.CONNECTING
        self.logger.info(f"Connecting to MCP server at {self.config.server_url}")

        try:
            # Create session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=self.config.connection_pool_size,
                limit_per_host=self.config.connection_pool_size,
                keepalive_timeout=self.config.keepalive_interval
            )

            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "MCP-Client/1.0"}
            )

            # Test connection
            health_check = await self._health_check()
            if health_check:
                self.connection_state = ConnectionState.CONNECTED
                self._record_connection_event("connected")

                # Start background tasks
                await self._start_background_tasks()

                # Call connection handler
                if self.on_connect:
                    await self._safe_call_handler(self.on_connect)

                self.logger.info("Successfully connected to MCP server")
                return True
            else:
                raise Exception("Health check failed")

        except Exception as e:
            self.connection_state = ConnectionState.ERROR
            self._record_connection_event("connection_failed", str(e))
            self.logger.error(f"Failed to connect to MCP server: {e}")

            if self.session:
                await self.session.close()
                self.session = None

            return False

    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.connection_state == ConnectionState.DISCONNECTED:
            return

        self.logger.info("Disconnecting from MCP server")
        self.connection_state = ConnectionState.DISCONNECTED

        # Stop background tasks
        await self._stop_background_tasks()

        # Close session
        if self.session:
            await self.session.close()
            self.session = None

        # Call disconnect handler
        if self.on_disconnect:
            await self._safe_call_handler(self.on_disconnect)

        self._record_connection_event("disconnected")
        self.logger.info("Disconnected from MCP server")

    async def send_request(self, request_type: MessageType, payload: Dict[str, Any],
                          timeout: Optional[int] = None) -> MCPResponse:
        """Send request to MCP server."""
        if self.connection_state != ConnectionState.CONNECTED:
            raise Exception("Not connected to MCP server")

        request_id = str(uuid.uuid4())
        request = MCPRequest(
            id=request_id,
            type=request_type,
            payload=payload,
            timestamp=datetime.now(),
            timeout=timeout or self.config.timeout
        )

        self.active_requests[request_id] = request

        try:
            response = await self._execute_request(request)
            self._update_performance_metrics(True, response.processing_time)
            return response
        except Exception as e:
            self._update_performance_metrics(False, 0)
            raise e
        finally:
            self.active_requests.pop(request_id, None)

    async def send_command(self, command: str, **kwargs) -> MCPResponse:
        """Send command to MCP server."""
        payload = {"command": command, **kwargs}
        return await self.send_request(MessageType.COMMAND, payload)

    async def analyze_document(self, filename: str, content: str, query: str) -> MCPResponse:
        """Analyze document through MCP server."""
        payload = {
            "documents": [{
                "filename": filename,
                "content": content,
                "type": "text"
            }],
            "query": query,
            "rag_mode": True
        }
        return await self.send_request(MessageType.DOCUMENT_ANALYSIS, payload)

    async def call_agent(self, agent_id: str, method: str, params: Dict[str, Any]) -> MCPResponse:
        """Call specific agent method."""
        payload = {
            "agent_id": agent_id,
            "method": method,
            "params": params
        }
        return await self.send_request(MessageType.AGENT_CALL, payload)

    async def get_server_status(self) -> MCPResponse:
        """Get server status and information."""
        return await self.send_request(MessageType.SYSTEM_CONTROL, {"action": "status"})

    async def get_agents(self) -> MCPResponse:
        """Get list of available agents."""
        return await self.send_request(MessageType.SYSTEM_CONTROL, {"action": "agents"})

    async def reload_agents(self) -> MCPResponse:
        """Reload all agents."""
        return await self.send_request(MessageType.SYSTEM_CONTROL, {"action": "reload"})

    async def _execute_request(self, request: MCPRequest) -> MCPResponse:
        """Execute HTTP request to server."""
        start_time = time.time()

        # Determine endpoint based on request type
        endpoint_map = {
            MessageType.COMMAND: "/api/mcp/command",
            MessageType.QUERY: "/api/mcp/query",
            MessageType.DOCUMENT_ANALYSIS: "/api/mcp/analyze",
            MessageType.AGENT_CALL: "/api/mcp/agent",
            MessageType.SYSTEM_CONTROL: "/api/mcp/system"
        }

        endpoint = endpoint_map.get(request.type, "/api/mcp/command")
        url = f"{self.config.server_url}{endpoint}"

        try:
            async with self.session.post(url, json=request.payload) as response:
                response_data = await response.json()
                processing_time = time.time() - start_time

                if response.status == 200:
                    return MCPResponse(
                        id=request.id,
                        status="success",
                        data=response_data,
                        timestamp=datetime.now(),
                        processing_time=processing_time
                    )
                else:
                    error_msg = response_data.get("detail", f"HTTP {response.status}")
                    return MCPResponse(
                        id=request.id,
                        status="error",
                        data=response_data,
                        timestamp=datetime.now(),
                        processing_time=processing_time,
                        error=error_msg
                    )

        except asyncio.TimeoutError:
            raise Exception(f"Request timeout after {request.timeout} seconds")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    async def _health_check(self) -> bool:
        """Perform health check on server."""
        try:
            async with self.session.get(f"{self.config.server_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "ok"
                return False
        except:
            return False

    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        self._connection_monitor_task = asyncio.create_task(self._connection_monitor())

    async def _stop_background_tasks(self) -> None:
        """Stop background tasks."""
        tasks = [self._keepalive_task, self._connection_monitor_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _keepalive_loop(self) -> None:
        """Keepalive loop to maintain connection."""
        while self.connection_state == ConnectionState.CONNECTED:
            try:
                await asyncio.sleep(self.config.keepalive_interval)
                if self.connection_state == ConnectionState.CONNECTED:
                    await self._health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"Keepalive failed: {e}")

    async def _connection_monitor(self) -> None:
        """Monitor connection and handle reconnection."""
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                if self.connection_state == ConnectionState.CONNECTED:
                    if not await self._health_check():
                        self.logger.warning("Connection lost, attempting reconnection")
                        if self.config.auto_reconnect:
                            await self._attempt_reconnection()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Connection monitor error: {e}")

    async def _attempt_reconnection(self) -> None:
        """Attempt to reconnect to server."""
        self.connection_state = ConnectionState.RECONNECTING

        for attempt in range(self.config.max_retries):
            try:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

                if await self._health_check():
                    self.connection_state = ConnectionState.CONNECTED
                    self.logger.info("Reconnection successful")
                    return

            except Exception as e:
                self.logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")

        self.connection_state = ConnectionState.ERROR
        self.logger.error("All reconnection attempts failed")

    def _record_connection_event(self, event: str, details: str = "") -> None:
        """Record connection event."""
        self.connection_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details
        })

        # Keep only last 100 events
        if len(self.connection_history) > 100:
            self.connection_history = self.connection_history[-100:]

    def _update_performance_metrics(self, success: bool, response_time: float) -> None:
        """Update performance metrics."""
        self.performance_metrics["total_requests"] += 1

        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1

        # Update average response time
        total = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )

    async def _safe_call_handler(self, handler: Callable) -> None:
        """Safely call event handler."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()
        except Exception as e:
            self.logger.error(f"Event handler error: {e}")

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "state": self.connection_state.value,
            "server_url": self.config.server_url,
            "connected_since": self.connection_history[-1]["timestamp"] if self.connection_history else None,
            "performance_metrics": self.performance_metrics.copy(),
            "active_requests": len(self.active_requests),
            "connection_history": self.connection_history[-10:]  # Last 10 events
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

class MCPClientManager:
    """Advanced client manager with connection pooling and load balancing."""

    def __init__(self, server_urls: List[str], pool_size: int = 5):
        self.server_urls = server_urls
        self.pool_size = pool_size
        self.client_pools: Dict[str, List[MCPServerClient]] = {}
        self.current_server_index = 0
        self.server_health: Dict[str, bool] = {}

    async def initialize(self) -> None:
        """Initialize client pools for all servers."""
        for server_url in self.server_urls:
            self.client_pools[server_url] = []
            self.server_health[server_url] = False

            # Create client pool for this server
            for _ in range(self.pool_size):
                client = create_mcp_client(server_url)
                self.client_pools[server_url].append(client)

    async def get_client(self) -> MCPServerClient:
        """Get available client with load balancing."""
        # Find healthy server
        healthy_servers = [url for url, health in self.server_health.items() if health]

        if not healthy_servers:
            # Try to connect to servers
            for server_url in self.server_urls:
                pool = self.client_pools[server_url]
                for client in pool:
                    if await client.connect():
                        self.server_health[server_url] = True
                        return client

            raise Exception("No healthy servers available")

        # Round-robin load balancing
        server_url = healthy_servers[self.current_server_index % len(healthy_servers)]
        self.current_server_index += 1

        # Get available client from pool
        pool = self.client_pools[server_url]
        for client in pool:
            if client.connection_state == ConnectionState.CONNECTED:
                return client

        # Try to connect a client
        for client in pool:
            if await client.connect():
                return client

        raise Exception(f"No available clients for server {server_url}")

    async def execute_request(self, request_type: MessageType, payload: Dict[str, Any]) -> MCPResponse:
        """Execute request with automatic failover."""
        last_error = None

        for _ in range(len(self.server_urls)):
            try:
                client = await self.get_client()
                return await client.send_request(request_type, payload)
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"All servers failed. Last error: {last_error}")

    async def shutdown(self) -> None:
        """Shutdown all client connections."""
        for pool in self.client_pools.values():
            for client in pool:
                await client.disconnect()

# Factory functions
def create_mcp_client(server_url: str = "http://localhost:8000", **config_kwargs) -> MCPServerClient:
    """Create MCP client with configuration."""
    config = ConnectionConfig(server_url=server_url, **config_kwargs)
    return MCPServerClient(config)

def create_mcp_client_manager(server_urls: List[str], pool_size: int = 5) -> MCPClientManager:
    """Create MCP client manager with multiple servers."""
    return MCPClientManager(server_urls, pool_size)

if __name__ == "__main__":
    async def demo():
        """Demo the MCP client."""
        print("🤖 MCP Server Client Demo")
        print("=" * 40)

        # Create client
        client = create_mcp_client()

        try:
            # Connect
            print("🔗 Connecting to server...")
            if await client.connect():
                print("✅ Connected successfully!")

                # Get server status
                print("\n📊 Getting server status...")
                status = await client.get_server_status()
                print(f"Status: {status.status}")

                # Get agents
                print("\n🤖 Getting agents...")
                agents = await client.get_agents()
                print(f"Agents: {agents.data.get('total_agents', 0)}")

                # Send test command
                print("\n💬 Sending test command...")
                response = await client.send_command("hello")
                print(f"Response: {response.status}")

                # Show connection info
                print("\n📈 Connection Info:")
                info = client.get_connection_info()
                print(f"State: {info['state']}")
                print(f"Total Requests: {info['performance_metrics']['total_requests']}")
                print(f"Success Rate: {info['performance_metrics']['successful_requests']}/{info['performance_metrics']['total_requests']}")

            else:
                print("❌ Connection failed!")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await client.disconnect()
            print("👋 Disconnected")

    asyncio.run(demo())
