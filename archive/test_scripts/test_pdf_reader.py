#!/usr/bin/env python3
"""Test PDF Reader functionality"""

import os
from pathlib import Path

def test_pdf_reader():
    print("🔍 TEST 3: PDF Reader Module")
    
    try:
        from data.multimodal.pdf_reader import extract_text_from_pdf, EnhancedPDFReader
        
        # Find PDF files
        pdf_dir = Path("data/multimodal/uploaded_pdfs")
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"PDF files found: {len(pdf_files)}")
        
        if pdf_files:
            # Test basic extraction
            test_pdf = pdf_files[0]
            result = extract_text_from_pdf(str(test_pdf), verbose=False)
            success = len(result) > 0 and not result.startswith('❌')
            print(f"Text extraction: {'SUCCESS' if success else 'FAILED'}")
            print(f"Text length: {len(result)}")
            
            # Test enhanced reader
            reader = EnhancedPDFReader()
            print(f"Enhanced reader LLM: {reader.llm is not None}")
            print(f"Enhanced reader Embeddings: {reader.embeddings is not None}")
            
            print("✅ PDF Reader: PASS" if success else "❌ PDF Reader: FAIL")
            return success
        else:
            print("No PDF files found for testing")
            print("✅ PDF Reader: PASS (no files to test)")
            return True
            
    except Exception as e:
        print(f"❌ PDF Reader: FAIL - {e}")
        return False

if __name__ == "__main__":
    test_pdf_reader()
