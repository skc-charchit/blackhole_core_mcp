@echo off
title MCP System Local Interface
color 0A

echo.
echo ========================================
echo    MCP SYSTEM - LOCAL INTERFACE
echo ========================================
echo.
echo 🎯 Enhanced Model Context Protocol
echo 📁 Modular Agent System
echo 🤖 Multiple Client Interfaces
echo.
echo ========================================
echo.

echo 🚀 Starting MCP System...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check for required files
if not exist "enhanced_mcp_server.py" (
    if not exist "start_mcp_server.py" (
        echo ❌ MCP Server files not found!
        echo Please make sure you're in the correct directory.
        pause
        exit /b 1
    )
)

echo ✅ MCP Server files found
echo.

REM Start the local interface
echo 🌐 Starting Local Interface...
echo.
echo Choose your interface:
echo.
echo 1. 🎯 Complete Local Interface (Recommended)
echo 2. 🚀 Quick Launcher
echo 3. 🌐 Dashboard Only
echo 4. 💻 CLI Only
echo 5. 🐍 Interactive Client Only
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🎯 Starting Complete Local Interface...
    python local_interface.py
) else if "%choice%"=="2" (
    echo.
    echo 🚀 Starting Quick Launcher...
    python launch_mcp.py
) else if "%choice%"=="3" (
    echo.
    echo 🌐 Opening Dashboard...
    start mcp_dashboard.html
    echo ✅ Dashboard opened in browser
    echo 💡 Make sure MCP server is running separately
) else if "%choice%"=="4" (
    echo.
    echo 💻 Starting CLI Client...
    python mcp_client/cli_client.py interactive
) else if "%choice%"=="5" (
    echo.
    echo 🐍 Starting Interactive Client...
    python start_mcp_client.py
) else (
    echo.
    echo ❌ Invalid choice. Starting Complete Local Interface...
    python local_interface.py
)

echo.
echo 👋 MCP System closed
pause
