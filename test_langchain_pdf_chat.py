#!/usr/bin/env python3
"""
Test LangChain PDF Chat Integration
Verify that LangChain RAG is working for PDF question answering
"""

import requests
import time
import sys
from datetime import datetime
from pathlib import Path

def test_langchain_availability():
    """Test if LangChain components are available."""
    print("🧪 TESTING LANGCHAIN AVAILABILITY")
    print("=" * 60)
    
    try:
        # Test LangChain imports
        sys.path.insert(0, str(Path(__file__).parent / "data" / "multimodal"))
        from pdf_reader import EnhancedPDFReader
        
        # Initialize PDF reader
        pdf_reader = EnhancedPDFReader()
        
        print(f"   ✅ EnhancedPDFReader imported successfully")
        print(f"   🤖 LLM Available: {pdf_reader.llm is not None}")
        print(f"   🔗 Embeddings Available: {pdf_reader.embeddings is not None}")
        print(f"   📝 Text Splitter Available: {pdf_reader.text_splitter is not None}")
        print(f"   💾 Memory Available: {pdf_reader.memory is not None}")
        
        if pdf_reader.llm:
            print(f"   🎯 LangChain RAG: READY")
            return True, pdf_reader
        else:
            print(f"   ⚠️ LangChain RAG: NOT AVAILABLE (missing API key or dependencies)")
            return False, pdf_reader
            
    except Exception as e:
        print(f"   ❌ LangChain Error: {e}")
        return False, None

