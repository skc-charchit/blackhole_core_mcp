#!/bin/bash
# Deployment script for Blackhole Core MCP

# Exit on error
set -e

# Print commands
set -x

# Create necessary directories
mkdir -p uploads logs temp processed public

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "Python 3.8 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi

# Install required packages
pip install -r requirements.txt

# Check if MongoDB is installed and running
if command -v mongod &> /dev/null; then
    echo "MongoDB is installed."
    
    # Check if MongoDB is running
    if pgrep -x "mongod" > /dev/null; then
        echo "MongoDB is running."
    else
        echo "MongoDB is not running. Starting MongoDB..."
        if command -v systemctl &> /dev/null; then
            sudo systemctl start mongod
        else
            echo "Could not start MongoDB. Please start it manually."
        fi
    fi
else
    echo "MongoDB is not installed locally. Make sure you have a MongoDB connection string in your .env file."
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# API key for external services (replace with your actual key when needed)
API_KEY=your_api_key

# MongoDB connection strings
# Cloud MongoDB URI - for production use
MONGO_URI=mongodb+srv://user1:admin@cluster0.vielvkx.mongodb.net/?retryWrites=true&w=majority

# Local MongoDB URI - for development and testing
MONGO_URI_LOCAL=mongodb://localhost:27017/

# Application settings
DEBUG=false

# MongoDB database and collection names
MONGO_DB_NAME=blackhole_db
MONGO_COLLECTION_NAME=agent_outputs

# Server configuration
PORT=8000
HOST=0.0.0.0

# File storage paths
UPLOAD_DIR=uploads
TEMP_DIR=temp
PROCESSED_DIR=processed

# Logging configuration
LOG_LEVEL=info
LOG_FILE=logs/blackhole.log
EOL
    echo ".env file created. Please update it with your actual configuration."
fi

# Test MongoDB connection
echo "Testing MongoDB connection..."
python -c "from blackhole_core.data_source.mongodb import test_connection; print('MongoDB connection successful!' if test_connection() else 'MongoDB connection failed!')"

# Start the server
echo "Starting the server..."
python app.py
