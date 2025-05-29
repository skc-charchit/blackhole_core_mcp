#!/usr/bin/env python3
"""Test File Organization System"""

import os
from pathlib import Path

def test_file_organization():
    print("🔍 TEST 11: File Organization System")
    
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
    
    # Check Python modules
    py_files = ['__init__.py', 'pdf_reader.py', 'image_ocr.py']
    for py_file in py_files:
        py_path = base_dir / py_file
        if py_path.exists():
            print(f"✅ {py_file}: Exists")
        else:
            print(f"❌ {py_file}: Missing")
            all_good = False
    
    print("✅ File Organization: PASS" if all_good else "❌ File Organization: FAIL")
    return all_good

if __name__ == "__main__":
    test_file_organization()
