#!/usr/bin/env python3
"""
Test Inter-Agent Communication System
Comprehensive testing of agent coordination and MongoDB integration
"""

import asyncio
import requests
import json
from datetime import datetime

class InterAgentSystemTester:
    """Test the inter-agent communication system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
    
    def test_server_health(self):
        """Test server health and inter-agent status."""
        print("🔍 TESTING SERVER HEALTH & INTER-AGENT STATUS")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            
            if response.status_code == 200:
                health = response.json()
                
                print(f"✅ Server Status: {health.get('status', 'unknown')}")
                print(f"🚀 Server Ready: {health.get('ready', False)}")
                print(f"🤖 Agents Loaded: {health.get('agents_loaded', 0)}")
                print(f"💾 MongoDB Connected: {health.get('mongodb_connected', False)}")
                print(f"🔗 Inter-Agent Communication: {health.get('inter_agent_communication', False)}")
                
                # Check inter-agent status details
                inter_status = health.get('inter_agent_status')
                if inter_status:
                    print(f"\n📊 INTER-AGENT DETAILS:")
                    print(f"   Active Agents: {inter_status.get('active_agents', 0)}")
                    print(f"   Inactive Agents: {inter_status.get('inactive_agents', 0)}")
                    print(f"   Agent Status: {inter_status.get('agent_status', {})}")
                
                self.test_results['server_health'] = True
                return True
            else:
                print(f"❌ Server Health Check Failed: HTTP {response.status_code}")
                self.test_results['server_health'] = False
                return False
                
        except Exception as e:
            print(f"❌ Server Health Check Error: {e}")
            self.test_results['server_health'] = False
            return False
    
    def test_inter_agent_status(self):
        """Test dedicated inter-agent status endpoint."""
        print("\n🔗 TESTING INTER-AGENT STATUS ENDPOINT")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.base_url}/api/inter-agent/status", timeout=5)
            
            if response.status_code == 200:
                status = response.json()
                
                print(f"✅ Inter-Agent System: {status.get('system', 'unknown')}")
                print(f"💾 MongoDB Connected: {status.get('mongodb_connected', False)}")
                print(f"🤖 Total Agents: {status.get('total_agents', 0)}")
                print(f"⚡ Active Agents: {status.get('active_agents', 0)}")
                print(f"⚠️ Inactive Agents: {status.get('inactive_agents', 0)}")
                
                # Show communication capabilities
                comm_caps = status.get('communication_capabilities', {})
                if comm_caps:
                    print(f"\n🔗 COMMUNICATION CAPABILITIES:")
                    for agent, can_talk_to in comm_caps.items():
                        print(f"   {agent} → {can_talk_to}")
                
                self.test_results['inter_agent_status'] = True
                return True
            else:
                print(f"❌ Inter-Agent Status Failed: HTTP {response.status_code}")
                self.test_results['inter_agent_status'] = False
                return False
                
        except Exception as e:
            print(f"❌ Inter-Agent Status Error: {e}")
            self.test_results['inter_agent_status'] = False
            return False
    
    def test_single_agent_commands(self):
        """Test single agent commands."""
        print("\n🤖 TESTING SINGLE AGENT COMMANDS")
        print("=" * 60)
        
        single_agent_tests = [
            ("Calculate 20% of 500", "math_agent"),
            ("What is the weather in Mumbai?", "weather_agent"),
            ("Analyze this text: Hello world", "document_agent")
        ]
        
        for command, expected_agent in single_agent_tests:
            print(f"\n📤 Testing: {command}")
            
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
                    
                    print(f"   ✅ Status: {status}")
                    print(f"   🤖 Agent Used: {agent_used}")
                    print(f"   💾 MongoDB Stored: {stored}")
                    
                    if "result" in result:
                        print(f"   📊 Result: {result['result']}")
                    
                    self.test_results[f'single_{expected_agent}'] = status == "success"
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    self.test_results[f'single_{expected_agent}'] = False
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.test_results[f'single_{expected_agent}'] = False
    
    def test_multi_agent_coordination(self):
        """Test multi-agent coordination."""
        print("\n🔗 TESTING MULTI-AGENT COORDINATION")
        print("=" * 60)
        
        multi_agent_tests = [
            "Calculate the cost of heating based on Mumbai weather",
            "Analyze weather data and provide mathematical insights", 
            "Process weather forecast and calculate temperature trends",
            "Calculate heating costs based on weather temperature analysis"
        ]
        
        for command in multi_agent_tests:
            print(f"\n🎯 Testing Multi-Agent: {command}")
            
            try:
                # Test automatic coordination through regular command
                response = requests.post(
                    f"{self.base_url}/api/mcp/command",
                    json={"command": command},
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    status = result.get("status", "unknown")
                    agent_used = result.get("agent_used", "unknown")
                    stored = result.get("stored_in_mongodb", False)
                    
                    print(f"   ✅ Status: {status}")
                    print(f"   🤖 Agent/Coordination: {agent_used}")
                    print(f"   💾 MongoDB Stored: {stored}")
                    
                    # Check if it's a coordination result
                    if "participating_agents" in result:
                        participating = result.get("participating_agents", [])
                        inactive = result.get("inactive_agents", [])
                        print(f"   🔗 Participating Agents: {participating}")
                        print(f"   ⚠️ Inactive Agents: {inactive}")
                        
                        # Show individual agent results
                        agent_results = result.get("results", {})
                        for agent_id, agent_result in agent_results.items():
                            agent_status = agent_result.get("status", "unknown")
                            print(f"      • {agent_id}: {agent_status}")
                    
                    self.test_results[f'multi_agent_{len(self.test_results)}'] = status == "success"
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    self.test_results[f'multi_agent_{len(self.test_results)}'] = False
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.test_results[f'multi_agent_{len(self.test_results)}'] = False
    
    def test_direct_coordination_endpoint(self):
        """Test direct coordination endpoint."""
        print("\n🎯 TESTING DIRECT COORDINATION ENDPOINT")
        print("=" * 60)
        
        coordination_command = "Calculate weather-based heating costs and analyze the data"
        
        print(f"📤 Testing Direct Coordination: {coordination_command}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/mcp/coordinate",
                json={"command": coordination_command},
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                
                status = result.get("status", "unknown")
                task = result.get("task", "unknown")
                participating = result.get("participating_agents", [])
                inactive = result.get("inactive_agents", [])
                stored = result.get("stored_in_mongodb", False)
                
                print(f"   ✅ Status: {status}")
                print(f"   🎯 Task: {task}")
                print(f"   🔗 Participating: {participating}")
                print(f"   ⚠️ Inactive: {inactive}")
                print(f"   💾 MongoDB Stored: {stored}")
                
                # Show results from each agent
                agent_results = result.get("results", {})
                for agent_id, agent_result in agent_results.items():
                    agent_status = agent_result.get("status", "unknown")
                    print(f"      • {agent_id}: {agent_status}")
                
                self.test_results['direct_coordination'] = status == "success"
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                self.test_results['direct_coordination'] = False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results['direct_coordination'] = False
    
    def test_inactive_agent_handling(self):
        """Test how system handles inactive agents."""
        print("\n⚠️ TESTING INACTIVE AGENT HANDLING")
        print("=" * 60)
        
        inactive_agent_tests = [
            "Send email about weather calculations",  # Should trigger gmail (inactive)
            "Create calendar reminder for weather analysis",  # Should trigger calendar (inactive)
            "Email the heating cost calculations and schedule a meeting"  # Both inactive
        ]
        
        for command in inactive_agent_tests:
            print(f"\n📤 Testing Inactive Agent Command: {command}")
            
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
                    
                    print(f"   ✅ Status: {status}")
                    print(f"   🤖 Agent Used: {agent_used}")
                    
                    # Check if coordination was attempted
                    if "participating_agents" in result:
                        participating = result.get("participating_agents", [])
                        inactive = result.get("inactive_agents", [])
                        print(f"   🔗 Active Participants: {participating}")
                        print(f"   ⚠️ Inactive Agents: {inactive}")
                    
                    self.test_results[f'inactive_handling_{len(self.test_results)}'] = True
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    self.test_results[f'inactive_handling_{len(self.test_results)}'] = False
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.test_results[f'inactive_handling_{len(self.test_results)}'] = False
    
    def generate_summary(self):
        """Generate test summary."""
        print("\n" + "=" * 80)
        print("📊 INTER-AGENT COMMUNICATION SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed Tests: {passed_tests}")
        print(f"❌ Failed Tests: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT: Inter-agent communication system is working excellently!")
        elif success_rate >= 60:
            print(f"\n👍 GOOD: Inter-agent communication system is working well!")
        elif success_rate >= 40:
            print(f"\n⚠️ FAIR: Inter-agent communication system needs some attention!")
        else:
            print(f"\n🔧 NEEDS WORK: Inter-agent communication system requires troubleshooting!")
        
        print(f"\n🌐 ACCESS POINTS:")
        print(f"   • Server Health: {self.base_url}/api/health")
        print(f"   • Inter-Agent Status: {self.base_url}/api/inter-agent/status")
        print(f"   • Command API: {self.base_url}/api/mcp/command")
        print(f"   • Coordination API: {self.base_url}/api/mcp/coordinate")
    
    def run_all_tests(self):
        """Run all tests."""
        print("🧪 COMPREHENSIVE INTER-AGENT COMMUNICATION SYSTEM TEST")
        print("=" * 80)
        print("🎯 Testing unified agent network with MongoDB integration")
        print("⚠️ Gmail and Calendar agents are intentionally inactive")
        print("=" * 80)
        
        # Run all test categories
        if self.test_server_health():
            self.test_inter_agent_status()
            self.test_single_agent_commands()
            self.test_multi_agent_coordination()
            self.test_direct_coordination_endpoint()
            self.test_inactive_agent_handling()
        
        # Generate summary
        self.generate_summary()

def main():
    """Main test function."""
    tester = InterAgentSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
