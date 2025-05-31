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
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
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

class PDFChatRequest(BaseModel):
    question: str
    pdf_id: Optional[str] = None
    session_id: Optional[str] = None

class DocumentChatRequest(BaseModel):
    question: str
    document_content: str
    document_name: Optional[str] = "document"
    session_id: Optional[str] = None

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

@app.get("/pdf-chat")
async def serve_pdf_chat_interface():
    """Serve PDF chat interface."""
    try:
        with open("pdf_chat_interface.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content)
    except FileNotFoundError:
        return HTMLResponse("<h1>PDF Chat Interface not found</h1><p>Please ensure pdf_chat_interface.html exists.</p>")

@app.get("/")
async def serve_interface():
    """Serve interactive web interface."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Agent System - Interactive Interface</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            .query-section {
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                backdrop-filter: blur(10px);
            }
            .query-input {
                width: 100%;
                padding: 15px;
                font-size: 16px;
                border: none;
                border-radius: 10px;
                margin-bottom: 15px;
                background: rgba(255,255,255,0.9);
                color: #333;
                outline: none;
            }
            .query-input:focus {
                box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
            }
            .query-btn {
                background: #4CAF50;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                cursor: pointer;
                margin-right: 10px;
                margin-bottom: 10px;
                transition: all 0.3s;
            }
            .query-btn:hover {
                background: #45a049;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .query-btn:active {
                transform: translateY(0);
            }
            .examples {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .example {
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s;
                border: 2px solid transparent;
            }
            .example:hover {
                background: rgba(255,255,255,0.2);
                border-color: #4CAF50;
                transform: translateY(-2px);
            }
            .output-section {
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                backdrop-filter: blur(10px);
                min-height: 200px;
            }
            .loading {
                text-align: center;
                padding: 50px;
                font-size: 18px;
            }
            .result {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 15px;
                animation: fadeIn 0.5s ease-in;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .result-success { border-left: 5px solid #4CAF50; }
            .result-error { border-left: 5px solid #f44336; }
            .status-section {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }
            .status-card {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                transition: all 0.3s;
            }
            .status-card:hover {
                background: rgba(255,255,255,0.15);
            }
            .history {
                max-height: 300px;
                overflow-y: auto;
                background: rgba(255,255,255,0.05);
                padding: 15px;
                border-radius: 10px;
            }
            .history-item {
                padding: 10px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                margin-bottom: 10px;
                cursor: pointer;
                transition: background 0.3s;
            }
            .history-item:hover {
                background: rgba(255,255,255,0.1);
            }
            .btn-group {
                text-align: center;
                margin: 20px 0;
            }
            .btn {
                background: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .btn:hover {
                background: #1976D2;
                transform: translateY(-2px);
            }
            .spinner {
                border: 4px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top: 4px solid #4CAF50;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                z-index: 1000;
                animation: slideIn 0.3s ease-out;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); }
                to { transform: translateX(0); }
            }
            .notification.success { background: #4CAF50; }
            .notification.error { background: #f44336; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 MCP Agent System</h1>
                <p>Ask questions, get intelligent responses with MongoDB storage</p>
                <div id="systemStatus" class="status-section">
                    <div class="status-card">
                        <h3>🚀 Server</h3>
                        <p id="serverStatus">Checking...</p>
                    </div>
                    <div class="status-card">
                        <h3>💾 MongoDB</h3>
                        <p id="mongoStatus">Checking...</p>
                    </div>
                    <div class="status-card">
                        <h3>🤖 Agents</h3>
                        <p id="agentStatus">Checking...</p>
                    </div>
                </div>
            </div>

            <div class="query-section">
                <h2>💬 Ask Your Question</h2>
                <input type="text" id="queryInput" class="query-input" placeholder="Type your question here... (e.g., Calculate 25 * 4, What is the weather in Mumbai?)" />
                <div>
                    <button id="sendBtn" class="query-btn">🚀 Send Query</button>
                    <button id="clearBtn" class="query-btn" style="background: #ff9800;">🗑️ Clear</button>
                    <button id="historyBtn" class="query-btn" style="background: #9c27b0;">📝 History</button>
                </div>

                <h3 style="margin-top: 20px;">💡 Try These Examples:</h3>
                <div class="examples">
                    <div class="example" data-query="Calculate 25 * 4">
                        <strong>🔢 Math:</strong> Calculate 25 * 4
                    </div>
                    <div class="example" data-query="What is the weather in Mumbai?">
                        <strong>🌤️ Weather:</strong> What is the weather in Mumbai?
                    </div>
                    <div class="example" data-query="Analyze this text: Hello world, this is a test document.">
                        <strong>📄 Document:</strong> Analyze this text: Hello world, this is a test document.
                    </div>
                    <div class="example" data-query="Calculate 20% of 500">
                        <strong>🔢 Percentage:</strong> Calculate 20% of 500
                    </div>
                    <div class="example" data-query="Weather forecast for Delhi">
                        <strong>🌤️ Forecast:</strong> Weather forecast for Delhi
                    </div>
                    <div class="example" data-query="Process document with multiple paragraphs and analyze content structure">
                        <strong>📄 Analysis:</strong> Process document with multiple paragraphs
                    </div>
                </div>
            </div>

            <div class="output-section">
                <h2>📤 Response</h2>
                <div id="output">
                    <div class="loading">
                        <p>👋 Welcome! Ask a question above to get started.</p>
                        <p>Your queries will be processed by intelligent agents and stored in MongoDB.</p>
                    </div>
                </div>
            </div>

            <div class="btn-group">
                <a href="/pdf-chat" class="btn" style="background: #e91e63;">📄 PDF Chat Interface</a>
                <a href="/api/health" class="btn" target="_blank">🔍 System Health</a>
                <a href="/api/agents" class="btn" target="_blank">🤖 Agent Status</a>
                <a href="/docs" class="btn" target="_blank">📚 API Documentation</a>
                <button id="refreshBtn" class="btn">🔄 Refresh Status</button>
            </div>
        </div>

        <script>
            let queryHistory = [];
            let isProcessing = false;

            // Initialize when page loads
            document.addEventListener('DOMContentLoaded', function() {
                refreshStatus();
                setupEventListeners();
                focusInput();
            });

            function setupEventListeners() {
                // Send button
                document.getElementById('sendBtn').addEventListener('click', sendQuery);

                // Clear button
                document.getElementById('clearBtn').addEventListener('click', clearOutput);

                // History button
                document.getElementById('historyBtn').addEventListener('click', showHistory);

                // Refresh button
                document.getElementById('refreshBtn').addEventListener('click', refreshStatus);

                // Enter key in input
                document.getElementById('queryInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && !isProcessing) {
                        sendQuery();
                    }
                });

                // Example buttons
                document.querySelectorAll('.example').forEach(example => {
                    example.addEventListener('click', function() {
                        const query = this.getAttribute('data-query');
                        setQuery(query);
                        showNotification('Example loaded! Click Send Query or press Enter.', 'success');
                    });
                });

                // Auto-refresh status every 30 seconds
                setInterval(refreshStatus, 30000);
            }

            function focusInput() {
                document.getElementById('queryInput').focus();
            }

            function showNotification(message, type = 'success') {
                // Remove existing notifications
                const existing = document.querySelector('.notification');
                if (existing) {
                    existing.remove();
                }

                const notification = document.createElement('div');
                notification.className = `notification ${type}`;
                notification.textContent = message;
                document.body.appendChild(notification);

                // Auto-remove after 3 seconds
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 3000);
            }

            function refreshStatus() {
                fetch('/api/health')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('serverStatus').innerHTML = data.ready ? '✅ Ready' : '❌ Not Ready';
                        document.getElementById('mongoStatus').innerHTML = data.mongodb_connected ? '✅ Connected' : '❌ Disconnected';
                        document.getElementById('agentStatus').innerHTML = `✅ ${data.system?.loaded_agents || 0} Loaded`;
                    })
                    .catch(error => {
                        document.getElementById('serverStatus').innerHTML = '❌ Error';
                        document.getElementById('mongoStatus').innerHTML = '❌ Error';
                        document.getElementById('agentStatus').innerHTML = '❌ Error';
                        console.error('Status check failed:', error);
                    });
            }

            function setQuery(query) {
                document.getElementById('queryInput').value = query;
                focusInput();
            }

            function sendQuery() {
                if (isProcessing) {
                    showNotification('Please wait for the current query to complete.', 'error');
                    return;
                }

                const query = document.getElementById('queryInput').value.trim();
                if (!query) {
                    showNotification('Please enter a query!', 'error');
                    focusInput();
                    return;
                }

                isProcessing = true;
                document.getElementById('sendBtn').disabled = true;
                document.getElementById('sendBtn').innerHTML = '⏳ Processing...';

                // Show loading spinner
                document.getElementById('output').innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>⏳ Processing your query: "${query}"</p>
                        <p>Please wait while our agents work on your request...</p>
                    </div>
                `;

                // Send query to server
                fetch('/api/mcp/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({command: query})
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    displayResult(query, data);
                    queryHistory.unshift({query: query, result: data, timestamp: new Date()});

                    // Clear input and focus for next query
                    document.getElementById('queryInput').value = '';
                    focusInput();

                    showNotification('Query processed successfully!', 'success');
                })
                .catch(error => {
                    displayError(query, error);
                    showNotification('Query failed. Please try again.', 'error');
                })
                .finally(() => {
                    isProcessing = false;
                    document.getElementById('sendBtn').disabled = false;
                    document.getElementById('sendBtn').innerHTML = '🚀 Send Query';
                });
            }

            function displayResult(query, result) {
                const isSuccess = result.status === 'success';
                const resultClass = isSuccess ? 'result-success' : 'result-error';

                let output = `
                    <div class="result ${resultClass}">
                        <h3>📤 Query: ${query}</h3>
                        <p><strong>🤖 Agent:</strong> ${result.agent_used || 'Unknown'}</p>
                        <p><strong>✅ Status:</strong> ${result.status?.toUpperCase() || 'UNKNOWN'}</p>
                `;

                if (isSuccess) {
                    if (result.result !== undefined) {
                        output += `<p><strong>🔢 Answer:</strong> ${result.result}</p>`;
                    }
                    if (result.city && result.weather_data) {
                        const weather = result.weather_data;
                        output += `
                            <p><strong>🌍 Location:</strong> ${result.city}, ${result.country || ''}</p>
                            <p><strong>🌡️ Temperature:</strong> ${weather.temperature || 'N/A'}°C</p>
                            <p><strong>☁️ Conditions:</strong> ${weather.description || 'N/A'}</p>
                            <p><strong>💧 Humidity:</strong> ${weather.humidity || 'N/A'}%</p>
                            <p><strong>💨 Wind:</strong> ${weather.wind_speed || 'N/A'} m/s</p>
                        `;
                    }
                    if (result.total_documents) {
                        output += `<p><strong>📄 Documents Processed:</strong> ${result.total_documents}</p>`;
                        if (result.authors_found && result.authors_found.length > 0) {
                            output += `<p><strong>👤 Authors:</strong> ${result.authors_found.join(', ')}</p>`;
                        }
                    }
                    if (result.message) {
                        output += `<p><strong>💬 Message:</strong> ${result.message}</p>`;
                    }
                } else {
                    output += `<p><strong>🚨 Error:</strong> ${result.message || 'Unknown error'}</p>`;
                    if (result.available_agents) {
                        output += `<p><strong>🤖 Available Agents:</strong> ${result.available_agents.join(', ')}</p>`;
                    }
                }

                output += `
                        <p><strong>💾 MongoDB:</strong> ${result.stored_in_mongodb ? '✅ Stored' : '❌ Not Stored'}</p>
                        <p><strong>🕐 Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    </div>
                `;

                document.getElementById('output').innerHTML = output;
            }

            function displayError(query, error) {
                document.getElementById('output').innerHTML = `
                    <div class="result result-error">
                        <h3>📤 Query: ${query}</h3>
                        <p><strong>🚨 Error:</strong> ${error.message || 'Connection failed'}</p>
                        <p><strong>💡 Suggestion:</strong> Check if the server is running and try again.</p>
                        <p><strong>🕐 Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    </div>
                `;
            }

            function clearOutput() {
                document.getElementById('output').innerHTML = `
                    <div class="loading">
                        <p>👋 Output cleared. Ask a new question!</p>
                        <p>Type your query above and click Send Query or press Enter.</p>
                    </div>
                `;
                document.getElementById('queryInput').value = '';
                focusInput();
                showNotification('Output cleared!', 'success');
            }

            function showHistory() {
                if (queryHistory.length === 0) {
                    document.getElementById('output').innerHTML = `
                        <div class="loading">
                            <p>📝 No query history yet.</p>
                            <p>Start asking questions to build your history!</p>
                        </div>
                    `;
                    return;
                }

                let historyHtml = '<h3>📝 Query History</h3><div class="history">';
                queryHistory.slice(0, 10).forEach((item, index) => {
                    const statusIcon = item.result.status === 'success' ? '✅' : '❌';
                    const timeStr = item.timestamp.toLocaleTimeString();
                    historyHtml += `
                        <div class="history-item" onclick="setQuery('${item.query.replace(/'/g, "\\'")}')">
                            <strong>${index + 1}. [${timeStr}] ${statusIcon} ${item.query}</strong>
                            <br><small>Agent: ${item.result.agent_used || 'Unknown'} | Click to reuse query</small>
                        </div>
                    `;
                });
                historyHtml += '</div>';
                historyHtml += '<p style="margin-top: 15px; text-align: center;"><small>💡 Click any history item to reuse that query</small></p>';

                document.getElementById('output').innerHTML = historyHtml;
            }
        </script>
    </body>
    </html>
    """)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Store uploaded documents in memory for chat sessions
