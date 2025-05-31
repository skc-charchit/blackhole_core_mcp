#!/usr/bin/env python3
"""
Enhanced MongoDB Storage for Agents
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "blackhole_core" / "data_source"))

from mongodb import get_agent_outputs_collection
from datetime import datetime

async def store_agent_result(agent_id, command, result, metadata=None):
    """Store agent result in MongoDB with enhanced data."""
    try:
        collection = get_agent_outputs_collection()
        
        document = {
            "agent_id": agent_id,
            "command": command,
            "result": result,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
            "stored_by": "enhanced_storage"
        }
        
        result = collection.insert_one(document)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Storage error: {e}")
        return None

def get_agent_history(agent_id, limit=10):
    """Get agent command history from MongoDB."""
    try:
        collection = get_agent_outputs_collection()
        
        cursor = collection.find(
            {"agent_id": agent_id}
        ).sort("timestamp", -1).limit(limit)
        
        return list(cursor)
    except Exception as e:
        print(f"History retrieval error: {e}")
        return []

def get_all_agent_stats():
    """Get statistics for all agents."""
    try:
        collection = get_agent_outputs_collection()
        
        pipeline = [
            {"$group": {
                "_id": "$agent_id",
                "total_commands": {"$sum": 1},
                "last_used": {"$max": "$timestamp"}
            }}
        ]
        
        return list(collection.aggregate(pipeline))
    except Exception as e:
        print(f"Stats retrieval error: {e}")
        return []

if __name__ == "__main__":
    # Test the enhanced storage
    import asyncio
    
    async def test():
        result = await store_agent_result(
            "test_agent", 
            "test command", 
            {"test": "result"}
        )
        print(f"Stored with ID: {result}")
        
        history = get_agent_history("test_agent")
        print(f"History: {len(history)} entries")
        
        stats = get_all_agent_stats()
        print(f"Stats: {stats}")
    
    asyncio.run(test())
