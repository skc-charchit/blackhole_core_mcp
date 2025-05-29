#!/usr/bin/env python3
"""
Simple MCP Server - Working version with direct agent integration
"""

import os
import sys
import logging
import asyncio
import importlib.util
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("simple_mcp_server")

# FastAPI app
app = FastAPI(
    title="Simple MCP Server",
    description="Simplified Model Context Protocol Server",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class MCPCommandRequest(BaseModel):
    command: str

# Global state
loaded_agents = {}
server_ready = False

# Agent configurations
AGENT_CONFIGS = {
    "math_agent": {
        "path": "agents/specialized/math_agent.py",
        "class_name": "MathAgent",
        "keywords": ["calculate", "compute", "math", "+", "-", "*", "/", "%", "percent"]
    },
    "document_agent": {
        "path": "agents/core/document_processor.py", 
        "class_name": "DocumentProcessorAgent",
        "keywords": ["analyze", "document", "text", "process"]
    },
    "gmail_agent": {
        "path": "agents/communication/real_gmail_agent.py",
        "class_name": "RealGmailAgent", 
        "keywords": ["email", "send", "mail", "@"]
    },
    "calendar_agent": {
        "path": "agents/specialized/calendar_agent.py",
        "class_name": "CalendarAgent",
        "keywords": ["remind", "reminder", "schedule", "calendar", "meeting"]
    },
    "weather_agent": {
        "path": "agents/data/realtime_weather_agent.py",
        "class_name": "RealTimeWeatherAgent",
        "keywords": ["weather", "temperature", "temp", "forecast", "climate"]
    }
}

async def load_agent(agent_id: str, config: Dict) -> Optional[Any]:
    """Load a single agent safely."""
    try:
        agent_path = Path(config["path"])
        
        if not agent_path.exists():
            logger.warning(f"Agent file not found: {agent_path}")
            return None
        
        # Dynamic import
        spec = importlib.util.spec_from_file_location(agent_id, agent_path)
        if spec is None or spec.loader is None:
            logger.error(f"Could not load spec for {agent_id}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[agent_id] = module
        spec.loader.exec_module(module)
        
        # Get agent class
        agent_class = getattr(module, config["class_name"], None)
        if agent_class is None:
            logger.error(f"Class {config['class_name']} not found in {agent_id}")
            return None
        
        # Create instance
        agent_instance = agent_class()
        logger.info(f"✅ Loaded agent: {agent_id}")
        return agent_instance
        
    except Exception as e:
        logger.error(f"❌ Failed to load {agent_id}: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    global loaded_agents, server_ready
    
    try:
        logger.info("🚀 Starting Simple MCP Server...")
        
        # Load agents
        for agent_id, config in AGENT_CONFIGS.items():
            logger.info(f"Loading {agent_id}...")
            agent = await load_agent(agent_id, config)
            
            if agent:
                loaded_agents[agent_id] = {
                    "instance": agent,
                    "config": config,
                    "status": "loaded"
                }
            else:
                logger.warning(f"Failed to load {agent_id}")
        
        logger.info(f"✅ Loaded {len(loaded_agents)} agents: {list(loaded_agents.keys())}")
        server_ready = True
        logger.info("🎉 Simple MCP Server started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "server": "simple_mcp_server",
        "ready": server_ready,
        "agents_loaded": len(loaded_agents),
        "available_agents": list(loaded_agents.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", response_class=HTMLResponse)
async def serve_interface():
    """Serve the main interface."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple MCP Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
            h1 { text-align: center; margin-bottom: 20px; }
            .feature { background: rgba(255,255,255,0.1); padding: 15px; margin: 10px 0; border-radius: 8px; }
            .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Simple MCP Server</h1>
            <p style="text-align: center; font-size: 1.2em;">Simplified Model Context Protocol Server</p>

            <div class="feature">
                <h3>🔢 Math Agent</h3>
                <p>Calculate 20% of 500</p>
            </div>

            <div class="feature">
                <h3>📄 Document Agent</h3>
                <p>Analyze this text: Hello world</p>
            </div>

            <div class="feature">
                <h3>📧 Gmail Agent</h3>
                <p>Send email to test@example.com</p>
            </div>

            <div class="feature">
                <h3>📅 Calendar Agent</h3>
                <p>Create reminder for tomorrow</p>
            </div>

            <div class="feature">
                <h3>🌤️ Weather Agent</h3>
                <p>What is the weather in Mumbai?</p>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <a href="/docs" class="btn">📚 API Documentation</a>
                <a href="/api/health" class="btn">🔍 Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/api/mcp/command")
async def process_command(request: MCPCommandRequest):
    """Process MCP commands."""
    if not server_ready:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    try:
        command = request.command.lower().strip()
        logger.info(f"Processing command: {command}")
        
        # Find matching agent
        matching_agent = None
        agent_id = None
        
        for aid, agent_data in loaded_agents.items():
            keywords = agent_data["config"]["keywords"]
            if any(keyword in command for keyword in keywords):
                matching_agent = agent_data["instance"]
                agent_id = aid
                break
        
        if not matching_agent:
            return {
                "status": "success",
                "message": f"Command processed but no specific agent matched",
                "command": request.command,
                "available_agents": list(loaded_agents.keys()),
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
        
        # Add server metadata
        result["agent_used"] = agent_id
        result["server"] = "simple_mcp_server"
        result["timestamp"] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return {
            "status": "error",
            "message": f"Command processing failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/agents")
async def list_agents():
    """List all loaded agents."""
    return {
        "status": "success",
        "agents": {
            agent_id: {
                "status": agent_data["status"],
                "class_name": agent_data["config"]["class_name"],
                "keywords": agent_data["config"]["keywords"]
            }
            for agent_id, agent_data in loaded_agents.items()
        },
        "total_agents": len(loaded_agents),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Simple MCP Server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("🔍 Health check at: http://localhost:8000/api/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
