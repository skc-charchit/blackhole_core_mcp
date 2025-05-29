#!/usr/bin/env python3
"""
MCP Production Server Startup Script
Starts the Model Context Protocol server with live data integration
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed."""
    print("🔍 Checking requirements...")
    
    try:
        import fastapi
        import uvicorn
        import requests
        import pymongo
        import python_dotenv
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment configuration."""
    print("🔍 Checking environment configuration...")
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check critical environment variables
    checks = {
        "MongoDB URI": os.getenv('MONGO_URI'),
        "OpenWeatherMap API Key": os.getenv('OPENWEATHER_API_KEY'),
        "Gmail Email": os.getenv('GMAIL_EMAIL'),
        "Gmail App Password": os.getenv('GMAIL_APP_PASSWORD')
    }
    
    all_configured = True
    for name, value in checks.items():
        if value and value.strip():
            print(f"✅ {name}: Configured")
        else:
            print(f"⚠️ {name}: Not configured")
            if name in ["MongoDB URI"]:
                all_configured = False
    
    if not all_configured:
        print("❌ Critical environment variables missing")
        print("💡 Please configure .env file with required credentials")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def check_agents():
    """Check if agents are available."""
    print("🔍 Checking agents...")
    
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("❌ Agents directory not found")
        return False
    
    # Check for key agent files
    key_agents = [
        "agents/data/realtime_weather_agent.py",
        "agents/communication/real_gmail_agent.py",
        "agents/core/document_processor.py"
    ]
    
    missing_agents = []
    for agent_path in key_agents:
        if not Path(agent_path).exists():
            missing_agents.append(agent_path)
    
    if missing_agents:
        print(f"❌ Missing agents: {', '.join(missing_agents)}")
        return False
    
    print("✅ All key agents are available")
    return True

def start_server():
    """Start the MCP server."""
    print("🚀 Starting MCP Production Server...")
    
    # Get configuration
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    print(f"📡 Server will start on: http://{host}:{port}")
    print("🌤️ Real-time weather data: Enabled")
    print("📧 Email automation: Enabled")
    print("📄 Document processing: Enabled")
    print("🤖 Automated workflows: Enabled")
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "mcp_server:app",
            "--host", host,
            "--port", str(port),
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def show_usage_info():
    """Show usage information."""
    print("\n📚 MCP PRODUCTION SERVER USAGE:")
    print("=" * 50)
    print("🌐 Web Interface: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/api/health")
    
    print("\n💬 Example Commands:")
    print("🌤️ Weather: 'What is the weather in Mumbai?'")
    print("📄 Document: 'Extract important points from this PDF'")
    print("📧 Workflow: 'Process document and email summary to manager@company.com'")
    
    print("\n🔧 API Endpoints:")
    print("POST /api/mcp/command - Process natural language commands")
    print("POST /api/mcp/analyze - Analyze documents")
    print("POST /api/mcp/workflow - Execute automated workflows")
    print("GET /api/mcp/agents - List available agents")

def main():
    """Main startup function."""
    print("🤖 MCP PRODUCTION SERVER STARTUP")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed")
        return False
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed")
        return False
    
    # Check agents
    if not check_agents():
        print("\n❌ Agents check failed")
        return False
    
    print("\n✅ All checks passed! Starting server...")
    print("=" * 50)
    
    # Show usage info
    show_usage_info()
    
    print("\n🚀 Starting server in 3 seconds...")
    time.sleep(3)
    
    # Start server
    return start_server()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Startup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        sys.exit(1)
