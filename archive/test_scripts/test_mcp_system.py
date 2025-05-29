#!/usr/bin/env python3
"""
Comprehensive test for the Enhanced MCP System
"""

import requests
import json

def test_mcp_commands():
    """Test various MCP commands to verify the system works correctly."""
    
    print("🕳️ BlackHole Core MCP - Comprehensive System Test")
    print("=" * 60)
    
    # Test commands
    test_commands = [
        "search for documents about AI",
        "get live weather data",
        "find information about machine learning",
        "analyze this text: BlackHole Core MCP is an advanced system",
        "help",
        "what can you do"
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n🔍 Test {i}: {command}")
        print("-" * 40)
        
        try:
            response = requests.post(
                'http://localhost:8000/api/mcp/command',
                json={'command': command},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {result.get('status')}")
                print(f"🤖 Agent: {result.get('agent_used')}")
                print(f"📝 Type: {result.get('command_type')}")
                print(f"⏱️ Time: {result.get('processing_time_ms')}ms")
                
                # Show result preview
                if 'result' in result:
                    result_str = json.dumps(result['result'], indent=2)
                    preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
                    print(f"📊 Result Preview:\n{preview}")
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test MCP status
    print(f"\n🔍 Testing MCP Status")
    print("-" * 40)
    
    try:
        response = requests.get('http://localhost:8000/api/mcp/status')
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Total Agents: {status.get('total_agents')}")
            print(f"✅ Available Agents: {status.get('available_agents')}")
            
            for agent_name, agent_info in status.get('agents', {}).items():
                status_icon = "✅" if agent_info.get('status') == 'available' else "❌"
                print(f"{status_icon} {agent_name}: {agent_info.get('status')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    # Test help system
    print(f"\n🔍 Testing Help System")
    print("-" * 40)
    
    try:
        response = requests.get('http://localhost:8000/api/mcp/help')
        if response.status_code == 200:
            help_data = response.json()
            print(f"✅ Help Status: {help_data.get('status')}")
            
            commands = help_data.get('result', {}).get('commands', [])
            print(f"✅ Available Commands: {len(commands)}")
            
            for cmd in commands[:3]:  # Show first 3 commands
                print(f"  📝 {cmd.get('command')}: {cmd.get('description')}")
        else:
            print(f"❌ Help failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Help error: {e}")
    
    print(f"\n🎉 MCP System Test Complete!")
    print("=" * 60)
    print("🌐 Access the MCP Interface at: http://localhost:8000/mcp_interface.html")
    print("📚 API Documentation at: http://localhost:8000/docs")
    print("🔧 System Status at: http://localhost:8000/api/mcp/status")

if __name__ == "__main__":
    test_mcp_commands()
