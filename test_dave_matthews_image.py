#!/usr/bin/env python3
"""
Test Image-to-Text with Dave Matthews Quote Image
Test OCR functionality with the specific image file
"""

import os
import sys
import base64
import requests
from pathlib import Path
from datetime import datetime

def test_image_file_exists():
    """Check if the test image file exists."""
    print("📁 CHECKING IMAGE FILE")
    print("=" * 50)
    
    image_path = Path(r"D:\Work_Station\blackhole_core_mcp\data\multimodal\uploaded_images\black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp")
    
    print(f"🔍 Looking for: {image_path}")
    
    if image_path.exists():
        print("✅ Image file found!")
        
        # Get file info
        file_size = image_path.stat().st_size
        print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"📝 File extension: {image_path.suffix}")
        print(f"📂 Directory: {image_path.parent}")
        
        return str(image_path)
    else:
        print("❌ Image file not found!")
        
        # Check if directory exists
        if image_path.parent.exists():
            print(f"📂 Directory exists: {image_path.parent}")
            print("📋 Files in directory:")
            for file in image_path.parent.iterdir():
                if file.is_file():
                    print(f"   • {file.name}")
        else:
            print(f"❌ Directory doesn't exist: {image_path.parent}")
        
        return None

def test_direct_ocr_module(image_path):
    """Test OCR module directly with the image."""
    print("\n🔧 TESTING DIRECT OCR MODULE")
    print("=" * 50)
    
    try:
        # Add the multimodal directory to path
        sys.path.append('data/multimodal')
        from image_ocr import extract_text_from_image
        
        print(f"📸 Processing image: {Path(image_path).name}")
        print("⏳ Extracting text...")
        
        # Extract text with debug mode
        extracted_text = extract_text_from_image(
            image_path,
            debug=True,
            preprocessing_level=2,
            try_multiple_methods=True
        )
        
        print("\n📝 EXTRACTED TEXT:")
        print("=" * 40)
        print(extracted_text)
        print("=" * 40)
        
        print(f"\n📊 Text length: {len(extracted_text)} characters")
        print(f"📊 Word count: {len(extracted_text.split())}")
        
        # Check if it contains expected content
        if "dave matthews" in extracted_text.lower():
            print("✅ Dave Matthews detected in text!")
        if "black" in extracted_text.lower() and "white" in extracted_text.lower():
            print("✅ Quote keywords detected!")
        
        return extracted_text
        
    except Exception as e:
        print(f"❌ OCR module error: {e}")
        return None

