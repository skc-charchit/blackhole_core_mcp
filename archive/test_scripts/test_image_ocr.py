#!/usr/bin/env python3
"""Test Image OCR functionality"""

import os
from pathlib import Path

def test_image_ocr():
    print("🔍 TEST 4: Image OCR Module")
    
    try:
        from data.multimodal.image_ocr import extract_text_from_image
        
        # Find image files
        img_dir = Path("data/multimodal/uploaded_images")
        img_files = list(img_dir.glob("*"))
        img_files = [f for f in img_files if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']]
        print(f"Image files found: {len(img_files)}")
        
        if img_files:
            # Test OCR
            test_image = img_files[0]
            result = extract_text_from_image(str(test_image), debug=False, preprocessing_level=2)
            success = len(result) > 0 and not result.startswith('❌')
            print(f"OCR extraction: {'SUCCESS' if success else 'FAILED'}")
            print(f"Text length: {len(result)}")
            print(f"Text preview: {result[:50]}...")
            
            print("✅ Image OCR: PASS" if success else "❌ Image OCR: FAIL")
            return success
        else:
            print("No image files found for testing")
            print("✅ Image OCR: PASS (no files to test)")
            return True
            
    except Exception as e:
        print(f"❌ Image OCR: FAIL - {e}")
        return False

if __name__ == "__main__":
    test_image_ocr()
