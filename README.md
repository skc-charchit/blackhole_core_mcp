# 🚀 Blackhole Core MCP (FastAPI Version)

A modular AI-powered framework for ingesting multimodal data (images, PDFs, text), processing them via agents and pipelines, and storing structured insights into MongoDB. This version uses FastAPI for the backend API.

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [Usage](#usage)
- [Modules](#modules)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

Blackhole Core MCP is a framework designed to process various types of data (text, images, PDFs) using AI agents and store the results in a structured format. It provides a modular architecture that allows for easy extension and customization.

## Features

- **FastAPI Backend**: Modern, high-performance API with automatic OpenAPI documentation
- **Multimodal Data Processing**: Extract text from images and PDFs
- **Agent-Based Architecture**: Process data using specialized agents
- **MongoDB Integration**: Store and retrieve structured data
- **Modular Design**: Easily extend with new agents and data sources
- **Robust Error Handling**: Graceful fallbacks and detailed logging
- **Comprehensive Testing**: Unit tests for core components
- **Swagger UI**: Interactive API documentation at /docs
- **ReDoc**: Alternative API documentation at /redoc

## Project Structure

```
project_root/
├── adapter/                  # Adapter modules for external systems
├── api/                      # API endpoints
├── blackhole_core/           # Core functionality
│   ├── agents/               # AI agents for data processing
│   └── data_source/          # Data source connectors
├── data/                     # Data processing modules
│   ├── multimodal/           # Multimodal data processing (images, PDFs)
│   └── pipelines/            # Processing pipelines
├── logs/                     # Log files
├── tests/                    # Test modules
├── utils/                    # Utility modules
├── .env                      # Environment variables
├── .gitignore                # Git ignore file
├── Dockerfile                # Docker configuration
├── docker-compose.yaml       # Docker Compose configuration
├── LICENSE                   # License file
├── README.md                 # This file
├── requirements.txt          # Python dependencies
└── run_tests.py              # Test runner script
```

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB (local or cloud)
- Tesseract OCR (for image processing)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/blackhole_core_mcp.git
   cd blackhole_core_mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR:
   - Windows: Download and install from [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

## Environment Setup

1. Copy the example environment file or create a new `.env` file:
   ```bash
   # If .env.example exists
   cp .env.example .env
   # Otherwise create a new file
   touch .env
   ```

2. Edit the `.env` file with your configuration:
   ```
   # API key for external services
   API_KEY=your_api_key

   # MongoDB connection strings
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGO_URI_LOCAL=mongodb://localhost:27017/

   # Application settings
   DEBUG=true

   # MongoDB database and collection names
   MONGO_DB_NAME=blackhole_db
   MONGO_COLLECTION_NAME=agent_outputs

   # Tesseract OCR path (if needed)
   TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
   ```

## Usage

### Running with Docker

```bash
# Start MongoDB and the API
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Running Locally

```bash
# Ensure MongoDB is running (via docker-compose or locally)
docker-compose up -d mongo

# Run the demo pipeline to process a sample PDF and image
python data/pipelines/blackhole_demo.py

# Run the combined demo pipeline
python data/pipelines/combined_demo_pipeline.py

# Test MongoDB connection
python blackhole_core/data_source/mongodb.py

# Start the FastAPI web server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Accessing the Web Interface and API Documentation

Once the server is running, you can access:
- Web interface: http://localhost:8000
- API documentation (Swagger UI): http://localhost:8000/docs
- Alternative API documentation (ReDoc): http://localhost:8000/redoc

The interface provides the following functionality:
- Upload and process images
- Upload and process PDFs
- Search the archive
- Get weather data
- View all results stored in MongoDB

The API documentation provides interactive testing of all endpoints.

## Deployment to Production

### Option 1: Docker Deployment

1. Update the `.env` file with production settings:
   ```
   DEBUG=false
   MONGO_URI=your_production_mongodb_uri
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d --build
   ```

3. The application will be available at http://your-server-ip:8000

### Option 2: Traditional Deployment

1. Set up a server with Python and MongoDB installed.

2. Clone the repository and navigate to the project directory.

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Update the `.env` file with production settings.

5. Run the deployment script:
   ```bash
   bash deploy.sh
   ```

6. For production use, it's recommended to set up a reverse proxy (Nginx/Apache) and use Uvicorn with multiple workers:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Deployment Setup (Render Backend + Netlify Frontend with Proxy)

This project is configured for deployment with the backend on Render and the frontend on Netlify, using a Netlify proxy to avoid CORS issues:

#### Backend Deployment (Render)

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket).

2. Log in to Render and click "New Web Service".

3. Select your repository and configure the deployment settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment variables:
     - `MONGO_URI`: Your MongoDB connection string
     - `CORS_ORIGINS`: `*` (or your specific origins including your Netlify domain)

4. Click "Create Web Service".

5. Your backend API will be available at the Render URL (e.g., https://blackhole-core-api.onrender.com).

#### Frontend Deployment (Netlify)

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket).

2. Log in to Netlify and click "New site from Git".

3. Select your repository and configure the deployment settings:
   - Build command: `node update_env.js`
   - Publish directory: `public`

4. Click "Deploy site".

5. After deployment, go to Site settings > Build & deploy > Environment variables and add:
   - `RENDER_BACKEND_URL`: Your Render backend URL (e.g., https://blackhole-core-api.onrender.com)

6. Trigger a new deployment for the environment variables to take effect.

7. Your frontend will be accessible at the Netlify URL (e.g., https://blackholebody.netlify.app).

8. The frontend is automatically configured to use the Netlify proxy to avoid CORS issues.

#### How the Proxy Works

The Netlify proxy works as follows:

1. The frontend makes requests to `/api/*` endpoints on the Netlify domain
2. Netlify redirects these requests to the `/.netlify/functions/proxy` function
3. The proxy function forwards the requests to the Render backend
4. The proxy function returns the response from the Render backend to the frontend

This approach avoids CORS issues because the frontend is making requests to the same domain (Netlify) rather than directly to the Render backend.

## Modules

### blackhole_core

Core functionality for the project:

- **agents**: AI agents for processing data
  - `archive_search_agent.py`: Searches archives based on document text
  - `live_data_agent.py`: Fetches and processes live data from APIs

- **data_source**: Data source connectors
  - `mongodb.py`: MongoDB connection and operations

### data

Data processing modules:

- **multimodal**: Multimodal data processing
  - `image_ocr.py`: Extracts text from images using OCR
  - `pdf_reader.py`: Extracts text from PDF documents

- **pipelines**: Processing pipelines
  - `blackhole_demo.py`: Demo pipeline for processing images
  - `combined_demo_pipeline.py`: Demo pipeline for processing both images and PDFs

### utils

Utility modules:

- `logger.py`: Centralized logging configuration

## Testing

Run tests using the test runner script:

```bash
# Run all tests
python run_tests.py

# Run tests with higher verbosity
python run_tests.py -v 3

# Run tests in a specific directory
python run_tests.py -d tests/specific_dir

# Run tests matching a specific pattern
python run_tests.py -p test_specific*.py
```

## Troubleshooting

### MongoDB Connection Issues

- Check if MongoDB is running: `docker-compose ps`
- Verify MongoDB URI in `.env` file
- Check logs for connection errors: `cat logs/blackhole_*.log`

### Image Processing Issues

- Verify Tesseract OCR is installed and in PATH
- Check the path in `.env` file if using Windows
- Try preprocessing the image for better OCR results

### General Issues

- Check the logs in the `logs` directory
- Increase verbosity with `DEBUG=true` in `.env`
- Run tests to verify component functionality

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

