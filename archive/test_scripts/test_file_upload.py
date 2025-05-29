#!/usr/bin/env python3
"""Test File Upload API"""

import requests
import tempfile
import os

def test_file_upload():
    print("🔍 TEST 8: File Upload API")
    
    try:
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test file for API upload testing.\nIt contains multiple lines.\nTesting file upload functionality.")
            temp_file = f.name
        
        # Test file upload
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_upload.txt', f, 'text/plain')}
            data = {'enable_llm': 'false', 'save_to_db': 'true'}
            
            response = requests.post(
                'http://localhost:8000/api/process-document',
                files=files,
                data=data,
                timeout=30
            )
        
        # Clean up
        os.unlink(temp_file)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Upload status: {response.status_code} - SUCCESS")
            print(f"Filename: {result.get('filename', 'N/A')}")
            print(f"Text length: {len(result.get('extracted_text', ''))}")
            print("✅ File Upload API: PASS")
            return True
        else:
            print(f"Upload status: {response.status_code} - FAILED")
            print(f"Response: {response.text}")
            print("❌ File Upload API: FAIL")
            return False
            
    except Exception as e:
        print(f"❌ File Upload API: FAIL - {e}")
        return False

if __name__ == "__main__":
    test_file_upload()
