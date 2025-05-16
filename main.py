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
from fastapi.responses import FileResponse
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
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from blackhole_core.data_source.mongodb import get_agent_outputs_collection, test_connection
from data.multimodal.image_ocr import extract_text_from_image
from data.multimodal.pdf_reader import extract_text_from_pdf
from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
from blackhole_core.agents.live_data_agent import LiveDataAgent

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

ALLOWED_EXTENSIONS = {
    # Text files
    'txt', 'md', 'rtf', 'csv', 'json', 'xml', 'html', 'htm',
    # Document files
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'odt', 'ods', 'odp',
    # Image files
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg', 'heic', 'heif',
    'raw', 'cr2', 'nef', 'arw', 'dng', 'orf', 'rw2', 'pef', 'srw', 'dcr',  # RAW formats
    'jfif', 'exif', 'ppm', 'pgm', 'pbm', 'pnm', 'ico', 'cur',  # Additional image formats
    # Archive files (for future use)
    'zip', 'rar', '7z', 'tar', 'gz'
}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="public"), name="static")

# Request schemas
class TaskRequest(BaseModel):
    agent: str
    input: str

class SearchRequest(BaseModel):
    query: str

# Helper functions
def allowed_file(filename):
    """
    Check if the file extension is allowed.
    More flexible implementation that allows files without extensions
    and treats them as potentially processable.
    """
    # If no filename, reject
    if not filename:
        return False

    # If no extension, we'll try to process it anyway
    if '.' not in filename:
        logger.warning(f"File {filename} has no extension, will try to process it anyway")
        return True

    # Check if extension is in allowed list
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_EXTENSIONS:
        return True

    # If extension not in allowed list, log warning but still allow
    logger.warning(f"File extension '{ext}' not in allowed list, but will try to process it anyway")
    return True

def save_upload_file(upload_file: UploadFile) -> str:
    """Save an uploaded file to the upload folder."""
    filename = Path(upload_file.filename).name
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as buffer:
        buffer.write(upload_file.file.read())

    return filepath

def save_to_mongodb(result: Dict) -> Dict:
    """Save a result to MongoDB and return the updated result."""
    try:
        collection = get_agent_outputs_collection()
        if isinstance(result, dict):
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
    """Serve the main index page."""
    return FileResponse("public/index.html")

