#!/usr/bin/env python3
"""
MongoDB Data Verification Script
Check if data is being stored properly in all collections
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def verify_mongodb_data():
    """Verify data in MongoDB collections."""
    print("🔍 MONGODB DATA VERIFICATION")
    print("=" * 60)
    
    try:
        from database.mongodb_manager import mongodb_manager
        
        # Connect to MongoDB
        await mongodb_manager.connect()
        
        # Get database stats
        stats = await mongodb_manager.get_database_stats()
        
        print("📊 DATABASE OVERVIEW:")
        print(f"   Database size: {stats.get('database', {}).get('size_mb', 0)} MB")
        print(f"   Storage size: {stats.get('database', {}).get('storage_mb', 0)} MB")
        print(f"   Total indexes: {stats.get('database', {}).get('indexes', 0)}")
        print()
        
        # Check each collection
        collections_to_check = [
            'conversations',
            'agent_logs', 
            'extracted_data',
            'query_cache',
            'user_sessions',
            'agent_performance'
        ]
        
        for collection_name in collections_to_check:
            if collection_name in stats:
                count = stats[collection_name]['document_count']
                print(f"📋 {collection_name}: {count} documents")
                
                # Show recent documents if any exist
                if count > 0:
                    collection = mongodb_manager.collections[collection_name]
                    recent_docs = list(collection.find().sort("timestamp", -1).limit(3))
                    
                    print(f"   📝 Recent entries:")
                    for i, doc in enumerate(recent_docs, 1):
                        timestamp = doc.get('timestamp', 'No timestamp')
                        if isinstance(timestamp, datetime):
                            timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        
                        if collection_name == 'conversations':
                            query = doc.get('query', 'No query')[:50]
                            print(f"      {i}. Query: {query}... ({timestamp})")
                        
                        elif collection_name == 'agent_logs':
                            agent = doc.get('agent_id', 'Unknown')
                            status = doc.get('status', 'Unknown')
                            print(f"      {i}. Agent: {agent}, Status: {status} ({timestamp})")
                        
                        elif collection_name == 'extracted_data':
                            source = doc.get('source_file', 'Unknown')
                            text_len = doc.get('text_length', 0)
                            print(f"      {i}. Source: {source}, Text: {text_len} chars ({timestamp})")
                        
                        else:
                            print(f"      {i}. Document exists ({timestamp})")
                
                print()
        
        # Test search functionality
        print("🔍 TESTING SEARCH FUNCTIONALITY:")
        
        # Search conversations
        conv_results = await mongodb_manager.search_conversations("weather", limit=3)
        print(f"   Weather conversations: {len(conv_results)} found")
        
        # Search extracted data
        data_results = await mongodb_manager.search_extracted_data("dave matthews", limit=3)
        print(f"   Dave Matthews extracts: {len(data_results)} found")
        
        print()
        
        # Test agent performance
        print("📈 AGENT PERFORMANCE METRICS:")
        performance = await mongodb_manager.get_agent_performance(hours=24)
        
        if performance:
            for agent_id, metrics in performance.items():
                success_rate = metrics.get('success_rate', 0) * 100
                avg_time = metrics.get('avg_execution_time', 0)
                total_exec = metrics.get('total_executions', 0)
                
                print(f"   🤖 {agent_id}:")
                print(f"      Executions: {total_exec}")
                print(f"      Success rate: {success_rate:.1f}%")
                print(f"      Avg time: {avg_time:.2f}s")
        else:
            print("   No performance data available yet")
        
        print("\n✅ MongoDB verification completed!")
        return True
        
    except Exception as e:
        print(f"❌ MongoDB verification failed: {e}")
        return False

async def test_conversation_engine():
    """Test conversation engine functionality."""
    print("\n🗣️ CONVERSATION ENGINE TEST")
    print("=" * 60)
    
    try:
        from core.conversation_engine import conversation_engine
        
        # Test query processing
        test_query = "What is 10% of 500?"
        user_id = "test_user"
        session_id = "test_session"
        
        print(f"📝 Testing query: {test_query}")
        
        result = await conversation_engine.process_query(user_id, session_id, test_query)
        
        print(f"📊 Result status: {result.get('status', 'unknown')}")
        print(f"💬 Response: {result.get('message', 'No message')[:100]}...")
        print(f"🤖 Agent used: {result.get('agent_used', 'unknown')}")
        
        # Test context retrieval
        context = await conversation_engine.get_conversation_context(user_id, session_id)
        print(f"📚 Context entries: {len(context)}")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ Conversation engine test failed: {e}")
        return False

async def test_inter_agent_coordinator():
    """Test inter-agent coordinator."""
    print("\n🤖 INTER-AGENT COORDINATOR TEST")
    print("=" * 60)
    
    try:
        from core.inter_agent_coordinator import inter_agent_coordinator
        
        # Get coordination stats
        stats = await inter_agent_coordinator.get_coordination_stats()
        
        print(f"📊 Registered agents: {stats.get('registered_agents', 0)}")
        print(f"🔄 Available workflows: {stats.get('available_workflows', 0)}")
        print(f"⚡ Workflow patterns: {', '.join(stats.get('workflow_patterns', []))}")
        
        # Test multi-agent coordination
        test_task = "Check weather in Delhi and calculate 20% of 1000"
        user_id = "test_user"
        session_id = "test_session"
        
        print(f"\n📝 Testing coordination: {test_task}")
        
        result = await inter_agent_coordinator.coordinate_multi_agent_task(
            test_task, user_id, session_id
        )
        
        print(f"📊 Coordination status: {result.get('status', 'unknown')}")
        print(f"💬 Response: {result.get('message', 'No message')[:100]}...")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ Inter-agent coordinator test failed: {e}")
        return False

async def main():
    """Main verification function."""
    print("🧪 COMPREHENSIVE SYSTEM VERIFICATION")
    print("=" * 80)
    print("🎯 Verifying MongoDB data storage and system functionality")
    print("=" * 80)
    
    tests = [
        ("MongoDB Data", verify_mongodb_data),
        ("Conversation Engine", test_conversation_engine),
        ("Inter-Agent Coordinator", test_inter_agent_coordinator)
    ]
    
    passed_tests = 0
    
    for test_name, test_function in tests:
        print(f"\n🔄 Running {test_name} test...")
        
        try:
            result = await test_function()
            if result:
                print(f"✅ {test_name} test PASSED")
                passed_tests += 1
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("📊 VERIFICATION RESULTS")
    print("=" * 80)
    print(f"✅ Passed tests: {passed_tests}/{len(tests)}")
    print(f"📈 Success rate: {(passed_tests/len(tests))*100:.1f}%")
    
    if passed_tests == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your MCP system is working perfectly!")
        print("💾 MongoDB integration confirmed")
        print("🗣️ Conversational AI operational")
        print("🤖 Inter-agent coordination ready")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("🔧 Check the error messages above")
    
    return passed_tests == len(tests)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\n🎉 System verification completed successfully!")
        else:
            print("\n🔧 System verification found issues.")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
