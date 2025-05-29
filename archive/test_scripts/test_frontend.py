#!/usr/bin/env python3
"""Test Frontend Connection"""

import requests

def test_frontend():
    print("🔍 TEST 9: Frontend Connection")
    
    try:
        # Test main frontend page
        response = requests.get('http://localhost:8000/')
        if response.status_code == 200:
            print(f"Frontend page: {response.status_code} - SUCCESS")
            print(f"Content length: {len(response.text)}")
            
            # Check if it contains expected elements
            content = response.text.lower()
            has_title = 'blackhole' in content
            has_upload = 'upload' in content or 'file' in content
            has_test = 'test' in content or 'connection' in content
            
            print(f"Has title: {has_title}")
            print(f"Has upload: {has_upload}")
            print(f"Has test: {has_test}")
            
            success = has_title and (has_upload or has_test)
            print("✅ Frontend Connection: PASS" if success else "❌ Frontend Connection: FAIL")
            return success
        else:
            print(f"Frontend page: {response.status_code} - FAILED")
            print("❌ Frontend Connection: FAIL")
            return False
            
    except Exception as e:
        print(f"❌ Frontend Connection: FAIL - {e}")
        return False

if __name__ == "__main__":
    test_frontend()
