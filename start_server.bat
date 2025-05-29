@echo off
echo 🚀 Starting BlackHole Core MCP Server...
echo ==========================================

echo 📍 Server will be available at: http://localhost:8000
echo 📚 API docs will be available at: http://localhost:8000/docs
echo 🔧 Health check: http://localhost:8000/health
echo.

echo Starting server...
python main.py

echo.
echo Server stopped. Press any key to exit...
pause
