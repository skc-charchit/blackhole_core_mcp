#!/usr/bin/env python3
"""
Simple Image OCR Test with Dave Matthews Quote
Direct test of OCR functionality
"""

import os
import sys
from pathlib import Path

def test_image_exists():
    """Check if the image file exists."""
    print("📁 CHECKING IMAGE FILE")
    print("=" * 50)
    
    image_path = Path(r"D:\Work_Station\blackhole_core_mcp\data\multimodal\uploaded_images\black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp")
    
    print(f"🔍 Looking for: {image_path.name}")
    print(f"📂 In directory: {image_path.parent}")
    
    if image_path.exists():
        print("✅ Image file found!")
        
        # Get file info
        file_size = image_path.stat().st_size
        print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"📝 File type: {image_path.suffix}")
        
        return str(image_path)
    else:
        print("❌ Image file not found!")
        
        # Check directory contents
        if image_path.parent.exists():
            print(f"\n📋 Files in {image_path.parent.name}:")
            for file in image_path.parent.iterdir():
                if file.is_file():
                    print(f"   • {file.name}")
        
        return None

def test_direct_ocr(image_path):
    """Test direct OCR on the image."""
    print("\n🔧 TESTING DIRECT OCR")
    print("=" * 50)
    
    try:
        # Add multimodal directory to path
        multimodal_path = Path("data/multimodal")
        if multimodal_path.exists():
            sys.path.insert(0, str(multimodal_path))
            print(f"✅ Added to path: {multimodal_path}")
        else:
            print(f"❌ Multimodal directory not found: {multimodal_path}")
            return None
        
        # Import OCR function
        from image_ocr import extract_text_from_image
        print("✅ OCR module imported successfully")
        
        print(f"📸 Processing: {Path(image_path).name}")
        print("⏳ Extracting text (this may take a moment)...")
        
        # Extract text with enhanced settings
        extracted_text = extract_text_from_image(
            image_path,
            debug=True,
            preprocessing_level=2,
            try_multiple_methods=True
        )
        
        print("\n📝 EXTRACTED TEXT:")
        print("=" * 60)
        print(extracted_text)
        print("=" * 60)
        
        # Analysis
        print(f"\n📊 ANALYSIS:")
        print(f"   Text length: {len(extracted_text)} characters")
        print(f"   Word count: {len(extracted_text.split())}")
        print(f"   Lines: {len(extracted_text.splitlines())}")
        
        # Check for expected content
        text_lower = extracted_text.lower()
        
        checks = {
            "Dave Matthews": "dave matthews" in text_lower or ("dave" in text_lower and "matthews" in text_lower),
            "Quote keywords": any(word in text_lower for word in ["black", "white", "nothing", "color"]),
            "Readable text": len(extracted_text.strip()) > 10
        }
        
        print(f"\n🔍 CONTENT CHECKS:")
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
        
        return extracted_text
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure the OCR module is available")
        return None
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None

def test_tesseract_availability():
    """Test if Tesseract is available."""
    print("\n🔧 CHECKING TESSERACT OCR")
    print("=" * 50)
    
    try:
        import pytesseract
        print("✅ Pytesseract imported successfully")
        
        # Try to get version
        version = pytesseract.get_tesseract_version()
        print(f"📋 Tesseract version: {version}")
        
        # Check Tesseract path
        tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
        print(f"📍 Tesseract path: {tesseract_cmd}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tesseract error: {e}")
        print("💡 Install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
        return False

def test_image_libraries():
    """Test required image processing libraries."""
    print("\n📚 CHECKING IMAGE LIBRARIES")
    print("=" * 50)
    
    libraries = {
        "PIL (Pillow)": "PIL",
        "OpenCV": "cv2",
        "NumPy": "numpy"
    }
    
    available = {}
    
    for lib_name, import_name in libraries.items():
        try:
            __import__(import_name)
            print(f"✅ {lib_name} available")
            available[lib_name] = True
        except ImportError:
            print(f"❌ {lib_name} not available")
            available[lib_name] = False
    
    return available

def show_image_info(image_path):
    """Show detailed image information."""
    print("\n🖼️ IMAGE INFORMATION")
    print("=" * 50)
    
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            print(f"📐 Dimensions: {img.size[0]} x {img.size[1]} pixels")
            print(f"🎨 Mode: {img.mode}")
            print(f"📝 Format: {img.format}")
            
            # Check if it's a good candidate for OCR
            width, height = img.size
            total_pixels = width * height
            
            print(f"📊 Total pixels: {total_pixels:,}")
            
            if total_pixels < 50000:
                print("⚠️ Image might be too small for good OCR results")
            elif total_pixels > 10000000:
                print("⚠️ Image might be very large - OCR could be slow")
            else:
                print("✅ Image size looks good for OCR")
            
            return True
            
    except Exception as e:
        print(f"❌ Error reading image: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 DAVE MATTHEWS IMAGE OCR TEST")
    print("=" * 80)
    print("🎯 Testing OCR with Dave Matthews quote image")
    print("📸 Image: black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp")
    print("=" * 80)
    
    # Test 1: Check if image exists
    image_path = test_image_exists()
    if not image_path:
        print("\n❌ Cannot proceed without the image file")
        return False
    
    # Test 2: Check Tesseract
    tesseract_ok = test_tesseract_availability()
    
    # Test 3: Check image libraries
    libraries = test_image_libraries()
    
    # Test 4: Show image info
    image_info_ok = show_image_info(image_path)
    
    # Test 5: Run OCR if everything is ready
    if tesseract_ok and libraries.get("PIL (Pillow)", False):
        extracted_text = test_direct_ocr(image_path)
        
        if extracted_text:
            print("\n🎉 OCR TEST SUCCESSFUL!")
            print("✅ Successfully extracted text from Dave Matthews image")
            print("🖼️ Your image-to-text system is working!")
            
            # Show a preview of the extracted text
            preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
            print(f"\n📝 Text preview: {preview}")
            
            return True
        else:
            print("\n🔧 OCR extraction failed")
            return False
    else:
        print("\n⚠️ Prerequisites not met for OCR testing")
        print("💡 Install missing libraries and try again")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Image OCR test completed successfully!")
            print("🖼️ Your system can extract text from images!")
        else:
            print("\n🔧 Image OCR test needs attention")
            print("💡 Check the error messages above")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
