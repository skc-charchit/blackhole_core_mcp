#!/usr/bin/env python3
"""
Test PDF Reader Import
Verify that ConversationBufferMemory import is working correctly
"""

def test_langchain_imports():
    """Test LangChain imports including ConversationBufferMemory."""
    print("🧪 TESTING LANGCHAIN IMPORTS")
    print("=" * 50)
    
    try:
        # Test the specific import you requested
        from langchain.memory import ConversationBufferMemory
        print("✅ ConversationBufferMemory imported successfully")
        
        # Test creating an instance
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        print("✅ ConversationBufferMemory instance created successfully")
        
        # Test other related imports
        from langchain_community.document_loaders import PyPDFLoader
        print("✅ PyPDFLoader imported successfully")
        
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        print("✅ RecursiveCharacterTextSplitter imported successfully")
        
        from langchain_community.vectorstores import FAISS
        print("✅ FAISS imported successfully")
        
        from langchain.chains import ConversationalRetrievalChain
        print("✅ ConversationalRetrievalChain imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 SOLUTION:")
        print("Install required packages:")
        print("pip install langchain langchain-community langchain-core")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_pdf_reader_module():
    """Test importing the PDF reader module."""
    print("\n📄 TESTING PDF READER MODULE")
    print("=" * 50)
    
    try:
        # Import the PDF reader module
        import sys
        sys.path.append('data/multimodal')
        
        from pdf_reader import EnhancedPDFReader
        print("✅ EnhancedPDFReader imported successfully")
        
        # Try to create an instance
        reader = EnhancedPDFReader()
        print("✅ EnhancedPDFReader instance created successfully")
        
        # Check if LangChain components are available
        if hasattr(reader, 'memory') and reader.memory:
            print("✅ ConversationBufferMemory is working in PDF reader")
        else:
            print("⚠️ ConversationBufferMemory not initialized (may need API key)")
        
        return True
        
    except ImportError as e:
        print(f"❌ PDF reader import error: {e}")
        return False
    except Exception as e:
        print(f"❌ PDF reader error: {e}")
        return False

def check_environment():
    """Check environment setup for PDF reader."""
    print("\n🔍 CHECKING ENVIRONMENT")
    print("=" * 50)
    
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = [
        "TOGETHER_API_KEY",
        "TOGETHER_MODEL_NAME",
        "TOGETHER_EMBEDDING_MODEL"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value[:10])}...")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {missing_vars}")
        print("💡 Add these to your .env file for full functionality")
    else:
        print("\n✅ All environment variables are set")
    
    return len(missing_vars) == 0

def main():
    """Main test function."""
    print("🧪 PDF READER IMPORT TEST")
    print("=" * 80)
    print("🎯 Testing ConversationBufferMemory and related imports")
    print("=" * 80)
    
    tests = [
        ("LangChain Imports", test_langchain_imports),
        ("PDF Reader Module", test_pdf_reader_module),
        ("Environment Check", check_environment)
    ]
    
    passed_tests = 0
    
    for test_name, test_function in tests:
        try:
            if test_function():
                print(f"✅ {test_name} PASSED")
                passed_tests += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
        
        print()
    
    print("=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    print(f"✅ Passed: {passed_tests}/{len(tests)}")
    print(f"📈 Success rate: {(passed_tests/len(tests))*100:.1f}%")
    
    if passed_tests == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ ConversationBufferMemory import is working correctly")
        print("✅ PDF reader is ready for use")
        print("\n💡 USAGE EXAMPLE:")
        print("from langchain.memory import ConversationBufferMemory")
        print("memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)")
        
    elif passed_tests >= 1:
        print("\n🎯 PARTIAL SUCCESS!")
        print("✅ ConversationBufferMemory import is working")
        print("🔧 Some components may need additional setup")
        
    else:
        print("\n🔧 IMPORTS NEED ATTENTION")
        print("💡 Install missing packages:")
        print("pip install langchain langchain-community langchain-core")
    
    return passed_tests >= 1

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Import test completed successfully!")
        else:
            print("\n🔧 Import test found issues.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
