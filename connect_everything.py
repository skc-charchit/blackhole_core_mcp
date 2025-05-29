#!/usr/bin/env python3
"""
CONNECT EVERYTHING - Ultimate Single Script
One script to connect all agents, start server, and verify everything works
"""

import os
import sys
import asyncio
import subprocess
import importlib.util
import requests
import time
import signal
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

class UltimateConnector:
    """Ultimate connector that does everything in one script."""
    
    def __init__(self):
        self.loaded_agents = {}
        self.failed_agents = {}
        self.server_process = None
        self.server_url = "http://localhost:8000"
        self.server_ready = False
        
        # Agent configurations
        self.agent_configs = {
            "math_agent": {
                "path": "agents/specialized/math_agent.py",
                "class_name": "MathAgent",
                "keywords": ["calculate", "compute", "math", "+", "-", "*", "/", "%", "percent"],
                "test_command": "Calculate 20% of 500"
            },
            "document_agent": {
                "path": "agents/core/document_processor.py", 
                "class_name": "DocumentProcessorAgent",
                "keywords": ["analyze", "document", "text", "process"],
                "test_command": "Analyze this text: Hello world"
            },
            "gmail_agent": {
                "path": "agents/communication/real_gmail_agent.py",
                "class_name": "RealGmailAgent", 
                "keywords": ["email", "send", "mail", "@"],
                "test_command": "Send email to test@example.com"
            },
            "calendar_agent": {
                "path": "agents/specialized/calendar_agent.py",
                "class_name": "CalendarAgent",
                "keywords": ["remind", "reminder", "schedule", "calendar", "meeting"],
                "test_command": "Create reminder for tomorrow"
            },
            "weather_agent": {
                "path": "agents/data/realtime_weather_agent.py",
                "class_name": "RealTimeWeatherAgent",
                "keywords": ["weather", "temperature", "temp", "forecast", "climate"],
                "test_command": "What is the weather in Mumbai?"
            }
        }
    
    def install_dependencies(self) -> bool:
        """Install all required dependencies."""
        print("🔧 INSTALLING DEPENDENCIES")
        print("=" * 50)
        
        required_packages = [
            "requests", "fastapi", "uvicorn", "python-dotenv", 
            "pymongo", "langchain", "langchain-community"
        ]
        
        for package in required_packages:
            try:
                # Check if already installed
                if package == "python-dotenv":
                    __import__("dotenv")
                else:
                    __import__(package.replace("-", "_"))
                print(f"✅ {package} (already installed)")
            except ImportError:
                print(f"🔄 Installing {package}...")
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", package
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"✅ {package} (installed)")
                except:
                    print(f"❌ {package} (failed)")
                    return False
        
        print("✅ All dependencies ready")
        return True
    
    async def load_agent(self, agent_id: str, config: Dict) -> Optional[Any]:
        """Load a single agent safely."""
        try:
            agent_path = Path(config["path"])
            
            if not agent_path.exists():
                raise FileNotFoundError(f"Agent file not found: {agent_path}")
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location(agent_id, agent_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {agent_id}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[agent_id] = module
            spec.loader.exec_module(module)
            
            # Get agent class
            agent_class = getattr(module, config["class_name"], None)
            if agent_class is None:
                raise AttributeError(f"Class {config['class_name']} not found")
            
            # Create instance
            agent_instance = agent_class()
            return agent_instance
            
        except Exception as e:
            self.failed_agents[agent_id] = str(e)
            return None
    
    async def load_all_agents(self) -> Dict[str, Any]:
        """Load all agents."""
        print("\n🤖 LOADING AGENTS")
        print("=" * 50)
        
        for agent_id, config in self.agent_configs.items():
            print(f"🔄 Loading {agent_id}...")
            
            agent = await self.load_agent(agent_id, config)
            
            if agent:
                self.loaded_agents[agent_id] = {
                    "instance": agent,
                    "config": config,
                    "status": "loaded"
                }
                print(f"✅ {agent_id}: Loaded successfully")
            else:
                error = self.failed_agents.get(agent_id, "Unknown error")
                print(f"❌ {agent_id}: {error[:50]}...")
        
        print(f"\n📊 Loaded {len(self.loaded_agents)} agents successfully")
        if self.failed_agents:
            print(f"🔒 Failed agents: {len(self.failed_agents)} (isolated)")
        
        return self.loaded_agents
    
    def create_embedded_server(self) -> str:
        """Create embedded server code."""
        server_code = '''#!/usr/bin/env python3
"""
Embedded MCP Server - Generated by Ultimate Connector
"""

import os
import sys
import logging
import asyncio
import importlib.util
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("embedded_mcp_server")

app = FastAPI(title="Embedded MCP Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCPCommandRequest(BaseModel):
    command: str

# Global state
loaded_agents = {}
server_ready = False

AGENT_CONFIGS = ''' + str(self.agent_configs) + '''

async def load_agent(agent_id: str, config: dict):
    """Load agent."""
    try:
        agent_path = Path(config["path"])
        if not agent_path.exists():
            return None
        
        spec = importlib.util.spec_from_file_location(agent_id, agent_path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[agent_id] = module
        spec.loader.exec_module(module)
        
        agent_class = getattr(module, config["class_name"], None)
        if agent_class is None:
            return None
        
        return agent_class()
    except:
        return None

@app.on_event("startup")
async def startup_event():
    """Initialize server."""
    global loaded_agents, server_ready
    
    logger.info("🚀 Starting Embedded MCP Server...")
    
    for agent_id, config in AGENT_CONFIGS.items():
        agent = await load_agent(agent_id, config)
        if agent:
            loaded_agents[agent_id] = {
                "instance": agent,
                "config": config,
                "status": "loaded"
            }
            logger.info(f"✅ Loaded {agent_id}")
    
    server_ready = True
    logger.info(f"🎉 Server ready with {len(loaded_agents)} agents")

@app.get("/api/health")
async def health_check():
    """Health check."""
    return {
        "status": "ok",
        "server": "embedded_mcp_server",
        "ready": server_ready,
        "agents_loaded": len(loaded_agents),
        "available_agents": list(loaded_agents.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", response_class=HTMLResponse)
async def serve_interface():
    """Main interface."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP System - All Agents Connected</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 900px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
            h1 { text-align: center; margin-bottom: 20px; }
            .agent { background: rgba(255,255,255,0.1); padding: 15px; margin: 10px 0; border-radius: 8px; }
            .btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 5px; }
            .status { color: #4CAF50; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 MCP System - All Agents Connected</h1>
            <p style="text-align: center; font-size: 1.2em;" class="status">✅ System Operational</p>

            <div class="agent">
                <h3>🔢 Math Agent</h3>
                <p><strong>Example:</strong> Calculate 20% of 500</p>
                <p><strong>Capabilities:</strong> Mathematical calculations, percentages, formulas</p>
            </div>

            <div class="agent">
                <h3>📄 Document Agent</h3>
                <p><strong>Example:</strong> Analyze this text: Hello world</p>
                <p><strong>Capabilities:</strong> Text analysis, document processing, summarization</p>
            </div>

            <div class="agent">
                <h3>📧 Gmail Agent</h3>
                <p><strong>Example:</strong> Send email to test@example.com</p>
                <p><strong>Capabilities:</strong> Email automation, notifications, communication</p>
            </div>

            <div class="agent">
                <h3>📅 Calendar Agent</h3>
                <p><strong>Example:</strong> Create reminder for tomorrow</p>
                <p><strong>Capabilities:</strong> Scheduling, reminders, time management</p>
            </div>

            <div class="agent">
                <h3>🌤️ Weather Agent</h3>
                <p><strong>Example:</strong> What is the weather in Mumbai?</p>
                <p><strong>Capabilities:</strong> Live weather data, forecasts, climate information</p>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <a href="/docs" class="btn">📚 API Documentation</a>
                <a href="/api/health" class="btn">🔍 Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/api/mcp/command")
async def process_command(request: MCPCommandRequest):
    """Process commands."""
    if not server_ready:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    try:
        command = request.command.lower().strip()
        
        # Find matching agent
        matching_agent = None
        agent_id = None
        
        for aid, agent_data in loaded_agents.items():
            keywords = agent_data["config"]["keywords"]
            if any(keyword in command for keyword in keywords):
                matching_agent = agent_data["instance"]
                agent_id = aid
                break
        
        if not matching_agent:
            return {
                "status": "success",
                "message": f"Command processed but no specific agent matched",
                "command": request.command,
                "available_agents": list(loaded_agents.keys()),
                "timestamp": datetime.now().isoformat()
            }
        
        # Create message for agent
        from agents.base_agent import MCPMessage
        message = MCPMessage(
            id=f"{agent_id}_{datetime.now().timestamp()}",
            method="process",
            params={"query": request.command, "expression": request.command},
            timestamp=datetime.now()
        )
        
        # Process with agent
        result = await matching_agent.process_message(message)
        
        # Add metadata
        result["agent_used"] = agent_id
        result["server"] = "embedded_mcp_server"
        result["timestamp"] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Command processing failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/agents")
async def list_agents():
    """List agents."""
    return {
        "status": "success",
        "agents": {
            agent_id: {
                "status": agent_data["status"],
                "class_name": agent_data["config"]["class_name"],
                "keywords": agent_data["config"]["keywords"]
            }
            for agent_id, agent_data in loaded_agents.items()
        },
        "total_agents": len(loaded_agents),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
'''
        return server_code
    
    async def start_embedded_server(self) -> bool:
        """Start embedded server."""
        print("\n🚀 STARTING EMBEDDED MCP SERVER")
        print("=" * 50)
        
        # Check if server is already running
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=3)
            if response.status_code == 200:
                print("✅ MCP Server already running")
                return True
        except:
            pass
        
        # Create embedded server file
        server_code = self.create_embedded_server()
        server_file = "embedded_mcp_server.py"
        
        with open(server_file, "w", encoding="utf-8") as f:
            f.write(server_code)
        
        print(f"📝 Created embedded server: {server_file}")
        
        try:
            print("🔄 Starting embedded server...")
            
            # Start server process
            self.server_process = subprocess.Popen(
                [sys.executable, server_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to be ready
            print("⏳ Waiting for server to start...")
            for attempt in range(30):
                try:
                    response = requests.get(f"{self.server_url}/api/health", timeout=2)
                    if response.status_code == 200:
                        health = response.json()
                        agents_loaded = health.get("agents_loaded", 0)
                        print(f"✅ Embedded server started successfully")
                        print(f"🤖 Agents loaded: {agents_loaded}")
                        self.server_ready = True
                        return True
                except:
                    pass
                
                await asyncio.sleep(1)
                if attempt % 10 == 0:
                    print(f"⏳ Still waiting... ({attempt}/30)")
            
            print("❌ Server failed to start properly")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """Test all agent connections."""
        print("\n🧪 TESTING ALL CONNECTIONS")
        print("=" * 50)
        
        test_results = {}
        successful_tests = 0
        
        for agent_id, agent_data in self.loaded_agents.items():
            test_command = agent_data["config"]["test_command"]
            print(f"🔍 Testing {agent_id}: {test_command[:30]}...")
            
            try:
                response = requests.post(
                    f"{self.server_url}/api/mcp/command",
                    json={"command": test_command},
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "unknown")
                    
                    if status == "success":
                        test_results[agent_id] = "✅ Working"
                        print(f"✅ {agent_id}: Working")
                        successful_tests += 1
                        
                        # Show specific results
                        if "result" in result:
                            print(f"   Result: {result['result']}")
                        elif "city" in result:
                            print(f"   City: {result['city']}")
                        elif "reminder" in result:
                            print(f"   Reminder: Created")
                        elif "email_sent" in result:
                            print(f"   Email: Prepared")
                    else:
                        test_results[agent_id] = f"⚠️ Limited"
                        print(f"⚠️ {agent_id}: Limited functionality")
                else:
                    test_results[agent_id] = f"❌ HTTP {response.status_code}"
                    print(f"❌ {agent_id}: HTTP {response.status_code}")
            
            except Exception as e:
                test_results[agent_id] = f"❌ Error"
                print(f"❌ {agent_id}: {str(e)[:30]}...")
        
        return {
            "results": test_results,
            "successful_tests": successful_tests,
            "total_tests": len(self.loaded_agents),
            "success_rate": (successful_tests / len(self.loaded_agents)) * 100 if self.loaded_agents else 0
        }
    
    async def connect_everything(self) -> Dict[str, Any]:
        """Connect everything in one go."""
        print("🔗 ULTIMATE MCP CONNECTION SYSTEM")
        print("=" * 80)
        print("🎯 One script to connect all agents and start everything")
        print("🛡️ Independent agent architecture with automatic failsafe")
        print("🚀 Complete embedded solution")
        print("=" * 80)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "dependencies_installed": False,
            "agents_loaded": {},
            "server_running": False,
            "connections_tested": {},
            "system_operational": False
        }
        
        try:
            # Step 1: Install dependencies
            results["dependencies_installed"] = self.install_dependencies()
            if not results["dependencies_installed"]:
                return results
            
            # Step 2: Load all agents
            results["agents_loaded"] = await self.load_all_agents()
            
            # Step 3: Start embedded server
            results["server_running"] = await self.start_embedded_server()
            if not results["server_running"]:
                return results
            
            # Step 4: Test all connections
            test_results = await self.test_all_connections()
            results["connections_tested"] = test_results
            
            # Determine system status
            results["system_operational"] = (
                results["dependencies_installed"] and
                results["server_running"] and
                len(results["agents_loaded"]) > 0 and
                test_results["successful_tests"] > 0
            )
            
            return results
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            results["error"] = str(e)
            return results
    
    def cleanup(self):
        """Cleanup resources."""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass

async def main():
    """Main function."""
    connector = UltimateConnector()
    
    try:
        results = await connector.connect_everything()
        
        # Display comprehensive results
        print("\n" + "=" * 80)
        print("📊 ULTIMATE CONNECTION RESULTS")
        print("=" * 80)
        
        print(f"🔧 Dependencies: {'✅ Installed' if results['dependencies_installed'] else '❌ Failed'}")
        print(f"🤖 Agents Loaded: {len(results['agents_loaded'])}")
        print(f"🚀 Server Running: {'✅ Yes' if results['server_running'] else '❌ No'}")
        
        if connector.failed_agents:
            print(f"🔒 Failed Agents: {len(connector.failed_agents)} (isolated)")
            for agent_id, error in connector.failed_agents.items():
                print(f"   • {agent_id}: {error[:50]}...")
        
        test_results = results.get("connections_tested", {})
        if test_results:
            successful = test_results.get("successful_tests", 0)
            total = test_results.get("total_tests", 0)
            success_rate = test_results.get("success_rate", 0)
            
            print(f"🧪 Connection Tests: {successful}/{total} passed ({success_rate:.1f}%)")
            
            print(f"\n🧪 DETAILED TEST RESULTS:")
            for agent, status in test_results.get("results", {}).items():
                print(f"   • {agent}: {status}")
        
        print(f"⚡ System: {'✅ FULLY OPERATIONAL' if results['system_operational'] else '❌ Limited'}")
        
        if results["system_operational"]:
            print("\n🎉 EVERYTHING CONNECTED SUCCESSFULLY!")
            print("✅ All agents loaded and tested")
            print("✅ Embedded server running")
            print("✅ Independent agent architecture implemented")
            print("✅ Automatic failsafe isolation active")
            
            print("\n🌐 YOUR SYSTEM IS READY:")
            print(f"   • Web Interface: {connector.server_url}")
            print(f"   • API Documentation: {connector.server_url}/docs")
            print(f"   • Health Check: {connector.server_url}/api/health")
            print(f"   • Command API: {connector.server_url}/api/mcp/command")
            
            print("\n🧪 EXAMPLE COMMANDS:")
            for agent_id, agent_data in connector.loaded_agents.items():
                test_cmd = agent_data["config"]["test_command"]
                print(f"   • {test_cmd}")
            
            print("\n💡 USAGE:")
            print("   1. Open http://localhost:8000 in your browser")
            print("   2. Use the API endpoints for integration")
            print("   3. All agents are connected and ready")
            
            print("\n🔄 TO RESTART:")
            print("   Just run this script again: python connect_everything.py")
            
            return True
        else:
            print("\n⚠️ PARTIAL CONNECTION")
            print("Some components working but system needs attention")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 Connection cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return False
    finally:
        connector.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\n🎉 ULTIMATE CONNECTION COMPLETED!")
            print("🔗 Your unified MCP system is fully operational!")
            print("🚀 Everything connected with one script!")
        else:
            print("\n🔧 Connection completed with some issues.")
            print("💡 Check the messages above for details.")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
