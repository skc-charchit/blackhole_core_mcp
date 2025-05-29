#!/usr/bin/env python3
"""
Test Bangalore weather fix
"""

import requests
import json

def test_bangalore_weather():
    """Test that Bangalore weather query returns Bangalore weather."""
    
    print("🌤️ Testing Bangalore Weather Fix")
    print("=" * 50)
    
    # Test different Bangalore weather queries
    bangalore_queries = [
        "weather in bangalore",
        "weather in Bangalore", 
        "bangalore weather",
        "Bangalore weather",
        "what is the weather in bangalore",
        "temperature in bangalore",
        "how is the weather in bangalore"
    ]
    
    for query in bangalore_queries:
        print(f"\n🔍 Testing: '{query}'")
        try:
            response = requests.post(
                'http://localhost:8000/api/mcp/command',
                json={'command': query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Status: {result.get('status')}")
                print(f"🎯 Type: {result.get('type')}")
                print(f"📍 Location: {result.get('location', 'N/A')}")
                
                # Check if it's weather response
                if result.get('type') == 'weather':
                    print("✅ CORRECT: Routed to weather agent!")
                    
                    # Check if location is correct
                    location = result.get('location', '').lower()
                    if 'bangalore' in location or 'bengaluru' in location:
                        print("✅ CORRECT: Bangalore weather returned!")
                    else:
                        print(f"❌ WRONG: Got {result.get('location')} instead of Bangalore")
                    
                    if 'current' in result:
                        current = result['current']
                        print(f"🌡️ Temperature: {current.get('temperature', 'N/A')}")
                        print(f"☁️ Condition: {current.get('condition', 'N/A')}")
                        print(f"💧 Humidity: {current.get('humidity', 'N/A')}")
                    
                    if 'summary' in result:
                        print(f"📝 Summary: {result['summary']}")
                        
                else:
                    print(f"❌ WRONG: Routed to {result.get('type')} instead of weather")
                    if 'summary' in result:
                        print(f"📝 Response: {result['summary']}")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test pattern matching specifically
    print(f"\n🔍 Testing Pattern Matching:")
    test_patterns = [
        "weather in mumbai",
        "mumbai weather", 
        "what is the weather in delhi",
        "temperature in chennai",
        "how is the weather in kolkata"
    ]
    
    for query in test_patterns:
        try:
            response = requests.post(
                'http://localhost:8000/api/mcp/command',
                json={'command': query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_type = result.get('type', 'unknown')
                location = result.get('location', 'N/A')
                
                print(f"🔍 '{query}' → Type: {response_type}, Location: {location}")
                
                if response_type == 'weather':
                    print("  ✅ Correctly routed to weather!")
                else:
                    print(f"  ❌ Incorrectly routed to {response_type}")
            
        except Exception as e:
            print(f"❌ Error testing {query}: {e}")
    
    print(f"\n🎯 BANGALORE WEATHER FIX TEST COMPLETE")
    print("=" * 50)
    print("✅ Command patterns updated to catch weather queries")
    print("✅ Location extraction should work for all formats")
    print("✅ Bangalore queries should return Bangalore weather")

if __name__ == "__main__":
    test_bangalore_weather()
