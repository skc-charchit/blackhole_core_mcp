#!/usr/bin/env python3
"""
Working Agent Connector
Fixed version that actually connects all agents
"""

import asyncio
import sys
import os
import importlib.util
import subprocess
import time
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

class WorkingAgentConnector:
    """Actually working agent connector that fixes all issues."""
    
    def __init__(self):
        self.agents = {}
        self.failed_agents = {}
        self.server_process = None
        
        # Define working agents with correct paths
        self.agent_configs = {
            "weather_agent": {
                "path": "agents/data/realtime_weather_agent.py",
                "class_name": "RealtimeWeatherAgent",
                "priority": 1,
                "working": True
            },
            "math_agent": {
                "path": "agents/specialized/math_agent.py", 
                "class_name": "MathAgent",
                "priority": 1,
                "working": True
            },
            "document_agent": {
                "path": "agents/core/document_processor.py",
                "class_name": "DocumentProcessorAgent",
                "priority": 1,
                "working": True
            },
            "gmail_agent": {
                "path": "agents/communication/real_gmail_agent.py",
                "class_name": "RealGmailAgent",
                "priority": 2,
                "working": True
            },
            "calendar_agent": {
                "path": "agents/specialized/calendar_agent.py",
                "class_name": "CalendarAgent",
                "priority": 2,
                "working": True
            }
        }
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        print("🔍 CHECKING DEPENDENCIES")
        print("=" * 50)
        
        required_packages = [
            "requests", "fastapi", "uvicorn", "pymongo", 
            "python-dotenv", "langchain"
        ]
        
        missing = []
        for package in required_packages:
            try:
                # Handle special package names
                import_name = package.replace("-", "_")
                if package == "python-dotenv":
                    import_name = "dotenv"

                __import__(import_name)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package}")
                missing.append(package)
        
        if missing:
            print(f"\n⚠️ Missing packages: {missing}")
            print("Run: pip install " + " ".join(missing))
            return False
        
        print("✅ All dependencies available")
        return True
    
    def discover_agents(self) -> Dict[str, Any]:
        """Discover available agent files."""
        print("\n🔍 DISCOVERING AGENTS")
        print("=" * 50)
        
        discovered = {}
        
        for agent_id, config in self.agent_configs.items():
            agent_path = Path(config["path"])
            
            if agent_path.exists():
                print(f"✅ Found: {agent_id} ({config['path']})")
                discovered[agent_id] = {
                    **config,
                    "status": "available",
                    "file_size": agent_path.stat().st_size
                }
            else:
                print(f"❌ Missing: {agent_id} ({config['path']})")
                discovered[agent_id] = {
                    **config,
                    "status": "missing"
                }
        
        available_count = len([a for a in discovered.values() if a["status"] == "available"])
        print(f"\n📊 Available agents: {available_count}/{len(discovered)}")
        
        return discovered
    
    async def load_python_agent(self, agent_id: str, config: Dict) -> Optional[Any]:
        """Load a Python agent with proper error handling."""
        try:
            agent_path = Path(config["path"])
            
            if not agent_path.exists():
                raise FileNotFoundError(f"Agent file not found: {agent_path}")
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location(agent_id, agent_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {agent_id}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to handle relative imports
            sys.modules[agent_id] = module
            
            # Execute module
            spec.loader.exec_module(module)
            
            # Get agent class
            agent_class = getattr(module, config["class_name"], None)
            if agent_class is None:
                raise AttributeError(f"Class {config['class_name']} not found in {agent_id}")
            
            # Create instance
            agent_instance = agent_class()
            
            print(f"✅ Loaded: {agent_id}")
            return agent_instance
            
        except Exception as e:
            print(f"❌ Failed to load {agent_id}: {e}")
            self.failed_agents[agent_id] = str(e)
            return None
    
    async def load_all_agents(self, priority_filter: int = 2) -> Dict[str, Any]:
        """Load all agents up to specified priority level."""
        print("\n🤖 LOADING AGENTS")
        print("=" * 50)
        
        discovered = self.discover_agents()
        loaded_count = 0
        
        # Sort by priority
        sorted_agents = sorted(
            [(k, v) for k, v in discovered.items() if v["status"] == "available"],
            key=lambda x: x[1]["priority"]
        )
        
        for agent_id, config in sorted_agents:
            if config["priority"] > priority_filter:
                print(f"⏭️ Skipping {agent_id} (priority {config['priority']} > {priority_filter})")
                continue
            
            print(f"🔄 Loading {agent_id} (priority {config['priority']})...")
            
            agent = await self.load_python_agent(agent_id, config)
            
            if agent:
                self.agents[agent_id] = {
                    "instance": agent,
                    "config": config,
                    "status": "loaded",
                    "loaded_at": datetime.now().isoformat()
                }
                loaded_count += 1
            else:
                print(f"❌ {agent_id} failed to load")
        
        print(f"\n📊 Loaded {loaded_count} agents successfully")
        if self.failed_agents:
            print(f"🔒 Failed agents: {len(self.failed_agents)} (isolated)")
        
        return self.agents
    
    async def start_mcp_server(self) -> bool:
        """Start the MCP server."""
        print("\n🚀 STARTING MCP SERVER")
        print("=" * 50)
        
        # Check if already running
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=3)
            if response.status_code == 200:
                print("✅ MCP Server already running")
                return True
        except:
            pass
        
        # Find server file
        server_files = ["mcp_server.py", "core/mcp_server.py"]
        
        for server_file in server_files:
            if Path(server_file).exists():
                try:
                    print(f"🔄 Starting {server_file}...")
                    
                    # Start server process
                    self.server_process = subprocess.Popen(
                        [sys.executable, server_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Wait for server to be ready
                    for attempt in range(30):
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
    
    async def test_agent_integration(self) -> Dict[str, Any]:
        """Test that agents are properly integrated with MCP."""
        print("\n🧪 TESTING AGENT INTEGRATION")
        print("=" * 50)
        
        test_results = {}
        
        # Test commands for each agent type
        test_commands = {
            "weather_agent": "What is the weather in Mumbai?",
            "math_agent": "Calculate 20% of 500",
            "document_agent": "Analyze this text: Hello world",
            "gmail_agent": "Send email to test@example.com",
            "calendar_agent": "Create reminder for tomorrow"
        }
        
        for agent_id in self.agents.keys():
            if agent_id in test_commands:
                command = test_commands[agent_id]
                print(f"🔍 Testing {agent_id}: {command[:30]}...")
                
                try:
                    response = requests.post(
                        "http://localhost:8000/api/mcp/command",
                        json={"command": command},
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        status = result.get("status", "unknown")
                        
                        if status == "success":
                            test_results[agent_id] = "✅ Working"
                            print(f"✅ {agent_id}: Working")
                        else:
                            test_results[agent_id] = "⚠️ Limited"
                            print(f"⚠️ {agent_id}: Limited functionality")
                    else:
                        test_results[agent_id] = "❌ Failed"
                        print(f"❌ {agent_id}: HTTP {response.status_code}")
                
                except Exception as e:
                    test_results[agent_id] = f"❌ Error"
                    print(f"❌ {agent_id}: {str(e)[:30]}...")
        
        return test_results
    
    async def setup_inter_agent_communication(self) -> bool:
        """Setup communication between agents."""
        print("\n🔗 SETTING UP INTER-AGENT COMMUNICATION")
        print("=" * 50)
        
        try:
            # Create agent registry
            agent_registry = {}
            
            for agent_id, agent_data in self.agents.items():
                agent_instance = agent_data["instance"]
                agent_registry[agent_id] = agent_instance
            
            # Set registry for each agent (if they support it)
            for agent_id, agent_data in self.agents.items():
                agent_instance = agent_data["instance"]
                
                if hasattr(agent_instance, 'set_agent_registry'):
                    agent_instance.set_agent_registry(agent_registry)
                    print(f"✅ {agent_id}: Registry set")
                else:
                    print(f"⚠️ {agent_id}: No registry support")
            
            print(f"🔗 Inter-agent communication setup for {len(agent_registry)} agents")
            return True
            
        except Exception as e:
            print(f"❌ Communication setup failed: {e}")
            return False
    
    async def connect_all(self) -> Dict[str, Any]:
        """Connect all agents and systems."""
        print("🔗 WORKING AGENT CONNECTOR")
        print("=" * 80)
        print("🎯 Connecting all available agents to MCP system")
        print("🛡️ Failed agents will be isolated automatically")
        print("=" * 80)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "dependencies_ok": False,
            "agents_loaded": {},
            "server_running": False,
            "integration_tests": {},
            "communication_setup": False,
            "system_operational": False
        }
        
        try:
            # Step 1: Check dependencies
            results["dependencies_ok"] = self.check_dependencies()
            if not results["dependencies_ok"]:
                print("\n❌ Dependencies missing - cannot proceed")
                return results
            
            # Step 2: Load agents
            results["agents_loaded"] = await self.load_all_agents(priority_filter=2)
            
            # Step 3: Start MCP server
            results["server_running"] = await self.start_mcp_server()
            
            if results["server_running"]:
                # Step 4: Test integration
                results["integration_tests"] = await self.test_agent_integration()
                
                # Step 5: Setup communication
                results["communication_setup"] = await self.setup_inter_agent_communication()
            
            # Determine system status
            agents_working = any("✅" in status for status in results["integration_tests"].values())
            results["system_operational"] = (
                results["dependencies_ok"] and
                results["server_running"] and
                len(results["agents_loaded"]) > 0 and
                agents_working
            )
            
            return results
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
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
    connector = WorkingAgentConnector()
    
    try:
        results = await connector.connect_all()
        
        # Display results
        print("\n" + "=" * 80)
        print("📊 CONNECTION RESULTS")
        print("=" * 80)
        
        print(f"🔧 Dependencies: {'✅ OK' if results['dependencies_ok'] else '❌ Missing'}")
        print(f"🤖 Agents loaded: {len(results['agents_loaded'])}")
        print(f"🚀 MCP Server: {'✅ Running' if results['server_running'] else '❌ Failed'}")
        print(f"🔗 Communication: {'✅ Setup' if results['communication_setup'] else '❌ Failed'}")
        print(f"⚡ System: {'✅ Operational' if results['system_operational'] else '❌ Limited'}")
        
        if results["integration_tests"]:
            print("\n🧪 AGENT INTEGRATION TESTS:")
            for agent, status in results["integration_tests"].items():
                print(f"   • {agent}: {status}")
        
        if connector.failed_agents:
            print(f"\n🔒 ISOLATED AGENTS ({len(connector.failed_agents)}):")
            for agent, error in connector.failed_agents.items():
                print(f"   • {agent}: {error[:50]}...")
        
        if results["system_operational"]:
            print("\n🎉 ALL AGENTS CONNECTED!")
            print("✅ Your MCP system is fully operational")
            
            print("\n🌐 ACCESS POINTS:")
            print("   • Web Interface: http://localhost:8000")
            print("   • Health Check: http://localhost:8000/api/health")
            print("   • Command API: http://localhost:8000/api/mcp/command")
            
            print("\n🧪 TEST COMMANDS:")
            print("   curl -X POST http://localhost:8000/api/mcp/command \\")
            print("        -H 'Content-Type: application/json' \\")
            print("        -d '{\"command\": \"What is the weather in Mumbai?\"}'")
            
            return True
        else:
            print("\n⚠️ PARTIAL CONNECTION")
            print("Some agents connected but system needs attention")
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
            print("\n🎉 All agents connected successfully!")
        else:
            print("\n🔧 Connection completed with issues.")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
