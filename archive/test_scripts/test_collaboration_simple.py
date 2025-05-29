#!/usr/bin/env python3
"""
Simple test for inter-agent collaboration
"""

import requests
import json

def test_collaboration():
    """Test the collaboration system with a simple request."""
    
    print("🤖 Testing Inter-Agent Collaboration")
    print("=" * 50)
    
    # Test collaborative request
    test_request = {
        "command": "comprehensive analysis of multi-agent systems with detailed insights"
    }
    
    try:
        print("📤 Sending collaborative request...")
        print(f"Request: {test_request['command']}")
        
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Response received!")
            print(f"Status: {result.get('status')}")
            print(f"Type: {result.get('type')}")
            
            if result.get('type') == 'collaborative':
                print(f"\n🎉 COLLABORATION SUCCESS!")
                collaboration_info = result.get('collaboration_info', {})
                agents_involved = collaboration_info.get('agents_involved', [])
                print(f"Agents involved: {', '.join(agents_involved)}")
                print(f"Workflow ID: {collaboration_info.get('workflow_id')}")
                
                # Show result
                result_data = result.get('result', {})
                if 'final_result' in result_data:
                    final_result = result_data['final_result']
                    print(f"Synthesis: {final_result.get('synthesis', 'N/A')}")
                
            else:
                print(f"\nℹ️ Single agent response: {result.get('type')}")
                print(f"Agent used: {result.get('agent_used', 'N/A')}")
            
            print(f"Processing time: {result.get('processing_time_ms', 0)}ms")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test complete!")

if __name__ == "__main__":
    test_collaboration()
