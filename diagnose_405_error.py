#!/usr/bin/env python3
"""
Diagnose 405 Method Not Allowed errors
"""

import requests

def diagnose_endpoints():
    """Test all endpoints to find 405 errors."""
    
    print("🔍 Diagnosing 405 Method Not Allowed Errors")
    print("=" * 50)
    
    # Test basic health endpoint first
    print("\n1. Testing Basic Health Endpoint:")
    try:
        response = requests.get('http://localhost:8000/api/health')
        print(f"GET /api/health: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test MCP endpoints
    print("\n2. Testing MCP Endpoints:")
    
    mcp_endpoints = [
        ('/api/mcp/command', 'POST'),
        ('/api/mcp/help', 'GET'),
        ('/api/mcp/status', 'GET'),
        ('/api/mcp/history', 'GET')
    ]
    
    for endpoint, expected_method in mcp_endpoints:
        print(f"\nTesting {endpoint}:")
        
        # Test GET
        try:
            get_resp = requests.get(f'http://localhost:8000{endpoint}')
            print(f"  GET: {get_resp.status_code}")
            if get_resp.status_code == 405:
                print(f"  GET: Method Not Allowed")
            elif get_resp.status_code != 200:
                print(f"  GET Error: {get_resp.text}")
        except Exception as e:
            print(f"  GET Error: {e}")
        
        # Test POST
        try:
            post_data = {'command': 'test'} if 'command' in endpoint else {}
            post_resp = requests.post(f'http://localhost:8000{endpoint}', json=post_data)
            print(f"  POST: {post_resp.status_code}")
            if post_resp.status_code == 405:
                print(f"  POST: Method Not Allowed")
            elif post_resp.status_code != 200:
                print(f"  POST Error: {post_resp.text}")
        except Exception as e:
            print(f"  POST Error: {e}")
    
    # Test if server is running properly
    print("\n3. Testing Server Status:")
    try:
        response = requests.get('http://localhost:8000/')
        print(f"Frontend: {response.status_code}")
        
        response = requests.get('http://localhost:8000/docs')
        print(f"API Docs: {response.status_code}")
    except Exception as e:
        print(f"Server test error: {e}")
    
    # Test specific MCP command
    print("\n4. Testing Specific MCP Command:")
    try:
        command_data = {'command': 'help'}
        response = requests.post('http://localhost:8000/api/mcp/command', json=command_data)
        print(f"MCP Command Status: {response.status_code}")
        if response.status_code == 405:
            print("❌ MCP Command endpoint has Method Not Allowed error")
            print("This suggests the endpoint is not properly registered")
        elif response.status_code == 200:
            print("✅ MCP Command endpoint is working")
        else:
            print(f"MCP Command Error: {response.text}")
    except Exception as e:
        print(f"MCP Command Error: {e}")

if __name__ == "__main__":
    diagnose_endpoints()
