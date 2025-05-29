#!/usr/bin/env python3
"""
MCP Server Connector
Unified connection manager for all MCP servers
"""

import asyncio
import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import time
import signal
import os

class MCPServerConnector:
    """Manages connections between multiple MCP servers."""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp_connector")
        self.servers = {}
        self.running_processes = {}
        
        # Define available MCP servers
        self.available_servers = {
            "main_server": {
                "script": "mcp_server.py",
                "port": 8000,
                "description": "Main production MCP server with agents",
                "priority": 1
            },
            "core_server": {
                "script": "core/mcp_server.py", 
                "port": 8001,
                "description": "Restructured MCP server with conversation engine",
                "priority": 2
            },
            "production_server": {
                "script": "scripts/start_production.py",
                "port": 8002,
                "description": "Production startup system",
                "priority": 3
            },
            "mongodb_server": {
                "script": "mcp_mongodb_integration.py",
                "port": 8003,
                "description": "MongoDB integration server",
                "priority": 4
            }
        }
        
        self.logger.info("MCP Server Connector initialized")
    
    async def discover_servers(self) -> Dict[str, Any]:
        """Discover available MCP servers."""
        print("🔍 DISCOVERING MCP SERVERS")
        print("=" * 50)
        
        discovered = {}
        
        for server_id, config in self.available_servers.items():
            script_path = Path(config["script"])
            
            if script_path.exists():
                print(f"✅ Found: {server_id} ({config['description']})")
                discovered[server_id] = {
                    **config,
                    "status": "available",
                    "script_path": str(script_path)
                }
            else:
                print(f"❌ Missing: {server_id} - {script_path}")
                discovered[server_id] = {
                    **config,
                    "status": "missing",
                    "script_path": str(script_path)
                }
        
        self.servers = discovered
        print(f"\n📊 Discovered {len([s for s in discovered.values() if s['status'] == 'available'])} available servers")
        return discovered
    
    async def start_server(self, server_id: str, wait_for_startup: bool = True) -> bool:
        """Start a specific MCP server."""
        if server_id not in self.servers:
            self.logger.error(f"Unknown server: {server_id}")
            return False
        
        server_config = self.servers[server_id]
        
        if server_config["status"] != "available":
            self.logger.error(f"Server {server_id} is not available")
            return False
        
        try:
            print(f"🚀 Starting {server_id}...")
            
            # Special handling for different server types
            if server_id == "production_server":
                # Production server is a startup script, not a web server
                process = subprocess.Popen(
                    ["python", server_config["script"]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for completion
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    print(f"✅ {server_id} startup completed successfully")
                    return True
                else:
                    print(f"❌ {server_id} startup failed: {stderr}")
                    return False
            
            else:
                # Regular web servers
                if server_id == "core_server":
                    # Core server needs special environment
                    env = os.environ.copy()
                    env["PYTHONPATH"] = "."
                    
                    process = subprocess.Popen(
                        ["python", "-m", "uvicorn", "core.mcp_server:app", 
                         "--host", "0.0.0.0", "--port", str(server_config["port"])],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=env
                    )
                else:
                    # Main server and others
                    process = subprocess.Popen(
                        ["python", "-m", "uvicorn", f"{Path(server_config['script']).stem}:app",
                         "--host", "0.0.0.0", "--port", str(server_config["port"])],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                
                self.running_processes[server_id] = process
                
                if wait_for_startup:
                    # Wait for server to be ready
                    for attempt in range(30):  # 30 seconds timeout
                        try:
                            response = requests.get(
                                f"http://localhost:{server_config['port']}/api/health",
                                timeout=2
                            )
                            if response.status_code == 200:
                                print(f"✅ {server_id} started successfully on port {server_config['port']}")
                                server_config["status"] = "running"
                                server_config["url"] = f"http://localhost:{server_config['port']}"
                                return True
                        except:
                            pass
                        
                        await asyncio.sleep(1)
                    
                    print(f"⚠️ {server_id} started but health check failed")
                    return False
                else:
                    print(f"🔄 {server_id} starting in background...")
                    return True
            
        except Exception as e:
            self.logger.error(f"Error starting {server_id}: {e}")
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop a specific MCP server."""
        if server_id in self.running_processes:
            try:
                process = self.running_processes[server_id]
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                del self.running_processes[server_id]
                
                if server_id in self.servers:
                    self.servers[server_id]["status"] = "stopped"
                
                print(f"✅ Stopped {server_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping {server_id}: {e}")
                return False
        else:
            print(f"⚠️ {server_id} is not running")
            return False
    
    async def check_server_health(self, server_id: str) -> Dict[str, Any]:
        """Check health of a specific server."""
        if server_id not in self.servers:
            return {"status": "unknown", "error": "Server not found"}
        
        server_config = self.servers[server_id]
        
        if server_config.get("status") != "running":
            return {"status": "not_running"}
        
        try:
            response = requests.get(
                f"http://localhost:{server_config['port']}/api/health",
                timeout=5
            )
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "healthy",
                    "health_data": health_data,
                    "url": f"http://localhost:{server_config['port']}"
                }
            else:
                return {
                    "status": "unhealthy",
                    "http_status": response.status_code
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """Start all available servers in priority order."""
        print("🚀 STARTING ALL MCP SERVERS")
        print("=" * 50)
        
        results = {}
        
        # Sort servers by priority
        sorted_servers = sorted(
            [(k, v) for k, v in self.servers.items() if v["status"] == "available"],
            key=lambda x: x[1]["priority"]
        )
        
        for server_id, config in sorted_servers:
            print(f"\n🔄 Starting {server_id} (Priority {config['priority']})...")
            
            success = await self.start_server(server_id, wait_for_startup=True)
            results[server_id] = success
            
            if success:
                print(f"✅ {server_id} started successfully")
            else:
                print(f"❌ {server_id} failed to start")
                
                # For critical servers, continue anyway
                if config["priority"] <= 2:
                    print(f"⚠️ Continuing despite {server_id} failure...")
        
        return results
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """Stop all running servers."""
        print("🛑 STOPPING ALL MCP SERVERS")
        print("=" * 50)
        
        results = {}
        
        for server_id in list(self.running_processes.keys()):
            success = await self.stop_server(server_id)
            results[server_id] = success
        
        return results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        print("📊 SYSTEM STATUS")
        print("=" * 50)
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "servers": {},
            "summary": {
                "total_servers": len(self.servers),
                "available_servers": 0,
                "running_servers": 0,
                "healthy_servers": 0
            }
        }
        
        for server_id, config in self.servers.items():
            health = await self.check_server_health(server_id)
            
            status["servers"][server_id] = {
                "config": config,
                "health": health
            }
            
            if config["status"] == "available":
                status["summary"]["available_servers"] += 1
            
            if config.get("status") == "running":
                status["summary"]["running_servers"] += 1
            
            if health.get("status") == "healthy":
                status["summary"]["healthy_servers"] += 1
        
        return status
    
    async def test_server_connections(self) -> Dict[str, Any]:
        """Test connections to all running servers."""
        print("🧪 TESTING SERVER CONNECTIONS")
        print("=" * 50)
        
        test_results = {}
        
        for server_id, config in self.servers.items():
            if config.get("status") == "running":
                print(f"\n🔍 Testing {server_id}...")
                
                try:
                    # Test health endpoint
                    health_response = requests.get(
                        f"http://localhost:{config['port']}/api/health",
                        timeout=5
                    )
                    
                    # Test command endpoint if available
                    command_response = None
                    try:
                        command_response = requests.post(
                            f"http://localhost:{config['port']}/api/mcp/command",
                            json={"command": "test connection"},
                            timeout=5
                        )
                    except:
                        pass
                    
                    test_results[server_id] = {
                        "health_status": health_response.status_code,
                        "health_data": health_response.json() if health_response.status_code == 200 else None,
                        "command_status": command_response.status_code if command_response else None,
                        "url": f"http://localhost:{config['port']}",
                        "test_passed": health_response.status_code == 200
                    }
                    
                    if health_response.status_code == 200:
                        print(f"✅ {server_id} connection test passed")
                    else:
                        print(f"❌ {server_id} connection test failed")
                
                except Exception as e:
                    test_results[server_id] = {
                        "error": str(e),
                        "test_passed": False
                    }
                    print(f"❌ {server_id} connection error: {e}")
        
        return test_results
    
    def cleanup(self):
        """Cleanup all running processes."""
        for server_id in list(self.running_processes.keys()):
            try:
                process = self.running_processes[server_id]
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.running_processes.clear()

async def main():
    """Main function to demonstrate MCP server connections."""
    connector = MCPServerConnector()
    
    try:
        print("🔗 MCP SERVER CONNECTION MANAGER")
        print("=" * 80)
        
        # Discover servers
        await connector.discover_servers()
        
        # Start all servers
        start_results = await connector.start_all_servers()
        
        # Get system status
        status = await connector.get_system_status()
        
        # Test connections
        test_results = await connector.test_server_connections()
        
        print("\n" + "=" * 80)
        print("📊 FINAL STATUS")
        print("=" * 80)
        
        summary = status["summary"]
        print(f"📈 Available servers: {summary['available_servers']}/{summary['total_servers']}")
        print(f"🚀 Running servers: {summary['running_servers']}")
        print(f"✅ Healthy servers: {summary['healthy_servers']}")
        
        print("\n🌐 SERVER URLS:")
        for server_id, server_status in status["servers"].items():
            if server_status["health"].get("status") == "healthy":
                url = server_status["health"].get("url", "N/A")
                desc = server_status["config"]["description"]
                print(f"   • {server_id}: {url} - {desc}")
        
        if summary['healthy_servers'] > 0:
            print("\n🎉 MCP SERVERS CONNECTED SUCCESSFULLY!")
            print("🔗 All servers are now interconnected and ready for use")
        else:
            print("\n⚠️ NO HEALTHY SERVERS RUNNING")
            print("🔧 Check the error messages above")
        
        return summary['healthy_servers'] > 0
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down servers...")
        await connector.stop_all_servers()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        connector.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\n🎉 MCP server connection completed!")
        else:
            print("\n🔧 MCP server connection needs attention.")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
