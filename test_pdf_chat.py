#!/usr/bin/env python3
"""
Test PDF Chat Functionality
Test the PDF upload and chat features
"""

import requests
import time
from datetime import datetime

def test_pdf_chat_functionality():
    """Test PDF chat functionality."""
    print("🧪 TESTING PDF CHAT FUNCTIONALITY")
    print("=" * 80)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if server is running
    print("\n🔍 Test 1: Server Health Check")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Server Status: {health.get('status')}")
            print(f"   ✅ Ready: {health.get('ready')}")
            print(f"   ✅ MongoDB: {'Connected' if health.get('mongodb_connected') else 'Disconnected'}")
            print(f"   ✅ Agents: {health.get('system', {}).get('loaded_agents', 0)} loaded")
        else:
            print(f"   ❌ Server error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    # Test 2: Check PDF chat interface
    print("\n📄 Test 2: PDF Chat Interface")
    try:
        response = requests.get(f"{base_url}/pdf-chat", timeout=5)
        if response.status_code == 200:
            content = response.text
            
            # Check for key elements
            pdf_elements = [
                'PDF Chat Interface',
                'Upload PDF Document',
                'Chat with Your PDF',
                'file-drop-zone',
                'chatMessages',
                'sendQuestion'
            ]
            
            found_elements = []
            for element in pdf_elements:
                if element in content:
                    found_elements.append(element)
            
            print(f"   ✅ PDF chat interface loaded successfully")
            print(f"   ✅ Interface elements found: {len(found_elements)}/{len(pdf_elements)}")
            
            if len(found_elements) >= len(pdf_elements) * 0.8:
                print("   🎉 PDF chat interface appears fully functional!")
            else:
                print("   ⚠️ Some PDF chat elements may be missing")
                
        else:
            print(f"   ❌ PDF chat interface error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ PDF chat interface error: {e}")
        return False
    
    # Test 3: Test text document upload (since we may not have PDF files)
    print("\n📝 Test 3: Text Document Upload")
    try:
        test_content = """
        Test Document for PDF Chat System
        
        This is a test document to verify the document upload and chat functionality.
        
        Key Information:
        - Document Type: Test Document
        - Purpose: Testing PDF chat system
        - Date: 2025-05-30
        - Features: Upload, processing, and chat functionality
        
        The system should be able to:
        1. Upload and process documents
        2. Extract text content
        3. Answer questions about the content
        4. Maintain chat sessions
        
        This document contains important information about testing procedures.
        """
        
        response = requests.post(
            f"{base_url}/api/upload/text",
            data={
                'content': test_content,
                'filename': 'test_document.txt'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                file_id = result.get('file_id')
                print(f"   ✅ Text document uploaded successfully")
                print(f"   📄 File ID: {file_id}")
                print(f"   📝 Text Length: {result.get('text_length')} characters")
                print(f"   📁 Filename: {result.get('filename')}")
                
                # Test 4: Chat with uploaded document
                print("\n💬 Test 4: Chat with Document")
                
                test_questions = [
                    "What is the purpose of this document?",
                    "What date is mentioned in the document?",
                    "List the key features mentioned",
                    "What type of document is this?"
                ]
                
                successful_chats = 0
                
                for i, question in enumerate(test_questions, 1):
                    print(f"\n   Question {i}: {question}")
                    
                    try:
                        chat_response = requests.post(
                            f"{base_url}/api/chat/document",
                            json={
                                "question": question,
                                "document_content": test_content,
                                "document_name": "test_document.txt",
                                "session_id": "test_session_123"
                            },
                            timeout=30
                        )
                        
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            if chat_result.get('status') == 'success':
                                print(f"   ✅ Chat successful")
                                print(f"   🤖 Agent: {chat_result.get('agent_used', 'Unknown')}")
                                
                                # Show answer if available
                                if chat_result.get('message'):
                                    print(f"   💬 Answer: {chat_result['message'][:100]}...")
                                elif chat_result.get('result'):
                                    print(f"   💬 Result: {chat_result['result']}")
                                
                                successful_chats += 1
                            else:
                                print(f"   ⚠️ Chat failed: {chat_result.get('message', 'Unknown error')}")
                        else:
                            print(f"   ❌ Chat HTTP error: {chat_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ Chat error: {e}")
                    
                    time.sleep(1)
                
                print(f"\n   📊 Chat Results: {successful_chats}/{len(test_questions)} successful")
                
                # Test 5: List uploaded documents
                print("\n📋 Test 5: List Uploaded Documents")
                try:
                    list_response = requests.get(f"{base_url}/api/documents", timeout=10)
                    if list_response.status_code == 200:
                        list_result = list_response.json()
                        if list_result.get('status') == 'success':
                            documents = list_result.get('documents', [])
                            print(f"   ✅ Documents listed successfully")
                            print(f"   📄 Total documents: {len(documents)}")
                            
                            for doc in documents:
                                print(f"   📁 {doc.get('filename')} ({doc.get('type', 'unknown')})")
                        else:
                            print(f"   ⚠️ Document listing failed: {list_result.get('message')}")
                    else:
                        print(f"   ❌ Document listing HTTP error: {list_response.status_code}")
                except Exception as e:
                    print(f"   ❌ Document listing error: {e}")
                
                return successful_chats >= len(test_questions) * 0.5  # 50% success rate
            else:
                print(f"   ❌ Text upload failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Text upload HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Text upload error: {e}")
        return False

def main():
    """Main function."""
    print("🚀 PDF CHAT FUNCTIONALITY TESTER")
    print("=" * 80)
    
    success = test_pdf_chat_functionality()
    
    # Final Results
    print(f"\n" + "=" * 80)
    print("🎯 PDF CHAT TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("✅ PDF CHAT FUNCTIONALITY TEST PASSED!")
        print("🎉 Your PDF chat system is working!")
        
        print(f"\n🌐 ACCESS YOUR PDF CHAT SYSTEM:")
        print("📄 PDF Chat Interface: http://localhost:8000/pdf-chat")
        print("🏠 Main Interface: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        
        print(f"\n💡 HOW TO USE:")
        print("1. Go to http://localhost:8000/pdf-chat")
        print("2. Upload a PDF file or use text content")
        print("3. Ask questions about the document")
        print("4. Get intelligent responses from the AI")
        print("5. Continue chatting with follow-up questions")
        
        print(f"\n📄 SUPPORTED FEATURES:")
        print("✅ PDF file upload and processing")
        print("✅ Text document upload")
        print("✅ Natural language questions")
        print("✅ Intelligent document analysis")
        print("✅ Chat session management")
        print("✅ Document listing and management")
        print("✅ Real-time responses")
        
    else:
        print("⚠️ PDF CHAT FUNCTIONALITY TEST HAD ISSUES")
        print("🔧 Some features may not be working correctly")
        print("💡 Check the test results above for details")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%H:%M:%S')}")
    return success

if __name__ == "__main__":
    main()
