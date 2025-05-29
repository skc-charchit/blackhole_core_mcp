#!/usr/bin/env python3
"""Test API with LLM functionality using user's credentials"""

import requests
import tempfile
import os

def test_api_with_llm():
    print("🔍 Testing API with LLM (Your Credentials)")
    print("=" * 45)
    
    try:
        # Create a test document
        test_content = """
        BlackHole Core MCP Test Document
        
        This is a comprehensive test document for the BlackHole Core MCP system.
        It contains information about:
        
        1. Document Processing Capabilities
        2. AI-powered Analysis Features
        3. Multi-modal Content Handling
        4. Database Storage and Retrieval
        
        The system can process PDFs, images, and text files with advanced
        natural language processing capabilities using Together.ai's LLM models.
        
        Key Features:
        - PDF text extraction
        - Image OCR processing
        - Question answering
        - Document summarization
        - MongoDB storage
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        print("📄 Created test document")
        
        # Test 1: Upload without LLM
        print("\n🔍 Test 1: Upload without LLM")
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_no_llm.txt', f, 'text/plain')}
            data = {'enable_llm': 'false', 'save_to_db': 'true'}
            
            response = requests.post(
                'http://localhost:8000/api/process-document',
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload without LLM: SUCCESS")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Text length: {len(result.get('extracted_text', ''))}")
        else:
            print(f"❌ Upload without LLM: FAILED ({response.status_code})")
        
        # Test 2: Upload with LLM enabled
        print("\n🔍 Test 2: Upload with LLM enabled")
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_with_llm.txt', f, 'text/plain')}
            data = {'enable_llm': 'true', 'save_to_db': 'true'}
            
            response = requests.post(
                'http://localhost:8000/api/process-document',
                files=files,
                data=data,
                timeout=60  # Longer timeout for LLM processing
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload with LLM: SUCCESS")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Text length: {len(result.get('extracted_text', ''))}")
            print(f"   Has summary: {'summary' in result}")
            print(f"   Has analysis: {'analysis' in result}")
            
            if 'summary' in result:
                print(f"   Summary preview: {result['summary'][:100]}...")
        else:
            print(f"❌ Upload with LLM: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
        
        # Clean up
        os.unlink(temp_file)
        
        print("\n🎉 API with LLM testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ API with LLM test failed: {e}")
        return False

if __name__ == "__main__":
    test_api_with_llm()