@app.get("/env.js")
async def env_js():
    """Serve the env.js file."""
    return FileResponse("public/env.js")

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

    # Test PDF reader
    pdf_reader_working = False
    pdf_reader_error = None
    try:
        sample_path = os.path.join('data', 'multimodal', 'sample.pdf')
        if os.path.exists(sample_path):
            text = extract_text_from_pdf(sample_path, include_page_numbers=True, verbose=False)
            pdf_reader_working = len(text) > 0
        else:
            pdf_reader_error = f"Sample PDF not found at {sample_path}"
    except Exception as e:
        pdf_reader_working = False
        pdf_reader_error = str(e)

    return {
        'status': 'ok',
        'mongodb': 'connected' if mongo_connected else 'disconnected',
        'mongodb_error': mongo_error,
        'pdf_reader': 'working' if pdf_reader_working else 'not working',
        'pdf_reader_error': pdf_reader_error,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/test-connection")
async def test_connection_route():
    """Simple test endpoint for connection testing."""
    return {
        'message': 'Connection successful!',
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/test")
async def api_test():
    """Test API endpoint."""
    return {
        'message': 'API is working!',
        'pdf_reader_path': os.path.abspath('./data/multimodal/pdf_reader.py') if os.path.exists('./data/multimodal/pdf_reader.py') else 'File not found',
        'timestamp': datetime.now().isoformat()
    }

@app.get("/debug/routes")
async def debug_routes():
    """List all routes."""
    routes = []
    for route in app.routes:
        routes.append({
            'path': route.path,
            'name': route.name,
            'methods': [method for method in route.methods if method != 'OPTIONS' and method != 'HEAD']
        })
    return routes

@app.get("/debug/env")
async def debug_env():
    """Show environment variables (with sensitive info hidden)."""
    # Return environment variables (hide sensitive info)
    mongo_uri = os.environ.get('MONGO_URI', 'not set')
    if 'mongodb+srv://' in mongo_uri:
        # Hide password in the URI
        parts = mongo_uri.split('@')
        if len(parts) > 1:
            auth_part = parts[0].split('://')
            if len(auth_part) > 1:
                user_pass = auth_part[1].split(':')
                if len(user_pass) > 1:
                    # Replace password with asterisks
                    hidden_uri = f"{auth_part[0]}://{user_pass[0]}:******@{parts[1]}"
                    mongo_uri = hidden_uri

    return {
        'MONGO_URI': mongo_uri,
        'CORS_ORIGINS': os.environ.get('CORS_ORIGINS', 'not set'),
        'DEBUG': os.environ.get('DEBUG', 'not set'),
        'PORT': os.environ.get('PORT', 'not set'),
        'MONGO_DB_NAME': os.environ.get('MONGO_DB_NAME', 'not set'),
        'MONGO_COLLECTION_NAME': os.environ.get('MONGO_COLLECTION_NAME', 'not set'),
        'PYTHON_PATH': sys.executable,
        'WORKING_DIR': os.getcwd(),
        'FILES_IN_MULTIMODAL': os.listdir('data/multimodal') if os.path.exists('data/multimodal') else []
    }

@app.post("/api/process-image")
async def process_image(file: UploadFile = File(...)):
    """Process an uploaded image."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if file.filename == '':
        raise HTTPException(status_code=400, detail="No selected file")

    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed")

    filepath = save_upload_file(file)

    try:
        # Extract text from image with enhanced capabilities
        extracted_text = extract_text_from_image(
            filepath,
            debug=True,
            preprocessing_level=2,
            try_multiple_methods=True
        )

        # Check if extraction failed
        if extracted_text and extracted_text.startswith("❌ Error:"):
            logger.warning(f"Image text extraction failed: {extracted_text}")
            # Create a placeholder message
            extracted_text = f"The image '{file.filename}' could not be processed. It may be corrupted or in an unsupported format."

            # Create a placeholder image with error message if needed
            try:
                import cv2
                import numpy as np
                error_img_path = os.path.join(UPLOAD_FOLDER, f"error_{file.filename}.png")
                blank_img = np.ones((300, 500, 3), np.uint8) * 255  # White background
                # Add error text
                cv2.putText(
                    blank_img,
                    "Image could not be processed",
                    (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )
                cv2.imwrite(error_img_path, blank_img)
                logger.info(f"Created error image at {error_img_path}")
            except Exception as e:
                logger.error(f"Error creating placeholder image: {e}")

        # Process with ArchiveSearchAgent
        agent = ArchiveSearchAgent()
        result = agent.plan({"document_text": extracted_text})

        # Save result to MongoDB
        result = save_to_mongodb(result)

        return {
            'filename': file.filename,
            'extracted_text': extracted_text,
            'agent_result': result
        }
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        # Create a friendly error message
        error_message = f"The image '{file.filename}' could not be processed. It may be corrupted or in an unsupported format."

        # Try to create a placeholder result
        try:
            agent = ArchiveSearchAgent()
            result = agent.plan({"document_text": error_message})

            # Save result to MongoDB
            result = save_to_mongodb(result)

            return {
                'filename': file.filename,
                'extracted_text': error_message,
                'agent_result': result,
                'error': str(e)
            }
        except Exception as agent_err:
            logger.error(f"Error creating placeholder result: {agent_err}")
            raise HTTPException(status_code=500, detail=f"{error_message}. Details: {str(e)}")

@app.post("/api/process-document")
async def process_document(file: UploadFile = File(...)):
    """Process any uploaded document (PDF, DOCX, PPTX, etc.)."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if file.filename == '':
        raise HTTPException(status_code=400, detail="No selected file")

    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed")

    filepath = save_upload_file(file)

    try:
        # Determine file type and extract text accordingly
        file_ext = os.path.splitext(file.filename)[1].lower()

        # Image formats
        image_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif', '.heic', '.heif']

        if file_ext == '.pdf':
            # Extract text from PDF with enhanced capabilities
            extracted_text = extract_text_from_pdf(
                filepath,
                include_page_numbers=True,
                verbose=True,
                try_ocr=True
            )
        elif file_ext in image_formats or file_ext == '':  # Handle images and files without extension
            # Try to process as image with enhanced capabilities
            extracted_text = extract_text_from_image(
                filepath,
                debug=True,
                preprocessing_level=2,
                try_multiple_methods=True
            )
        elif file_ext in ['.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']:
            # Extract text from Office documents
            if HAS_TEXTRACT:
                try:
                    extracted_text = textract.process(filepath).decode('utf-8')
                except Exception as e:
                    # If textract fails, try to process as image
                    logger.warning(f"Textract failed for {file.filename}, trying image OCR as fallback")
                    extracted_text = extract_text_from_image(
                        filepath,
                        debug=True,
                        preprocessing_level=2,
                        try_multiple_methods=True
                    )
            else:
                # Try to process as image if textract is not available
                logger.warning(f"Textract not available, trying image OCR as fallback for {file.filename}")
                extracted_text = extract_text_from_image(
                    filepath,
                    debug=True,
                    preprocessing_level=2,
                    try_multiple_methods=True
                )
        elif file_ext in ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm']:
            # Read text files directly
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading text file: {str(e)}")
        else:
            # Try to handle other file types
            if HAS_TEXTRACT:
                try:
                    extracted_text = textract.process(filepath).decode('utf-8')
                except Exception as e:
                    # If textract fails, try to process as image
                    logger.warning(f"Textract failed for {file.filename}, trying image OCR as fallback")
                    extracted_text = extract_text_from_image(
                        filepath,
                        debug=True,
                        preprocessing_level=2,
                        try_multiple_methods=True
                    )
            else:
                # Try to process as image if textract is not available
                logger.warning(f"Textract not available, trying image OCR as fallback for {file.filename}")
                extracted_text = extract_text_from_image(
                    filepath,
                    debug=True,
                    preprocessing_level=2,
                    try_multiple_methods=True
                )

        # Process with ArchiveSearchAgent
        agent = ArchiveSearchAgent()
        result = agent.plan({"document_text": extracted_text})

        # Save result to MongoDB
        result = save_to_mongodb(result)

        return {
            'filename': file.filename,
            'extracted_text': extracted_text,
            'agent_result': result
        }
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    """Process an uploaded PDF (redirects to process-document)."""
    return await process_document(file)

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

@app.get("/api/results")
async def get_results():
    """Get all results from MongoDB."""
    try:
        collection = get_agent_outputs_collection()
        results = list(collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(100))

        # Convert results to JSON-serializable format
        for result in results:
            if 'timestamp' in result:
                result['timestamp'] = str(result['timestamp'])

        return results
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Original MCP Adapter route
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

# Run the application
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=debug)
