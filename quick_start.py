#!/usr/bin/env python3
"""
Quick start script for BlackHole Core MCP
This will start the server and show you exactly what's happening
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def print_banner():
    print("🚀 BlackHole Core MCP - Quick Start")
    print("=" * 50)
    print("📍 Starting your application on localhost...")
    print("=" * 50)

def check_requirements():
    print("🔍 Checking requirements...")
    
    # Check if main.py exists
    if not Path("main.py").exists():
        print("❌ main.py not found!")
        return False
    
    # Check if we can import required modules
    try:
        import fastapi
        print("✅ FastAPI available")
    except ImportError:
        print("❌ FastAPI not installed")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn available")
    except ImportError:
        print("❌ Uvicorn not installed")
        return False
    
    print("✅ All requirements satisfied")
    return True

def start_server():
    print("\n🚀 Starting server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print("\n" + "=" * 50)
    
    # Start the server
    try:
        import uvicorn
        from main import app
        
        print("✅ Application imported successfully")
        print("🚀 Starting Uvicorn server...")
        
        # Open browser after a short delay
        import threading
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8000")
                print("🌐 Browser opened automatically")
            except:
                print("🌐 Please open http://localhost:8000 in your browser")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\nTrying alternative startup method...")
        
        # Alternative: use subprocess
        try:
            subprocess.run([sys.executable, "main.py"], check=True)
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            print("\nPlease try running manually:")
            print("python main.py")

def main():
    print_banner()
    
    if not check_requirements():
        print("\n❌ Requirements check failed")
        input("Press Enter to exit...")
        return
    
    print("\n🎯 Everything looks good! Starting server...")
    start_server()

if __name__ == "__main__":
    main()
