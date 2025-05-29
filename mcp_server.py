#!/usr/bin/env python3
"""
Production MCP Server - Model Context Protocol with Live Data Integration
Real-time weather, document processing, and email automation
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import MCP components
from agents.agent_loader import MCPAgentLoader
from mcp_mongodb_integration import MCPMongoDBIntegration
from mcp_workflow_engine import MCPWorkflowEngine

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger = logging.getLogger("mcp_server")

# FastAPI app
app = FastAPI(
    title="MCP Production Server",
    description="Model Context Protocol with Live Data Integration",
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

class MCPDocument(BaseModel):
    filename: str
    content: str
    type: str = "text"

class MCPAnalyzeRequest(BaseModel):
    documents: List[MCPDocument]
    query: str
    rag_mode: bool = True

# Global state
server_initialized = False
agent_loader = None
mongodb_integration = None
workflow_engine = None

@app.on_event("startup")
async def startup_event():
    """Initialize MCP server on startup."""
    global server_initialized, agent_loader, mongodb_integration, workflow_engine

    try:
        logger.info("Starting MCP Production Server...")

        # Initialize agent loader
        logger.info("Loading agents...")
        agent_loader = MCPAgentLoader()
        loaded_agents = agent_loader.load_all_agents()
        logger.info(f"Loaded {len(loaded_agents)} agents: {list(loaded_agents.keys())}")

        # Initialize MongoDB integration
        logger.info("Initializing MongoDB integration...")
        mongodb_integration = MCPMongoDBIntegration()
        if await mongodb_integration.connect():
            logger.info("MongoDB integration connected successfully")
        else:
            logger.warning("MongoDB integration failed to connect")
            mongodb_integration = None

        # Initialize workflow engine
        logger.info("Initializing workflow engine...")
        workflow_engine = MCPWorkflowEngine(mongodb_integration)
        logger.info("Workflow engine initialized successfully")

        server_initialized = True
        logger.info("MCP Production Server started successfully")

    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "mcp_server": "running",
        "agents_loaded": len(agent_loader.loaded_agents) if agent_loader else 0,
        "mongodb_connected": mongodb_integration is not None,
        "workflow_engine": workflow_engine is not None,
        "timestamp": datetime.now().isoformat()
    }

# Main interface
@app.get("/", response_class=HTMLResponse)
async def serve_interface():
    """Serve the main interface."""
    try:
        if os.path.exists("mcp_realtime_interface.html"):
            return FileResponse("mcp_realtime_interface.html")
        else:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>MCP Production Server</title>
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
                    <h1>🤖 MCP Production Server</h1>
                    <p style="text-align: center; font-size: 1.2em;">Model Context Protocol with Live Data Integration</p>

                    <div class="feature">
                        <h3>🌤️ Real-Time Weather</h3>
                        <p>Ask: "What is the weather in Mumbai?" - Get live weather data from OpenWeatherMap</p>
                    </div>

                    <div class="feature">
                        <h3>📄 Document Processing</h3>
                        <p>Upload PDFs and ask: "Extract important points and email them to manager@company.com"</p>
                    </div>

                    <div class="feature">
                        <h3>🤖 Automated Workflows</h3>
                        <p>Complex multi-step automation with natural language commands</p>
                    </div>

                    <div style="text-align: center; margin-top: 30px;">
                        <a href="/docs" class="btn">📚 API Documentation</a>
                        <a href="/api/health" class="btn">🔍 Health Check</a>
                    </div>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error serving interface: {e}")
        return HTMLResponse(f"<h1>Error loading interface: {e}</h1>")

# Command processing endpoint
@app.post("/api/mcp/command")
async def process_command(request: MCPCommandRequest):
    """Process MCP commands."""
    if not server_initialized:
        raise HTTPException(status_code=503, detail="Server not initialized")

    try:
        command = request.command.lower().strip()
        logger.info(f"Processing command: {command}")

        # Check for mathematical queries
        math_keywords = ['calculate', 'compute', 'what is', 'solve', 'math', '+', '-', '*', '/', '%', 'percent']
        if any(keyword in command for keyword in math_keywords):
            # Process with math agent
            if "math_agent" in agent_loader.loaded_agents:
                try:
                    math_agent_data = agent_loader.loaded_agents["math_agent"]
                    math_agent = math_agent_data["agent"]

                    from agents.base_agent import MCPMessage
                    math_message = MCPMessage(
                        id=f"math_{datetime.now().timestamp()}",
                        method="process",
                        params={"expression": request.command},
                        timestamp=datetime.now()
                    )

                    math_result = await math_agent.process_message(math_message)

                    if math_result.get("status") == "success":
                        return {
                            "status": "success",
                            "message": "Mathematical calculation completed",
                            "math_response": math_result.get("explanation", ""),
                            "result": math_result.get("result", ""),
                            "formatted_result": math_result.get("formatted_result", ""),
                            "expression": math_result.get("expression", request.command),
                            "agent_used": "math_agent",
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "status": "error",
                            "message": math_result.get("message", "Math calculation failed"),
                            "suggestions": math_result.get("suggestions", []),
                            "examples": math_result.get("examples", []),
                            "agent_used": "math_agent",
                            "timestamp": datetime.now().isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error processing math query: {e}")
                    return {
                        "status": "error",
                        "message": f"Math processing failed: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }

        # Check for calendar/reminder queries
        calendar_keywords = ['remind', 'reminder', 'schedule', 'meeting', 'appointment', 'calendar']
        if any(keyword in command for keyword in calendar_keywords):
            # Process with calendar agent
            if "calendar_agent" in agent_loader.loaded_agents:
                try:
                    calendar_agent_data = agent_loader.loaded_agents["calendar_agent"]
                    calendar_agent = calendar_agent_data["agent"]

                    from agents.base_agent import MCPMessage
                    calendar_message = MCPMessage(
                        id=f"calendar_{datetime.now().timestamp()}",
                        method="process",
                        params={"query": request.command},
                        timestamp=datetime.now()
                    )

                    calendar_result = await calendar_agent.process_message(calendar_message)

                    if calendar_result.get("status") == "success":
                        return {
                            "status": "success",
                            "message": "Calendar operation completed",
                            "calendar_response": calendar_result.get("message", ""),
                            "reminder": calendar_result.get("reminder", {}),
                            "event": calendar_result.get("event", {}),
                            "agent_used": "calendar_agent",
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "status": "error",
                            "message": calendar_result.get("message", "Calendar operation failed"),
                            "suggestions": calendar_result.get("suggestions", []),
                            "examples": calendar_result.get("examples", []),
                            "agent_used": "calendar_agent",
                            "timestamp": datetime.now().isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error processing calendar query: {e}")
                    return {
                        "status": "error",
                        "message": f"Calendar processing failed: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }

        # Check if this is a weather query
        weather_keywords = ['weather', 'temperature', 'temp', 'forecast', 'climate']
        if any(keyword in command for keyword in weather_keywords):
            # Process with real-time weather agent
            if "realtime_weather_agent" in agent_loader.loaded_agents:
                try:
                    weather_agent_data = agent_loader.loaded_agents["realtime_weather_agent"]
                    weather_agent = weather_agent_data["agent"]

                    # Create message for weather agent
                    from agents.base_agent import MCPMessage
                    weather_message = MCPMessage(
                        id=f"weather_{datetime.now().timestamp()}",
                        method="process",
                        params={"query": request.command},
                        timestamp=datetime.now()
                    )

                    # Process with weather agent
                    weather_result = await weather_agent.process_message(weather_message)

                    if weather_result.get("status") == "success":
                        return {
                            "status": "success",
                            "message": "Live weather data retrieved successfully",
                            "weather_response": weather_result.get("formatted_response", ""),
                            "city": weather_result.get("city", ""),
                            "country": weather_result.get("country", ""),
                            "weather_data": weather_result.get("weather_data", {}),
                            "data_source": weather_result.get("data_source", "unknown"),
                            "agent_used": "realtime_weather_agent",
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "status": "error",
                            "message": weather_result.get("message", "Weather query failed"),
                            "suggestions": weather_result.get("suggestions", []),
                            "examples": weather_result.get("examples", []),
                            "agent_used": "realtime_weather_agent",
                            "timestamp": datetime.now().isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error processing weather query: {e}")
                    return {
                        "status": "error",
                        "message": f"Weather processing failed: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }

        # Check for email queries
        email_keywords = ['email', 'send', 'mail to', '@']
        if any(keyword in command for keyword in email_keywords):
            # Process with Gmail agent
            if "real_gmail_agent" in agent_loader.loaded_agents:
                try:
                    gmail_agent_data = agent_loader.loaded_agents["real_gmail_agent"]
                    gmail_agent = gmail_agent_data["agent"]

                    # Extract email address and content from command
                    import re
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', request.command)

                    if email_match:
                        to_email = email_match.group(0)

                        # Create email content based on command
                        if "weather" in command:
                            subject = "Weather Alert"
                            content = f"Weather notification as requested: {request.command}"
                            template = "weather_summary"
                        elif "document" in command or "analysis" in command:
                            subject = "Document Analysis"
                            content = f"Document analysis as requested: {request.command}"
                            template = "document_summary"
                        else:
                            subject = "MCP System Notification"
                            content = f"Automated message: {request.command}"
                            template = "general_analysis"

                        from agents.base_agent import MCPMessage
                        email_message = MCPMessage(
                            id=f"email_{datetime.now().timestamp()}",
                            method="send_email",
                            params={
                                "to_email": to_email,
                                "subject": subject,
                                "content": content,
                                "template": template
                            },
                            timestamp=datetime.now()
                        )

                        email_result = await gmail_agent.process_message(email_message)

                        if email_result.get("status") == "success":
                            return {
                                "status": "success",
                                "message": "Email sent successfully",
                                "email_response": email_result.get("message", ""),
                                "to_email": to_email,
                                "subject": subject,
                                "email_sent": email_result.get("email_sent", False),
                                "agent_used": "real_gmail_agent",
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            return {
                                "status": "error",
                                "message": email_result.get("message", "Email sending failed"),
                                "agent_used": "real_gmail_agent",
                                "timestamp": datetime.now().isoformat()
                            }
                    else:
                        return {
                            "status": "error",
                            "message": "No email address found in command",
                            "example": "Try: 'Send email to john@example.com about weather update'",
                            "agent_used": "real_gmail_agent",
                            "timestamp": datetime.now().isoformat()
                        }

                except Exception as e:
                    logger.error(f"Error processing email query: {e}")
                    return {
                        "status": "error",
                        "message": f"Email processing failed: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }

        # Default response for other commands
        return {
            "status": "success",
            "message": f"Command '{request.command}' processed by MCP Production Server",
            "available_agents": list(agent_loader.loaded_agents.keys()),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document analysis endpoint
@app.post("/api/mcp/analyze")
async def analyze_documents(request: MCPAnalyzeRequest):
    """Analyze documents with agents."""
    if not server_initialized:
        raise HTTPException(status_code=503, detail="Server not initialized")

    try:
        logger.info(f"Analyzing {len(request.documents)} documents with query: {request.query}")

        if not request.documents:
            raise HTTPException(status_code=400, detail="No documents provided")

        # Process with document processor if available
        if mongodb_integration:
            results = []
            for doc in request.documents:
                result = await mongodb_integration.process_document_with_agent(
                    doc.filename, doc.content, request.query
                )
                results.append(result)

            successful_results = [r for r in results if r.get("status") == "success"]

            if successful_results:
                comprehensive_answer = f"Processed {len(successful_results)} document(s):\n"
                for i, result in enumerate(successful_results, 1):
                    output = result.get("output", {})
                    comprehensive_answer += f"\n{i}. {result.get('filename', 'Document')}:\n"

                    if "important_points" in output:
                        comprehensive_answer += f"   Important Points: {', '.join(output['important_points'][:3])}\n"
                    if "summary" in output:
                        comprehensive_answer += f"   Summary: {output['summary'][:100]}...\n"

                return {
                    "status": "success",
                    "comprehensive_answer": comprehensive_answer,
                    "results": successful_results,
                    "mongodb_storage": True,
                    "timestamp": datetime.now().isoformat()
                }

        return {
            "status": "error",
            "message": "Document processing not available",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in document analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Workflow execution endpoint
@app.post("/api/mcp/workflow")
async def execute_workflow(request: MCPAnalyzeRequest):
    """Execute automated workflows."""
    if not server_initialized or not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        user_request = request.query
        documents = request.documents

        logger.info(f"Processing workflow request: {user_request}")

        # Parse user request into workflow plan
        workflow_plan = workflow_engine.parse_user_request(user_request, documents)

        if not workflow_plan:
            return {
                "status": "error",
                "message": "Could not understand the request. Please try a simpler format.",
                "examples": [
                    "process weather.pdf and email summary to john@example.com",
                    "analyze document and email important points to manager@company.com",
                    "extract key findings and send to researcher@university.edu"
                ],
                "timestamp": datetime.now().isoformat()
            }

        # Execute the workflow
        workflow_result = await workflow_engine.execute_workflow(workflow_plan)

        if workflow_result["status"] == "success":
            return {
                "status": "success",
                "comprehensive_answer": f"Workflow completed successfully!\n\n"
                                      f"Description: {workflow_result['description']}\n"
                                      f"Execution time: {workflow_result['execution_time']:.3f} seconds\n\n"
                                      f"Results: {workflow_result['final_result'].get('status', 'completed')}",
                "workflow_id": workflow_result["workflow_id"],
                "workflow_description": workflow_result["description"],
                "execution_time": workflow_result["execution_time"],
                "workflow_results": workflow_result["all_results"],
                "mongodb_storage": mongodb_integration is not None,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"Workflow execution failed: {workflow_result.get('error', 'Unknown error')}",
                "workflow_description": workflow_result.get("description", "Unknown workflow"),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error in workflow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agents endpoint
@app.get("/api/mcp/agents")
async def get_agents():
    """Get available agents."""
    if not server_initialized:
        raise HTTPException(status_code=503, detail="Server not initialized")

    try:
        agents_info = {}
        if agent_loader:
            for agent_id, agent_data in agent_loader.loaded_agents.items():
                agents_info[agent_id] = {
                    "name": agent_data.get("name", agent_id),
                    "description": agent_data.get("description", ""),
                    "capabilities": agent_data.get("capabilities", []),
                    "category": agent_data.get("category", "unknown")
                }

        return {
            "status": "success",
            "agents": agents_info,
            "total_agents": len(agents_info),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8000"))

    logger.info(f"Starting MCP Production Server on {host}:{port}")

    uvicorn.run(
        "mcp_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
