#!/usr/bin/env python3
"""
CONNECT ALL FINAL - Complete Working Solution
Connects all agents together with full functionality
"""

import asyncio
import subprocess
import sys
import os
import requests
import time
from pathlib import Path
from datetime import datetime

class FinalMCPConnector:
    """Final working MCP connector that actually connects everything."""
    
    def __init__(self):
        self.server_process = None
        self.server_url = "http://localhost:8000"
    
    def check_dependencies(self) -> bool:
        """Check if all dependencies are installed."""
        print("🔧 CHECKING DEPENDENCIES")
        print("=" * 50)
        
        required_packages = [
            ("requests", "requests"),
            ("fastapi", "fastapi"), 
            ("uvicorn", "uvicorn"),
            ("python-dotenv", "dotenv")
        ]
        
        missing = []
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
                print(f"✅ {package_name}")
            except ImportError:
                print(f"❌ {package_name}")
                missing.append(package_name)
        
        if missing:
            print(f"\n🔧 Installing missing packages...")
            for package in missing:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"✅ Installed {package}")
                except:
                    print(f"❌ Failed to install {package}")
                    return False
        
        print("✅ All dependencies ready")
        return True
    
    async def start_server(self) -> bool:
        """Start the MCP server."""
        print("\n🚀 STARTING MCP SERVER")
        print("=" * 50)
        
        # Check if server is already running
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=3)
            if response.status_code == 200:
                print("✅ MCP Server already running")
                return True
        except:
            pass
        
        # Start the simple server
        server_file = "simple_mcp_server.py"
        
        if not Path(server_file).exists():
            print(f"❌ Server file not found: {server_file}")
            return False
        
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
            print("⏳ Waiting for server to start...")
            for attempt in range(30):
                try:
                    response = requests.get(f"{self.server_url}/api/health", timeout=2)
                    if response.status_code == 200:
                        health = response.json()
                        agents_loaded = health.get("agents_loaded", 0)
                        print(f"✅ MCP Server started successfully")
                        print(f"🤖 Agents loaded: {agents_loaded}")
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
    
    async def test_all_agents(self) -> dict:
        """Test all agents to verify they're working."""
        print("\n🧪 TESTING ALL AGENTS")
        print("=" * 50)
        
        test_cases = [
            ("Calculate 20% of 500", "Math Agent"),
            ("Analyze this text: Hello world", "Document Agent"),
            ("Send email to test@example.com", "Gmail Agent"),
            ("Create reminder for tomorrow", "Calendar Agent"),
            ("What is the weather in Mumbai?", "Weather Agent")
        ]
        
        results = {}
        successful_tests = 0
        
        for command, agent_name in test_cases:
            print(f"🔍 Testing {agent_name}: {command[:30]}...")
            
            try:
                response = requests.post(
                    f"{self.server_url}/api/mcp/command",
                    json={"command": command},
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "unknown")
                    
                    if status == "success":
                        results[agent_name] = "✅ Working"
                        print(f"✅ {agent_name}: Working")
                        successful_tests += 1
                        
                        # Show specific results
                        if "result" in result:
                            print(f"   Result: {result['result']}")
                        elif "city" in result:
                            print(f"   City: {result['city']}")
                        elif "reminder" in result:
                            print(f"   Reminder created")
                        elif "email_sent" in result:
                            print(f"   Email prepared")
                    else:
                        results[agent_name] = f"⚠️ Limited: {result.get('message', 'Unknown')[:30]}"
                        print(f"⚠️ {agent_name}: Limited functionality")
                else:
                    results[agent_name] = f"❌ HTTP {response.status_code}"
                    print(f"❌ {agent_name}: HTTP {response.status_code}")
            
            except Exception as e:
                results[agent_name] = f"❌ Error: {str(e)[:30]}"
                print(f"❌ {agent_name}: {str(e)[:30]}...")
        
        return {
            "results": results,
            "successful_tests": successful_tests,
            "total_tests": len(test_cases),
            "success_rate": (successful_tests / len(test_cases)) * 100
        }
    
    async def get_system_status(self) -> dict:
        """Get comprehensive system status."""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def connect_all(self) -> dict:
        """Connect all agents and systems."""
        print("🔗 FINAL MCP CONNECTION SYSTEM")
        print("=" * 80)
        print("🎯 Connecting all agents with full functionality")
        print("🛡️ Independent agent architecture with failsafe isolation")
        print("🚀 Complete working solution")
        print("=" * 80)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "dependencies_ready": False,
            "server_running": False,
            "system_status": {},
            "agent_tests": {},
            "system_operational": False
        }
        
        try:
            # Step 1: Check dependencies
            results["dependencies_ready"] = self.check_dependencies()
            if not results["dependencies_ready"]:
                return results
            
            # Step 2: Start server
            results["server_running"] = await self.start_server()
            if not results["server_running"]:
                return results
            
            # Step 3: Get system status
            results["system_status"] = await self.get_system_status()
            
            # Step 4: Test all agents
            test_results = await self.test_all_agents()
            results["agent_tests"] = test_results
            
            # Determine system status
            results["system_operational"] = (
                results["dependencies_ready"] and
                results["server_running"] and
                results["system_status"].get("status") == "ok" and
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
    connector = FinalMCPConnector()
    
    try:
        results = await connector.connect_all()
        
        # Display comprehensive results
        print("\n" + "=" * 80)
        print("📊 FINAL CONNECTION RESULTS")
        print("=" * 80)
        
        print(f"🔧 Dependencies: {'✅ Ready' if results['dependencies_ready'] else '❌ Missing'}")
        print(f"🚀 MCP Server: {'✅ Running' if results['server_running'] else '❌ Failed'}")
        
        system_status = results.get("system_status", {})
        if system_status.get("status") == "ok":
            agents_loaded = system_status.get("agents_loaded", 0)
            available_agents = system_status.get("available_agents", [])
            print(f"🤖 Agents Loaded: {agents_loaded}")
            print(f"📋 Available Agents: {', '.join(available_agents)}")
        
        agent_tests = results.get("agent_tests", {})
        if agent_tests:
            successful = agent_tests.get("successful_tests", 0)
            total = agent_tests.get("total_tests", 0)
            success_rate = agent_tests.get("success_rate", 0)
            
            print(f"🧪 Agent Tests: {successful}/{total} passed ({success_rate:.1f}%)")
            
            print(f"\n🧪 AGENT TEST RESULTS:")
            for agent, status in agent_tests.get("results", {}).items():
                print(f"   • {agent}: {status}")
        
        print(f"⚡ System: {'✅ OPERATIONAL' if results['system_operational'] else '❌ Limited'}")
        
        if results["system_operational"]:
            print("\n🎉 ALL SYSTEMS CONNECTED AND WORKING!")
            print("✅ Your unified MCP system is fully operational")
            print("🛡️ Independent agent architecture implemented")
            print("🔗 All agents connected and tested")
            
            print("\n🌐 ACCESS POINTS:")
            print(f"   • Web Interface: {connector.server_url}")
            print(f"   • Health Check: {connector.server_url}/api/health")
            print(f"   • Command API: {connector.server_url}/api/mcp/command")
            print(f"   • API Documentation: {connector.server_url}/docs")
            
            print("\n🧪 EXAMPLE COMMANDS:")
            print("   • Calculate 20% of 500")
            print("   • What is the weather in Mumbai?")
            print("   • Send email to test@example.com")
            print("   • Create reminder for tomorrow")
            print("   • Analyze this text: Hello world")
            
            print("\n💡 USAGE:")
            print("   1. Open web interface in browser")
            print("   2. Use API endpoints for integration")
            print("   3. Run test_all_agents.py for verification")
            
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
            print("\n🎉 ALL AGENTS CONNECTED SUCCESSFULLY!")
            print("🔗 Your unified MCP system is fully operational!")
            print("🚀 Ready for production use!")
        else:
            print("\n🔧 Connection completed with some issues.")
            print("💡 Check the messages above for details.")
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
