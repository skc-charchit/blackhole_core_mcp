import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Type
from datetime import datetime, timezone
import uvicorn

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import your agents here
from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
from blackhole_core.agents.live_data_agent import LiveDataAgent

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
    "LiveDataAgent": LiveDataAgent
}

# Home route
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI MCP Adapter is running successfully with multi-agent support!"}

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
        "timestamp": str(datetime.now(timezone.utc))
    }

    return response

# Run with uvicorn if executed directly
if __name__ == "__main__":
    uvicorn.run("data.api.mcp_adapter:app", host="127.0.0.1", port=8000, reload=True)
