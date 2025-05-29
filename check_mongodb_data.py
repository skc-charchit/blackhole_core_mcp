#!/usr/bin/env python3
"""
Quick MongoDB Data Checker
"""

import os
from dotenv import load_dotenv
import pymongo
from datetime import datetime

# Load environment variables
load_dotenv()

def check_mongodb_data():
    """Check what data is in MongoDB."""
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(os.getenv('MONGO_URI'))
        db = client[os.getenv('MONGO_DB_NAME', 'blackhole_db')]
        collection = db[os.getenv('MONGO_COLLECTION_NAME', 'agent_outputs')]
        
        print("🔍 MongoDB Data Analysis")
        print("=" * 40)
        
        # Collections
        collections = db.list_collection_names()
        print(f"📁 Collections: {collections}")
        
        # Agent outputs count
        total_docs = collection.count_documents({})
        print(f"📊 Total agent outputs: {total_docs}")
        
        # Agent types
        agents = list(collection.distinct('agent'))
        print(f"🤖 Agent types: {agents}")
        
        # Recent documents
        recent = list(collection.find().sort('_id', -1).limit(5))
        print(f"\n📄 Recent documents ({len(recent)}):")
        for i, doc in enumerate(recent, 1):
            agent = doc.get('agent', 'unknown')
            timestamp = doc.get('timestamp', doc.get('created_at', 'unknown'))
            has_output = 'output' in doc
            print(f"  {i}. Agent: {agent}, Has output: {has_output}, Time: {timestamp}")
        
        # Check for specific agent data
        doc_agents = collection.count_documents({'agent': {'$regex': 'document', '$options': 'i'}})
        pdf_agents = collection.count_documents({'agent': {'$regex': 'pdf', '$options': 'i'}})
        ocr_agents = collection.count_documents({'agent': {'$regex': 'ocr', '$options': 'i'}})
        
        print(f"\n🎯 Specific agent data:")
        print(f"  📄 Document agents: {doc_agents}")
        print(f"  📄 PDF agents: {pdf_agents}")
        print(f"  🖼️ OCR agents: {ocr_agents}")
        
        # Sample document structure
        sample = collection.find_one()
        if sample:
            print(f"\n📋 Sample document structure:")
            print(f"  Keys: {list(sample.keys())}")
            if 'output' in sample:
                output_keys = list(sample['output'].keys()) if isinstance(sample['output'], dict) else ['non-dict output']
                print(f"  Output keys: {output_keys}")
        
        client.close()
        
        print("\n✅ MongoDB is connected and contains data!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_mongodb_data()
