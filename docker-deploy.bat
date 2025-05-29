@echo off
REM BlackHole Core MCP - Docker Deployment Script for Windows
REM This script helps deploy the application using Docker Compose

setlocal enabledelayedexpansion

echo 🚀 BlackHole Core MCP - Docker Deployment
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from template...
    copy .env.docker .env
    echo [WARNING] Please edit .env file with your actual configuration (especially TOGETHER_API_KEY)
    echo [WARNING] Then run this script again.
    pause
    exit /b 1
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "data\multimodal\uploaded_pdfs" mkdir "data\multimodal\uploaded_pdfs"
if not exist "data\multimodal\uploaded_images" mkdir "data\multimodal\uploaded_images"
if not exist "data\multimodal\processed_outputs" mkdir "data\multimodal\processed_outputs"
if not exist "uploads" mkdir "uploads"
if not exist "logs" mkdir "logs"

echo [SUCCESS] Directories created

REM Parse command line arguments
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=up

if "%COMMAND%"=="up" goto :start
if "%COMMAND%"=="start" goto :start
if "%COMMAND%"=="down" goto :stop
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="restart" goto :restart
if "%COMMAND%"=="logs" goto :logs
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="health" goto :health
goto :usage

:start
echo [INFO] Starting BlackHole Core MCP with Docker Compose...
docker-compose up -d

echo [INFO] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo [ERROR] Some services failed to start. Check logs with: docker-compose logs
    pause
    exit /b 1
) else (
    echo [SUCCESS] Services started successfully!
    echo.
    echo 🌐 Application URLs:
    echo    - BlackHole Core MCP: http://localhost:8000
    echo    - API Documentation: http://localhost:8000/docs
    echo    - MongoDB Express: http://localhost:8081
    echo.
    echo 📋 Default Credentials:
    echo    - MongoDB Express: admin / blackhole_admin_2024
    echo.
    echo 🔧 Useful Commands:
    echo    - View logs: docker-compose logs -f
    echo    - Stop services: docker-compose down
    echo    - Restart: docker-compose restart
)
goto :end

:stop
echo [INFO] Stopping BlackHole Core MCP services...
docker-compose down
echo [SUCCESS] Services stopped
goto :end

:restart
echo [INFO] Restarting BlackHole Core MCP services...
docker-compose restart
echo [SUCCESS] Services restarted
goto :end

:logs
echo [INFO] Showing logs...
docker-compose logs -f
goto :end

:build
echo [INFO] Building BlackHole Core MCP Docker image...
docker-compose build --no-cache
echo [SUCCESS] Build completed
goto :end

:clean
echo [INFO] Cleaning up Docker resources...
docker-compose down -v
docker system prune -f
echo [SUCCESS] Cleanup completed
goto :end

:status
echo [INFO] Service status:
docker-compose ps
goto :end

:health
echo [INFO] Checking service health...
echo 🔍 BlackHole App Health:
curl -s http://localhost:8000/api/health 2>nul || echo Service not responding
echo.
echo 🔍 MongoDB Status:
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" 2>nul || echo MongoDB not responding
goto :end

:usage
echo Usage: %0 {up^|down^|restart^|logs^|build^|clean^|status^|health}
echo.
echo Commands:
echo   up/start  - Start all services
echo   down/stop - Stop all services
echo   restart   - Restart all services
echo   logs      - Show service logs
echo   build     - Rebuild Docker images
echo   clean     - Clean up Docker resources
echo   status    - Show service status
echo   health    - Check service health
goto :end

:end
if "%COMMAND%"=="logs" goto :skip_pause
pause
:skip_pause