def test_pdf_chat_with_langchain():
    """Test PDF chat functionality with LangChain."""
    print("\n📄 TESTING PDF CHAT WITH LANGCHAIN")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check server health
    print("\n🔍 Step 1: Server Health Check")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Server Status: {health.get('status')}")
            print(f"   ✅ Ready: {health.get('ready')}")
        else:
            print(f"   ❌ Server error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    # Test 2: Upload a test document
    print("\n📤 Step 2: Upload Test Document")
    
    # Create a comprehensive test document
    test_content = """
    LangChain RAG Test Document
    
    This is a comprehensive test document for verifying LangChain RAG functionality in the PDF chat system.
    
    SECTION 1: INTRODUCTION
    This document contains various types of information to test the question-answering capabilities:
    - Technical specifications
    - Important dates and numbers
    - Key concepts and definitions
    - Procedural information
    
    SECTION 2: TECHNICAL SPECIFICATIONS
    System Requirements:
    - Memory: 8GB RAM minimum, 16GB recommended
    - Storage: 500GB SSD
    - Processor: Intel i5 or AMD Ryzen 5
    - Operating System: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
    
    SECTION 3: IMPORTANT DATES
    - Project Start Date: January 15, 2025
    - Beta Release: March 1, 2025
    - Final Release: May 30, 2025
    - End of Support: December 31, 2027
    
    SECTION 4: KEY CONCEPTS
    LangChain: A framework for developing applications powered by language models.
    RAG (Retrieval-Augmented Generation): A technique that combines retrieval of relevant documents with generation.
    Vector Store: A database that stores vector embeddings for semantic search.
    Embeddings: Numerical representations of text that capture semantic meaning.
    
    SECTION 5: PROCEDURES
    To implement RAG:
    1. Split documents into chunks
    2. Create embeddings for each chunk
    3. Store embeddings in a vector database
    4. For queries, retrieve relevant chunks
    5. Use LLM to generate answers based on retrieved context
    
    SECTION 6: PERFORMANCE METRICS
    Expected Performance:
    - Query Response Time: < 2 seconds
    - Accuracy: > 85%
    - Relevance Score: > 0.8
    - User Satisfaction: > 90%
    
    SECTION 7: CONCLUSION
    This document serves as a comprehensive test case for LangChain RAG functionality.
    It contains structured information that can be used to verify question-answering capabilities.
    """
    
    try:
        response = requests.post(
            f"{base_url}/api/upload/text",
            data={
                'content': test_content,
                'filename': 'langchain_rag_test.txt'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                file_id = result.get('file_id')
                print(f"   ✅ Document uploaded successfully")
                print(f"   📄 File ID: {file_id}")
                print(f"   📝 Text Length: {result.get('text_length')} characters")
                
                # Test 3: LangChain RAG Questions
                print("\n🧠 Step 3: LangChain RAG Question Testing")
                
                test_questions = [
                    {
                        "question": "What are the system requirements mentioned in the document?",
                        "expected_keywords": ["8GB", "RAM", "500GB", "SSD", "Intel", "AMD"]
                    },
                    {
                        "question": "When is the final release date?",
                        "expected_keywords": ["May 30, 2025", "final release"]
                    },
                    {
                        "question": "What is RAG and how does it work?",
                        "expected_keywords": ["Retrieval-Augmented Generation", "retrieval", "generation", "chunks"]
                    },
                    {
                        "question": "What are the expected performance metrics?",
                        "expected_keywords": ["2 seconds", "85%", "accuracy", "satisfaction"]
                    },
                    {
                        "question": "List the steps to implement RAG",
                        "expected_keywords": ["split", "embeddings", "vector", "retrieve", "LLM"]
                    }
                ]
                
                successful_rag_tests = 0
                langchain_used = 0
                
                for i, test in enumerate(test_questions, 1):
                    print(f"\n   Question {i}: {test['question']}")
                    
                    try:
                        chat_response = requests.post(
                            f"{base_url}/api/chat/document",
                            json={
                                "question": test['question'],
                                "document_content": test_content,
                                "document_name": "langchain_rag_test.txt",
                                "session_id": "langchain_test_session"
                            },
                            timeout=30
                        )
                        
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            if chat_result.get('status') == 'success':
                                print(f"   ✅ Chat successful")
                                print(f"   🤖 Agent: {chat_result.get('agent_used', 'Unknown')}")
                                
                                # Check if LangChain was used
                                if chat_result.get('rag_enabled'):
                                    print(f"   🧠 LangChain RAG: ENABLED")
                                    langchain_used += 1
                                elif chat_result.get('llm_powered'):
                                    print(f"   🤖 LLM Powered: YES")
                                else:
                                    print(f"   ⚠️ Basic Processing: Used")
                                
                                # Check answer quality
                                answer = ""
                                if chat_result.get('answer'):
                                    answer = chat_result['answer']
                                elif chat_result.get('message'):
                                    answer = chat_result['message']
                                elif chat_result.get('result'):
                                    answer = str(chat_result['result'])
                                
                                if answer:
                                    print(f"   💬 Answer: {answer[:100]}...")
                                    
                                    # Check if answer contains expected keywords
                                    answer_lower = answer.lower()
                                    found_keywords = [kw for kw in test['expected_keywords'] 
                                                    if kw.lower() in answer_lower]
                                    
                                    if found_keywords:
                                        print(f"   ✅ Keywords found: {found_keywords}")
                                        successful_rag_tests += 1
                                    else:
                                        print(f"   ⚠️ Expected keywords not found")
                                else:
                                    print(f"   ⚠️ No answer received")
                            else:
                                print(f"   ❌ Chat failed: {chat_result.get('message', 'Unknown error')}")
                        else:
                            print(f"   ❌ Chat HTTP error: {chat_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ Chat error: {e}")
                    
                    time.sleep(1)
                
                # Results Summary
                print(f"\n📊 LANGCHAIN RAG TEST RESULTS:")
                print(f"   ✅ Successful Tests: {successful_rag_tests}/{len(test_questions)}")
                print(f"   🧠 LangChain RAG Used: {langchain_used}/{len(test_questions)}")
                
                success_rate = (successful_rag_tests / len(test_questions)) * 100
                rag_usage_rate = (langchain_used / len(test_questions)) * 100
                
                print(f"   📈 Success Rate: {success_rate:.1f}%")
                print(f"   🎯 RAG Usage Rate: {rag_usage_rate:.1f}%")
                
                return success_rate >= 60 and rag_usage_rate >= 50
                
            else:
                print(f"   ❌ Document upload failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Document upload HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Document upload error: {e}")
        return False

def main():
    """Main function."""
    print("🧠 LANGCHAIN PDF CHAT INTEGRATION TESTER")
    print("=" * 80)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test LangChain availability
    langchain_available, pdf_reader = test_langchain_availability()
    
    # Test PDF chat functionality
    if langchain_available:
        print(f"\n🎉 LangChain is available! Testing RAG functionality...")
        success = test_pdf_chat_with_langchain()
    else:
        print(f"\n⚠️ LangChain not fully available. Testing basic functionality...")
        success = test_pdf_chat_with_langchain()  # Still test, but expect fallback
    
    # Final Results
    print(f"\n" + "=" * 80)
    print("🎯 LANGCHAIN PDF CHAT TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("✅ LANGCHAIN PDF CHAT TEST PASSED!")
        if langchain_available:
            print("🧠 LangChain RAG is working correctly!")
            print("🎉 Your PDF chat system uses advanced AI for question answering!")
        else:
            print("⚠️ LangChain not available, but fallback system works!")
        
        print(f"\n🌐 ACCESS YOUR ENHANCED PDF CHAT:")
        print("📄 PDF Chat Interface: http://localhost:8000/pdf-chat")
        print("🏠 Main Interface: http://localhost:8000")
        
        print(f"\n🧠 LANGCHAIN FEATURES:")
        if langchain_available:
            print("✅ RAG (Retrieval-Augmented Generation)")
            print("✅ Vector embeddings for semantic search")
            print("✅ Conversation memory")
            print("✅ Document chunking and processing")
            print("✅ LLM-powered intelligent responses")
        else:
            print("⚠️ Install LangChain dependencies for full RAG functionality")
            print("💡 pip install langchain langchain-community langchain-together")
        
    else:
        print("⚠️ LANGCHAIN PDF CHAT TEST HAD ISSUES")
        print("🔧 Some features may not be working correctly")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%H:%M:%S')}")
    return success

if __name__ == "__main__":
    main()
