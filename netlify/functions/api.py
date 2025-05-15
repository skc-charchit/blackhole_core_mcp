import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Type
from datetime import datetime
from mangum import Mangum

# Import your agents here - adjust imports as needed for Netlify
try:
    from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
except ImportError:
    # Mock class for when running on Netlify without full dependencies
    class ArchiveSearchAgent:
        def __init__(self, memory=None, source=None):
            self.memory = memory
            self.source = source

        def plan(self, query):
            return {
                "agent": "ArchiveSearchAgent",
                "input": query,
                "output": "This is a mock response from the Netlify deployment",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"deployment": "netlify"}
            }

# FastAPI app instance
app = FastAPI(
    title="MCP Adapter API",
    description="FastAPI-powered multi-agent adapter for Blackhole Core.",
    version="2.0"
)

# Request schema
class TaskRequest(BaseModel):
    agent: str
    input: str

# Available agent mappings
available_agents: Dict[str, Type] = {
    "ArchiveSearchAgent": ArchiveSearchAgent,
}

# Home route
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI MCP Adapter is running successfully on Netlify!"}

# POST route to run the agent task
@app.post("/run_task")
def run_task(request: TaskRequest) -> Dict[str, Any]:
    agent_name = request.agent
    task_input = request.input

    # Validate agent existence
    if agent_name not in available_agents:
        raise HTTPException(status_code=400, detail=f"❌ Unknown agent '{agent_name}' specified.")

    # Initialize and run agent
    agent_class = available_agents[agent_name]
    agent = agent_class()
    result = agent.plan({"document_text": task_input})

    response = {
        "agent": agent_name,
        "input": {"document_text": task_input},
        "output": result,
        "timestamp": str(datetime.utcnow()),
        "deployment": "netlify"
    }

    return response

# Create handler for AWS Lambda / Netlify Functions
handler = Mangum(app)
