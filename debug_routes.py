import os
import datetime
import sys
from flask import jsonify

def register_debug_routes(app):
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Blackhole Core MCP API is running',
            'status': 'ok',
            'endpoints': ['/api/health', '/api/weather', '/api/process-image', '/api/process-pdf', '/api/search'],
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    @app.route('/debug/routes')
    def debug_routes():
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
    
    @app.route('/test-connection')
    def test_connection():
        return jsonify({
            'message': 'Connection successful!',
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    @app.route('/api/test')
    def api_test():
        return jsonify({
            'message': 'API is working!',
            'pdf_reader_path': os.path.abspath('./data/multimodal/pdf_reader.py') if os.path.exists('./data/multimodal/pdf_reader.py') else 'File not found',
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    @app.route('/api/health')
    def health_check():
        # Test MongoDB connection
        mongo_connected = False
        mongo_error = None
        try:
            from blackhole_core.data_source.mongodb import test_connection
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
                from data.multimodal.pdf_reader import extract_text_from_pdf
                text = extract_text_from_pdf(sample_path, max_chars=100)
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
