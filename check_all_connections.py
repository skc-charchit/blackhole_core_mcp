#!/usr/bin/env python3
"""
Check All Connections
Comprehensive test of all MCP system connections
"""

import os
import sys
import requests
import time
from datetime import datetime
from pathlib import Path

class ConnectionChecker:
    """Comprehensive connection checker for MCP system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {}
        
    def print_header(self, title):
        """Print formatted header."""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
    
    def print_test(self, test_name, status, details=""):
        """Print test result."""
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}: {'PASS' if status else 'FAIL'}")
        if details:
            print(f"   {details}")
    
    def check_server_health(self):
        """Check server health and status."""
        print("\n🔍 CHECKING SERVER HEALTH")
        print("-" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                
                # Check basic health
                server_status = health.get('status') == 'ok'
                server_ready = health.get('ready', False)
                
                self.print_test("Server Status", server_status, f"Status: {health.get('status')}")
                self.print_test("Server Ready", server_ready, f"Ready: {server_ready}")
                
                # Check system info
                system = health.get('system', {})
                loaded_agents = system.get('loaded_agents', 0)
                failed_agents = system.get('failed_agents', 0)
                
                self.print_test("Agents Loaded", loaded_agents > 0, f"Loaded: {loaded_agents}, Failed: {failed_agents}")
                
                # Check MongoDB
                mongodb_connected = health.get('mongodb_connected', False)
                self.print_test("MongoDB Connection", mongodb_connected, f"Connected: {mongodb_connected}")
                
                self.results['server'] = {
                    'status': server_status,
                    'ready': server_ready,
                    'agents': loaded_agents,
                    'mongodb': mongodb_connected
                }
                
                return server_status and server_ready
            else:
                self.print_test("Server Response", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Server Connection", False, f"Error: {e}")
            return False
    
    def check_mongodb_connection(self):
        """Check MongoDB connection directly."""
        print("\n💾 CHECKING MONGODB CONNECTION")
        print("-" * 60)
        
        try:
            # Add MongoDB path
            sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))
            
            from mongodb import test_connection, get_agent_outputs_collection
            
            # Test connection
            connection_ok = test_connection()
            self.print_test("MongoDB Connection", connection_ok)
            
            if connection_ok:
                # Test collection access
                try:
                    collection = get_agent_outputs_collection()
                    doc_count = collection.count_documents({})
                    self.print_test("Collection Access", True, f"Documents: {doc_count}")
                    
                    # Test write operation
                    test_doc = {
                        "test": True,
                        "timestamp": datetime.now(),
                        "checker": "connection_test"
                    }
                    result = collection.insert_one(test_doc)
                    self.print_test("Write Operation", True, f"Inserted: {result.inserted_id}")
                    
                    self.results['mongodb'] = {
                        'connected': True,
                        'documents': doc_count,
                        'writable': True
                    }
                    return True
                    
                except Exception as e:
                    self.print_test("Collection Operations", False, f"Error: {e}")
                    self.results['mongodb'] = {'connected': True, 'operations': False}
                    return False
            else:
                self.results['mongodb'] = {'connected': False}
                return False
                
        except Exception as e:
            self.print_test("MongoDB Module", False, f"Error: {e}")
            self.results['mongodb'] = {'error': str(e)}
            return False
    
    def check_agents(self):
        """Check all agent connections."""
        print("\n🤖 CHECKING AGENT CONNECTIONS")
        print("-" * 60)
        
        # Get agent status
        try:
            response = requests.get(f"{self.base_url}/api/agents", timeout=5)
            if response.status_code == 200:
                agents_data = response.json()
                agents = agents_data.get('agents', {})
                
                print(f"📊 Total Agents Found: {len(agents)}")
                
                loaded_agents = []
                for agent_id, agent_info in agents.items():
                    status = agent_info.get('status', 'unknown')
                    health = agent_info.get('health', 'unknown')
                    
                    agent_ok = status == 'loaded' and health == 'healthy'
                    self.print_test(f"Agent {agent_id}", agent_ok, f"Status: {status}, Health: {health}")
                    
                    if agent_ok:
                        loaded_agents.append(agent_id)
                
                self.results['agents'] = {
                    'total': len(agents),
                    'loaded': len(loaded_agents),
                    'list': loaded_agents
                }
                
                return len(loaded_agents) > 0
            else:
                self.print_test("Agent API", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Agent Check", False, f"Error: {e}")
            return False
    
    def test_agent_functionality(self):
        """Test agent functionality with real queries."""
        print("\n🧪 TESTING AGENT FUNCTIONALITY")
        print("-" * 60)
        
        test_queries = [
            {
                "query": "Calculate 15 + 25",
                "agent": "math_agent",
                "expected_result": 40.0,
                "description": "Math Agent Test"
            },
            {
                "query": "What is the weather in Mumbai?",
                "agent": "weather_agent",
                "expected_field": "city",
                "description": "Weather Agent Test"
            },
            {
                "query": "Analyze this text: Connection test successful",
                "agent": "document_agent",
                "expected_field": "total_documents",
                "description": "Document Agent Test"
            }
        ]
        
        working_agents = 0
        agent_results = {}
        
        for test in test_queries:
            print(f"\n   Testing: {test['description']}")
            print(f"   Query: {test['query']}")
            
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
                    
                    print(f"   Status: {status}")
                    print(f"   Agent: {agent_used}")
                    
                    if status == 'success':
                        # Check specific results
                        if 'expected_result' in test:
                            actual = result.get('result')
                            expected = test['expected_result']
                            result_ok = actual == expected
                            print(f"   Result: {actual} (Expected: {expected})")
                        elif 'expected_field' in test:
                            field = test['expected_field']
                            result_ok = field in result
                            print(f"   Field '{field}': {'Present' if result_ok else 'Missing'}")
                        else:
                            result_ok = True
                        
                        mongodb_stored = result.get('stored_in_mongodb', False)
                        print(f"   MongoDB: {'Stored' if mongodb_stored else 'Not Stored'}")
                        
                        if result_ok:
                            working_agents += 1
                            self.print_test(test['description'], True)
                        else:
                            self.print_test(test['description'], False, "Unexpected result")
                        
                        agent_results[test['agent']] = {
                            'working': result_ok,
                            'status': status,
                            'mongodb': mongodb_stored
                        }
                    else:
                        self.print_test(test['description'], False, f"Status: {status}")
                        agent_results[test['agent']] = {'working': False, 'status': status}
                else:
                    self.print_test(test['description'], False, f"HTTP {response.status_code}")
                    agent_results[test['agent']] = {'working': False, 'error': f"HTTP {response.status_code}"}
                    
            except Exception as e:
                self.print_test(test['description'], False, f"Error: {e}")
                agent_results[test['agent']] = {'working': False, 'error': str(e)}
            
            time.sleep(1)
        
        self.results['agent_functionality'] = {
            'working': working_agents,
            'total': len(test_queries),
            'details': agent_results
        }
        
        print(f"\n📊 Agent Functionality: {working_agents}/{len(test_queries)} working")
        return working_agents >= len(test_queries) * 0.67  # 67% success rate
    
    def check_web_interface(self):
        """Check web interface functionality."""
        print("\n🌐 CHECKING WEB INTERFACE")
        print("-" * 60)
        
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                content = response.text
                
                # Check for essential elements
                essential_elements = [
                    ('Input Box', 'id="queryInput"'),
                    ('Send Button', 'id="sendBtn"'),
                    ('Clear Button', 'id="clearBtn"'),
                    ('History Button', 'id="historyBtn"'),
                    ('Example Queries', 'class="example"'),
                    ('JavaScript Functions', 'sendQuery()'),
                    ('Event Listeners', 'addEventListener'),
                    ('Display Function', 'displayResult'),
                    ('Status Section', 'id="systemStatus"'),
                    ('Output Section', 'id="output"')
                ]
                
                found_elements = 0
                for name, element in essential_elements:
                    present = element in content
                    self.print_test(name, present)
                    if present:
                        found_elements += 1
                
                interactive_score = (found_elements / len(essential_elements)) * 100
                print(f"\n📊 Interactive Elements: {found_elements}/{len(essential_elements)} ({interactive_score:.0f}%)")
                
                self.results['web_interface'] = {
                    'accessible': True,
                    'elements': found_elements,
                    'total': len(essential_elements),
                    'score': interactive_score
                }
                
                return interactive_score >= 80
            else:
                self.print_test("Web Interface Access", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Web Interface", False, f"Error: {e}")
            return False
    
    def check_api_endpoints(self):
        """Check API endpoint functionality."""
        print("\n🔌 CHECKING API ENDPOINTS")
        print("-" * 60)
        
        endpoints = [
            ("/api/health", "Health Check"),
            ("/api/agents", "Agent Status"),
            ("/docs", "API Documentation"),
            ("/api/agents/discover", "Agent Discovery")
        ]
        
        working_endpoints = 0
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                success = response.status_code == 200
                self.print_test(name, success, f"HTTP {response.status_code}")
                if success:
                    working_endpoints += 1
            except Exception as e:
                self.print_test(name, False, f"Error: {e}")
        
        self.results['api_endpoints'] = {
            'working': working_endpoints,
            'total': len(endpoints)
        }
        
        return working_endpoints >= len(endpoints) * 0.75  # 75% success rate
    
    def generate_final_report(self):
        """Generate comprehensive final report."""
        self.print_header("📊 COMPREHENSIVE CONNECTION REPORT")
        
        print(f"🕐 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate overall health
        tests = [
            ('Server Health', self.results.get('server', {}).get('status', False)),
            ('MongoDB Connection', self.results.get('mongodb', {}).get('connected', False)),
            ('Agent Status', len(self.results.get('agents', {}).get('loaded', [])) > 0),
            ('Agent Functionality', self.results.get('agent_functionality', {}).get('working', 0) > 0),
            ('Web Interface', self.results.get('web_interface', {}).get('accessible', False)),
            ('API Endpoints', self.results.get('api_endpoints', {}).get('working', 0) > 0)
        ]
        
        passed_tests = sum(1 for _, status in tests if status)
        total_tests = len(tests)
        health_score = (passed_tests / total_tests) * 100
        
        print(f"\n🎯 OVERALL SYSTEM HEALTH: {health_score:.0f}%")
        print(f"📊 Tests Passed: {passed_tests}/{total_tests}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, status in tests:
            icon = "✅" if status else "❌"
            print(f"   {icon} {test_name}: {'PASS' if status else 'FAIL'}")
        
        # Detailed component status
        print(f"\n🔍 COMPONENT DETAILS:")
        
        # Server
        server = self.results.get('server', {})
        print(f"   🚀 Server: Ready={server.get('ready')}, Agents={server.get('agents')}")
        
        # MongoDB
        mongodb = self.results.get('mongodb', {})
        if mongodb.get('connected'):
            print(f"   💾 MongoDB: Connected, Documents={mongodb.get('documents', 0)}")
        else:
            print(f"   💾 MongoDB: Disconnected")
        
        # Agents
        agents = self.results.get('agents', {})
        agent_func = self.results.get('agent_functionality', {})
        print(f"   🤖 Agents: {agents.get('loaded', 0)} loaded, {agent_func.get('working', 0)} functional")
        
        # Interface
        interface = self.results.get('web_interface', {})
        print(f"   🌐 Interface: {interface.get('score', 0):.0f}% interactive")
        
        # API
        api = self.results.get('api_endpoints', {})
        print(f"   🔌 API: {api.get('working', 0)}/{api.get('total', 0)} endpoints working")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if health_score >= 90:
            print("   🎉 EXCELLENT! All systems working perfectly")
            print("   ✅ Your MCP system is production-ready")
        elif health_score >= 75:
            print("   👍 GOOD! Most systems working well")
            print("   🔧 Minor issues detected - check failed components")
        elif health_score >= 50:
            print("   ⚠️ FAIR! System partially functional")
            print("   🔧 Several issues need attention")
        else:
            print("   ❌ POOR! Major issues detected")
            print("   🚨 System needs significant troubleshooting")
        
        print(f"\n🌐 ACCESS YOUR SYSTEM:")
        print(f"   🚀 Web Interface: {self.base_url}")
        print(f"   📊 Health Check: {self.base_url}/api/health")
        print(f"   🤖 Agent Status: {self.base_url}/api/agents")
        
        return health_score >= 75
    
    def run_all_checks(self):
        """Run all connection checks."""
        self.print_header("🔍 CHECKING ALL MCP SYSTEM CONNECTIONS")
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all checks
        server_ok = self.check_server_health()
        mongodb_ok = self.check_mongodb_connection()
        agents_ok = self.check_agents()
        functionality_ok = self.test_agent_functionality()
        interface_ok = self.check_web_interface()
        api_ok = self.check_api_endpoints()
        
        # Generate final report
        overall_ok = self.generate_final_report()
        
        return overall_ok

def main():
    """Main function."""
    checker = ConnectionChecker()
    
    try:
        success = checker.run_all_checks()
        
        if success:
            print(f"\n✅ ALL CONNECTIONS WORKING FINE!")
            print("🎉 Your MCP system is healthy and ready to use!")
        else:
            print(f"\n⚠️ SOME CONNECTION ISSUES DETECTED")
            print("🔧 Check the report above for details")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Connection check failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Connection check completed successfully!")
    else:
        print("\n🔧 Connection check completed with issues.")
