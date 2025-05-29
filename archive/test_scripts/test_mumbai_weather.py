#!/usr/bin/env python3
"""
Test Mumbai weather fix
"""

import requests
import json

def test_mumbai_weather():
    """Test that Mumbai weather query returns Mumbai weather."""
    
    print("🌤️ Testing Mumbai Weather Fix")
    print("=" * 40)
    
    # Test different Mumbai weather queries
    mumbai_queries = [
        "what is the weather in Mumbai",
        "weather in Mumbai",
        "Mumbai weather",
        "temperature in Mumbai",
        "weather for Mumbai"
    ]
    
    for query in mumbai_queries:
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
                print(f"📍 Location: {result.get('location', 'N/A')}")
                
                if result.get('location', '').lower() == 'mumbai':
                    print("✅ CORRECT: Mumbai weather returned!")
                else:
                    print(f"❌ WRONG: Got {result.get('location')} instead of Mumbai")
                
                if 'current' in result:
                    current = result['current']
                    print(f"🌡️ Temperature: {current.get('temperature', 'N/A')}")
                    print(f"☁️ Condition: {current.get('condition', 'N/A')}")
                
                if 'summary' in result:
                    print(f"📝 Summary: {result['summary']}")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test other cities to make sure they work too
    print(f"\n🌍 Testing Other Cities:")
    other_cities = [
        "weather in London",
        "weather in New York", 
        "weather in Tokyo"
    ]
    
    for query in other_cities:
        try:
            response = requests.post(
                'http://localhost:8000/api/mcp/command',
                json={'command': query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                expected_city = query.split()[-1]  # Get last word (city name)
                actual_city = result.get('location', '')
                
                print(f"🔍 {query} → {actual_city}")
                if expected_city.lower() in actual_city.lower():
                    print("✅ Correct location!")
                else:
                    print(f"❌ Expected {expected_city}, got {actual_city}")
            
        except Exception as e:
            print(f"❌ Error testing {query}: {e}")
    
    print(f"\n🎯 MUMBAI WEATHER FIX TEST COMPLETE")
    print("=" * 40)
    print("✅ Location extraction should now work correctly")
    print("✅ Mumbai queries should return Mumbai weather")
    print("✅ Other cities should work as expected")

if __name__ == "__main__":
    test_mumbai_weather()
