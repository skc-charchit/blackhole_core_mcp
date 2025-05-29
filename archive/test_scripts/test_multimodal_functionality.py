#!/usr/bin/env python3
"""
Test multimodal functionality with real files
"""

import os
import sys
from pathlib import Path

def test_pdf_processing():
    """Test PDF processing functionality."""
    print("📄 Testing PDF Processing")
    print("=" * 30)
    
    try:
        from data.multimodal.pdf_reader import extract_text_from_pdf, EnhancedPDFReader
        
        # Find PDF files
        pdf_dir = Path("data/multimodal/uploaded_pdfs")
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("❌ No PDF files found for testing")
            return False
        
        print(f"✅ Found {len(pdf_files)} PDF files")
        
        # Test basic PDF extraction
        test_pdf = pdf_files[0]
        print(f"🔍 Testing with: {test_pdf.name}")
        
        result = extract_text_from_pdf(str(test_pdf), verbose=True)
        
        if result and not result.startswith("❌"):
            print(f"✅ PDF text extraction successful")
            print(f"   - Extracted {len(result)} characters")
            print(f"   - Preview: {result[:100]}...")
            
            # Test enhanced PDF reader
            try:
                reader = EnhancedPDFReader()
                if reader.llm:
                    print("✅ Enhanced PDF reader with LLM available")
                    
                    # Test loading PDF
                    success = reader.load_and_process_pdf(str(test_pdf), verbose=True)
                    if success:
                        print("✅ PDF loaded and processed for Q&A")
                        
                        # Test asking a question
                        answer = reader.ask_question("What is this document about?", verbose=True)
                        if answer and not answer.startswith("❌"):
                            print("✅ Q&A functionality working")
                            print(f"   - Answer: {answer[:100]}...")
                        else:
                            print("❌ Q&A functionality failed")
                    else:
                        print("❌ PDF processing for Q&A failed")
                else:
                    print("⚠️ Enhanced PDF reader available but LLM not configured")
                    
            except Exception as e:
                print(f"❌ Enhanced PDF reader error: {e}")
            
            return True
        else:
            print(f"❌ PDF text extraction failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ PDF processing error: {e}")
        return False

def test_image_processing():
    """Test image processing functionality."""
    print("\n🖼️ Testing Image Processing")
    print("=" * 30)
    
    try:
        from data.multimodal.image_ocr import extract_text_from_image
        
        # Find image files
        img_dir = Path("data/multimodal/uploaded_images")
        img_files = list(img_dir.glob("*"))
        img_files = [f for f in img_files if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']]
        
        if not img_files:
            print("❌ No image files found for testing")
            return False
        
        print(f"✅ Found {len(img_files)} image files")
        
        # Test image OCR
        test_image = img_files[0]
        print(f"🔍 Testing with: {test_image.name}")
        
        result = extract_text_from_image(str(test_image), debug=True, preprocessing_level=2)
        
        if result and not result.startswith("❌"):
            print(f"✅ Image OCR successful")
            print(f"   - Extracted {len(result)} characters")
            print(f"   - Preview: {result[:100]}...")
            return True
        else:
            print(f"❌ Image OCR failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Image processing error: {e}")
        return False

def test_api_integration():
    """Test API integration with multimodal processing."""
    print("\n🔗 Testing API Integration")
    print("=" * 30)
    
    try:
        import requests
        
        # Test file upload API
        pdf_dir = Path("data/multimodal/uploaded_pdfs")
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if pdf_files:
            test_pdf = pdf_files[0]
            print(f"🔍 Testing API with: {test_pdf.name}")
            
            with open(test_pdf, 'rb') as f:
                files = {'file': (test_pdf.name, f, 'application/pdf')}
                data = {'enable_llm': 'false', 'save_to_db': 'true'}
                
                response = requests.post(
                    'http://localhost:8000/api/process-document',
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ API file processing successful")
                    print(f"   - Filename: {result.get('filename', 'N/A')}")
                    print(f"   - Text length: {len(result.get('extracted_text', ''))}")
                    return True
                else:
                    print(f"❌ API file processing failed: {response.status_code}")
                    print(f"   - Response: {response.text}")
                    return False
        else:
            print("❌ No PDF files available for API testing")
            return False
            
    except Exception as e:
        print(f"❌ API integration error: {e}")
        return False

def test_file_organization():
    """Test file organization system."""
    print("\n📁 Testing File Organization")
    print("=" * 30)
    
    base_dir = Path("data/multimodal")
    
    # Check directory structure
    subdirs = {
        'uploaded_pdfs': 'PDF uploads',
        'uploaded_images': 'Image uploads', 
        'processed_outputs': 'Processed outputs'
    }
    
    all_good = True
    
    for subdir, description in subdirs.items():
        subdir_path = base_dir / subdir
        if subdir_path.exists():
            file_count = len(list(subdir_path.glob('*')))
            print(f"✅ {description}: {file_count} files")
        else:
            print(f"❌ {description}: Directory missing")
            all_good = False
    
    return all_good

def main():
    """Main test function."""
    print("🔍 BlackHole Core MCP - Multimodal Functionality Test")
    print("=" * 60)
    
    results = {}
    
    # Test file organization
    results['file_organization'] = test_file_organization()
    
    # Test PDF processing
    results['pdf_processing'] = test_pdf_processing()
    
    # Test image processing
    results['image_processing'] = test_image_processing()
    
    # Test API integration
    results['api_integration'] = test_api_integration()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 25)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All multimodal functionality is working!")
    elif passed_tests >= total_tests * 0.7:
        print("⚠️ Most functionality working, some issues to resolve")
    else:
        print("❌ Major multimodal functionality issues detected")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    main()