def test_document_processor_agent(image_path):
    """Test document processor agent with the image."""
    print("\n📄 TESTING DOCUMENT PROCESSOR AGENT")
    print("=" * 50)
    
    try:
        # Import document processor
        sys.path.append('.')
        from agents.core.document_processor import DocumentProcessorAgent
        from agents.base_agent import MCPMessage
        
        # Create agent
        doc_processor = DocumentProcessorAgent()
        print("✅ Document processor created")
        
        # Create message for image processing
        message = MCPMessage(
            id=f"image_test_{datetime.now().timestamp()}",
            method="process",
            params={
                "file_path": image_path,
                "command": "extract_text"
            },
            timestamp=datetime.now()
        )
        
        print(f"📸 Processing image through agent...")
        
        # Process the image
        result = await doc_processor.process_message(message)
        
        print(f"\n📊 AGENT RESULT:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Agent: {result.get('agent', 'unknown')}")
        
        if result.get('status') == 'success':
            extracted_text = result.get('extracted_text', '')
            print(f"   Text length: {len(extracted_text)} characters")
            
            if extracted_text:
                print("\n📝 EXTRACTED TEXT (Agent):")
                print("=" * 40)
                print(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
                print("=" * 40)
                return extracted_text
            else:
                print("⚠️ No text extracted by agent")
                return None
        else:
            print(f"❌ Agent processing failed: {result.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Document processor error: {e}")
        return None

def test_mcp_server_api(image_path):
    """Test MCP server API with the image."""
    print("\n🌐 TESTING MCP SERVER API")
    print("=" * 50)
    
    try:
        # Read image file and encode to base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        print(f"📸 Image encoded: {len(image_base64)} characters")
        
        # Send to MCP server
        response = requests.post(
            "http://localhost:8000/api/mcp/analyze",
            json={
                "documents": [
                    {
                        "filename": Path(image_path).name,
                        "content": image_base64,
                        "type": "image"
                    }
                ],
                "query": "Extract all text from this Dave Matthews quote image",
                "rag_mode": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server response: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'success':
                comprehensive_answer = result.get('comprehensive_answer', '')
                print("\n📝 SERVER RESPONSE:")
                print("=" * 40)
                print(comprehensive_answer)
                print("=" * 40)
                return comprehensive_answer
            else:
                print(f"❌ Server processing failed: {result.get('message', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ MCP server API error: {e}")
        return None

def test_mcp_command_interface(image_path):
    """Test MCP command interface."""
    print("\n💬 TESTING MCP COMMAND INTERFACE")
    print("=" * 50)
    
    try:
        # Test with natural language command
        command = f"Extract text from the image at {image_path}"
        
        response = requests.post(
            "http://localhost:8000/api/mcp/command",
            json={"command": command},
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Command response: {result.get('status', 'unknown')}")
            print(f"💬 Message: {result.get('message', 'No message')}")
            print(f"🤖 Agent: {result.get('agent_used', 'unknown')}")
            
            return result.get('status') == 'success'
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Command interface error: {e}")
        return False

def analyze_extracted_text(text):
    """Analyze the extracted text for Dave Matthews quote content."""
    print("\n🔍 ANALYZING EXTRACTED TEXT")
    print("=" * 50)
    
    if not text:
        print("❌ No text to analyze")
        return
    
    text_lower = text.lower()
    
    # Check for Dave Matthews
    if "dave matthews" in text_lower:
        print("✅ Dave Matthews name detected")
    elif "dave" in text_lower and "matthews" in text_lower:
        print("✅ Dave Matthews name detected (separate words)")
    else:
        print("⚠️ Dave Matthews name not clearly detected")
    
    # Check for quote keywords
    quote_keywords = ["black", "white", "nothing", "color", "quote"]
    detected_keywords = [word for word in quote_keywords if word in text_lower]
    
    if detected_keywords:
        print(f"✅ Quote keywords detected: {', '.join(detected_keywords)}")
    else:
        print("⚠️ Quote keywords not clearly detected")
    
    # Check for common OCR issues
    if len(text) < 10:
        print("⚠️ Very short text - possible OCR issue")
    elif len(text) > 1000:
        print("⚠️ Very long text - possible over-extraction")
    else:
        print(f"✅ Text length reasonable: {len(text)} characters")
    
    # Word analysis
    words = text.split()
    print(f"📊 Word count: {len(words)}")
    print(f"📊 Average word length: {sum(len(word) for word in words) / len(words):.1f}" if words else "N/A")

async def main():
    """Main test function."""
    print("🧪 DAVE MATTHEWS IMAGE OCR TEST")
    print("=" * 80)
    print("🎯 Testing image-to-text with specific Dave Matthews quote image")
    print("=" * 80)
    
    # Step 1: Check if image exists
    image_path = test_image_file_exists()
    
    if not image_path:
        print("\n❌ Cannot proceed without the image file")
        print("💡 Please check the file path and try again")
        return False
    
    # Step 2: Test direct OCR module
    ocr_text = test_direct_ocr_module(image_path)
    
    # Step 3: Test document processor agent
    # agent_text = test_document_processor_agent(image_path)
    
    # Step 4: Test MCP server API
    api_text = test_mcp_server_api(image_path)
    
    # Step 5: Test MCP command interface
    command_success = test_mcp_command_interface(image_path)
    
    # Step 6: Analyze results
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    results = {
        "Image file found": image_path is not None,
        "Direct OCR module": ocr_text is not None,
        "MCP server API": api_text is not None,
        "Command interface": command_success
    }
    
    for test_name, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    print(f"\n📈 Success rate: {success_count}/{total_tests} ({(success_count/total_tests)*100:.1f}%)")
    
    # Analyze the best extracted text
    best_text = ocr_text or api_text
    if best_text:
        analyze_extracted_text(best_text)
        
        print("\n🎉 IMAGE-TO-TEXT TEST COMPLETED!")
        print("✅ Successfully extracted text from Dave Matthews quote image")
        print("🖼️ Your OCR system is working with real image files")
        
    else:
        print("\n🔧 IMAGE-TO-TEXT NEEDS ATTENTION")
        print("⚠️ No text was successfully extracted")
        print("💡 Check OCR configuration and image quality")
    
    return success_count >= 2

if __name__ == "__main__":
    import asyncio
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n🎉 Dave Matthews image OCR test successful!")
        else:
            print("\n🔧 OCR test needs attention. Check configuration.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("💡 Make sure the MCP server is running and image file exists")
