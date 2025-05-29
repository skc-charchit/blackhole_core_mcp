#!/usr/bin/env python3
"""
Production MCP Server - Scalable and Modular
Auto-discovery, fault tolerance, and production-ready architecture
"""

import os
import sys
import logging
import asyncio
import importlib.util
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import threading
import time

load_dotenv()

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server.log')
    ]
)
logger = logging.getLogger("production_mcp_server")

app = FastAPI(
    title="Production MCP Server",
    version="2.0.0",
    description="Scalable, modular, and production-ready MCP server with auto-discovery"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB integration
try:
    # Use existing MongoDB module
    sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))
    from mongodb import get_mongo_client, get_agent_outputs_collection, test_connection
    from mcp_mongodb_integration import MCPMongoDBIntegration
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("MongoDB integration not available")

# Inter-agent communication
try:
    from inter_agent_communication import initialize_inter_agent_system, AgentCommunicationHub
    INTER_AGENT_AVAILABLE = True
except ImportError:
    INTER_AGENT_AVAILABLE = False
    logger.warning("Inter-agent communication not available")

class MCPCommandRequest(BaseModel):
    command: str

class AgentManagementRequest(BaseModel):
    agent_id: str
    action: str  # activate, deactivate, restart, move
    target_folder: Optional[str] = None

# Global state
loaded_agents = {}
failed_agents = {}
agent_health_status = {}
server_ready = False
mongodb_integration = None
inter_agent_hub = None
health_monitor_task = None
agent_discovery_task = None

# Configuration
AGENT_FOLDERS = {
    "live": Path("agents/live"),
    "inactive": Path("agents/inactive"),
    "future": Path("agents/future"),
    "templates": Path("agents/templates")
}

SERVER_CONFIG = {
    "health_check_interval": 30,
    "agent_discovery_interval": 60,
    "max_agent_failures": 3,
    "agent_recovery_timeout": 120,
    "auto_recovery_enabled": True,
    "hot_swap_enabled": True
}

