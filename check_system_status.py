#!/usr/bin/env python3
"""
System Status Checker
Comprehensive check of all MCP system components
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any

class SystemStatusChecker:
    """Check the status of all MCP system components."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    def check_server_health(self) -> Dict[str, Any]:
        """Check server health."""
        print("🔍 Checking Server Health...")
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ Server Status: {health_data.get('status', 'unknown')}")
                print(f"   ✅ Server Ready: {health_data.get('ready', False)}")
                print(f"   ✅ MongoDB Connected: {health_data.get('mongodb_connected', False)}")
                print(f"   ✅ Inter-Agent Communication: {health_data.get('inter_agent_communication', False)}")
                
                system_info = health_data.get('system', {})
                print(f"   📊 Loaded Agents: {system_info.get('loaded_agents', 0)}")
                print(f"   📊 Failed Agents: {system_info.get('failed_agents', 0)}")
                print(f"   📊 Total Discovered: {system_info.get('total_discovered', 0)}")
                
                return {"status": "healthy", "data": health_data}
            else:
                print(f"   ❌ Server Health Check Failed: HTTP {response.status_code}")
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"   ❌ Server Health Check Error: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_agents_status(self) -> Dict[str, Any]:
        """Check agents status."""
        print("\n🤖 Checking Agents Status...")
        try:
            response = requests.get(f"{self.base_url}/api/agents", timeout=10)
            if response.status_code == 200:
                agents_data = response.json()
                agents = agents_data.get('agents', {})
                summary = agents_data.get('summary', {})
                
                print(f"   📊 Total Agents: {summary.get('total_agents', 0)}")
                print(f"   ✅ Loaded Agents: {summary.get('loaded_agents', 0)}")
                print(f"   ❌ Failed Agents: {summary.get('failed_agents', 0)}")
                print(f"   🔍 Discovered Agents: {summary.get('discovered_agents', 0)}")
                
                print("\n   📋 Agent Details:")
                for agent_id, agent_info in agents.items():
                    status = agent_info.get('status', 'unknown')
                    if status == 'loaded':
                        print(f"      ✅ {agent_id}: {status}")
                    elif status == 'failed':
                        error = agent_info.get('error', 'Unknown error')
                        print(f"      ❌ {agent_id}: {status} - {error[:50]}...")
                    else:
                        print(f"      ⚠️ {agent_id}: {status}")
                
                return {"status": "checked", "data": agents_data}
            else:
                print(f"   ❌ Agents Check Failed: HTTP {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"   ❌ Agents Check Error: {e}")
            return {"status": "error", "error": str(e)}
    
    def test_command_processing(self) -> Dict[str, Any]:
        """Test command processing."""
        print("\n🧪 Testing Command Processing...")
        
        test_commands = [
            {"command": "Calculate 25 * 4", "expected_agent": "math_agent"},
            {"command": "What is the weather in Mumbai?", "expected_agent": "weather_agent"},
            {"command": "Analyze this text: Hello world", "expected_agent": "document_agent"}
        ]
        
        results = []
        
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
                    status = result.get('status', 'unknown')
                    agent_used = result.get('agent_used', 'unknown')
                    stored = result.get('stored_in_mongodb', False)
                    
                    print(f"      ✅ Status: {status}")
                    print(f"      🤖 Agent Used: {agent_used}")
                    print(f"      💾 MongoDB Stored: {stored}")
                    
                    if 'result' in result:
                        print(f"      📊 Result: {result['result']}")
                    elif 'city' in result:
                        print(f"      🌍 City: {result['city']}")
                    elif 'message' in result:
                        print(f"      💬 Message: {result['message'][:50]}...")
                    
                    results.append({
                        "command": test['command'],
                        "status": status,
                        "agent_used": agent_used,
                        "stored": stored,
                        "success": status == "success"
                    })
                else:
                    print(f"      ❌ HTTP Error: {response.status_code}")
                    results.append({
                        "command": test['command'],
                        "status": "http_error",
                        "error": response.status_code,
                        "success": False
                    })
            except Exception as e:
                print(f"      ❌ Error: {e}")
                results.append({
                    "command": test['command'],
                    "status": "error",
                    "error": str(e),
                    "success": False
                })
        
        successful_tests = sum(1 for r in results if r.get('success', False))
        print(f"\n   📊 Command Processing Results: {successful_tests}/{len(results)} successful")
        
        return {"status": "tested", "results": results, "success_rate": successful_tests / len(results)}
    
    def check_mongodb_storage(self) -> Dict[str, Any]:
        """Check MongoDB storage functionality."""
        print("\n💾 Checking MongoDB Storage...")
        
        # Test with a simple command that should store data
        try:
            response = requests.post(
                f"{self.base_url}/api/mcp/command",
                json={"command": "Calculate 10 + 5"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                stored = result.get('stored_in_mongodb', False)
                mongodb_id = result.get('mongodb_id', None)
                storage_method = result.get('storage_method', 'unknown')
                
                print(f"   💾 Storage Status: {'✅ Stored' if stored else '❌ Not Stored'}")
                print(f"   🆔 MongoDB ID: {mongodb_id if mongodb_id else 'None'}")
                print(f"   🔧 Storage Method: {storage_method}")
                
                return {
                    "status": "checked",
                    "stored": stored,
                    "mongodb_id": mongodb_id,
                    "storage_method": storage_method
                }
            else:
                print(f"   ❌ Storage Test Failed: HTTP {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"   ❌ Storage Test Error: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_agent_discovery(self) -> Dict[str, Any]:
        """Check agent discovery functionality."""
        print("\n🔍 Checking Agent Discovery...")
        try:
            response = requests.get(f"{self.base_url}/api/agents/discover", timeout=10)
            if response.status_code == 200:
                discovery_data = response.json()
                discovered = discovery_data.get('discovered', {})
                
                print(f"   📂 Live Agents: {len(discovered.get('live', []))}")
                print(f"   📂 Inactive Agents: {len(discovered.get('inactive', []))}")
                print(f"   📂 Future Agents: {len(discovered.get('future', []))}")
                print(f"   📂 Template Agents: {len(discovered.get('templates', []))}")
                
                for folder, agents in discovered.items():
                    if agents:
                        print(f"      {folder}: {', '.join(agents)}")
                
                return {"status": "checked", "data": discovery_data}
            else:
                print(f"   ❌ Discovery Check Failed: HTTP {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"   ❌ Discovery Check Error: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive system summary."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE SYSTEM STATUS SUMMARY")
        print("="*80)
        
        # Calculate overall health
        health_checks = [
            self.results.get('server_health', {}).get('status') == 'healthy',
            self.results.get('agents_status', {}).get('status') == 'checked',
            self.results.get('command_processing', {}).get('success_rate', 0) > 0.5,
            self.results.get('mongodb_storage', {}).get('stored', False),
            self.results.get('agent_discovery', {}).get('status') == 'checked'
        ]
        
        healthy_components = sum(health_checks)
        total_components = len(health_checks)
        overall_health = (healthy_components / total_components) * 100
        
        print(f"🎯 Overall System Health: {overall_health:.1f}% ({healthy_components}/{total_components} components healthy)")
        
        # Component status
        print(f"\n📋 Component Status:")
        print(f"   🚀 Server: {'✅ Healthy' if health_checks[0] else '❌ Unhealthy'}")
        print(f"   🤖 Agents: {'✅ Working' if health_checks[1] else '❌ Issues'}")
        print(f"   🧪 Command Processing: {'✅ Working' if health_checks[2] else '❌ Issues'}")
        print(f"   💾 MongoDB Storage: {'✅ Working' if health_checks[3] else '❌ Issues'}")
        print(f"   🔍 Agent Discovery: {'✅ Working' if health_checks[4] else '❌ Issues'}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if overall_health >= 90:
            print("   🎉 Excellent! System is running optimally.")
        elif overall_health >= 70:
            print("   👍 Good! System is mostly functional with minor issues.")
        elif overall_health >= 50:
            print("   ⚠️ Fair! System has some issues that need attention.")
        else:
            print("   🔧 Poor! System needs significant attention.")
        
        # Specific issues
        if not health_checks[0]:
            print("   🔧 Fix server health issues")
        if not health_checks[1]:
            print("   🔧 Resolve agent loading problems")
        if not health_checks[2]:
            print("   🔧 Debug command processing failures")
        if not health_checks[3]:
            print("   🔧 Fix MongoDB storage connectivity")
        if not health_checks[4]:
            print("   🔧 Resolve agent discovery issues")
        
        return {
            "overall_health_percent": overall_health,
            "healthy_components": healthy_components,
            "total_components": total_components,
            "component_status": {
                "server": health_checks[0],
                "agents": health_checks[1],
                "command_processing": health_checks[2],
                "mongodb_storage": health_checks[3],
                "agent_discovery": health_checks[4]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def run_full_check(self) -> Dict[str, Any]:
        """Run comprehensive system check."""
        print("🧪 COMPREHENSIVE MCP SYSTEM STATUS CHECK")
        print("="*80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Run all checks
        self.results['server_health'] = self.check_server_health()
        self.results['agents_status'] = self.check_agents_status()
        self.results['command_processing'] = self.test_command_processing()
        self.results['mongodb_storage'] = self.check_mongodb_storage()
        self.results['agent_discovery'] = self.check_agent_discovery()
        
        # Generate summary
        self.results['summary'] = self.generate_summary()
        
        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        return self.results

def main():
    """Main function."""
    checker = SystemStatusChecker()
    results = checker.run_full_check()
    
    # Save results to file
    with open('system_status_report.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: system_status_report.json")
    
    # Return exit code based on overall health
    overall_health = results['summary']['overall_health_percent']
    if overall_health >= 70:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Issues detected

if __name__ == "__main__":
    main()
