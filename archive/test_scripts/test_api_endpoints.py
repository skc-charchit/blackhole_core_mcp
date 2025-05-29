#!/usr/bin/env python3
"""Test API Endpoints"""

import requests

def test_api_endpoints():
    print("🔍 TEST 7: API Endpoints")
    
    endpoints = [
        '/api/health',
        '/api/test', 
        '/api/results'
    ]
    
    all_pass = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}')
            status = "PASS" if response.status_code == 200 else "FAIL"
            print(f'{endpoint}: {response.status_code} - {status}')
            if response.status_code != 200:
                all_pass = False
        except Exception as e:
            print(f'{endpoint}: ERROR - {e}')
            all_pass = False
    
    print("✅ API Endpoints: PASS" if all_pass else "❌ API Endpoints: FAIL")
    return all_pass

if __name__ == "__main__":
    test_api_endpoints()
