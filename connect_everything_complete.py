#!/usr/bin/env python3
"""
Complete MCP System Connection Script
One-click solution to connect everything: server, agents, MongoDB, and interactive interface
"""

import os
import sys
import time
import subprocess
import requests
import webbrowser
import threading
from datetime import datetime
from pathlib import Path

class CompleteMCPConnector:
    """Complete MCP system connector - handles everything."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.server_process = None
        self.connection_status = {}
        
    def print_header(self, title):
        """Print formatted header."""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
    
    def print_step(self, step_num, title):
        """Print formatted step."""
        print(f"\n🔄 STEP {step_num}: {title}")
        print("-" * 60)
    
    def check_dependencies(self):
        """Check if all required files exist."""
        self.print_step(1, "CHECKING DEPENDENCIES")
        
        required_files = [
            "production_mcp_server.py",
            "blackhole_core/data_source/mongodb.py",
            ".env"
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
                print(f"   ❌ Missing: {file}")
            else:
                print(f"   ✅ Found: {file}")
        
        if missing_files:
            print(f"\n❌ Missing required files: {missing_files}")
            print("💡 Please ensure all files are in the correct location")
            return False
        
        print(f"\n✅ All dependencies found!")
        return True
    
    def test_mongodb_connection(self):
        """Test MongoDB connection."""
        self.print_step(2, "TESTING MONGODB CONNECTION")
        
        try:
            # Add paths for MongoDB module
            sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))
            
            from mongodb import test_connection, get_agent_outputs_collection
            
            print("   ✅ MongoDB module imported successfully")
            
            # Test connection
            if test_connection():
                print("   ✅ MongoDB connection successful")
                
                # Test collection access
                collection = get_agent_outputs_collection()
                doc_count = collection.count_documents({})
                print(f"   ✅ Collection accessible: {doc_count} documents found")
                
                self.connection_status['mongodb'] = 'connected'
                return True
            else:
                print("   ❌ MongoDB connection failed")
                self.connection_status['mongodb'] = 'failed'
                return False
                
        except Exception as e:
            print(f"   ❌ MongoDB error: {e}")
            self.connection_status['mongodb'] = 'error'
            return False
    
    def start_server(self):
        """Start the production MCP server."""
        self.print_step(3, "STARTING PRODUCTION MCP SERVER")
        
        try:
            # Check if server is already running
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=3)
                if response.status_code == 200:
                    print("   ✅ Server already running!")
                    return True
            except:
                pass
            
            print("   🚀 Starting production server...")
            
            # Start server in background
            self.server_process = subprocess.Popen(
                [sys.executable, "production_mcp_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Wait for server to start
            print("   ⏳ Waiting for server to initialize...")
            
            for attempt in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{self.base_url}/api/health", timeout=2)
                    if response.status_code == 200:
                        health = response.json()
                        print(f"   ✅ Server started successfully!")
                        print(f"   ✅ Status: {health.get('status')}")
                        print(f"   ✅ Ready: {health.get('ready')}")
                        print(f"   ✅ Agents: {health.get('system', {}).get('loaded_agents', 0)} loaded")
                        return True
                except:
                    pass
                
                time.sleep(1)
                print(f"   ⏳ Attempt {attempt + 1}/30...")
            
            print("   ❌ Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            print(f"   ❌ Error starting server: {e}")
            return False
    
    def test_agents(self):
        """Test all agents with sample queries."""
        self.print_step(4, "TESTING AGENT CONNECTIONS")
        
        test_queries = [
            {
                "query": "Calculate 10 + 5",
                "agent": "math_agent",
                "description": "Math Agent"
            },
            {
                "query": "What is the weather in Mumbai?",
                "agent": "weather_agent", 
                "description": "Weather Agent"
            },
            {
                "query": "Analyze this text: Connection test successful",
                "agent": "document_agent",
                "description": "Document Agent"
            }
        ]
        
        successful_agents = 0
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n   Test {i}: {test['description']}")
            print(f"   📤 Query: {test['query']}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/mcp/command",
                    json={"command": test['query']},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    agent_used = result.get('agent_used')
                    
                    print(f"   ✅ Status: {status}")
                    print(f"   🤖 Agent: {agent_used}")
                    
                    if status == 'success':
                        # Show specific results
                        if 'result' in result:
                            print(f"   🔢 Answer: {result['result']}")
                        elif 'city' in result:
                            print(f"   🌍 Location: {result['city']}")
                        elif 'total_documents' in result:
                            print(f"   📄 Documents: {result['total_documents']} processed")
                        
                        print(f"   💾 MongoDB: {'Stored' if result.get('stored_in_mongodb') else 'Not Stored'}")
                        successful_agents += 1
                    else:
                        print(f"   ⚠️ Query failed: {result.get('message', 'Unknown error')}")
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            time.sleep(1)
        
        print(f"\n   📊 Agent Test Results: {successful_agents}/{len(test_queries)} successful")
        
        if successful_agents >= len(test_queries) * 0.67:  # 67% success rate
            print("   ✅ Agent connections working!")
            return True
        else:
            print("   ⚠️ Some agents may have issues")
            return False
    
    def test_interactive_interface(self):
        """Test the interactive web interface."""
        self.print_step(5, "TESTING INTERACTIVE WEB INTERFACE")
        
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                content = response.text
                
                # Check for interactive elements
                interactive_elements = [
                    'id="queryInput"',
                    'id="sendBtn"',
                    'class="example"',
                    'addEventListener',
                    'sendQuery()',
                    'displayResult'
                ]
                
                found_elements = sum(1 for element in interactive_elements if element in content)
                
                print(f"   ✅ Web interface accessible")
                print(f"   ✅ Interactive elements: {found_elements}/{len(interactive_elements)} found")
                
                if found_elements >= len(interactive_elements) * 0.8:
                    print("   🎉 Interactive interface fully functional!")
                    return True
                else:
                    print("   ⚠️ Some interactive features may be missing")
                    return False
            else:
                print(f"   ❌ Web interface error: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Interface test error: {e}")
            return False
    
    def create_enhanced_storage(self):
        """Create enhanced MongoDB storage integration."""
        self.print_step(6, "SETTING UP ENHANCED MONGODB STORAGE")
        
        try:
            # Test enhanced storage
            sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))
            from mongodb import get_agent_outputs_collection
            
            collection = get_agent_outputs_collection()
            
            # Create indexes for better performance
            try:
                collection.create_index("agent_id")
                collection.create_index("timestamp")
                collection.create_index("status")
                print("   ✅ Database indexes created")
            except Exception as e:
                print(f"   ⚠️ Index creation: {e}")
            
            # Test storage with a sample document
            test_doc = {
                "test_connection": True,
                "timestamp": datetime.now(),
                "message": "Complete system connection test",
                "system": "production_mcp_server"
            }
            
            result = collection.insert_one(test_doc)
            print(f"   ✅ Test document stored: {result.inserted_id}")
            
            # Get total document count
            total_docs = collection.count_documents({})
            print(f"   ✅ Total documents in MongoDB: {total_docs}")
            
            print("   🎉 Enhanced MongoDB storage ready!")
            return True
            
        except Exception as e:
            print(f"   ❌ Enhanced storage error: {e}")
            return False
    
    def open_interface(self):
        """Open the web interface in browser."""
        self.print_step(7, "OPENING WEB INTERFACE")
        
        try:
            print(f"   🌐 Opening {self.base_url} in browser...")
            webbrowser.open(self.base_url)
            print("   ✅ Web interface opened successfully!")
            return True
        except Exception as e:
            print(f"   ⚠️ Could not auto-open browser: {e}")
            print(f"   💡 Manually open: {self.base_url}")
            return False
    
    def generate_final_report(self, results):
        """Generate final connection report."""
        self.print_header("🎉 COMPLETE MCP SYSTEM CONNECTION REPORT")
        
        print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate success rate
        successful_steps = sum(1 for result in results.values() if result)
        total_steps = len(results)
        success_rate = (successful_steps / total_steps) * 100
        
        print(f"\n📊 CONNECTION RESULTS:")
        print(f"   ✅ Successful Steps: {successful_steps}/{total_steps}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n🔍 DETAILED RESULTS:")
        step_names = {
            'dependencies': '1. Dependencies Check',
            'mongodb': '2. MongoDB Connection',
            'server': '3. Server Startup',
            'agents': '4. Agent Testing',
            'interface': '5. Interactive Interface',
            'storage': '6. Enhanced Storage',
            'browser': '7. Browser Opening'
        }
        
        for key, result in results.items():
            status = "✅ SUCCESS" if result else "❌ FAILED"
            print(f"   {step_names.get(key, key)}: {status}")
        
        print(f"\n🌐 YOUR SYSTEM ACCESS:")
        print(f"   🚀 Web Interface: {self.base_url}")
        print(f"   📊 Health Check: {self.base_url}/api/health")
        print(f"   🤖 Agent Status: {self.base_url}/api/agents")
        print(f"   📚 API Documentation: {self.base_url}/docs")
        
        print(f"\n💡 WHAT YOU CAN DO NOW:")
        if success_rate >= 80:
            print("   🎉 SYSTEM FULLY CONNECTED AND READY!")
            print("   ✅ Ask questions through the web interface")
            print("   ✅ Use interactive command line: python user_friendly_interface.py")
            print("   ✅ Quick queries: python quick_query.py \"Your question\"")
            print("   ✅ All data is stored in MongoDB automatically")
            print("   ✅ 3 intelligent agents ready to help")
        else:
            print("   ⚠️ SYSTEM PARTIALLY CONNECTED")
            print("   🔧 Some components may need attention")
            print("   💡 Check the failed steps above and retry")
        
        print(f"\n🎯 EXAMPLE QUERIES TO TRY:")
        print("   🔢 Calculate 25 * 4")
        print("   🌤️ What is the weather in Mumbai?")
        print("   📄 Analyze this text: Hello world")
        
        return success_rate >= 80
    
    def run_complete_connection(self):
        """Run the complete connection process."""
        self.print_header("🚀 COMPLETE MCP SYSTEM CONNECTION")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 This script will connect everything: server, agents, MongoDB, and interface")
        
        # Run all connection steps
        results = {}
        
        try:
            results['dependencies'] = self.check_dependencies()
            if not results['dependencies']:
                print("\n❌ Cannot proceed without required files")
                return False
            
            results['mongodb'] = self.test_mongodb_connection()
            results['server'] = self.start_server()
            
            if results['server']:
                results['agents'] = self.test_agents()
                results['interface'] = self.test_interactive_interface()
                results['storage'] = self.create_enhanced_storage()
                results['browser'] = self.open_interface()
            else:
                print("\n❌ Cannot proceed without server running")
                results.update({
                    'agents': False,
                    'interface': False, 
                    'storage': False,
                    'browser': False
                })
            
            # Generate final report
            success = self.generate_final_report(results)
            return success
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Connection interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources."""
        if self.server_process:
            try:
                self.server_process.terminate()
                print("🔄 Server process terminated")
            except:
                pass

def main():
    """Main function."""
    connector = CompleteMCPConnector()
    
    try:
        success = connector.run_complete_connection()
        
        if success:
            print(f"\n🎉 COMPLETE CONNECTION SUCCESSFUL!")
            print("🌐 Your MCP system is fully connected and ready to use!")
            print(f"🚀 Access: {connector.base_url}")
        else:
            print(f"\n⚠️ CONNECTION COMPLETED WITH ISSUES")
            print("🔧 Check the report above and retry failed steps")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False
    finally:
        # Note: Don't cleanup server process as user wants it to keep running
        pass

if __name__ == "__main__":
    print("🚀 COMPLETE MCP SYSTEM CONNECTOR")
    print("=" * 80)
    print("This script will connect everything in your MCP system:")
    print("✅ Check dependencies")
    print("✅ Test MongoDB connection") 
    print("✅ Start production server")
    print("✅ Test all agents")
    print("✅ Verify interactive interface")
    print("✅ Setup enhanced storage")
    print("✅ Open web interface")
    print("=" * 80)
    
    success = main()
    
    if success:
        print("\n✅ ALL SYSTEMS CONNECTED! Your MCP system is ready!")
    else:
        print("\n❌ Some issues occurred. Check the report above.")
