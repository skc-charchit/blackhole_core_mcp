#!/usr/bin/env python3
"""
Test script to check multimodal dependencies and functionality
"""

import os
import sys
from pathlib import Path

def test_dependencies():
    """Test all multimodal dependencies."""
    print("🔍 Testing Multimodal Dependencies")
    print("=" * 50)
    
    results = {}
    
    # Test pytesseract
    try:
        import pytesseract
        results['pytesseract'] = True
        print("✅ pytesseract: Available")
        
        # Test Tesseract executable
        if sys.platform.startswith('win'):
            tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if not os.path.exists(tesseract_cmd):
                tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        else:
            tesseract_cmd = '/usr/bin/tesseract'
            
        if os.path.exists(tesseract_cmd):
            print(f"✅ Tesseract executable: Found at {tesseract_cmd}")
            results['tesseract_exe'] = True
        else:
            print(f"❌ Tesseract executable: Not found at {tesseract_cmd}")
            results['tesseract_exe'] = False
            
    except ImportError:
        results['pytesseract'] = False
        print("❌ pytesseract: Missing")
    
    # Test PIL/Pillow
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        results['PIL'] = True
        print("✅ PIL/Pillow: Available")
    except ImportError:
        results['PIL'] = False
        print("❌ PIL/Pillow: Missing")
    
    # Test OpenCV
    try:
        import cv2
        results['opencv'] = True
        print("✅ OpenCV (cv2): Available")
    except ImportError:
        results['opencv'] = False
        print("❌ OpenCV (cv2): Missing")
    
    # Test pdf2image
    try:
        from pdf2image import convert_from_path
        results['pdf2image'] = True
        print("✅ pdf2image: Available")
    except ImportError:
        results['pdf2image'] = False
        print("❌ pdf2image: Missing")
    
    # Test PyPDF2
    try:
        from PyPDF2 import PdfReader
        results['PyPDF2'] = True
        print("✅ PyPDF2: Available")
    except ImportError:
        results['PyPDF2'] = False
        print("❌ PyPDF2: Missing")
    
    # Test LangChain
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        results['langchain'] = True
        print("✅ LangChain: Available")
    except ImportError:
        results['langchain'] = False
        print("❌ LangChain: Missing")
    
    # Test Together.ai
    try:
        from langchain_together import Together
        results['langchain_together'] = True
        print("✅ langchain-together: Available")
    except ImportError:
        try:
            from langchain_community.llms import Together
            results['langchain_together'] = True
            print("✅ langchain-together (community): Available")
        except ImportError:
            results['langchain_together'] = False
            print("❌ langchain-together: Missing")
    
    # Test environment variables
    print("\n🔧 Environment Variables")
    print("=" * 30)
    
    together_api_key = os.getenv('TOGETHER_API_KEY')
    if together_api_key:
        print("✅ TOGETHER_API_KEY: Set")
        results['together_api_key'] = True
    else:
        print("❌ TOGETHER_API_KEY: Not set")
        results['together_api_key'] = False
    
    mongo_uri = os.getenv('MONGO_URI')
    if mongo_uri:
        print("✅ MONGO_URI: Set")
        results['mongo_uri'] = True
    else:
        print("❌ MONGO_URI: Not set")
        results['mongo_uri'] = False
    
    return results

def test_multimodal_functionality():
    """Test actual multimodal functionality."""
    print("\n🧪 Testing Multimodal Functionality")
    print("=" * 40)
    
    # Test PDF reader import
    try:
        from data.multimodal.pdf_reader import EnhancedPDFReader, extract_text_from_pdf
        print("✅ PDF Reader: Import successful")
        
        # Test PDF reader initialization
        try:
            reader = EnhancedPDFReader()
            print("✅ PDF Reader: Initialization successful")
            print(f"   - LLM Available: {reader.llm is not None}")
            print(f"   - Embeddings Available: {reader.embeddings is not None}")
        except Exception as e:
            print(f"❌ PDF Reader: Initialization failed - {e}")
            
    except Exception as e:
        print(f"❌ PDF Reader: Import failed - {e}")
    
    # Test image OCR import
    try:
        from data.multimodal.image_ocr import extract_text_from_image
        print("✅ Image OCR: Import successful")
    except Exception as e:
        print(f"❌ Image OCR: Import failed - {e}")

