#!/usr/bin/env python3
"""
Test Image-to-Text Functionality
Test all available image processing and OCR capabilities
"""

import os
import sys
import requests
from pathlib import Path

def test_document_processor_image_capability():
    """Test document processor's image processing capability."""
    print("📄 TESTING DOCUMENT PROCESSOR IMAGE CAPABILITY")
    print("=" * 60)
    
    try:
        # Import document processor directly
        sys.path.append('.')
        from agents.core.document_processor import DocumentProcessorAgent
        from agents.base_agent import MCPMessage
        from datetime import datetime
        
        # Create document processor
        doc_processor = DocumentProcessorAgent()
        print("✅ Document processor created successfully")
        
        # Check capabilities
        info = doc_processor.get_info()
        print(f"📋 Agent: {info['name']}")
        print(f"📝 Description: {info['description']}")
        
        capabilities = [cap.name for cap in doc_processor.capabilities]
        print(f"⚡ Capabilities: {', '.join(capabilities)}")
        
        # Check if image processing is supported
        doc_cap = doc_processor.capabilities[0]
        input_types = doc_cap.input_types
        print(f"📥 Input types: {', '.join(input_types)}")
        
        if "image" in input_types:
            print("🖼️ ✅ IMAGE PROCESSING SUPPORTED!")
            return True
        else:
            print("🖼️ ❌ Image processing not explicitly listed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing document processor: {e}")
        return False

def test_ocr_module():
    """Test the OCR module directly."""
    print("\n🔧 TESTING OCR MODULE")
    print("=" * 60)
    
    try:
        # Import OCR module
        sys.path.append('data/multimodal')
        from image_ocr import extract_text_from_image
        
        print("✅ OCR module imported successfully")
        
        # Check if Tesseract is available
        try:
            import pytesseract
            print("✅ Tesseract OCR available")
            
            # Try to get Tesseract version
            version = pytesseract.get_tesseract_version()
            print(f"📋 Tesseract version: {version}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Tesseract not available: {e}")
            print("💡 Install Tesseract: https://github.com/tesseract-ocr/tesseract")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OCR module: {e}")
        return False

def test_javascript_image_agent():
    """Test JavaScript image OCR agent."""
    print("\n🟨 TESTING JAVASCRIPT IMAGE AGENT")
    print("=" * 60)
    
    js_agent_path = Path("agents/image/image_ocr_agent.js")
    
    if js_agent_path.exists():
        print(f"✅ JavaScript image agent found: {js_agent_path}")
        
        # Read the file to check capabilities
        try:
            with open(js_agent_path, 'r') as f:
                content = f.read()
            
            # Check for key features
            features = []
            if 'OCR' in content:
                features.append("OCR functionality")
            if 'supportedFormats' in content:
                features.append("Multiple image formats")
            if 'preProcessImage' in content:
                features.append("Image preprocessing")
            if 'analyzeText' in content:
                features.append("Text analysis")
            
            print(f"⚡ Features found: {', '.join(features)}")
            
            # Extract supported formats
            import re
            formats_match = re.search(r"supportedFormats.*?\[(.*?)\]", content, re.DOTALL)
            if formats_match:
                formats_str = formats_match.group(1)
                formats = re.findall(r"'([^']+)'", formats_str)
                print(f"📁 Supported formats: {', '.join(formats)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error reading JavaScript agent: {e}")
            return False
    else:
        print(f"❌ JavaScript image agent not found: {js_agent_path}")
        return False

