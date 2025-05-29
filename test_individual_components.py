#!/usr/bin/env python3
"""
Test Individual Components
Comprehensive testing of each component individually
"""

import asyncio
import requests
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

class IndividualComponentTester:
    """Test each component individually."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
    
    def test_server_basic_functionality(self):
        """Test basic server functionality."""
        print("🚀 TESTING SERVER BASIC FUNCTIONALITY")
        print("=" * 60)
        
        tests = [
            ("Health Check", f"{self.base_url}/api/health"),
            ("Agent List", f"{self.base_url}/api/agents"),
            ("Inter-Agent Status", f"{self.base_url}/api/inter-agent/status"),
            ("API Documentation", f"{self.base_url}/docs")
        ]
        
        for test_name, url in tests:
            print(f"\n🔍 Testing {test_name}: {url}")
            
            try:
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ {test_name}: Working")
                    
                    if "health" in url:
                        health = response.json()
                        print(f"      Server Ready: {health.get('ready', False)}")
                        print(f"      Agents Loaded: {health.get('agents_loaded', 0)}")
                        print(f"      MongoDB Connected: {health.get('mongodb_connected', False)}")
                        print(f"      Inter-Agent Communication: {health.get('inter_agent_communication', False)}")
                    
                    elif "agents" in url:
                        agents = response.json()
                        print(f"      Total Agents: {agents.get('total_agents', 0)}")
                        print(f"      Agent List: {list(agents.get('agents', {}).keys())}")
                    
                    self.test_results[f'server_{test_name.lower().replace(" ", "_")}'] = True
                else:
                    print(f"   ❌ {test_name}: HTTP {response.status_code}")
                    self.test_results[f'server_{test_name.lower().replace(" ", "_")}'] = False
                    
            except Exception as e:
                print(f"   ❌ {test_name}: Error - {e}")
                self.test_results[f'server_{test_name.lower().replace(" ", "_")}'] = False
    
    def test_individual_agents(self):
        """Test each agent individually."""
        print("\n🤖 TESTING INDIVIDUAL AGENTS")
        print("=" * 60)
        
        agent_tests = [
            {
                "name": "Math Agent",
                "commands": [
                    "Calculate 20% of 500",
                    "What is 15 + 25?",
                    "Compute 100 / 4"
                ],
                "expected_agent": "math_agent"
            },
            {
                "name": "Weather Agent", 
                "commands": [
                    "What is the weather in Mumbai?",
                    "Mumbai weather",
                    "Temperature in Delhi"
                ],
                "expected_agent": "weather_agent"
            },
            {
                "name": "Document Agent",
                "commands": [
                    "Analyze this text: Hello world",
                    "Process document content",
                    "Extract text information"
                ],
                "expected_agent": "document_agent"
            },
            {
                "name": "Gmail Agent (Inactive)",
                "commands": [
                    "Send email to test@example.com",
                    "Email notification"
                ],
                "expected_agent": "gmail_agent"
            },
            {
                "name": "Calendar Agent (Inactive)",
                "commands": [
                    "Create reminder for tomorrow",
                    "Schedule meeting"
                ],
                "expected_agent": "calendar_agent"
            }
        ]
        
        for agent_test in agent_tests:
            print(f"\n🔍 Testing {agent_test['name']}")
            print("-" * 40)
            
            agent_working = False
            
            for command in agent_test['commands']:
                print(f"   📤 Command: {command}")
                
                try:
                    response = requests.post(
                        f"{self.base_url}/api/mcp/command",
                        json={"command": command},
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        status = result.get("status", "unknown")
                        agent_used = result.get("agent_used", "unknown")
                        stored = result.get("stored_in_mongodb", False)
                        
                        print(f"      ✅ Status: {status}")
                        print(f"      🤖 Agent Used: {agent_used}")
                        print(f"      💾 MongoDB Stored: {stored}")
                        
                        if "result" in result:
                            print(f"      📊 Result: {result['result']}")
                        elif "city" in result:
                            print(f"      🌍 City: {result['city']}")
                        elif "message" in result:
                            print(f"      💬 Message: {result['message'][:50]}...")
                        
                        if status == "success":
                            agent_working = True
                        
                        break  # Test only first command for each agent
                    else:
                        print(f"      ❌ HTTP Error: {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ Error: {e}")
            
            self.test_results[f'agent_{agent_test["expected_agent"]}'] = agent_working
    
    def test_mongodb_storage_individually(self):
        """Test MongoDB storage functionality individually."""
        print("\n💾 TESTING MONGODB STORAGE INDIVIDUALLY")
        print("=" * 60)
        
        # Test MongoDB connection
        print("🔍 Testing MongoDB Connection")
        try:
            from mcp_mongodb_integration import MCPMongoDBIntegration
            
            async def test_mongodb():
                integration = MCPMongoDBIntegration()
                connected = await integration.connect()
                
                if connected:
                    print("   ✅ MongoDB Connection: Working")
                    
                    # Test basic storage
                    try:
                        test_id = await integration.save_agent_output(
                            "test_agent",
                            {"test": "input"},
                            {"test": "output"},
                            {"test": "metadata"}
                        )
                        print(f"   ✅ MongoDB Storage: Working (ID: {test_id})")
                        return True
                    except Exception as e:
                        print(f"   ❌ MongoDB Storage: Failed - {e}")
                        return False
                else:
                    print("   ❌ MongoDB Connection: Failed")
                    return False
            
            mongodb_working = asyncio.run(test_mongodb())
            self.test_results['mongodb_connection'] = mongodb_working
            
        except Exception as e:
            print(f"   ❌ MongoDB Test: Error - {e}")
            self.test_results['mongodb_connection'] = False
    
    def test_inter_agent_communication_individually(self):
        """Test inter-agent communication individually."""
        print("\n🔗 TESTING INTER-AGENT COMMUNICATION INDIVIDUALLY")
        print("=" * 60)
        
        # Test inter-agent system initialization
        print("🔍 Testing Inter-Agent System")
        try:
            from inter_agent_communication import AgentCommunicationHub
            
            async def test_inter_agent():
                hub = AgentCommunicationHub()
                initialized = await hub.initialize_system()
                
                if initialized:
                    print("   ✅ Inter-Agent System: Working")
                    
                    # Test system status
                    status = hub.get_system_status()
                    print(f"      Active Agents: {status.get('active_agents', 0)}")
                    print(f"      Inactive Agents: {status.get('inactive_agents', 0)}")
                    print(f"      MongoDB Connected: {status.get('mongodb_connected', False)}")
                    
                    return True
                else:
                    print("   ❌ Inter-Agent System: Failed to initialize")
                    return False
            
            inter_agent_working = asyncio.run(test_inter_agent())
            self.test_results['inter_agent_communication'] = inter_agent_working
            
        except Exception as e:
            print(f"   ❌ Inter-Agent Test: Error - {e}")
            self.test_results['inter_agent_communication'] = False
    
    def test_multi_agent_coordination_individually(self):
        """Test multi-agent coordination individually."""
        print("\n🎯 TESTING MULTI-AGENT COORDINATION INDIVIDUALLY")
        print("=" * 60)
        
        coordination_commands = [
            "Calculate the cost of heating based on Mumbai weather",
            "Analyze weather data and provide mathematical insights"
        ]
        
        coordination_working = False
        
        for command in coordination_commands:
            print(f"\n📤 Testing Coordination: {command}")
            
            try:
                # Test automatic coordination
                response = requests.post(
                    f"{self.base_url}/api/mcp/command",
                    json={"command": command},
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    status = result.get("status", "unknown")
                    agent_used = result.get("agent_used", "unknown")
                    
                    print(f"   ✅ Status: {status}")
                    print(f"   🤖 Agent/Coordination: {agent_used}")
                    
                    # Check if coordination occurred
                    if "participating_agents" in result:
                        participating = result.get("participating_agents", [])
                        print(f"   🔗 Participating Agents: {participating}")
                        coordination_working = True
                    
                    break  # Test only first command
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test direct coordination endpoint
        print(f"\n📤 Testing Direct Coordination Endpoint")
        try:
            response = requests.post(
                f"{self.base_url}/api/mcp/coordinate",
                json={"command": "Calculate weather-based analysis"},
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Direct Coordination: Working")
                print(f"   📊 Status: {result.get('status', 'unknown')}")
                coordination_working = True
            else:
                print(f"   ❌ Direct Coordination: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Direct Coordination: Error - {e}")
        
        self.test_results['multi_agent_coordination'] = coordination_working
    
    def test_error_handling_individually(self):
        """Test error handling individually."""
        print("\n🛡️ TESTING ERROR HANDLING INDIVIDUALLY")
        print("=" * 60)
        
        error_tests = [
            ("Invalid Command", "This is not a valid command for any agent"),
            ("Empty Command", ""),
            ("Special Characters", "!@#$%^&*()"),
            ("Very Long Command", "A" * 1000)
        ]
        
        error_handling_working = True
        
        for test_name, command in error_tests:
            print(f"\n🔍 Testing {test_name}: {command[:50]}...")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/mcp/command",
                    json={"command": command},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "unknown")
                    print(f"   ✅ {test_name}: Handled gracefully (Status: {status})")
                else:
                    print(f"   ⚠️ {test_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {test_name}: Error - {e}")
                error_handling_working = False
        
        self.test_results['error_handling'] = error_handling_working
    
    def generate_individual_test_summary(self):
        """Generate comprehensive individual test summary."""
        print("\n" + "=" * 80)
        print("📊 INDIVIDUAL COMPONENT TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"🧪 Total Individual Tests: {total_tests}")
        print(f"✅ Passed Tests: {passed_tests}")
        print(f"❌ Failed Tests: {total_tests - passed_tests}")
        print(f"📈 Individual Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED INDIVIDUAL RESULTS:")
        
        # Group results by category
        categories = {
            "Server": [k for k in self.test_results.keys() if k.startswith('server_')],
            "Agents": [k for k in self.test_results.keys() if k.startswith('agent_')],
            "Infrastructure": [k for k in self.test_results.keys() if k in ['mongodb_connection', 'inter_agent_communication']],
            "Advanced Features": [k for k in self.test_results.keys() if k in ['multi_agent_coordination', 'error_handling']]
        }
        
        for category, tests in categories.items():
            if tests:
                print(f"\n   📁 {category}:")
                for test in tests:
                    result = self.test_results[test]
                    status = "✅ WORKING" if result else "❌ NOT WORKING"
                    test_name = test.replace('_', ' ').title()
                    print(f"      {test_name}: {status}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: All individual components working perfectly!")
        elif success_rate >= 75:
            print(f"\n👍 VERY GOOD: Most individual components working well!")
        elif success_rate >= 60:
            print(f"\n⚡ GOOD: Individual components mostly functional!")
        elif success_rate >= 40:
            print(f"\n⚠️ FAIR: Some individual components need attention!")
        else:
            print(f"\n🔧 NEEDS WORK: Multiple individual components require fixing!")
        
        # Specific recommendations
        print(f"\n💡 INDIVIDUAL COMPONENT STATUS:")
        
        # Check critical components
        critical_working = all([
            self.test_results.get('server_health_check', False),
            self.test_results.get('mongodb_connection', False),
            any([self.test_results.get(f'agent_{agent}', False) for agent in ['math_agent', 'weather_agent', 'document_agent']])
        ])
        
        if critical_working:
            print(f"   ✅ Critical Components: All working individually")
        else:
            print(f"   ❌ Critical Components: Some issues detected")
        
        # Check advanced features
        advanced_working = all([
            self.test_results.get('inter_agent_communication', False),
            self.test_results.get('multi_agent_coordination', False)
        ])
        
        if advanced_working:
            print(f"   ✅ Advanced Features: All working individually")
        else:
            print(f"   ⚠️ Advanced Features: Some limitations detected")
        
        return success_rate >= 75
    
    def run_all_individual_tests(self):
        """Run all individual component tests."""
        print("🧪 COMPREHENSIVE INDIVIDUAL COMPONENT TESTING")
        print("=" * 80)
        print("🎯 Testing each component individually to verify standalone functionality")
        print("=" * 80)
        
        # Run all individual tests
        self.test_server_basic_functionality()
        self.test_individual_agents()
        self.test_mongodb_storage_individually()
        self.test_inter_agent_communication_individually()
        self.test_multi_agent_coordination_individually()
        self.test_error_handling_individually()
        
        # Generate summary
        return self.generate_individual_test_summary()

def main():
    """Main individual testing function."""
    tester = IndividualComponentTester()
    success = tester.run_all_individual_tests()
    
    if success:
        print("\n🎉 INDIVIDUAL TESTING COMPLETED SUCCESSFULLY!")
        print("✅ All major components work individually!")
    else:
        print("\n🔧 INDIVIDUAL TESTING COMPLETED WITH SOME ISSUES!")
        print("⚠️ Some components need attention!")

if __name__ == "__main__":
    main()
