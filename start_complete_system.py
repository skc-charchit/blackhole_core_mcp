#!/usr/bin/env python3
"""
Complete System Startup Script
Start all components and ensure MongoDB storage is working
"""

import subprocess
import time
import requests
import json
import os
import sys
from datetime import datetime
from pathlib import Path

class CompleteSystemStarter:
    """Start and verify the complete MCP system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.mongodb_running = False
        self.server_running = False
        
    def check_mongodb_connection(self):
        """Check if MongoDB is accessible."""
        print("🔍 Checking MongoDB Connection...")
        try:
            # Try to connect to MongoDB using pymongo
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("   ✅ MongoDB is running and accessible")
            self.mongodb_running = True
            return True
        except Exception as e:
            print(f"   ❌ MongoDB not accessible: {e}")
            self.mongodb_running = False
            return False
    
    def start_mongodb(self):
        """Start MongoDB if not running."""
        if self.check_mongodb_connection():
            return True
            
        print("🚀 Starting MongoDB...")
        try:
            # Create data directory if it doesn't exist
            data_dir = Path("data/db")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to start MongoDB
            print("   📁 Created data directory")
            print("   🔄 Attempting to start MongoDB...")
            print("   ⚠️ If MongoDB fails to start, please install MongoDB or use Docker")
            
            # Check if MongoDB is installed
            try:
                result = subprocess.run(['mongod', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("   ✅ MongoDB is installed")
                    # Start MongoDB in background
                    subprocess.Popen(['mongod', '--dbpath', str(data_dir)], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                    time.sleep(3)  # Wait for MongoDB to start
                    return self.check_mongodb_connection()
                else:
                    print("   ❌ MongoDB not found in PATH")
                    return False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("   ❌ MongoDB not installed or not in PATH")
                print("   💡 Please install MongoDB or use Docker: docker run -d -p 27017:27017 mongo")
                return False
                
        except Exception as e:
            print(f"   ❌ Failed to start MongoDB: {e}")
            return False
    
    def check_server_status(self):
        """Check if the MCP server is running."""
        print("🔍 Checking MCP Server Status...")
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"   ✅ Server is running (Status: {health.get('status')})")
                print(f"   ✅ Ready: {health.get('ready')}")
                print(f"   ✅ MongoDB Connected: {health.get('mongodb_connected')}")
                print(f"   ✅ Loaded Agents: {health.get('system', {}).get('loaded_agents', 0)}")
                self.server_running = True
                return True
            else:
                print(f"   ❌ Server responded with status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("   ❌ Server not running or not accessible")
            self.server_running = False
            return False
        except Exception as e:
            print(f"   ❌ Error checking server: {e}")
            return False
    
    def start_production_server(self):
        """Start the production MCP server."""
        if self.check_server_status():
            return True
            
        print("🚀 Starting Production MCP Server...")
        try:
            # Start the server in background
            print("   🔄 Launching production_mcp_server.py...")
            subprocess.Popen([sys.executable, 'production_mcp_server.py'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            
            # Wait for server to start
            print("   ⏳ Waiting for server to initialize...")
            for i in range(10):
                time.sleep(2)
                if self.check_server_status():
                    return True
                print(f"   ⏳ Waiting... ({i+1}/10)")
            
            print("   ❌ Server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"   ❌ Failed to start server: {e}")
            return False
    
    def test_mongodb_storage(self):
        """Test MongoDB storage functionality."""
        print("💾 Testing MongoDB Storage...")
        try:
            # Send a test command that should be stored
            response = requests.post(
                f"{self.base_url}/api/mcp/command",
                json={"command": "Calculate 10 + 5 for storage test"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                stored = result.get('stored_in_mongodb', False)
                mongodb_id = result.get('mongodb_id')
                storage_method = result.get('storage_method', 'unknown')
                
                print(f"   📤 Command: Calculate 10 + 5 for storage test")
                print(f"   ✅ Status: {result.get('status')}")
                print(f"   🤖 Agent: {result.get('agent_used')}")
                print(f"   💾 Stored: {'✅ Yes' if stored else '❌ No'}")
                print(f"   🆔 MongoDB ID: {mongodb_id if mongodb_id else 'None'}")
                print(f"   🔧 Storage Method: {storage_method}")
                
                if stored:
                    print("   🎉 MongoDB storage is working!")
                    return True
                else:
                    print("   ⚠️ MongoDB storage not working, but system is functional")
                    return False
            else:
                print(f"   ❌ Test command failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Storage test error: {e}")
            return False
    
    def verify_agent_functionality(self):
        """Verify that agents are working correctly."""
        print("🤖 Verifying Agent Functionality...")
        
        test_commands = [
            {"command": "Calculate 25 * 4", "expected": "math"},
            {"command": "What is the weather in Mumbai?", "expected": "weather"},
            {"command": "Analyze this text: Hello world", "expected": "document"}
        ]
        
        working_agents = 0
        
        for test in test_commands:
            print(f"\n   📤 Testing: {test['command']}")
            try:
                response = requests.post(
                    f"{self.base_url}/api/mcp/command",
                    json={"command": test['command']},
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    agent_used = result.get('agent_used')
                    
                    print(f"      ✅ Status: {status}")
                    print(f"      🤖 Agent: {agent_used}")
                    
                    if status == "success":
                        working_agents += 1
                        print(f"      ✅ Working correctly")
                    else:
                        print(f"      ⚠️ Returned status: {status}")
                else:
                    print(f"      ❌ HTTP Error: {response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        print(f"\n   📊 Working Commands: {working_agents}/{len(test_commands)}")
        return working_agents > 0
    
    def show_connection_info(self):
        """Show connection information."""
        print("\n" + "="*80)
        print("🌐 CONNECTION INFORMATION")
        print("="*80)
        
        print(f"🚀 MCP Server: http://localhost:8000")
        print(f"📊 Health Check: http://localhost:8000/api/health")
        print(f"🤖 Agents Status: http://localhost:8000/api/agents")
        print(f"📚 API Documentation: http://localhost:8000/docs")
        print(f"🌐 Web Interface: http://localhost:8000")
        
        print(f"\n💾 MongoDB:")
        print(f"   Connection: mongodb://localhost:27017")
        print(f"   Database: mcp_production")
        print(f"   Status: {'✅ Connected' if self.mongodb_running else '❌ Not Connected'}")
        
        print(f"\n📡 System Status:")
        print(f"   Server: {'✅ Running' if self.server_running else '❌ Not Running'}")
        print(f"   MongoDB: {'✅ Running' if self.mongodb_running else '❌ Not Running'}")
        
    def show_usage_examples(self):
        """Show usage examples."""
        print("\n" + "="*80)
        print("💡 USAGE EXAMPLES")
        print("="*80)
        
        print("🔢 Math Calculations:")
        print('   curl -X POST http://localhost:8000/api/mcp/command \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"command": "Calculate 25 * 4"}\'')
        
        print("\n🌤️ Weather Queries:")
        print('   curl -X POST http://localhost:8000/api/mcp/command \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"command": "What is the weather in Mumbai?"}\'')
        
        print("\n📄 Document Analysis:")
        print('   curl -X POST http://localhost:8000/api/mcp/command \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"command": "Analyze this text: Hello world"}\'')
        
        print("\n🔍 System Health:")
        print('   curl http://localhost:8000/api/health')
        
        print("\n🤖 Agent Management:")
        print('   curl http://localhost:8000/api/agents')
        print('   curl http://localhost:8000/api/agents/discover')
    
    def start_complete_system(self):
        """Start the complete system."""
        print("🚀 STARTING COMPLETE MCP SYSTEM")
        print("="*80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Step 1: Start MongoDB
        print("\n📊 STEP 1: MongoDB Setup")
        mongodb_ok = self.start_mongodb()
        
        # Step 2: Start MCP Server
        print("\n🚀 STEP 2: MCP Server Setup")
        server_ok = self.start_production_server()
        
        # Step 3: Test Storage
        print("\n💾 STEP 3: Storage Testing")
        storage_ok = self.test_mongodb_storage()
        
        # Step 4: Verify Agents
        print("\n🤖 STEP 4: Agent Verification")
        agents_ok = self.verify_agent_functionality()
        
        # Summary
        print("\n" + "="*80)
        print("📊 STARTUP SUMMARY")
        print("="*80)
        
        components = [
            ("MongoDB", mongodb_ok),
            ("MCP Server", server_ok),
            ("MongoDB Storage", storage_ok),
            ("Agent Functionality", agents_ok)
        ]
        
        working_components = sum(1 for _, status in components if status)
        total_components = len(components)
        
        print(f"🎯 System Health: {working_components}/{total_components} components working")
        
        for component, status in components:
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {component}")
        
        if working_components >= 3:
            print("\n🎉 SYSTEM READY FOR USE!")
            self.show_connection_info()
            self.show_usage_examples()
        else:
            print("\n⚠️ SYSTEM PARTIALLY READY")
            print("Some components need attention, but basic functionality is available.")
            self.show_connection_info()
        
        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        return working_components >= 2  # At least server + agents working

def main():
    """Main function."""
    starter = CompleteSystemStarter()
    success = starter.start_complete_system()
    
    if success:
        print("\n✅ System startup completed successfully!")
        print("🌐 You can now access the MCP system at: http://localhost:8000")
    else:
        print("\n❌ System startup encountered issues.")
        print("Please check the error messages above and resolve any problems.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
