"""
Main API server for the Blackhole Core MCP project.
This serves as the entry point for the backend using FastAPI.
"""

import os
import sys
import json
import logging
from typing import Dict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from bson import ObjectId

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import textract
    HAS_TEXTRACT = True
    logger.info("textract library is available")
except ImportError:
    HAS_TEXTRACT = False
    logger.warning("textract library not installed. Some document types may not be processed correctly.")

# Add project root to sys.path
# For Netlify deployment, we need to add the lib directory to sys.path
netlify_lib_path = os.path.join(os.path.dirname(__file__), 'lib')
if os.path.exists(netlify_lib_path):
    sys.path.append(netlify_lib_path)
    logger.info(f"Added Netlify lib path to sys.path: {netlify_lib_path}")

# Also add the current directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
logger.info(f"Added current directory to sys.path: {os.path.abspath(os.path.dirname(__file__))}")

# Import project modules
try:
    from blackhole_core.data_source.mongodb import get_agent_outputs_collection, test_connection
    from data.multimodal.image_ocr import extract_text_from_image
    from data.multimodal.pdf_reader import extract_text_from_pdf
    from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
    from blackhole_core.agents.live_data_agent import LiveDataAgent
    logger.info("Successfully imported project modules")
except ImportError as e:
    logger.error(f"Error importing project modules: {e}")
    # Create mock functions for testing
    def get_agent_outputs_collection():
        return None
    
    def test_connection():
        return False
    
    def extract_text_from_image(*args, **kwargs):
        return "Image text extraction not available"
    
    def extract_text_from_pdf(*args, **kwargs):
        return "PDF text extraction not available"
    
    class ArchiveSearchAgent:
        def __init__(self, *args, **kwargs):
            pass
        
        def plan(self, query):
            return {"error": "ArchiveSearchAgent not available", "query": query}
    
    class LiveDataAgent:
        def __init__(self, *args, **kwargs):
            pass
        
        def plan(self, query):
            return {"error": "LiveDataAgent not available", "query": query}

# Load environment variables
load_dotenv()

# Custom JSON encoder to handle MongoDB ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Initialize FastAPI app
app = FastAPI(
    title="Blackhole Core MCP API",
    description="FastAPI-powered multi-agent adapter for Blackhole Core.",
    version="2.0"
)

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', '*')
if cors_origins == '*':
    # Allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Allow specific origins
    origins = cors_origins.split(',')
    logger.info(f"CORS origins: {origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Configure upload folder
UPLOAD_FOLDER = os.getenv('UPLOAD_DIR', 'uploads')
logger.info(f"Using upload folder: {UPLOAD_FOLDER}")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Request schemas
class TaskRequest(BaseModel):
    agent: str
    input: str

class SearchRequest(BaseModel):
    query: str

# Helper functions
def save_to_mongodb(result: Dict) -> Dict:
    """Save a result to MongoDB and return the updated result."""
    try:
        collection = get_agent_outputs_collection()
        if collection and isinstance(result, dict):
            # Make a copy of the result to avoid modifying the original
            result_copy = result.copy()
            # Remove _id if exists
            result_copy.pop("_id", None)
            # Insert into MongoDB
            insert_result = collection.insert_one(result_copy)
            # Convert ObjectId to string
            result_copy["_id"] = str(insert_result.inserted_id)
            # Update the result with the copy
            result = result_copy
            logger.info("Result saved to MongoDB")
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}")
    
    return result

# Routes
@app.get("/")
async def read_root():
    """Root endpoint."""
    return {"message": "Blackhole Core MCP API is running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    # Test MongoDB connection
    mongo_connected = False
    mongo_error = None
    try:
        mongo_connected = test_connection()
    except Exception as e:
        mongo_connected = False
        mongo_error = str(e)

    return {
        'status': 'ok',
        'mongodb': 'connected' if mongo_connected else 'disconnected',
        'mongodb_error': mongo_error,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/test")
async def api_test():
    """Test API endpoint."""
    return {
        'message': 'API is working!',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/weather")
async def get_weather(location: str = Query("London")):
    """Get weather data for a location."""
    try:
        # Process with LiveDataAgent
        agent = LiveDataAgent(memory=[], api_url=f"https://wttr.in/{location}?format=j1")
        result = agent.plan({"query": f"{location} weather"})

        # Save result to MongoDB
        result = save_to_mongodb(result)

        return result
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_archive_post(request: SearchRequest):
    """Search the archive with text query (POST method)."""
    return await _search_archive(request.query)

@app.get("/api/search-archive")
async def search_archive_get(query: str = Query(...)):
    """Search the archive with text query (GET method)."""
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    return await _search_archive(query)

async def _search_archive(query: str):
    """Common function for searching the archive."""
    try:
        # Process with ArchiveSearchAgent
        agent = ArchiveSearchAgent()
        result = agent.plan({"document_text": query})

        # Save result to MongoDB
        result = save_to_mongodb(result)

        return result
    except Exception as e:
        logger.error(f"Error searching archive: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_task")
async def run_task(request: TaskRequest):
    """Run a task with the specified agent."""
    agent_name = request.agent
    task_input = request.input

    # Available agent mappings
    available_agents = {
        "ArchiveSearchAgent": ArchiveSearchAgent,
        "LiveDataAgent": LiveDataAgent
    }

    # Validate agent existence
    if agent_name not in available_agents:
        raise HTTPException(status_code=400, detail=f"❌ Unknown agent '{agent_name}' specified.")

    # Initialize and run agent
    agent_class = available_agents[agent_name]
    agent = agent_class()
    result = agent.plan({"document_text": task_input})

    # Save result to MongoDB
    result = save_to_mongodb(result)

    response = {
        "agent": agent_name,
        "input": {"document_text": task_input},
        "output": result,
        "timestamp": str(datetime.now(timezone.utc))
    }

    return response
