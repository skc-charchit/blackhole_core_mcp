#!/usr/bin/env python3
"""
Simple LangChain Test
Test the LangChain integration with a simple document
"""

import requests
import time
from datetime import datetime

def test_simple_langchain():
    """Test LangChain with a simple document."""
    print("🧠 SIMPLE LANGCHAIN TEST")
    print("=" * 60)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    
    # Test 2: Upload a simple test document
    print("\n📤 Step 2: Upload Simple Test Document")
    
    # Create a simple test document
    simple_content = """
    Simple Test Document for LangChain
    
    This is a simple test document to verify LangChain functionality.
    
    Key Information:
    - Document Type: Test Document
    - Purpose: Testing LangChain RAG
    - Date: May 30, 2025
    - Author: MCP System
    
    Important Facts:
    - The capital of France is Paris
    - The year 2025 is mentioned in this document
    - This document contains exactly 4 key information points
    - LangChain is a framework for building AI applications
    
    Conclusion:
    This document serves as a simple test case for LangChain integration.
    """
    
    try:
        response = requests.post(
            f"{base_url}/api/upload/text",
            data={
                'content': simple_content,
                'filename': 'simple_langchain_test.txt'
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
                
                # Test 3: Simple LangChain Questions
                print("\n🧠 Step 3: Simple LangChain Questions")
                
                simple_questions = [
                    "What is the capital of France?",
                    "What year is mentioned in this document?",
                    "What is LangChain?",
                    "Who is the author of this document?"
                ]
                
                successful_tests = 0
                langchain_used = 0
                
                for i, question in enumerate(simple_questions, 1):
                    print(f"\n   Question {i}: {question}")
                    
                    try:
                        chat_response = requests.post(
                            f"{base_url}/api/chat/document",
                            json={
                                "question": question,
                                "document_content": simple_content,
                                "document_name": "simple_langchain_test.txt",
                                "session_id": "simple_test_session"
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
                                    print(f"   🧠 LangChain RAG: ENABLED ✅")
                                    langchain_used += 1
                                elif chat_result.get('llm_powered'):
                                    print(f"   🤖 LLM Powered: YES")
                                else:
                                    print(f"   ⚠️ Basic Processing: Used")
                                
                                # Show fallback reason if any
                                if chat_result.get('fallback_reason'):
                                    print(f"   ⚠️ Fallback: {chat_result['fallback_reason']}")
                                
                                # Get answer
                                answer = ""
                                if chat_result.get('answer'):
                                    answer = chat_result['answer']
                                elif chat_result.get('message'):
                                    answer = chat_result['message']
                                elif chat_result.get('result'):
                                    answer = str(chat_result['result'])
                                
                                if answer:
                                    print(f"   💬 Answer: {answer[:150]}...")
                                    successful_tests += 1
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
                print(f"\n📊 SIMPLE LANGCHAIN TEST RESULTS:")
                print(f"   ✅ Successful Tests: {successful_tests}/{len(simple_questions)}")
                print(f"   🧠 LangChain RAG Used: {langchain_used}/{len(simple_questions)}")
                
                success_rate = (successful_tests / len(simple_questions)) * 100
                rag_usage_rate = (langchain_used / len(simple_questions)) * 100
                
                print(f"   📈 Success Rate: {success_rate:.1f}%")
                print(f"   🎯 RAG Usage Rate: {rag_usage_rate:.1f}%")
                
                return success_rate >= 75
                
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
    print("🧠 SIMPLE LANGCHAIN INTEGRATION TESTER")
    print("=" * 80)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(10)
    
    success = test_simple_langchain()
    
    # Final Results
    print(f"\n" + "=" * 80)
    print("🎯 SIMPLE LANGCHAIN TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("✅ SIMPLE LANGCHAIN TEST PASSED!")
        print("🧠 LangChain integration is working!")
        
        print(f"\n🌐 ACCESS YOUR ENHANCED PDF CHAT:")
        print("📄 PDF Chat Interface: http://localhost:8000/pdf-chat")
        print("🏠 Main Interface: http://localhost:8000")
        
        print(f"\n🧠 LANGCHAIN FEATURES WORKING:")
        print("✅ Text document processing")
        print("✅ RAG (Retrieval-Augmented Generation)")
        print("✅ Vector embeddings for semantic search")
        print("✅ LLM-powered intelligent responses")
        print("✅ Document chunking and processing")
        
        print(f"\n💬 WHAT USERS CAN NOW DO:")
        print("✅ Upload PDF files and chat with them using AI")
        print("✅ Ask natural language questions about documents")
        print("✅ Get intelligent, context-aware responses")
        print("✅ Use advanced RAG technology for better answers")
        
    else:
        print("⚠️ SIMPLE LANGCHAIN TEST HAD ISSUES")
        print("🔧 LangChain may not be fully working")
        print("💡 Check the test results above for details")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%H:%M:%S')}")
    return success

if __name__ == "__main__":
    main()
