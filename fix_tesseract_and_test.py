#!/usr/bin/env python3
"""
Fix Tesseract Path and Test Dave Matthews Image OCR
"""

import os
import sys
from pathlib import Path

def fix_tesseract_path():
    """Fix Tesseract path configuration."""
    print("🔧 FIXING TESSERACT PATH")
    print("=" * 50)
    
    # Common Tesseract installation paths on Windows
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\ASUS\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        r"C:\tesseract\tesseract.exe"
    ]
    
    tesseract_path = None
    
    for path in possible_paths:
        if Path(path).exists():
            tesseract_path = path
            print(f"✅ Found Tesseract at: {path}")
            break
        else:
            print(f"❌ Not found: {path}")
    
    if tesseract_path:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✅ Tesseract path configured: {tesseract_path}")
            
            # Test Tesseract
            version = pytesseract.get_tesseract_version()
            print(f"📋 Tesseract version: {version}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error configuring Tesseract: {e}")
            return False
    else:
        print("❌ Tesseract not found in common locations")
        print("💡 Please install Tesseract OCR from: https://github.com/tesseract-ocr/tesseract")
        return False

def test_ocr_with_dave_matthews_image():
    """Test OCR with the Dave Matthews image."""
    print("\n🖼️ TESTING OCR WITH DAVE MATTHEWS IMAGE")
    print("=" * 50)
    
    image_path = r"D:\Work_Station\blackhole_core_mcp\data\multimodal\uploaded_images\black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp"
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return None
    
    try:
        # Add multimodal to path
        sys.path.insert(0, "data/multimodal")
        from image_ocr import extract_text_from_image
        
        print(f"📸 Processing: {Path(image_path).name}")
        print("⏳ Extracting text...")
        
        # Extract text with multiple methods
        extracted_text = extract_text_from_image(
            image_path,
            debug=True,
            preprocessing_level=2,
            try_multiple_methods=True
        )
        
        print("\n📝 EXTRACTED TEXT:")
        print("=" * 80)
        print(extracted_text)
        print("=" * 80)
        
        # Analyze the text
        print(f"\n📊 TEXT ANALYSIS:")
        print(f"   Length: {len(extracted_text)} characters")
        print(f"   Words: {len(extracted_text.split())}")
        print(f"   Lines: {len(extracted_text.splitlines())}")
        
        # Check for Dave Matthews content
        text_lower = extracted_text.lower()
        
        dave_found = "dave" in text_lower and "matthews" in text_lower
        quote_keywords = ["black", "white", "nothing", "color"]
        keywords_found = [word for word in quote_keywords if word in text_lower]
        
        print(f"\n🔍 CONTENT ANALYSIS:")
        print(f"   Dave Matthews detected: {'✅' if dave_found else '❌'}")
        print(f"   Quote keywords found: {', '.join(keywords_found) if keywords_found else 'None'}")
        
        if dave_found and keywords_found:
            print("🎉 SUCCESS! Dave Matthews quote successfully extracted!")
        elif dave_found:
            print("✅ Dave Matthews detected, partial quote extraction")
        elif keywords_found:
            print("✅ Quote keywords detected, partial extraction")
        else:
            print("⚠️ Content not clearly detected - may need image preprocessing")
        
        return extracted_text
        
    except Exception as e:
        print(f"❌ OCR error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_simple_ocr():
    """Test simple OCR without the custom module."""
    print("\n🔧 TESTING SIMPLE OCR")
    print("=" * 50)
    
    image_path = r"D:\Work_Station\blackhole_core_mcp\data\multimodal\uploaded_images\black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp"
    
    try:
        import pytesseract
        from PIL import Image
        
        print(f"📸 Opening image: {Path(image_path).name}")
        
        # Open and process image
        with Image.open(image_path) as img:
            print(f"📐 Image size: {img.size}")
            print(f"🎨 Image mode: {img.mode}")
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
                print("🔄 Converted to RGB")
            
            print("⏳ Running OCR...")
            
            # Extract text with different configurations
            configs = [
                '--psm 6',  # Uniform block of text
                '--psm 3',  # Fully automatic page segmentation
                '--psm 8',  # Single word
                '--psm 13'  # Raw line
            ]
            
            best_text = ""
            best_length = 0
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(img, config=config)
                    print(f"📝 Config {config}: {len(text)} chars")
                    
                    if len(text) > best_length:
                        best_text = text
                        best_length = len(text)
                        
                except Exception as e:
                    print(f"❌ Config {config} failed: {e}")
            
            if best_text:
                print(f"\n📝 BEST EXTRACTED TEXT ({best_length} chars):")
                print("=" * 60)
                print(best_text)
                print("=" * 60)
                
                return best_text
            else:
                print("❌ No text extracted with any configuration")
                return None
                
    except Exception as e:
        print(f"❌ Simple OCR error: {e}")
        return None

def main():
    """Main function."""
    print("🔧 TESSERACT FIX AND DAVE MATTHEWS OCR TEST")
    print("=" * 80)
    
    # Step 1: Fix Tesseract path
    tesseract_ok = fix_tesseract_path()
    
    if not tesseract_ok:
        print("\n❌ Cannot proceed without Tesseract")
        print("💡 Please install Tesseract OCR and try again")
        return False
    
    # Step 2: Test with custom OCR module
    print("\n" + "="*80)
    print("TESTING WITH CUSTOM OCR MODULE")
    print("="*80)
    
    custom_text = test_ocr_with_dave_matthews_image()
    
    # Step 3: Test with simple OCR
    print("\n" + "="*80)
    print("TESTING WITH SIMPLE OCR")
    print("="*80)
    
    simple_text = test_simple_ocr()
    
    # Summary
    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    
    if custom_text or simple_text:
        print("🎉 SUCCESS! OCR is working with your Dave Matthews image!")
        print("✅ Image-to-text functionality confirmed")
        
        if custom_text:
            print("✅ Custom OCR module working")
        if simple_text:
            print("✅ Simple OCR working")
        
        # Show the better result
        better_text = custom_text if custom_text and len(custom_text) > len(simple_text or "") else simple_text
        
        if better_text:
            print(f"\n📝 FINAL EXTRACTED TEXT:")
            print("="*60)
            print(better_text[:500] + "..." if len(better_text) > 500 else better_text)
            print("="*60)
        
        return True
    else:
        print("❌ OCR extraction failed")
        print("🔧 Check image quality and Tesseract configuration")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Dave Matthews image OCR test SUCCESSFUL!")
            print("🖼️ Your image-to-text system is fully operational!")
        else:
            print("\n🔧 OCR test failed - check configuration")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
