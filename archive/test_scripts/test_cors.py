#!/usr/bin/env python3
"""Test CORS Headers"""

import requests

def test_cors():
    print("🔍 TEST 10: CORS Headers")
    
    try:
        # Test OPTIONS request for CORS
        response = requests.options('http://localhost:8000/api/health')
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('access-control-allow-origin'),
            'Access-Control-Allow-Methods': response.headers.get('access-control-allow-methods'),
            'Access-Control-Allow-Headers': response.headers.get('access-control-allow-headers')
        }
        
        print(f"OPTIONS status: {response.status_code}")
        print(f"CORS Origin: {cors_headers['Access-Control-Allow-Origin']}")
        print(f"CORS Methods: {cors_headers['Access-Control-Allow-Methods']}")
        print(f"CORS Headers: {cors_headers['Access-Control-Allow-Headers']}")
        
        # Check if CORS is properly configured
        has_origin = cors_headers['Access-Control-Allow-Origin'] == '*'
        has_methods = cors_headers['Access-Control-Allow-Methods'] is not None
        has_headers = cors_headers['Access-Control-Allow-Headers'] is not None
        
        success = has_origin and has_methods and has_headers
        print("✅ CORS Headers: PASS" if success else "❌ CORS Headers: FAIL")
        return success
        
    except Exception as e:
        print(f"❌ CORS Headers: FAIL - {e}")
        return False

if __name__ == "__main__":
    test_cors()
