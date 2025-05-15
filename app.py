"""
Main API server for the Blackhole Core MCP project.
This serves as the entry point for the backend.
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from bson import ObjectId
import json
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from blackhole_core.data_source.mongodb import get_mongo_client, get_agent_outputs_collection, test_connection
from data.multimodal.image_ocr import extract_text_from_image
from data.multimodal.pdf_reader import extract_text_from_pdf
from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
from blackhole_core.agents.live_data_agent import LiveDataAgent
import datetime

# Import logger
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(handler)

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

# Initialize Flask app
app = Flask(__name__, static_folder='public')
app.json_encoder = MongoJSONEncoder

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', '*')
if cors_origins != '*':
    cors_origins = cors_origins.split(',')
CORS(app, origins=cors_origins)

# Debug routes are defined below

# Configure upload folder
UPLOAD_FOLDER = os.getenv('UPLOAD_DIR', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main index page."""
    return send_from_directory('public', 'index.html')

@app.route('/env.js')
def env_js():
    """Serve the env.js file."""
    return send_from_directory('public', 'env.js')

@app.route('/api/health')
def health_check():
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

    return jsonify({
        'status': 'ok',
        'mongodb': 'connected' if mongo_connected else 'disconnected',
        'mongodb_error': mongo_error,
        'pdf_reader': 'working' if pdf_reader_working else 'not working',
        'pdf_reader_error': pdf_reader_error,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/test-connection')
def test_connection_route():
    """Simple test endpoint for connection testing."""
    return jsonify({
        'message': 'Connection successful!',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/test')
def api_test():
    """Test API endpoint."""
    return jsonify({
        'message': 'API is working!',
        'pdf_reader_path': os.path.abspath('./data/multimodal/pdf_reader.py') if os.path.exists('./data/multimodal/pdf_reader.py') else 'File not found',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/debug/routes')
def debug_routes():
    """List all routes."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': [method for method in rule.methods if method != 'OPTIONS' and method != 'HEAD'],
            'path': str(rule)
        })
    return jsonify(routes)

@app.route('/debug/env')
def debug_env():
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

    return jsonify({
        'MONGO_URI': mongo_uri,
        'CORS_ORIGINS': os.environ.get('CORS_ORIGINS', 'not set'),
        'DEBUG': os.environ.get('DEBUG', 'not set'),
        'PORT': os.environ.get('PORT', 'not set'),
        'MONGO_DB_NAME': os.environ.get('MONGO_DB_NAME', 'not set'),
        'MONGO_COLLECTION_NAME': os.environ.get('MONGO_COLLECTION_NAME', 'not set'),
        'PYTHON_PATH': sys.executable,
        'WORKING_DIR': os.getcwd(),
        'FILES_IN_MULTIMODAL': os.listdir('data/multimodal') if os.path.exists('data/multimodal') else []
    })

@app.route('/api/process-image', methods=['POST'])
def process_image():
    """Process an uploaded image."""
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Extract text from image
            extracted_text = extract_text_from_image(filepath, debug=True)

            # Process with ArchiveSearchAgent
            agent = ArchiveSearchAgent()
            result = agent.plan({"document_text": extracted_text})

            # Save result to MongoDB
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

            return jsonify({
                'filename': filename,
                'extracted_text': extracted_text,
                'agent_result': result
            })
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/process-pdf', methods=['POST'])
def process_pdf():
    """Process an uploaded PDF."""
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(filepath, include_page_numbers=True, verbose=True)

            # Process with ArchiveSearchAgent
            agent = ArchiveSearchAgent()
            result = agent.plan({"document_text": extracted_text})

            # Save result to MongoDB
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

            return jsonify({
                'filename': filename,
                'extracted_text': extracted_text,
                'agent_result': result
            })
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Get weather data for a location."""
    location = request.args.get('location', 'London')

    try:
        # Process with LiveDataAgent
        agent = LiveDataAgent(memory=[], api_url="https://wttr.in/{location}?format=j1".format(location=location))
        result = agent.plan({"query": f"{location} weather"})

        # Save result to MongoDB
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
                logger.info("Weather result saved to MongoDB")
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_archive():
    """Search the archive with text query."""
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400

    query = data['query']

    try:
        # Process with ArchiveSearchAgent
        agent = ArchiveSearchAgent()
        result = agent.plan({"document_text": query})

        # Save result to MongoDB
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
                logger.info("Search result saved to MongoDB")
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error searching archive: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get all results from MongoDB."""
    try:
        collection = get_agent_outputs_collection()
        results = list(collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(100))

        # Convert results to JSON-serializable format
        for result in results:
            if 'timestamp' in result:
                result['timestamp'] = str(result['timestamp'])

        return jsonify(results)
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
