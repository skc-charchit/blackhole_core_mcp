#!/usr/bin/env python3
"""
Test MongoDB Storage - Quick test to verify storage is working
"""

import requests
import json
from datetime import datetime

def test_command_storage():
    """Test if commands are being stored in MongoDB."""
    print("🧪 TESTING MONGODB STORAGE")
    print("=" * 50)
    
    # Test commands
    test_commands = [
        "Calculate 20% of 500",
        "What is the weather in Mumbai?",
        "Send email to test@example.com"
    ]
    
    for command in test_commands:
        print(f"\n📤 Testing: {command}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": command},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if stored in MongoDB
                stored = result.get("stored_in_mongodb", False)
                agent_used = result.get("agent_used", "unknown")
                status = result.get("status", "unknown")
                
                print(f"   ✅ Status: {status}")
                print(f"   🤖 Agent: {agent_used}")
                print(f"   💾 MongoDB Storage: {'✅ Stored' if stored else '❌ Not Stored'}")
                
                if "result" in result:
                    print(f"   📊 Result: {result['result']}")
                
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_command_storage()
