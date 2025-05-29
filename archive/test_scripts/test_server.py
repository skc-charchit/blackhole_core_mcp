#!/usr/bin/env python3
"""
Simple test server to verify the setup is working
"""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# Simple test app
app = FastAPI(title="BlackHole Core MCP Test Server")

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BlackHole Core MCP - Test Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .status { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .feature { background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 5px; }
            .button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 BlackHole Core MCP - Test Server</h1>
            
            <div class="status">
                ✅ <strong>Server is running successfully!</strong><br>
                Your BlackHole Core MCP setup is working properly.
            </div>
            
            <h2>🧪 Test Features</h2>
            
            <div class="feature">
                <h3>📊 API Health Check</h3>
                <a href="/health" class="button">Check Health</a>
                <p>Test the health endpoint to verify all components.</p>
            </div>
            
            <div class="feature">
                <h3>📚 API Documentation</h3>
                <a href="/docs" class="button">View API Docs</a>
                <p>Interactive Swagger UI for testing all endpoints.</p>
            </div>
            
            <div class="feature">
                <h3>🔧 System Info</h3>
                <a href="/info" class="button">System Info</a>
                <p>View system information and configuration.</p>
            </div>
            
            <h2>🎯 Next Steps</h2>
            <ol>
                <li>✅ Server is running - you can see this page!</li>
                <li>🔧 Test the health endpoint</li>
                <li>📚 Check the API documentation</li>
                <li>🚀 Start the full BlackHole Core MCP application</li>
            </ol>
            
            <div style="text-align: center; margin-top: 30px; color: #666;">
                <p>BlackHole Core MCP - Model Context Protocol Implementation</p>
                <p>Port: 8000 | Status: ✅ Running</p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "message": "Test server is running",
        "server": "BlackHole Core MCP Test",
        "python_version": sys.version,
        "working_directory": os.getcwd()
    }

@app.get("/info")
async def info():
    return {
        "server": "BlackHole Core MCP Test Server",
        "python_executable": sys.executable,
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment_variables": {
            "PATH": os.environ.get("PATH", "Not set")[:100] + "...",
            "PYTHONPATH": os.environ.get("PYTHONPATH", "Not set"),
        },
        "files_in_directory": os.listdir(".")[:10]  # First 10 files
    }

if __name__ == "__main__":
    print("🚀 Starting BlackHole Core MCP Test Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")
