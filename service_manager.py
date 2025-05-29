#!/usr/bin/env python3
"""
BlackHole Core MCP - Service Manager
Manage the application as a background service
"""

import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path

class BlackHoleServiceManager:
    def __init__(self):
        self.service_name = "BlackHole Core MCP"
        self.port = 8000
        self.host = "localhost"
        self.base_url = f"http://{self.host}:{self.port}"
        self.pid_file = Path("blackhole_service.pid")
        
    def print_status(self, message, status="INFO"):
        """Print colored status messages."""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m", 
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        
        color = colors.get(status, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}[{status}]{reset} {message}")

    def is_running(self):
        """Check if the service is running."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_status(self):
        """Get detailed service status."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "running": True,
                    "status": "healthy",
                    "mongodb": data.get("mongodb", "unknown"),
                    "timestamp": data.get("timestamp", "unknown")
                }
        except Exception as e:
            return {
                "running": False,
                "status": "stopped",
                "error": str(e)
            }

    def start(self):
        """Start the service in background."""
        if self.is_running():
            self.print_status(f"{self.service_name} is already running", "WARNING")
            return True

        self.print_status(f"Starting {self.service_name}...", "INFO")
        
        try:
            # Start the service
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.getcwd()
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment and check if it started
            time.sleep(3)
            
            if self.is_running():
                self.print_status(f"{self.service_name} started successfully", "SUCCESS")
                self.print_status(f"Service available at: {self.base_url}", "INFO")
                return True
            else:
                self.print_status(f"Failed to start {self.service_name}", "ERROR")
                return False
                
        except Exception as e:
            self.print_status(f"Error starting service: {e}", "ERROR")
            return False

    def stop(self):
        """Stop the service."""
        if not self.is_running():
            self.print_status(f"{self.service_name} is not running", "WARNING")
            return True

        self.print_status(f"Stopping {self.service_name}...", "INFO")
        
        try:
            # Try to read PID and kill process
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                try:
                    if os.name == 'nt':  # Windows
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                     capture_output=True)
                    else:  # Unix/Linux
                        os.kill(pid, 9)
                except:
                    pass
                
                self.pid_file.unlink()
            
            # Wait and verify
            time.sleep(2)
            
            if not self.is_running():
                self.print_status(f"{self.service_name} stopped successfully", "SUCCESS")
                return True
            else:
                self.print_status(f"Failed to stop {self.service_name}", "ERROR")
                return False
                
        except Exception as e:
            self.print_status(f"Error stopping service: {e}", "ERROR")
            return False

    def restart(self):
        """Restart the service."""
        self.print_status(f"Restarting {self.service_name}...", "INFO")
        self.stop()
        time.sleep(2)
        return self.start()

    def status(self):
        """Show service status."""
        status = self.get_status()
        
        self.print_status(f"{self.service_name} Status:", "INFO")
        print("=" * 50)
        
        if status["running"]:
            self.print_status(f"Status: {status['status']}", "SUCCESS")
            self.print_status(f"URL: {self.base_url}", "INFO")
            self.print_status(f"MongoDB: {status['mongodb']}", "SUCCESS" if status['mongodb'] == 'connected' else "WARNING")
            self.print_status(f"Last Check: {status.get('timestamp', 'Unknown')}", "INFO")
        else:
            self.print_status(f"Status: {status['status']}", "ERROR")
            if "error" in status:
                self.print_status(f"Error: {status['error']}", "ERROR")

    def test(self):
        """Test service functionality."""
        self.print_status("Testing service functionality...", "INFO")
        
        if not self.is_running():
            self.print_status("Service is not running", "ERROR")
            return False

        try:
            # Test health endpoint
            health = requests.get(f"{self.base_url}/api/health", timeout=10)
            self.print_status(f"Health Check: {health.status_code}", "SUCCESS" if health.status_code == 200 else "ERROR")
            
            # Test file upload
            files = {'file': ('service_test.txt', 'Service manager test file', 'text/plain')}
            data = {'enable_llm': 'false', 'save_to_db': 'true'}
            upload = requests.post(f"{self.base_url}/api/process-document", files=files, data=data, timeout=30)
            self.print_status(f"File Upload: {upload.status_code}", "SUCCESS" if upload.status_code == 200 else "ERROR")
            
            # Test results
            results = requests.get(f"{self.base_url}/api/results", timeout=10)
            self.print_status(f"Results API: {results.status_code}", "SUCCESS" if results.status_code == 200 else "ERROR")
            
            if results.status_code == 200:
                count = len(results.json())
                self.print_status(f"Documents in DB: {count}", "INFO")
            
            return True
            
        except Exception as e:
            self.print_status(f"Test failed: {e}", "ERROR")
            return False

def main():
    manager = BlackHoleServiceManager()
    
    if len(sys.argv) < 2:
        print("Usage: python service_manager.py [start|stop|restart|status|test]")
        print("\nCommands:")
        print("  start   - Start the service in background")
        print("  stop    - Stop the service")
        print("  restart - Restart the service")
        print("  status  - Show service status")
        print("  test    - Test service functionality")
        return

    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start()
    elif command == "stop":
        manager.stop()
    elif command == "restart":
        manager.restart()
    elif command == "status":
        manager.status()
    elif command == "test":
        manager.test()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: start, stop, restart, status, test")

if __name__ == "__main__":
    main()
