#!/usr/bin/env python3
"""
Test misspelling fix for city names
"""

import requests
import json

def test_misspelling_fix():
    """Test that misspelled city names are corrected."""
    
    print("🔤 Testing City Name Misspelling Fix")
    print("=" * 50)
    
    # Test misspelled city names
    misspelling_tests = [
        ("weather in banglore", "Bangalore"),
        ("weather in bengaluru", "Bangalore"), 
        ("weather in bombay", "Mumbai"),
        ("weather in calcutta", "Kolkata"),
        ("weather in madras", "Chennai"),
        ("weather in new delhi", "Delhi"),
        ("weather in ny", "New York"),
        ("weather in nyc", "New York"),
        ("weather in la", "Los Angeles")
    ]
    
    for query, expected_city in misspelling_tests:
        print(f"\n🔍 Testing: '{query}' → Should return {expected_city}")
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
                    
                    # Check if location is corrected
                    actual_location = result.get('location', '')
                    if expected_city.lower() in actual_location.lower():
                        print(f"✅ CORRECT: Misspelling corrected to {actual_location}!")
                    else:
                        print(f"❌ WRONG: Expected {expected_city}, got {actual_location}")
                    
                    if 'current' in result:
                        current = result['current']
                        print(f"🌡️ Temperature: {current.get('temperature', 'N/A')}")
                        print(f"☁️ Condition: {current.get('condition', 'N/A')}")
                    
                    if 'summary' in result:
                        print(f"📝 Summary: {result['summary']}")
                        
                else:
                    print(f"❌ WRONG: Routed to {result.get('type')} instead of weather")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test correct spellings still work
    print(f"\n✅ Testing Correct Spellings Still Work:")
    correct_tests = [
        ("weather in bangalore", "Bangalore"),
        ("weather in mumbai", "Mumbai"),
        ("weather in delhi", "Delhi"),
        ("weather in london", "London")
    ]
    
    for query, expected_city in correct_tests:
        try:
            response = requests.post(
                'http://localhost:8000/api/mcp/command',
                json={'command': query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                actual_location = result.get('location', '')
                
                print(f"🔍 '{query}' → {actual_location}")
                
                if expected_city.lower() in actual_location.lower():
                    print("  ✅ Correct spelling works!")
                else:
                    print(f"  ❌ Expected {expected_city}, got {actual_location}")
            
        except Exception as e:
            print(f"❌ Error testing {query}: {e}")
    
    print(f"\n🎯 MISSPELLING FIX TEST COMPLETE")
    print("=" * 50)
    print("✅ Common misspellings should be corrected")
    print("✅ banglore → bangalore")
    print("✅ bombay → mumbai") 
    print("✅ calcutta → kolkata")
    print("✅ Correct spellings should still work")

if __name__ == "__main__":
    test_misspelling_fix()
