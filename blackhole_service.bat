@echo off
echo 🚀 BlackHole Core MCP - Service Manager
echo ========================================

if "%1"=="" (
    echo Usage: blackhole_service.bat [start^|stop^|restart^|status^|test]
    echo.
    echo Commands:
    echo   start   - Start the service in background
    echo   stop    - Stop the service
    echo   restart - Restart the service
    echo   status  - Show service status
    echo   test    - Test service functionality
    echo.
    goto :end
)

python service_manager.py %1

:end
pause