class ProductionAgentManager:
    """Production-ready agent management with auto-discovery and fault tolerance."""
    
    def __init__(self):
        self.loaded_agents = {}
        self.failed_agents = {}
        self.agent_health_status = {}
        self.agent_metadata_cache = {}
        self.last_discovery_scan = None
        
    async def discover_agents(self) -> Dict[str, List[str]]:
        """Discover agents in all folders with auto-loading."""
        discovered = {
            "live": [],
            "inactive": [],
            "future": [],
            "templates": []
        }
        
        logger.info("🔍 Starting agent discovery...")
        
        for folder_name, folder_path in AGENT_FOLDERS.items():
            if not folder_path.exists():
                logger.warning(f"Agent folder not found: {folder_path}")
                continue
                
            for agent_file in folder_path.glob("*.py"):
                if agent_file.name.startswith("__"):
                    continue
                    
                try:
                    agent_metadata = await self.get_agent_metadata(agent_file)
                    if agent_metadata:
                        agent_id = agent_metadata.get("id", agent_file.stem)
                        discovered[folder_name].append(agent_id)
                        self.agent_metadata_cache[agent_id] = {
                            "metadata": agent_metadata,
                            "file_path": agent_file,
                            "folder": folder_name
                        }
                        
                        # Auto-load live agents
                        if folder_name == "live" and agent_metadata.get("auto_load", False):
                            await self.load_agent(agent_id, agent_file)
                            
                except Exception as e:
                    logger.error(f"Error discovering agent {agent_file}: {e}")
        
        self.last_discovery_scan = datetime.now()
        logger.info(f"✅ Agent discovery completed: {discovered}")
        return discovered
    
    async def get_agent_metadata(self, agent_file: Path) -> Optional[Dict[str, Any]]:
        """Get agent metadata from file."""
        try:
            spec = importlib.util.spec_from_file_location("temp_agent", agent_file)
            if spec is None or spec.loader is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Try to get metadata function
            if hasattr(module, 'get_agent_metadata'):
                return module.get_agent_metadata()
            elif hasattr(module, 'AGENT_METADATA'):
                return module.AGENT_METADATA
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting metadata from {agent_file}: {e}")
            return None
    
    async def load_agent(self, agent_id: str, agent_file: Path) -> bool:
        """Load a single agent with error handling."""
        try:
            logger.info(f"🔄 Loading agent: {agent_id}")
            
            spec = importlib.util.spec_from_file_location(agent_id, agent_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {agent_id}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[agent_id] = module
            spec.loader.exec_module(module)
            
            # Create agent instance
            if hasattr(module, 'create_agent'):
                agent_instance = module.create_agent()
            else:
                logger.error(f"Agent {agent_id} missing create_agent() function")
                return False
            
            # Store agent
            self.loaded_agents[agent_id] = {
                "instance": agent_instance,
                "metadata": self.agent_metadata_cache.get(agent_id, {}).get("metadata", {}),
                "file_path": agent_file,
                "loaded_at": datetime.now(),
                "status": "loaded"
            }
            
            # Initialize health monitoring
            self.agent_health_status[agent_id] = {
                "status": "healthy",
                "last_check": datetime.now(),
                "failure_count": 0
            }
            
            logger.info(f"✅ Successfully loaded agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load agent {agent_id}: {e}")
            self.failed_agents[agent_id] = {
                "error": str(e),
                "failed_at": datetime.now(),
                "file_path": agent_file
            }
            return False
    
    async def unload_agent(self, agent_id: str) -> bool:
        """Unload an agent safely."""
        try:
            if agent_id in self.loaded_agents:
                # Cleanup agent resources if needed
                agent_data = self.loaded_agents[agent_id]
                if hasattr(agent_data["instance"], "cleanup"):
                    await agent_data["instance"].cleanup()
                
                # Remove from loaded agents
                del self.loaded_agents[agent_id]
                
                # Remove from health monitoring
                if agent_id in self.agent_health_status:
                    del self.agent_health_status[agent_id]
                
                # Remove from sys.modules
                if agent_id in sys.modules:
                    del sys.modules[agent_id]
                
                logger.info(f"✅ Successfully unloaded agent: {agent_id}")
                return True
            else:
                logger.warning(f"Agent {agent_id} not loaded")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to unload agent {agent_id}: {e}")
            return False
    
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent."""
        try:
            if agent_id not in self.loaded_agents:
                logger.warning(f"Agent {agent_id} not loaded, cannot restart")
                return False
            
            agent_file = self.loaded_agents[agent_id]["file_path"]
            
            # Unload and reload
            await self.unload_agent(agent_id)
            return await self.load_agent(agent_id, agent_file)
            
        except Exception as e:
            logger.error(f"❌ Failed to restart agent {agent_id}: {e}")
            return False
    
    async def move_agent(self, agent_id: str, target_folder: str) -> bool:
        """Move agent between folders."""
        try:
            if agent_id not in self.agent_metadata_cache:
                logger.error(f"Agent {agent_id} not found in cache")
                return False
            
            if target_folder not in AGENT_FOLDERS:
                logger.error(f"Invalid target folder: {target_folder}")
                return False
            
            agent_info = self.agent_metadata_cache[agent_id]
            current_file = agent_info["file_path"]
            target_path = AGENT_FOLDERS[target_folder] / current_file.name
            
            # Unload if currently loaded
            if agent_id in self.loaded_agents:
                await self.unload_agent(agent_id)
            
            # Move file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            current_file.rename(target_path)
            
            # Update cache
            agent_info["file_path"] = target_path
            agent_info["folder"] = target_folder
            
            logger.info(f"✅ Moved agent {agent_id} to {target_folder}")
            
            # Auto-load if moved to live folder
            if target_folder == "live":
                await self.load_agent(agent_id, target_path)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to move agent {agent_id}: {e}")
            return False
    
    async def health_check_agent(self, agent_id: str) -> Dict[str, Any]:
        """Perform health check on a specific agent."""
        try:
            if agent_id not in self.loaded_agents:
                return {
                    "agent_id": agent_id,
                    "status": "not_loaded",
                    "timestamp": datetime.now().isoformat()
                }
            
            agent_instance = self.loaded_agents[agent_id]["instance"]
            
            # Call agent's health check if available
            if hasattr(agent_instance, "health_check"):
                health_result = await agent_instance.health_check()
            else:
                health_result = {
                    "agent_id": agent_id,
                    "status": "healthy",
                    "message": "No health check method available"
                }
            
            # Update health status
            self.agent_health_status[agent_id] = {
                "status": health_result.get("status", "unknown"),
                "last_check": datetime.now(),
                "failure_count": health_result.get("failure_count", 0),
                "details": health_result
            }
            
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed for {agent_id}: {e}")
            
            # Update failure count
            if agent_id in self.agent_health_status:
                self.agent_health_status[agent_id]["failure_count"] += 1
                self.agent_health_status[agent_id]["status"] = "unhealthy"
            
            return {
                "agent_id": agent_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check_all_agents(self) -> Dict[str, Any]:
        """Perform health check on all loaded agents."""
        health_results = {}
        
        for agent_id in self.loaded_agents.keys():
            health_results[agent_id] = await self.health_check_agent(agent_id)
        
        return health_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "server": "production_mcp_server",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "loaded_agents": len(self.loaded_agents),
            "failed_agents": len(self.failed_agents),
            "total_discovered": len(self.agent_metadata_cache),
            "last_discovery_scan": self.last_discovery_scan.isoformat() if self.last_discovery_scan else None,
            "agent_folders": {name: str(path) for name, path in AGENT_FOLDERS.items()},
            "server_config": SERVER_CONFIG,
            "mongodb_available": MONGODB_AVAILABLE,
            "inter_agent_available": INTER_AGENT_AVAILABLE
        }

# Global agent manager
agent_manager = ProductionAgentManager()

async def background_health_monitor():
    """Background task for continuous health monitoring."""
    while True:
        try:
            await asyncio.sleep(SERVER_CONFIG["health_check_interval"])
            
            if not server_ready:
                continue
            
            logger.info("🔍 Running background health checks...")
            health_results = await agent_manager.health_check_all_agents()
            
            # Handle unhealthy agents
            for agent_id, health in health_results.items():
                if health.get("status") == "unhealthy":
                    failure_count = agent_manager.agent_health_status.get(agent_id, {}).get("failure_count", 0)
                    
                    if failure_count >= SERVER_CONFIG["max_agent_failures"]:
                        logger.warning(f"⚠️ Agent {agent_id} exceeded failure threshold, moving to inactive")
                        
                        if SERVER_CONFIG["auto_recovery_enabled"]:
                            await agent_manager.move_agent(agent_id, "inactive")
            
        except Exception as e:
            logger.error(f"Background health monitor error: {e}")

async def background_agent_discovery():
    """Background task for periodic agent discovery."""
    while True:
        try:
            await asyncio.sleep(SERVER_CONFIG["agent_discovery_interval"])
            
            logger.info("🔍 Running background agent discovery...")
            await agent_manager.discover_agents()
            
        except Exception as e:
            logger.error(f"Background agent discovery error: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize production server."""
    global server_ready, mongodb_integration, inter_agent_hub, health_monitor_task, agent_discovery_task
    
    logger.info("🚀 Starting Production MCP Server...")
    
    # Create agent folders if they don't exist
    for folder_path in AGENT_FOLDERS.values():
        folder_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize MongoDB integration
    if MONGODB_AVAILABLE:
        try:
            # Test connection using existing MongoDB module
            mongodb_connected = test_connection()
            if mongodb_connected:
                logger.info("✅ MongoDB connection successful")
                # Initialize MCP MongoDB integration
                mongodb_integration = MCPMongoDBIntegration()
                connected = await mongodb_integration.connect()
                if connected:
                    logger.info("✅ MCP MongoDB integration connected")
                else:
                    logger.warning("⚠️ MCP MongoDB integration failed, but basic MongoDB is working")
            else:
                logger.warning("⚠️ MongoDB connection failed - using dummy mode")
        except Exception as e:
            logger.error(f"❌ MongoDB integration error: {e}")
    
    # Initialize Inter-Agent Communication
    if INTER_AGENT_AVAILABLE:
        try:
            inter_agent_hub = await initialize_inter_agent_system()
            logger.info("✅ Inter-agent communication system initialized")
        except Exception as e:
            logger.error(f"❌ Inter-agent communication error: {e}")
    
    # Discover and load agents
    await agent_manager.discover_agents()
    
    # Start background tasks
    health_monitor_task = asyncio.create_task(background_health_monitor())
    agent_discovery_task = asyncio.create_task(background_agent_discovery())
    
    server_ready = True
    logger.info(f"🎉 Production server ready with {len(agent_manager.loaded_agents)} agents")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    global health_monitor_task, agent_discovery_task
    
    logger.info("🛑 Shutting down Production MCP Server...")
    
    # Cancel background tasks
    if health_monitor_task:
        health_monitor_task.cancel()
    if agent_discovery_task:
        agent_discovery_task.cancel()
    
    # Unload all agents
    for agent_id in list(agent_manager.loaded_agents.keys()):
        await agent_manager.unload_agent(agent_id)
    
    logger.info("✅ Production server shutdown complete")

@app.get("/api/health")
async def health_check():
    """Comprehensive health check."""
    system_status = agent_manager.get_system_status()

    # Add health status for all agents
    agent_health = {}
    for agent_id in agent_manager.loaded_agents.keys():
        agent_health[agent_id] = agent_manager.agent_health_status.get(agent_id, {})

    return {
        "status": "ok",
        "ready": server_ready,
        "system": system_status,
        "agent_health": agent_health,
        "mongodb_connected": mongodb_integration is not None,
        "inter_agent_communication": inter_agent_hub is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/agents")
async def list_agents():
    """List all agents with detailed information."""
    agents_info = {}

    for agent_id, agent_data in agent_manager.loaded_agents.items():
        metadata = agent_data.get("metadata", {})
        health = agent_manager.agent_health_status.get(agent_id, {})

        agents_info[agent_id] = {
            "status": "loaded",
            "metadata": metadata,
            "health": health,
            "loaded_at": agent_data.get("loaded_at", "").isoformat() if agent_data.get("loaded_at") else "",
            "file_path": str(agent_data.get("file_path", ""))
        }

    # Add failed agents
    for agent_id, failure_data in agent_manager.failed_agents.items():
        agents_info[agent_id] = {
            "status": "failed",
            "error": failure_data.get("error", ""),
            "failed_at": failure_data.get("failed_at", "").isoformat() if failure_data.get("failed_at") else "",
            "file_path": str(failure_data.get("file_path", ""))
        }

    # Add discovered but not loaded agents
    for agent_id, cache_data in agent_manager.agent_metadata_cache.items():
        if agent_id not in agents_info:
            agents_info[agent_id] = {
                "status": "discovered",
                "metadata": cache_data.get("metadata", {}),
                "folder": cache_data.get("folder", ""),
                "file_path": str(cache_data.get("file_path", ""))
            }

    return {
        "status": "success",
        "agents": agents_info,
        "summary": {
            "total_agents": len(agents_info),
            "loaded_agents": len(agent_manager.loaded_agents),
            "failed_agents": len(agent_manager.failed_agents),
            "discovered_agents": len(agent_manager.agent_metadata_cache)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/agents/discover")
async def discover_agents():
    """Trigger agent discovery."""
    try:
        discovered = await agent_manager.discover_agents()
        return {
            "status": "success",
            "discovered": discovered,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent discovery failed: {str(e)}")

@app.post("/api/agents/manage")
async def manage_agent(request: AgentManagementRequest):
    """Manage agent lifecycle (activate, deactivate, restart, move)."""
    try:
        agent_id = request.agent_id
        action = request.action.lower()

        if action == "activate":
            # Move to live folder and load
            if agent_id in agent_manager.agent_metadata_cache:
                cache_data = agent_manager.agent_metadata_cache[agent_id]
                if cache_data["folder"] != "live":
                    success = await agent_manager.move_agent(agent_id, "live")
                    if success:
                        return {"status": "success", "message": f"Agent {agent_id} activated"}
                    else:
                        raise HTTPException(status_code=500, detail=f"Failed to activate agent {agent_id}")
                else:
                    return {"status": "success", "message": f"Agent {agent_id} already active"}
            else:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        elif action == "deactivate":
            # Move to inactive folder and unload
            success = await agent_manager.move_agent(agent_id, "inactive")
            if success:
                return {"status": "success", "message": f"Agent {agent_id} deactivated"}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to deactivate agent {agent_id}")

        elif action == "restart":
            # Restart agent
            success = await agent_manager.restart_agent(agent_id)
            if success:
                return {"status": "success", "message": f"Agent {agent_id} restarted"}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to restart agent {agent_id}")

        elif action == "move":
            # Move to specified folder
            if not request.target_folder:
                raise HTTPException(status_code=400, detail="Target folder required for move action")

            success = await agent_manager.move_agent(agent_id, request.target_folder)
            if success:
                return {"status": "success", "message": f"Agent {agent_id} moved to {request.target_folder}"}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to move agent {agent_id}")

        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent management failed: {str(e)}")

@app.get("/api/agents/{agent_id}/health")
async def agent_health_check(agent_id: str):
    """Get health status for specific agent."""
    try:
        health_result = await agent_manager.health_check_agent(agent_id)
        return health_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/api/mcp/command")
async def process_command(request: MCPCommandRequest):
    """Process MCP command with automatic agent selection."""
    if not server_ready:
        raise HTTPException(status_code=503, detail="Server not ready")

    try:
        command = request.command.lower().strip()

        # Find matching agent based on command content
        matching_agent = None
        agent_id = None

        # Smart agent selection based on command content
        if any(word in command for word in ["calculate", "math", "compute", "+", "-", "*", "/", "%", "="]):
            # Math-related commands
            for aid in ["math_agent"]:
                if aid in agent_manager.loaded_agents:
                    matching_agent = agent_manager.loaded_agents[aid]["instance"]
                    agent_id = aid
                    break
        elif any(word in command for word in ["weather", "temperature", "forecast", "climate"]):
            # Weather-related commands
            for aid in ["weather_agent"]:
                if aid in agent_manager.loaded_agents:
                    matching_agent = agent_manager.loaded_agents[aid]["instance"]
                    agent_id = aid
                    break
        elif any(word in command for word in ["analyze", "document", "text", "extract", "process"]):
            # Document-related commands
            for aid in ["document_agent"]:
                if aid in agent_manager.loaded_agents:
                    matching_agent = agent_manager.loaded_agents[aid]["instance"]
                    agent_id = aid
                    break
        elif any(word in command for word in ["email", "send", "mail", "gmail"]):
            # Email-related commands
            for aid in ["gmail_agent"]:
                if aid in agent_manager.loaded_agents:
                    matching_agent = agent_manager.loaded_agents[aid]["instance"]
                    agent_id = aid
                    break
        elif any(word in command for word in ["calendar", "schedule", "reminder", "meeting"]):
            # Calendar-related commands
            for aid in ["calendar_agent"]:
                if aid in agent_manager.loaded_agents:
                    matching_agent = agent_manager.loaded_agents[aid]["instance"]
                    agent_id = aid
                    break

        if not matching_agent:
            # Try to find any available agent
            if agent_manager.loaded_agents:
                agent_id = list(agent_manager.loaded_agents.keys())[0]
                matching_agent = agent_manager.loaded_agents[agent_id]["instance"]
            else:
                return {
                    "status": "error",
                    "message": "No agents available to process command",
                    "available_agents": list(agent_manager.loaded_agents.keys()),
                    "timestamp": datetime.now().isoformat()
                }

        # Create message for agent
        from agents.base_agent import MCPMessage
        message = MCPMessage(
            id=f"{agent_id}_{datetime.now().timestamp()}",
            method="process",
            params={"query": request.command, "expression": request.command},
            timestamp=datetime.now()
        )

        # Process with agent
        result = await matching_agent.process_message(message)

        # Add metadata
        result["agent_used"] = agent_id
        result["server"] = "production_mcp_server"
        result["timestamp"] = datetime.now().isoformat()

        # Store in MongoDB with guaranteed reporting
        if mongodb_integration:
            try:
                mongodb_id = await mongodb_integration.store_command_result(
                    command=request.command,
                    agent_used=agent_id,
                    result=result,
                    timestamp=datetime.now()
                )
                result["stored_in_mongodb"] = True
                result["mongodb_id"] = mongodb_id
                result["storage_method"] = "primary"
                logger.info(f"✅ Stored command result in MongoDB: {agent_id}")
            except Exception as e:
                logger.error(f"❌ Primary storage failed: {e}")

                # Fallback storage method
                try:
                    fallback_success = await mongodb_integration.force_store_result(
                        agent_id, request.command, result
                    )
                    result["stored_in_mongodb"] = fallback_success
                    result["storage_method"] = "fallback"
                    if fallback_success:
                        logger.info(f"✅ Fallback storage successful: {agent_id}")
                    else:
                        logger.error(f"❌ Fallback storage failed: {agent_id}")
                except Exception as e2:
                    logger.error(f"❌ Fallback storage also failed: {e2}")
                    result["stored_in_mongodb"] = False
                    result["storage_error"] = str(e2)
                    result["storage_method"] = "failed"
        else:
            result["stored_in_mongodb"] = False
            result["storage_error"] = "MongoDB integration not available"
            result["storage_method"] = "unavailable"

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": f"Command processing failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/")
async def serve_interface():
    """Serve production web interface."""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Production MCP Server - Scalable Agent Network</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }}
            h1 {{ text-align: center; margin-bottom: 20px; }}
            .status {{ color: #4CAF50; font-weight: bold; text-align: center; font-size: 1.2em; }}
            .section {{ background: rgba(255,255,255,0.1); padding: 20px; margin: 20px 0; border-radius: 10px; }}
            .btn {{ background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 5px; }}
            .agent {{ background: rgba(255,255,255,0.1); padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Production MCP Server</h1>
            <p class="status">✅ Scalable • Modular • Production-Ready</p>

            <div class="section">
                <h2>🎯 System Features</h2>
                <div class="grid">
                    <div class="agent">
                        <h3>🔍 Auto-Discovery</h3>
                        <p>Automatic agent detection and loading from organized folders</p>
                    </div>
                    <div class="agent">
                        <h3>🛡️ Fault Tolerance</h3>
                        <p>Graceful degradation and automatic failure isolation</p>
                    </div>
                    <div class="agent">
                        <h3>🔄 Hot Swapping</h3>
                        <p>Add, remove, restart agents without server downtime</p>
                    </div>
                    <div class="agent">
                        <h3>📊 Health Monitoring</h3>
                        <p>Continuous health checks and automatic recovery</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📁 Agent Architecture</h2>
                <div class="grid">
                    <div class="agent">
                        <h3>📂 live/</h3>
                        <p>Active and functional agents</p>
                    </div>
                    <div class="agent">
                        <h3>📂 inactive/</h3>
                        <p>Temporarily disabled agents</p>
                    </div>
                    <div class="agent">
                        <h3>📂 future/</h3>
                        <p>Agents prepared for future activation</p>
                    </div>
                    <div class="agent">
                        <h3>📂 templates/</h3>
                        <p>Agent templates and examples</p>
                    </div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <a href="/api/health" class="btn">🔍 System Health</a>
                <a href="/api/agents" class="btn">🤖 Agent Status</a>
                <a href="/docs" class="btn">📚 API Documentation</a>
                <a href="/api/agents/discover" class="btn">🔍 Discover Agents</a>
            </div>

            <div class="section">
                <h2>🌐 Production Endpoints</h2>
                <p><strong>Command Processing:</strong> POST /api/mcp/command</p>
                <p><strong>Agent Management:</strong> POST /api/agents/manage</p>
                <p><strong>Health Monitoring:</strong> GET /api/agents/{{agent_id}}/health</p>
                <p><strong>Agent Discovery:</strong> GET /api/agents/discover</p>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