uploaded_documents = {}
chat_sessions = {}

@app.post("/api/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file."""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Generate unique file ID
        file_id = f"pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = UPLOAD_DIR / file_id

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process PDF using enhanced PDF reader with LangChain
        try:
            # Import the enhanced PDF reader
            sys.path.insert(0, str(Path(__file__).parent / "data" / "multimodal"))
            from pdf_reader import EnhancedPDFReader

            # Initialize enhanced PDF reader
            pdf_reader = EnhancedPDFReader()

            # Extract text using the enhanced reader
            extracted_text = pdf_reader.extract_text_from_pdf(str(file_path), verbose=False)

            # If LLM is available, also prepare for Q&A
            qa_ready = False
            if pdf_reader.llm:
                try:
                    qa_ready = pdf_reader.load_and_process_pdf(str(file_path), verbose=False)
                    logger.info(f"PDF Q&A preparation: {'Success' if qa_ready else 'Failed'}")
                except Exception as e:
                    logger.warning(f"PDF Q&A preparation failed: {e}")

            # Store the PDF reader instance for later use
            if qa_ready:
                uploaded_documents[file_id + "_reader"] = pdf_reader

            # Store document info
            doc_info = {
                "file_id": file_id,
                "filename": file.filename,
                "file_path": str(file_path),
                "extracted_text": extracted_text,
                "upload_time": datetime.now().isoformat(),
                "file_size": len(content),
                "status": "processed"
            }

            uploaded_documents[file_id] = doc_info

            # Store in MongoDB if available
            if MONGODB_AVAILABLE and mongodb_integration:
                try:
                    await mongodb_integration.store_document(file_id, doc_info)
                except Exception as e:
                    logger.warning(f"Failed to store document in MongoDB: {e}")

            return {
                "status": "success",
                "file_id": file_id,
                "filename": file.filename,
                "text_length": len(extracted_text),
                "message": "PDF uploaded and processed successfully",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to process PDF: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/upload/text")
async def upload_text_document(
    content: str = Form(...),
    filename: str = Form(default="document.txt")
):
    """Upload text content as a document."""
    try:
        # Generate unique file ID
        file_id = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"

        # Store document info
        doc_info = {
            "file_id": file_id,
            "filename": filename,
            "extracted_text": content,
            "upload_time": datetime.now().isoformat(),
            "file_size": len(content),
            "status": "processed",
            "type": "text"
        }

        uploaded_documents[file_id] = doc_info

        # Store in MongoDB if available
        if MONGODB_AVAILABLE and mongodb_integration:
            try:
                await mongodb_integration.store_document(file_id, doc_info)
            except Exception as e:
                logger.warning(f"Failed to store document in MongoDB: {e}")

        return {
            "status": "success",
            "file_id": file_id,
            "filename": filename,
            "text_length": len(content),
            "message": "Text document uploaded successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/chat/pdf")
async def chat_with_pdf(request: PDFChatRequest):
    """Chat with uploaded PDF document using LangChain RAG."""
    try:
        # Get document
        if request.pdf_id and request.pdf_id in uploaded_documents:
            doc_info = uploaded_documents[request.pdf_id]
            document_name = doc_info["filename"]

            # Check if we have a LangChain-enabled PDF reader
            pdf_reader_key = request.pdf_id + "_reader"
            if pdf_reader_key in uploaded_documents:
                pdf_reader = uploaded_documents[pdf_reader_key]

                # Use LangChain RAG for intelligent Q&A
                try:
                    logger.info(f"Using LangChain RAG for question: {request.question}")
                    answer = pdf_reader.ask_question(request.question, verbose=False)

                    # Get document summary if available
                    summary = ""
                    try:
                        summary = pdf_reader.get_document_summary(max_length=150)
                    except:
                        pass

                    result = {
                        "status": "success",
                        "agent_used": "langchain_pdf_qa",
                        "answer": answer,
                        "document_summary": summary,
                        "pdf_id": request.pdf_id,
                        "pdf_filename": document_name,
                        "question": request.question,
                        "chat_type": "pdf_langchain",
                        "llm_powered": True,
                        "rag_enabled": True,
                        "timestamp": datetime.now().isoformat()
                    }

                    logger.info(f"LangChain RAG response generated successfully")

                except Exception as e:
                    logger.error(f"LangChain RAG failed: {e}")
                    # Fallback to basic text processing
                    result = await _fallback_pdf_chat(request, doc_info, document_name)
                    result["fallback_reason"] = f"LangChain error: {str(e)}"
            else:
                # Fallback to basic text processing
                logger.info("No LangChain reader available, using fallback method")
                result = await _fallback_pdf_chat(request, doc_info, document_name)
                result["fallback_reason"] = "LangChain not available"
        else:
            return {
                "status": "error",
                "message": "PDF not found. Please upload a PDF first.",
                "timestamp": datetime.now().isoformat()
            }

        # Store chat session
        if request.session_id:
            if request.session_id not in chat_sessions:
                chat_sessions[request.session_id] = []
            chat_sessions[request.session_id].append({
                "question": request.question,
                "answer": result,
                "timestamp": datetime.now().isoformat(),
                "pdf_id": request.pdf_id
            })

        return result

    except Exception as e:
        logger.error(f"PDF chat error: {e}")
        return {
            "status": "error",
            "message": f"Chat failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def _fallback_pdf_chat(request: PDFChatRequest, doc_info: dict, document_name: str):
    """Fallback PDF chat method with intelligent chunking."""
    document_text = doc_info["extracted_text"]

    # Intelligent chunking for large documents
    max_content_length = 3000  # Safe limit for processing

    if len(document_text) > max_content_length:
        # Smart chunking - find relevant content based on question
        question_lower = request.question.lower()

        # Split document into paragraphs
        paragraphs = document_text.split('\n\n')

        # Score paragraphs based on question relevance
        relevant_paragraphs = []
        for para in paragraphs:
            if len(para.strip()) > 50:  # Skip very short paragraphs
                # Simple relevance scoring
                para_lower = para.lower()
                score = 0
                for word in question_lower.split():
                    if len(word) > 3:  # Skip short words
                        score += para_lower.count(word)

                if score > 0 or len(relevant_paragraphs) < 3:  # Keep at least 3 paragraphs
                    relevant_paragraphs.append((score, para))

        # Sort by relevance and take top paragraphs
        relevant_paragraphs.sort(key=lambda x: x[0], reverse=True)

        # Combine relevant content
        selected_content = ""
        current_length = 0

        for score, para in relevant_paragraphs:
            if current_length + len(para) <= max_content_length:
                selected_content += para + "\n\n"
                current_length += len(para)
            else:
                break

        # If no relevant content found, use beginning of document
        if not selected_content.strip():
            selected_content = document_text[:max_content_length]
            selected_content += "\n\n[Document excerpt - showing most relevant portions]"
        else:
            selected_content += "[Showing most relevant sections from the document]"

        document_content = selected_content
    else:
        document_content = document_text

    # Create enhanced query with optimized content
    enhanced_query = f"""
    Based on the uploaded PDF document '{document_name}', please answer this question:

    Question: {request.question}

    Document content:
    {document_content}

    Please provide a detailed answer based on the document content.
    """

    # Process through document agent directly (bypass routing)
    result = await process_with_document_agent(enhanced_query)

    # Add PDF-specific information
    result["pdf_id"] = request.pdf_id
    result["pdf_filename"] = document_name
    result["question"] = request.question
    result["chat_type"] = "pdf_fallback"
    result["llm_powered"] = False
    result["rag_enabled"] = False
    result["content_chunked"] = len(document_text) > max_content_length

    return result

@app.post("/api/chat/document")
async def chat_with_document(request: DocumentChatRequest):
    """Chat with text document content using LangChain RAG."""
    try:
        # Try to use LangChain for better document processing
        try:
            # Import the enhanced PDF reader for text processing
            sys.path.insert(0, str(Path(__file__).parent / "data" / "multimodal"))
            from pdf_reader import EnhancedPDFReader

            # Initialize enhanced PDF reader
            pdf_reader = EnhancedPDFReader()

            if pdf_reader.llm and len(request.document_content) > 500:
                # Use LangChain for longer documents
                logger.info(f"Using LangChain for document chat: {request.question}")

                # Create a temporary document for processing
                temp_doc_id = f"temp_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # Process document with LangChain
                success = pdf_reader.load_and_process_text(
                    request.document_content,
                    document_name=request.document_name
                )

                if success:
                    # Ask question using LangChain RAG
                    answer = pdf_reader.ask_question(request.question, verbose=False)

                    # Get document summary
                    summary = ""
                    try:
                        summary = pdf_reader.get_document_summary(max_length=150)
                    except:
                        pass

                    result = {
                        "status": "success",
                        "agent_used": "langchain_document_qa",
                        "answer": answer,
                        "document_summary": summary,
                        "document_name": request.document_name,
                        "question": request.question,
                        "chat_type": "document_langchain",
                        "llm_powered": True,
                        "rag_enabled": True,
                        "timestamp": datetime.now().isoformat()
                    }

                    logger.info(f"LangChain document processing successful")

                else:
                    raise Exception("LangChain document processing failed")

            else:
                raise Exception("LangChain not available or document too short")

        except Exception as e:
            logger.warning(f"LangChain document processing failed: {e}")
            # Fallback to basic processing with chunking
            result = await _fallback_document_chat(request)
            result["fallback_reason"] = f"LangChain error: {str(e)}"

        # Store chat session
        if request.session_id:
            if request.session_id not in chat_sessions:
                chat_sessions[request.session_id] = []
            chat_sessions[request.session_id].append({
                "question": request.question,
                "answer": result,
                "timestamp": datetime.now().isoformat(),
                "document_name": request.document_name
            })

        return result

    except Exception as e:
        logger.error(f"Document chat error: {e}")
        return {
            "status": "error",
            "message": f"Chat failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def _fallback_document_chat(request: DocumentChatRequest):
    """Fallback document chat method with intelligent content chunking."""
    # Improved chunking based on token estimation
    max_content_length = 4000  # Increased limit for better context
    document_content = request.document_content

    if len(document_content) > max_content_length:
        # Intelligent truncation - try to keep complete sentences
        truncated_content = document_content[:max_content_length]

        # Find the last complete sentence
        last_period = truncated_content.rfind('. ')
        last_newline = truncated_content.rfind('\n')

        # Use the better breakpoint
        if last_period > max_content_length * 0.8:  # If we can keep 80% and end with sentence
            document_content = truncated_content[:last_period + 1]
        elif last_newline > max_content_length * 0.8:  # If we can keep 80% and end with paragraph
            document_content = truncated_content[:last_newline]
        else:
            document_content = truncated_content

        document_content += "\n\n[Document truncated for processing - showing first portion]"

    # Create enhanced query with document context
    enhanced_query = f"""
    Based on the document '{request.document_name}', please answer this question:

    Question: {request.question}

    Document content:
    {document_content}

    Please provide a detailed answer based on the document content.
    """

    # Process through document agent directly (bypass routing)
    result = await process_with_document_agent(enhanced_query)

    # Add document-specific information
    result["document_name"] = request.document_name
    result["question"] = request.question
    result["chat_type"] = "document_fallback"
    result["llm_powered"] = False
    result["rag_enabled"] = False
    result["content_truncated"] = len(request.document_content) > max_content_length

    return result

@app.get("/api/documents")
async def list_uploaded_documents():
    """List all uploaded documents."""
    try:
        documents = []
        for file_id, doc_info in uploaded_documents.items():
            documents.append({
                "file_id": file_id,
                "filename": doc_info["filename"],
                "upload_time": doc_info["upload_time"],
                "file_size": doc_info["file_size"],
                "text_length": len(doc_info["extracted_text"]),
                "status": doc_info["status"],
                "type": doc_info.get("type", "pdf")
            })

        return {
            "status": "success",
            "documents": documents,
            "total": len(documents),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list documents: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session history."""
    try:
        if session_id in chat_sessions:
            return {
                "status": "success",
                "session_id": session_id,
                "chat_history": chat_sessions[session_id],
                "total_messages": len(chat_sessions[session_id]),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Chat session not found",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get chat session: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def process_command_with_agents(command: str):
    """Process command using the existing agent system."""
    # Use the existing command processing logic
    request = MCPCommandRequest(command=command)
    return await process_command(request)

async def process_with_document_agent(command: str):
    """Process command directly with document agent, bypassing routing."""
    try:
        # Find document agent
        document_agent = None
        agent_id = "document_agent"

        if agent_id in agent_manager.loaded_agents:
            document_agent = agent_manager.loaded_agents[agent_id]["instance"]
        else:
            # Fallback to any available agent
            if agent_manager.loaded_agents:
                agent_id = list(agent_manager.loaded_agents.keys())[0]
                document_agent = agent_manager.loaded_agents[agent_id]["instance"]
            else:
                return {
                    "status": "error",
                    "message": "No document agent available",
                    "timestamp": datetime.now().isoformat()
                }

        # Create message for document agent
        from agents.base_agent import MCPMessage
        message = MCPMessage(
            id=f"{agent_id}_{datetime.now().timestamp()}",
            method="process",
            params={"query": command, "expression": command},
            timestamp=datetime.now()
        )

        # Process with document agent
        result = await document_agent.process_message(message)

        # Add metadata
        result["agent_used"] = agent_id
        result["server"] = "production_mcp_server"
        result["timestamp"] = datetime.now().isoformat()
        result["routing_method"] = "direct_document_agent"

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": f"Document agent processing failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