def check_file_structure():
    """Check multimodal file structure."""
    print("\n📁 Checking File Structure")
    print("=" * 30)
    
    base_dir = Path("data/multimodal")
    
    if base_dir.exists():
        print("✅ data/multimodal: Directory exists")
        
        # Check subdirectories
        subdirs = ['uploaded_pdfs', 'uploaded_images', 'processed_outputs']
        for subdir in subdirs:
            subdir_path = base_dir / subdir
            if subdir_path.exists():
                file_count = len(list(subdir_path.glob('*')))
                print(f"✅ {subdir}: Exists ({file_count} files)")
            else:
                print(f"❌ {subdir}: Missing")
        
        # Check Python files
        py_files = ['__init__.py', 'pdf_reader.py', 'image_ocr.py']
        for py_file in py_files:
            py_path = base_dir / py_file
            if py_path.exists():
                print(f"✅ {py_file}: Exists")
            else:
                print(f"❌ {py_file}: Missing")
    else:
        print("❌ data/multimodal: Directory missing")

def generate_recommendations(results):
    """Generate recommendations based on test results."""
    print("\n💡 Recommendations")
    print("=" * 20)
    
    missing_deps = []
    
    if not results.get('pytesseract', False):
        missing_deps.append("pip install pytesseract")
    
    if not results.get('PIL', False):
        missing_deps.append("pip install Pillow")
    
    if not results.get('opencv', False):
        missing_deps.append("pip install opencv-python")
    
    if not results.get('pdf2image', False):
        missing_deps.append("pip install pdf2image")
    
    if not results.get('PyPDF2', False):
        missing_deps.append("pip install PyPDF2")
    
    if not results.get('langchain', False):
        missing_deps.append("pip install langchain langchain-community")
    
    if not results.get('langchain_together', False):
        missing_deps.append("pip install langchain-together")
    
    if missing_deps:
        print("📦 Install missing dependencies:")
        for dep in missing_deps:
            print(f"   {dep}")
    
    if not results.get('tesseract_exe', False):
        print("🔧 Install Tesseract OCR:")
        if sys.platform.startswith('win'):
            print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        else:
            print("   sudo apt-get install tesseract-ocr (Ubuntu/Debian)")
            print("   brew install tesseract (macOS)")
    
    if not results.get('together_api_key', False):
        print("🔑 Set TOGETHER_API_KEY in .env file")
    
    if not results.get('mongo_uri', False):
        print("🗄️ Set MONGO_URI in .env file")

def main():
    """Main test function."""
    print("🔍 BlackHole Core MCP - Multimodal System Diagnostics")
    print("=" * 60)
    
    # Test dependencies
    results = test_dependencies()
    
    # Check file structure
    check_file_structure()
    
    # Test functionality
    test_multimodal_functionality()
    
    # Generate recommendations
    generate_recommendations(results)
    
    # Summary
    print("\n📊 Summary")
    print("=" * 15)
    
    total_deps = len([k for k in results.keys() if not k.endswith('_key') and not k.endswith('_uri')])
    working_deps = len([k for k, v in results.items() if v and not k.endswith('_key') and not k.endswith('_uri')])
    
    print(f"Dependencies: {working_deps}/{total_deps} working")
    
    if working_deps == total_deps:
        print("🎉 All dependencies are working!")
    elif working_deps >= total_deps * 0.7:
        print("⚠️ Most dependencies working, some issues to resolve")
    else:
        print("❌ Major dependency issues detected")

if __name__ == "__main__":
    main()
