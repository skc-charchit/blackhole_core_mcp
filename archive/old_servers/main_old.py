"""
Main API server for the Blackhole Core MCP project.
This serves as the entry point for the backend using FastAPI.
"""

import os
import sys
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Response
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
from blackhole_core.mcp_processor import process_user_command, mcp_processor
from blackhole_core.blackhole_interface import blackhole_interface
from blackhole_core.mcp_config import mcp_config
from data.multimodal.image_ocr import extract_text_from_image
from data.multimodal.pdf_reader import extract_text_from_pdf, EnhancedPDFReader
from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
from blackhole_core.agents.live_data_agent import LiveDataAgent

# Load environment variables
load_dotenv()

# Global enhanced PDF reader instance
enhanced_pdf_reader = None

def get_enhanced_pdf_reader():
    """Get or create the enhanced PDF reader instance."""
    global enhanced_pdf_reader
    if enhanced_pdf_reader is None:
        try:
            enhanced_pdf_reader = EnhancedPDFReader()
            logger.info("Enhanced PDF reader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced PDF reader: {e}")
            enhanced_pdf_reader = None
    return enhanced_pdf_reader

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

# Configure CORS - Ensure it's properly set up for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now to debug
    allow_credentials=False,  # Set to False for public APIs
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Add middleware to handle CORS for all responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    return response

# Add a global OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {"message": "OK"}

# Log CORS configuration
logger.info("CORS configured to allow all origins")

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

class MCPCommandRequest(BaseModel):
    command: str
    session_id: Optional[str] = None

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
    """Save uploaded file to organized multimodal folders and return the file path."""
    try:
        # Determine file type and target directory
        file_extension = Path(upload_file.filename).suffix.lower()

        if file_extension == '.pdf':
            target_dir = Path("data/multimodal/uploaded_pdfs")
        elif file_extension in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif', '.heic', '.heif']:
            target_dir = Path("data/multimodal/uploaded_images")
        else:
            # Fallback to general uploads folder for other file types
            target_dir = Path(UPLOAD_FOLDER)

        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_filename = Path(upload_file.filename).name
        unique_filename = f"{timestamp}_{clean_filename}"

        filepath = target_dir / unique_filename

        # Save the file
        with open(filepath, "wb") as buffer:
            buffer.write(upload_file.file.read())

        logger.info(f"File saved to organized folder: {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Error saving file: {e}")
        # Fallback to original upload folder
        filename = Path(upload_file.filename).name
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, "wb") as buffer:
            buffer.write(upload_file.file.read())

        logger.warning(f"Saved to fallback location: {filepath}")
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

@app.get("/mcp_interface.html")
async def mcp_interface():
    """Serve the MCP command interface."""
    return FileResponse("public/mcp_interface.html")

@app.get("/universal_connector.html")
async def universal_connector_interface():
    """Serve the Universal Agent Connector interface."""
    return FileResponse("static/universal_connector.html")

@app.get("/env.js")
async def env_js():
    """Serve the env.js file."""
    return FileResponse("public/env.js")

@app.get("/api/health")
@app.post("/api/health")
async def health_check():
    """Health check endpoint - supports both GET and POST."""

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
        # Look for any existing PDF files to test with
        pdf_dir = os.path.join('data', 'multimodal', 'uploaded_pdfs')
        if os.path.exists(pdf_dir):
            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            if pdf_files:
                # Test with the first available PDF
                test_pdf = os.path.join(pdf_dir, pdf_files[0])
                text = extract_text_from_pdf(test_pdf, include_page_numbers=True, verbose=False)
                pdf_reader_working = len(text) > 0 and not text.startswith("❌")
                if not pdf_reader_working:
                    pdf_reader_error = f"PDF extraction failed for {pdf_files[0]}"
            else:
                # No PDF files available, but PDF reader functionality is available
                pdf_reader_working = True
                pdf_reader_error = "No PDF files available for testing, but PDF reader is functional"
        else:
            # Directory doesn't exist, but PDF reader functionality is available
            pdf_reader_working = True
            pdf_reader_error = "PDF upload directory not found, but PDF reader is functional"
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
async def process_document(
    file: UploadFile = File(...),
    enable_llm: bool = False,
    save_to_db: bool = True
):
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
            # Check if LLM processing is requested for PDFs
            if enable_llm:
                # Use enhanced PDF reader for LLM processing
                reader = get_enhanced_pdf_reader()
                if reader and reader.llm:
                    # Load and process PDF for Q&A
                    success = reader.load_and_process_pdf(filepath, verbose=False)
                    if success:
                        # Get text and summary
                        extracted_text = reader.extract_text_from_pdf(filepath, verbose=False)
                        summary = reader.get_document_summary(max_length=200)

                        # Return enhanced result with LLM capabilities
                        result = {
                            'filename': file.filename,
                            'extracted_text': extracted_text,
                            'summary': summary,
                            'llm_enabled': True,
                            'ready_for_questions': True,
                            'message': 'PDF processed with LLM capabilities'
                        }

                        # Save result to MongoDB if requested
                        if save_to_db:
                            result = save_to_mongodb(result)

                        return result
                    else:
                        logger.warning("LLM processing failed, falling back to regular extraction")
                else:
                    logger.warning("Enhanced PDF reader not available, falling back to regular extraction")

            # Regular PDF text extraction
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
        agent_result = agent.plan({"document_text": extracted_text})

        # Prepare final result
        result = {
            'filename': file.filename,
            'extracted_text': extracted_text,
            'agent_result': agent_result,
            'llm_enabled': enable_llm
        }

        # Save result to MongoDB if requested
        if save_to_db:
            result = save_to_mongodb(result)

        return result
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    """Process an uploaded PDF (redirects to process-document)."""
    return await process_document(file)

