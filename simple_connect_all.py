#!/usr/bin/env python3
"""
Simple Connect All - Works with current setup
Connects all available components without complex dependencies
"""

import asyncio
import subprocess
import sys
import os
import time
import requests
from pathlib import Path
from datetime import datetime

class SimpleConnector:
    """Simple connector that works with existing setup."""
    
    def __init__(self):
        self.processes = {}
        self.available_agents = []
        self.connected_agents = []
        self.failed_agents = []
    
    def check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        return Path(file_path).exists()
    
    def discover_available_agents(self):
        """Discover which agents are actually available."""
        print("🔍 DISCOVERING AVAILABLE AGENTS")
        print("=" * 50)
        
        # Check for existing agent files
        agent_files = [
            ("realtime_weather_agent", "agents/data/realtime_weather_agent.py"),
            ("math_agent", "agents/specialized/math_agent.py"),
            ("document_processor", "agents/core/document_processor.py"),
            ("real_gmail_agent", "agents/communication/real_gmail_agent.py"),
            ("calendar_agent", "agents/specialized/calendar_agent.py"),
            ("image_ocr_agent", "agents/image/image_ocr_agent.js"),
            ("pdf_extractor", "agents/pdf/pdf_extractor_agent.js"),
            ("search_agent", "agents/search/search_agent.js")
        ]
        
        for agent_name, file_path in agent_files:
            if self.check_file_exists(file_path):
                self.available_agents.append({
                    "name": agent_name,
                    "path": file_path,
                    "type": "python" if file_path.endswith(".py") else "javascript"
                })
                print(f"✅ Found: {agent_name}")
            else:
                print(f"❌ Missing: {agent_name} ({file_path})")
        
        print(f"\n📊 Available agents: {len(self.available_agents)}")
        return self.available_agents
    
    async def start_mcp_server(self) -> bool:
        """Start the MCP server."""
        print("\n🚀 STARTING MCP SERVER")
        print("=" * 50)
        
        # Check if server is already running
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=3)
            if response.status_code == 200:
                print("✅ MCP Server already running")
                return True
        except:
            pass
        
        # Try to start the main server
        server_files = ["mcp_server.py", "core/mcp_server.py"]
        
        for server_file in server_files:
            if self.check_file_exists(server_file):
                try:
                    print(f"🔄 Starting {server_file}...")
                    
                    process = subprocess.Popen(
                        [sys.executable, server_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    self.processes["mcp_server"] = process
                    
                    # Wait for server to be ready
                    for attempt in range(20):
                        try:
                            response = requests.get("http://localhost:8000/api/health", timeout=2)
                            if response.status_code == 200:
                                print("✅ MCP Server started successfully")
                                return True
                        except:
                            pass
                        
                        await asyncio.sleep(1)
                    
                    print("⚠️ Server started but not responding")
                    return False
                    
                except Exception as e:
                    print(f"❌ Failed to start {server_file}: {e}")
                    continue
        
        print("❌ No working MCP server found")
        return False
    
    async def test_server_functionality(self) -> dict:
        """Test basic server functionality."""
        print("\n🧪 TESTING SERVER FUNCTIONALITY")
        print("=" * 50)
        
        tests = {
            "health_check": False,
            "agents_endpoint": False,
            "command_endpoint": False
        }
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                tests["health_check"] = True
                print("✅ Health check passed")
                
                health_data = response.json()
                print(f"   Server: {health_data.get('mcp_server', 'Unknown')}")
                print(f"   Status: {health_data.get('status', 'Unknown')}")
            else:
                print("❌ Health check failed")
        
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        try:
            # Test agents endpoint
            response = requests.get("http://localhost:8000/api/mcp/agents", timeout=5)
            if response.status_code == 200:
                tests["agents_endpoint"] = True
                print("✅ Agents endpoint working")
                
                agents_data = response.json()
                agent_count = len(agents_data.get("agents", {}))
                print(f"   Loaded agents: {agent_count}")
            else:
                print("❌ Agents endpoint failed")
        
        except Exception as e:
            print(f"❌ Agents endpoint error: {e}")
        
        try:
            # Test command endpoint
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": "test connection"},
                timeout=10
            )
            if response.status_code == 200:
                tests["command_endpoint"] = True
                print("✅ Command endpoint working")
                
                result = response.json()
                print(f"   Response: {result.get('status', 'Unknown')}")
            else:
                print("❌ Command endpoint failed")
        
        except Exception as e:
            print(f"❌ Command endpoint error: {e}")
        
        return tests
    
    async def test_agent_functionality(self) -> dict:
        """Test individual agent functionality."""
        print("\n🤖 TESTING AGENT FUNCTIONALITY")
        print("=" * 50)
        
        agent_tests = {}
        
        # Test weather agent
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": "What is the weather in Mumbai?"},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    agent_tests["weather"] = "✅ Working"
                    print("✅ Weather agent working")
                else:
                    agent_tests["weather"] = "⚠️ Limited"
                    print("⚠️ Weather agent limited functionality")
            else:
                agent_tests["weather"] = "❌ Failed"
                print("❌ Weather agent failed")
        
        except Exception as e:
            agent_tests["weather"] = f"❌ Error: {str(e)[:30]}"
            print(f"❌ Weather agent error: {e}")
        
        # Test math agent
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": "Calculate 20% of 500"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    agent_tests["math"] = "✅ Working"
                    print("✅ Math agent working")
                else:
                    agent_tests["math"] = "⚠️ Limited"
                    print("⚠️ Math agent limited functionality")
            else:
                agent_tests["math"] = "❌ Failed"
                print("❌ Math agent failed")
        
        except Exception as e:
            agent_tests["math"] = f"❌ Error: {str(e)[:30]}"
            print(f"❌ Math agent error: {e}")
        
        return agent_tests
    
    async def check_mongodb_connection(self) -> bool:
        """Check MongoDB connection."""
        print("\n💾 CHECKING MONGODB CONNECTION")
        print("=" * 50)
        
        try:
            from pymongo import MongoClient
            
            # Try to connect to MongoDB
            client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            
            print("✅ MongoDB connected successfully")
            
            # Check databases
            db_names = client.list_database_names()
            print(f"   Available databases: {len(db_names)}")
            
            if "blackhole_mcp" in db_names:
                print("   ✅ MCP database found")
            else:
                print("   ⚠️ MCP database not found (will be created)")
            
            client.close()
            return True
            
        except ImportError:
            print("⚠️ PyMongo not installed - MongoDB features disabled")
            return False
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup running processes."""
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
    
    async def connect_all(self) -> dict:
        """Connect all available components."""
        print("🔗 SIMPLE CONNECT ALL")
        print("=" * 80)
        print("🎯 Connecting available MCP components")
        print("🛡️ Graceful handling of missing components")
        print("=" * 80)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "available_agents": 0,
            "server_running": False,
            "server_tests": {},
            "agent_tests": {},
            "mongodb_connected": False,
            "system_operational": False
        }
        
        try:
            # Step 1: Discover agents
            agents = self.discover_available_agents()
            results["available_agents"] = len(agents)
            
            # Step 2: Start MCP server
            results["server_running"] = await self.start_mcp_server()
            
            if results["server_running"]:
                # Step 3: Test server functionality
                results["server_tests"] = await self.test_server_functionality()
                
                # Step 4: Test agent functionality
                results["agent_tests"] = await self.test_agent_functionality()
            
            # Step 5: Check MongoDB
            results["mongodb_connected"] = await self.check_mongodb_connection()
            
            # Determine system status
            server_working = results["server_running"] and any(results["server_tests"].values())
            agents_working = any("✅" in status for status in results["agent_tests"].values())
            
            results["system_operational"] = server_working and (agents_working or results["available_agents"] > 0)
            
            return results
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            results["error"] = str(e)
            return results

async def main():
    """Main function."""
    connector = SimpleConnector()
    
    try:
        results = await connector.connect_all()
        
        # Display final results
        print("\n" + "=" * 80)
        print("📊 CONNECTION RESULTS")
        print("=" * 80)
        
        print(f"🔍 Available agents: {results['available_agents']}")
        print(f"🚀 MCP Server: {'✅ Running' if results['server_running'] else '❌ Failed'}")
        print(f"💾 MongoDB: {'✅ Connected' if results['mongodb_connected'] else '❌ Disconnected'}")
        print(f"⚡ System: {'✅ Operational' if results['system_operational'] else '❌ Limited'}")
        
        if results["agent_tests"]:
            print("\n🤖 AGENT STATUS:")
            for agent, status in results["agent_tests"].items():
                print(f"   • {agent}: {status}")
        
        if results["system_operational"]:
            print("\n🎉 SYSTEM CONNECTED!")
            print("✅ Your MCP system is operational")
            
            print("\n🌐 ACCESS POINTS:")
            print("   • Web Interface: http://localhost:8000")
            print("   • Health Check: http://localhost:8000/api/health")
            print("   • API Endpoint: http://localhost:8000/api/mcp/command")
            
            print("\n🧪 TEST COMMANDS:")
            print("   curl -X POST http://localhost:8000/api/mcp/command \\")
            print("        -H 'Content-Type: application/json' \\")
            print("        -d '{\"command\": \"What is the weather in Mumbai?\"}'")
            
            return True
        else:
            print("\n⚠️ PARTIAL CONNECTION")
            print("Some components are working but system needs attention")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 Connection cancelled")
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
            print("\n🎉 Connection completed successfully!")
        else:
            print("\n🔧 Connection completed with issues.")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
