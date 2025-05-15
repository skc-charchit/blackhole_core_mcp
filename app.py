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

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from blackhole_core.data_source.mongodb import get_mongo_client, get_agent_outputs_collection, test_connection
from data.multimodal.image_ocr import extract_text_from_image
from data.multimodal.pdf_reader import extract_text_from_pdf
from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
from blackhole_core.agents.live_data_agent import LiveDataAgent

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

# Initialize Flask app
app = Flask(__name__, static_folder='public')

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', '*')
if cors_origins != '*':
    cors_origins = cors_origins.split(',')
CORS(app, origins=cors_origins)

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

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    # Check MongoDB connection
    mongo_status = test_connection()

    return jsonify({
        'status': 'ok',
        'mongodb': 'connected' if mongo_status else 'disconnected'
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
                    result.pop("_id", None)  # Remove _id if exists
                    collection.insert_one(result)
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
                    result.pop("_id", None)  # Remove _id if exists
                    collection.insert_one(result)
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
                result.pop("_id", None)  # Remove _id if exists
                collection.insert_one(result)
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
                result.pop("_id", None)  # Remove _id if exists
                collection.insert_one(result)
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