# PDF Q&A Request Models
class PDFQARequest(BaseModel):
    question: Optional[str] = None
    action: str = "ask_question"  # ask_question, get_summary, search
    pdf_path: Optional[str] = None
    k: Optional[int] = 3  # for search

class PDFQAUploadRequest(BaseModel):
    action: str = "load_pdf"
    enable_llm: bool = True

@app.post("/api/pdf-qa")
async def pdf_qa_endpoint(request: PDFQARequest):
    """Handle PDF question answering requests."""
    try:
        # Get the enhanced PDF reader
        reader = get_enhanced_pdf_reader()

        if not reader:
            raise HTTPException(
                status_code=500,
                detail="Enhanced PDF reader not available. Check LLM dependencies and API key."
            )

        if not reader.llm:
            raise HTTPException(
                status_code=500,
                detail="LLM functionality not available. Check Together.ai API key and dependencies."
            )

        # Handle different actions
        if request.action == "ask_question":
            if not request.question:
                raise HTTPException(status_code=400, detail="Question is required for ask_question action")

            answer = reader.ask_question(request.question, verbose=False)

            result = {
                "action": "ask_question",
                "question": request.question,
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            }

        elif request.action == "get_summary":
            summary = reader.get_document_summary()

            result = {
                "action": "get_summary",
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }

        elif request.action == "search":
            if not request.question:
                raise HTTPException(status_code=400, detail="Search query is required for search action")

            search_results = reader.search_document(request.question, k=request.k or 3)

            result = {
                "action": "search",
                "query": request.question,
                "results": search_results,
                "timestamp": datetime.now().isoformat()
            }

        elif request.action == "clear_memory":
            reader.clear_memory()

            result = {
                "action": "clear_memory",
                "message": "Conversation memory cleared",
                "timestamp": datetime.now().isoformat()
            }

        elif request.action == "status":
            # Check if PDF is loaded and ready
            pdf_loaded = reader.qa_chain is not None

            result = {
                "action": "status",
                "pdf_loaded": pdf_loaded,
                "llm_available": reader.llm is not None,
                "embeddings_available": reader.embeddings is not None,
                "ready_for_questions": pdf_loaded,
                "timestamp": datetime.now().isoformat()
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

        # Save result to MongoDB if available
        try:
            result = save_to_mongodb(result)
        except Exception as e:
            logger.warning(f"Failed to save PDF Q&A result to MongoDB: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PDF Q&A endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf-qa-upload")
async def pdf_qa_upload(file: UploadFile = File(...), enable_llm: bool = True):
    """Upload and process a PDF for question answering."""
    try:
        if not enable_llm:
            # Fall back to regular document processing
            return await process_document(file)

        # Get the enhanced PDF reader
        reader = get_enhanced_pdf_reader()

        if not reader:
            raise HTTPException(
                status_code=500,
                detail="Enhanced PDF reader not available. Check LLM dependencies and API key."
            )

        if not reader.llm:
            # Fall back to regular processing if LLM not available
            logger.warning("LLM not available, falling back to regular PDF processing")
            return await process_document(file)

        # Save the uploaded file
        filepath = save_upload_file(file)

        # Load and process the PDF for Q&A
        success = reader.load_and_process_pdf(filepath, verbose=False)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to process PDF for question answering")

        # Get basic document info
        text_preview = reader.extract_text_from_pdf(filepath, verbose=False)
        preview = text_preview[:500] + "..." if len(text_preview) > 500 else text_preview

        # Get document summary
        summary = reader.get_document_summary(max_length=200)

        result = {
            "action": "load_pdf",
            "filename": file.filename,
            "status": "success",
            "message": "PDF loaded and processed for question answering",
            "text_preview": preview,
            "summary": summary,
            "llm_enabled": True,
            "ready_for_questions": True,
            "timestamp": datetime.now().isoformat()
        }

        # Save result to MongoDB if available
        try:
            result = save_to_mongodb(result)
        except Exception as e:
            logger.warning(f"Failed to save PDF upload result to MongoDB: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PDF Q&A upload endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Enhanced BlackHole Core MCP Endpoints
@app.post("/api/blackhole/command")
async def process_blackhole_command(request: MCPCommandRequest):
    """
    Process command through your BlackHole Core interface.
    Maintains your perspective while enabling MCP functionality.
    """
    try:
        result = blackhole_interface.process_command(request.command)

        # Save to MongoDB if successful
        if result.get('status') == 'success':
            result = save_to_mongodb(result)

        return result
    except Exception as e:
        logger.error(f"Error processing BlackHole Core command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcp/command")
async def process_mcp_command(request: MCPCommandRequest):
    """
    Process a natural language command with clean responses and chat history.
    """
    try:
        # Use the enhanced execute_command with session support
        result = mcp_processor.execute_command(request.command, request.session_id)

        # Save to MongoDB if successful (raw data is already logged)
        if result.get('status') == 'success':
            # Don't double-save, just return the clean response
            pass

        return result
    except Exception as e:
        logger.error(f"Error processing MCP command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mcp/process-file")
async def process_file_via_mcp(
    file: UploadFile = File(...),
    command: str = "analyze this file",
    enable_llm: bool = True,
    save_to_db: bool = True
):
    """
    Process a file through the MCP system with natural language commands.
    Combines file upload with MCP command processing.
    """
    try:
        # Save the uploaded file
        filepath = save_upload_file(file)

        # Create enhanced command with file context
        enhanced_command = f"{command} - File: {file.filename}"

        # Process through document processor agent
        from blackhole_core.agents.document_processor_agent import DocumentProcessorAgent
        doc_agent = DocumentProcessorAgent()

        # Process the file
        file_result = doc_agent.plan({
            'file_path': filepath,
            'command_type': 'analyze',
            'original_command': command
        })

        # Create MCP-style response
        mcp_result = {
            'status': 'success',
            'command': enhanced_command,
            'command_type': 'file_processing',
            'agent_used': 'document_processor',
            'file_info': {
                'filename': file.filename,
                'filepath': filepath,
                'size': file.size,
                'content_type': file.content_type
            },
            'processing_options': {
                'llm_enabled': enable_llm,
                'save_to_db': save_to_db
            },
            'result': file_result,
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': 0  # Will be calculated by frontend
        }

        # Save to MongoDB if requested
        if save_to_db:
            mcp_result = save_to_mongodb(mcp_result)

        return mcp_result

    except Exception as e:
        logger.error(f"Error processing file via MCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/blackhole/help")
async def get_blackhole_help():
    """Get help information about your BlackHole Core system."""
    try:
        help_result = blackhole_interface.get_help()
        return help_result
    except Exception as e:
        logger.error(f"Error getting BlackHole Core help: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/blackhole/status")
async def get_blackhole_status():
    """Get comprehensive status of your BlackHole Core system."""
    try:
        status = blackhole_interface.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Error getting BlackHole Core status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/help")
async def get_mcp_help():
    """Get help information about available MCP commands."""
    try:
        help_result = mcp_processor._generate_help_response()
        return help_result
    except Exception as e:
        logger.error(f"Error getting MCP help: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/status")
async def get_mcp_status():
    """Get status of all MCP agents and system health."""
    try:
        status = mcp_processor.get_agent_status()
        return status
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/history")
async def get_mcp_history(limit: int = Query(10, ge=1, le=100)):
    """Get recent MCP command history."""
    try:
        history = mcp_processor.get_command_history(limit)
        return {
            'history': history,
            'count': len(history),
            'limit': limit
        }
    except Exception as e:
        logger.error(f"Error getting MCP history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat History Endpoints
@app.post("/api/chat/session")
async def create_chat_session(user_id: str = "default"):
    """Create a new chat session."""
    try:
        from blackhole_core.chat_history import chat_history
        session_id = chat_history.create_session(user_id)
        return {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'status': 'created'
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/session/{session_id}/history")
async def get_chat_history(session_id: str, limit: int = Query(50, ge=1, le=100)):
    """Get chat history for a session."""
    try:
        from blackhole_core.chat_history import chat_history
        history = chat_history.get_session_history(session_id, limit)
        return {
            'session_id': session_id,
            'history': history,
            'count': len(history),
            'limit': limit
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Get statistics for a chat session."""
    try:
        from blackhole_core.chat_history import chat_history
        stats = chat_history.get_session_stats(session_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/session/{session_id}/search")
async def search_chat_history(session_id: str, query: str, limit: int = Query(10, ge=1, le=50)):
    """Search through chat history."""
    try:
        from blackhole_core.chat_history import chat_history
        results = chat_history.search_history(session_id, query, limit)
        return {
            'session_id': session_id,
            'query': query,
            'results': results,
            'count': len(results)
        }
    except Exception as e:
        logger.error(f"Error searching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Universal Agent Connector Endpoints
@app.post("/api/agents/register")
async def register_external_agent(agent_config: dict):
    """Register a new external agent."""
    try:
        from blackhole_core.universal_connector import universal_connector
        from blackhole_core.agent_registry import agent_registry

        # Validate configuration
        errors = agent_registry.validate_config(agent_config)
        if errors:
            raise HTTPException(status_code=400, detail=f"Configuration errors: {errors}")

        # Add to registry
        success = agent_registry.add_agent_config(agent_config)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add agent to registry")

        # Register with universal connector
        connector_success = universal_connector.register_agent(agent_config)
        if not connector_success:
            raise HTTPException(status_code=500, detail="Failed to connect to agent")

        return {
            'status': 'success',
            'message': f"Agent {agent_config['id']} registered successfully",
            'agent_id': agent_config['id']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/connected")
async def get_connected_agents():
    """Get all connected agents."""
    try:
        from blackhole_core.universal_connector import universal_connector
        connected = universal_connector.get_connected_agents()

        return {
            'connected_agents': connected,
            'total_count': len(connected)
        }

    except Exception as e:
        logger.error(f"Error getting connected agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/registry")
async def get_agent_registry():
    """Get all agents in the registry."""
    try:
        from blackhole_core.agent_registry import agent_registry
        all_agents = agent_registry.get_all_agents()
        enabled_agents = agent_registry.get_enabled_agents()

        return {
            'all_agents': all_agents,
            'enabled_agents': enabled_agents,
            'total_count': len(all_agents),
            'enabled_count': len(enabled_agents)
        }

    except Exception as e:
        logger.error(f"Error getting agent registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/templates")
async def get_agent_templates():
    """Get agent configuration templates."""
    try:
        from blackhole_core.agent_registry import agent_registry
        templates = agent_registry.get_agent_templates()

        return {
            'templates': templates,
            'description': 'Use these templates to create your own agent configurations'
        }

    except Exception as e:
        logger.error(f"Error getting agent templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/enable")
async def enable_agent(agent_id: str):
    """Enable an agent."""
    try:
        from blackhole_core.agent_registry import agent_registry
        from blackhole_core.universal_connector import universal_connector

        success = agent_registry.enable_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Try to connect the agent
        config = agent_registry.get_agent_config(agent_id)
        if config:
            universal_connector.register_agent(config)

        return {
            'status': 'success',
            'message': f"Agent {agent_id} enabled",
            'agent_id': agent_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/disable")
async def disable_agent(agent_id: str):
    """Disable an agent."""
    try:
        from blackhole_core.agent_registry import agent_registry
        from blackhole_core.universal_connector import universal_connector

        success = agent_registry.disable_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Disconnect the agent
        universal_connector.disconnect_agent(agent_id)

        return {
            'status': 'success',
            'message': f"Agent {agent_id} disabled",
            'agent_id': agent_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agents/{agent_id}")
async def remove_agent(agent_id: str):
    """Remove an agent from the registry."""
    try:
        from blackhole_core.agent_registry import agent_registry
        from blackhole_core.universal_connector import universal_connector

        # Disconnect first
        universal_connector.disconnect_agent(agent_id)

        # Remove from registry
        success = agent_registry.remove_agent_config(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return {
            'status': 'success',
            'message': f"Agent {agent_id} removed",
            'agent_id': agent_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Backend Agent Management Endpoints
@app.get("/api/backend-agents")
async def get_backend_agents():
    """Get all backend agents and their collaboration capabilities."""
    try:
        from blackhole_core.backend_agent_manager import backend_agent_manager

        backend_agents = backend_agent_manager.get_backend_agents()
        collaboration_capabilities = backend_agent_manager.get_collaboration_capabilities()

        return {
            'backend_agents': backend_agents,
            'collaboration_capabilities': collaboration_capabilities,
            'total_count': len(backend_agents),
            'auto_connect_enabled': backend_agent_manager.auto_connect_enabled
        }

    except Exception as e:
        logger.error(f"Error getting backend agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backend-agents/reload")
async def reload_backend_agents():
    """Reload all backend agents from configuration files."""
    try:
        from blackhole_core.backend_agent_manager import backend_agent_manager

        result = backend_agent_manager.reload_backend_agents()

        return {
            'status': 'success',
            'message': 'Backend agents reloaded',
            'connected': result['connected'],
            'failed': result['failed'],
            'total_configs': result['total_configs']
        }

    except Exception as e:
        logger.error(f"Error reloading backend agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backend-agents/auto-connect/{enabled}")
async def set_auto_connect(enabled: bool):
    """Enable or disable automatic connection of backend agents."""
    try:
        from blackhole_core.backend_agent_manager import backend_agent_manager

        if enabled:
            backend_agent_manager.enable_auto_connect()
        else:
            backend_agent_manager.disable_auto_connect()

        return {
            'status': 'success',
            'auto_connect_enabled': enabled,
            'message': f"Auto-connect {'enabled' if enabled else 'disabled'}"
        }

    except Exception as e:
        logger.error(f"Error setting auto-connect: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Collaboration Endpoints
@app.post("/api/collaboration/process")
async def process_collaborative_request(request: dict):
    """Process a request that may require multiple agents to collaborate."""
    try:
        from blackhole_core.agent_orchestrator import agent_orchestrator
        import asyncio

        user_input = request.get('input', '')
        context = request.get('context', {})

        if not user_input:
            raise HTTPException(status_code=400, detail="Input is required")

        # Process collaborative request
        result = await agent_orchestrator.process_collaborative_request(user_input, context)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in collaborative processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collaboration/patterns")
async def get_collaboration_patterns():
    """Get available collaboration patterns."""
    try:
        from blackhole_core.agent_orchestrator import agent_orchestrator

        return {
            'patterns': agent_orchestrator.collaboration_patterns,
            'total_patterns': len(agent_orchestrator.collaboration_patterns)
        }

    except Exception as e:
        logger.error(f"Error getting collaboration patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn

    print("🚀 BlackHole Core MCP - Starting Server...")
    print("=" * 50)

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    workers = int(os.getenv("WORKERS", 1))

    print(f"📍 Server will start on: http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"👥 Workers: {workers}")
    print("=" * 50)

    logger.info(f"Starting BlackHole Core MCP server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Workers: {workers}")

    # Test MongoDB connection on startup
    print("🔍 Testing MongoDB connection...")
    try:
        if test_connection():
            print("✅ MongoDB connection successful")
            logger.info("✅ MongoDB connection successful")
        else:
            print("⚠️ MongoDB connection failed - some features may not work")
            logger.warning("⚠️ MongoDB connection failed - some features may not work")
    except Exception as e:
        print(f"⚠️ MongoDB connection test failed: {e}")
        logger.warning(f"⚠️ MongoDB connection test failed: {e}")

    # Test LLM availability
    print("🤖 Testing LLM availability...")
    try:
        pdf_reader = get_enhanced_pdf_reader()
        if pdf_reader and pdf_reader.llm:
            print("✅ LLM functionality available")
            logger.info("✅ LLM functionality available")
        else:
            print("⚠️ LLM functionality not available - check TOGETHER_API_KEY")
            logger.warning("⚠️ LLM functionality not available - check TOGETHER_API_KEY")
    except Exception as e:
        print(f"⚠️ LLM initialization failed: {e}")
        logger.warning(f"⚠️ LLM initialization failed: {e}")

    print("🚀 Starting Uvicorn server...")
    print(f"📱 Access your app at: http://localhost:{port}")
    print(f"📚 API docs at: http://localhost:{port}/docs")
    print("=" * 50)

    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=debug,
            workers=workers if not debug else 1,  # Use single worker in debug mode
            log_level="debug" if debug else "info"
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        logger.error(f"Error starting server: {e}")
        input("Press Enter to exit...")