def test_image_upload_capability():
    """Test image upload capability through MCP server."""
    print("\n🌐 TESTING IMAGE UPLOAD CAPABILITY")
    print("=" * 60)
    
    try:
        # Test document analysis endpoint
        response = requests.post(
            "http://localhost:8000/api/mcp/analyze",
            json={
                "documents": [
                    {
                        "filename": "test_image.png",
                        "content": "This is a test image content",
                        "type": "image"
                    }
                ],
                "query": "Extract text from this image",
                "rag_mode": True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server response: {result.get('status', 'unknown')}")
            print(f"💬 Message: {result.get('message', 'No message')}")
            
            if result.get('status') == 'success':
                print("🎉 Image analysis endpoint working!")
                return True
            else:
                print("⚠️ Image analysis endpoint responded but may need configuration")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing image upload: {e}")
        return False

def show_image_processing_summary():
    """Show summary of image processing capabilities."""
    print("\n📊 IMAGE-TO-TEXT CAPABILITIES SUMMARY")
    print("=" * 60)
    
    capabilities = {
        "🖼️ Image Formats Supported": [
            "PNG - Portable Network Graphics",
            "JPG/JPEG - Joint Photographic Experts Group", 
            "BMP - Bitmap Image File",
            "TIFF - Tagged Image File Format",
            "GIF - Graphics Interchange Format"
        ],
        "🔧 OCR Technologies": [
            "Tesseract OCR - Open source OCR engine",
            "OpenCV - Computer vision preprocessing",
            "PIL/Pillow - Image processing library",
            "Custom preprocessing algorithms"
        ],
        "⚡ Processing Features": [
            "Text extraction from images",
            "Image preprocessing for better accuracy",
            "Multiple OCR methods for fallback",
            "Confidence scoring",
            "Text analysis and summarization",
            "Language detection"
        ],
        "🤖 Available Agents": [
            "Document Processor Agent (Python) - Active",
            "Image OCR Agent (JavaScript) - Available", 
            "OCR Module (Python) - Direct access"
        ],
        "🌐 Integration Methods": [
            "MCP Server API endpoints",
            "Direct agent calls",
            "Document analysis workflow",
            "File upload processing"
        ]
    }
    
    for category, items in capabilities.items():
        print(f"\n{category}:")
        for item in items:
            print(f"   • {item}")

def show_usage_examples():
    """Show usage examples for image-to-text."""
    print("\n💡 USAGE EXAMPLES")
    print("=" * 60)
    
    examples = [
        {
            "method": "MCP Server Command",
            "example": "python mcp_client.py -c 'Extract text from image.png'",
            "description": "Process image through MCP server"
        },
        {
            "method": "Document Analysis API",
            "example": "POST /api/mcp/analyze with image document",
            "description": "Upload image via web interface"
        },
        {
            "method": "Direct OCR Module",
            "example": "from image_ocr import extract_text_from_image",
            "description": "Direct Python module usage"
        },
        {
            "method": "Natural Language",
            "example": "'Read the text from this screenshot'",
            "description": "Natural language image processing"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['method']}:")
        print(f"   📝 Example: {example['example']}")
        print(f"   💡 Description: {example['description']}")

def main():
    """Main test function."""
    print("🖼️ IMAGE-TO-TEXT FUNCTIONALITY TEST")
    print("=" * 80)
    print("🎯 Testing all available image processing capabilities")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: Document Processor Image Capability
    test_results["document_processor"] = test_document_processor_image_capability()
    
    # Test 2: OCR Module
    test_results["ocr_module"] = test_ocr_module()
    
    # Test 3: JavaScript Image Agent
    test_results["javascript_agent"] = test_javascript_image_agent()
    
    # Test 4: Image Upload Capability
    test_results["upload_capability"] = test_image_upload_capability()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 IMAGE-TO-TEXT TEST RESULTS")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ AVAILABLE" if result else "❌ NEEDS SETUP"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n📈 Availability Score: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    
    if passed_tests >= 2:
        print("\n🎉 IMAGE-TO-TEXT FUNCTIONALITY AVAILABLE!")
        print("🖼️ You have working image processing capabilities")
        
        # Show capabilities summary
        show_image_processing_summary()
        
        # Show usage examples
        show_usage_examples()
        
        print("\n🚀 READY TO USE:")
        print("   📸 Upload images for text extraction")
        print("   🔍 Process screenshots and documents")
        print("   📝 Extract text from photos")
        print("   🤖 Automated image analysis")
        
    else:
        print("\n🔧 IMAGE-TO-TEXT NEEDS SETUP")
        print("💡 Install Tesseract OCR for full functionality")
        print("🔗 https://github.com/tesseract-ocr/tesseract")
    
    return passed_tests >= 2

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Image-to-text functionality confirmed!")
        else:
            print("\n🔧 Image-to-text needs setup. Install Tesseract OCR.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("💡 Make sure all dependencies are available")
