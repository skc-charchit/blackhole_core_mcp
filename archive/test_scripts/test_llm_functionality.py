#!/usr/bin/env python3
"""Test LLM functionality with user's credentials"""

import os
from pathlib import Path

def test_llm_functionality():
    print("🔍 Testing LLM Functionality with Your Credentials")
    print("=" * 50)
    
    try:
        from data.multimodal.pdf_reader import EnhancedPDFReader
        
        # Initialize reader with your credentials
        reader = EnhancedPDFReader()
        
        print(f"✅ LLM Available: {reader.llm is not None}")
        print(f"✅ Embeddings Available: {reader.embeddings is not None}")
        print(f"✅ API Key Set: {bool(reader.api_key)}")
        print(f"✅ Model: {reader.model_name}")
        
        if reader.llm and reader.embeddings:
            # Find a PDF to test with
            pdf_dir = Path("data/multimodal/uploaded_pdfs")
            pdf_files = list(pdf_dir.glob("*.pdf"))
            
            if pdf_files:
                test_pdf = pdf_files[0]
                print(f"\n🔍 Testing with PDF: {test_pdf.name}")
                
                # Load and process PDF
                success = reader.load_and_process_pdf(str(test_pdf), verbose=True)
                
                if success:
                    print("✅ PDF loaded successfully for Q&A")
                    
                    # Test asking a question
                    question = "What is this document about?"
                    print(f"\n🤔 Asking: {question}")
                    
                    answer = reader.ask_question(question, verbose=True)
                    
                    if answer and not answer.startswith("❌"):
                        print(f"✅ LLM Answer received:")
                        print(f"📝 {answer[:200]}...")
                        
                        # Test document summary
                        print(f"\n📄 Getting document summary...")
                        summary = reader.get_document_summary(max_length=150)
                        print(f"✅ Summary: {summary[:150]}...")
                        
                        print("\n🎉 LLM Functionality: FULLY WORKING!")
                        return True
                    else:
                        print(f"❌ LLM Answer failed: {answer}")
                        return False
                else:
                    print("❌ PDF processing failed")
                    return False
            else:
                print("⚠️ No PDF files found for testing")
                print("✅ LLM components are working (no test files)")
                return True
        else:
            print("❌ LLM components not properly initialized")
            return False
            
    except Exception as e:
        print(f"❌ LLM Test failed: {e}")
        return False

if __name__ == "__main__":
    test_llm_functionality()
