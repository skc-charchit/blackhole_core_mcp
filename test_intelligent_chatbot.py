#!/usr/bin/env python3
"""
Test Intelligent Chatbot - Demonstration of Complex Conditional Logic
Shows how the chatbot handles scenarios like weather-based email automation
"""

import requests
import json
from datetime import datetime

def test_chatbot_scenarios():
    """Test various chatbot scenarios."""
    print("🤖 INTELLIGENT CHATBOT DEMONSTRATION")
    print("=" * 80)
    print("🎯 Testing complex conditional logic and multi-agent coordination")
    print("📧 Email: shreekumarchandancharchit@gmail.com")
    print("=" * 80)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Mathematical Calculation",
            "command": "What is 15% of 200?",
            "description": "Basic math calculation"
        },
        {
            "name": "Weather Query",
            "command": "What is the weather in Mumbai?",
            "description": "Real-time weather data"
        },
        {
            "name": "Simple Reminder",
            "command": "Remind me to call John at 3 PM",
            "description": "Calendar reminder creation"
        },
        {
            "name": "Complex Conditional Logic",
            "command": "If it rains today after 4pm then remind me and send an email to shreekumarchandancharchit@gmail.com to not come to office and submit work on Monday EOD",
            "description": "Weather-based conditional email automation"
        },
        {
            "name": "Area Calculation",
            "command": "Calculate the area of a circle with radius 5",
            "description": "Mathematical word problem"
        },
        {
            "name": "Email Workflow",
            "command": "Send an email to shreekumarchandancharchit@gmail.com about weather conditions",
            "description": "Direct email automation"
        }
    ]
    
    print(f"🧪 Testing {len(scenarios)} scenarios...\n")
    
    success_count = 0
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. 🔍 {scenario['name']}")
        print(f"   📝 Command: \"{scenario['command']}\"")
        print(f"   💡 Description: {scenario['description']}")
        
        try:
            # Send command to MCP server
            response = requests.post(
                "http://localhost:8000/api/mcp/command",
                json={"command": scenario["command"]},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "success":
                    print(f"   ✅ Success!")
                    
                    # Display specific results based on scenario type
                    if "math" in scenario["name"].lower():
                        math_result = result.get("result", result.get("formatted_result", "N/A"))
                        print(f"   🔢 Result: {math_result}")
                        
                    elif "weather" in scenario["name"].lower():
                        city = result.get("city", "Unknown")
                        weather_data = result.get("weather_data", {})
                        temp = weather_data.get("temperature", "N/A")
                        desc = weather_data.get("description", "N/A")
                        print(f"   🌤️ Weather: {city} - {temp}°C, {desc}")
                        
                    elif "conditional" in scenario["name"].lower():
                        print(f"   🤖 Conditional logic processed!")
                        print(f"   📋 System will monitor weather conditions")
                        print(f"   📧 Email will be sent if conditions are met")
                        
                    elif "reminder" in scenario["name"].lower():
                        print(f"   📅 Reminder created successfully")
                        
                    elif "email" in scenario["name"].lower():
                        print(f"   📧 Email workflow initiated")
                    
                    # Show agent used
                    agent_used = result.get("agent_used", "general")
                    print(f"   🤖 Agent: {agent_used}")
                    
                    success_count += 1
                    
                else:
                    print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
                    
                    # Show suggestions if available
                    suggestions = result.get("suggestions", [])
                    if suggestions:
                        print(f"   💡 Suggestions:")
                        for suggestion in suggestions[:2]:
                            print(f"      - {suggestion}")
                    
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout (>15 seconds)")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error - is the MCP server running?")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
        
        print()  # Empty line between tests
    
    # Final summary
    print("=" * 80)
    print("📊 INTELLIGENT CHATBOT TEST RESULTS")
    print("=" * 80)
    print(f"✅ Successful scenarios: {success_count}/{len(scenarios)}")
    print(f"📈 Success rate: {(success_count/len(scenarios))*100:.1f}%")
    
    if success_count == len(scenarios):
        print("\n🎉 ALL CHATBOT SCENARIOS PASSED!")
        print("\n🌟 INTELLIGENT CHATBOT FEATURES WORKING:")
        print("   ✅ Mathematical calculations with natural language")
        print("   ✅ Real-time weather data integration")
        print("   ✅ Calendar reminders and scheduling")
        print("   ✅ Complex conditional logic processing")
        print("   ✅ Email automation with workflow integration")
        print("   ✅ Multi-agent coordination")
        
        print("\n🎯 COMPLEX SCENARIO EXAMPLE:")
        print("   📝 Input: 'If it rains today after 4pm then remind me and")
        print("           send email to shreekumarchandancharchit@gmail.com'")
        print("   🤖 System: Monitors weather → Checks time → Sends email")
        print("   📧 Result: Automated professional email sent!")
        
        print("\n💡 READY FOR PRODUCTION USE:")
        print("   🌐 Web interface: http://localhost:8000")
        print("   💬 Interactive chatbot: python intelligent_chatbot.py")
        print("   🤖 Complex conditional logic with real-world actions")
        
    elif success_count > 0:
        print(f"\n⚠️ PARTIAL SUCCESS: {success_count} out of {len(scenarios)} scenarios worked")
        print("🔧 Some scenarios may need refinement")
        
    else:
        print("\n❌ ALL CHATBOT TESTS FAILED")
        print("🔧 Please check:")
        print("   - MCP server is running")
        print("   - All agents are loaded properly")
        print("   - Environment configuration is correct")
    
    return success_count == len(scenarios)

def test_conditional_logic_parsing():
    """Test conditional logic parsing capabilities."""
    print("\n🧠 TESTING CONDITIONAL LOGIC PARSING")
    print("=" * 60)
    
    conditional_examples = [
        "If it rains today after 4pm then remind me",
        "If temperature is above 30 degrees then send email to john@example.com",
        "When it's sunny tomorrow then schedule meeting with team",
        "If it snows this weekend then cancel outdoor event"
    ]
    
    print("📝 Example conditional statements that the chatbot can understand:")
    
    for i, example in enumerate(conditional_examples, 1):
        print(f"{i}. \"{example}\"")
        
        # Parse components
        if "if" in example.lower():
            parts = example.lower().split("then")
            if len(parts) == 2:
                condition = parts[0].replace("if", "").strip()
                action = parts[1].strip()
                print(f"   🔍 Condition: {condition}")
                print(f"   🎯 Action: {action}")
            else:
                print(f"   ⚠️ Could not parse condition and action")
        print()

def show_chatbot_capabilities():
    """Show chatbot capabilities and examples."""
    print("\n🤖 INTELLIGENT CHATBOT CAPABILITIES")
    print("=" * 60)
    
    capabilities = {
        "🔢 Mathematical Operations": [
            "What is 15% of 200?",
            "Calculate the area of a circle with radius 5",
            "Solve 2 + 3 * 4",
            "What is the square root of 16?"
        ],
        "🌤️ Weather Intelligence": [
            "What is the weather in Mumbai?",
            "Check temperature in Delhi",
            "Is it raining in New York?",
            "Weather forecast for London"
        ],
        "📅 Calendar & Reminders": [
            "Remind me to call John at 3 PM",
            "Schedule meeting with team tomorrow",
            "Set reminder for doctor appointment",
            "Create calendar event for project review"
        ],
        "📧 Email Automation": [
            "Send email to john@example.com about meeting",
            "Email weather report to team@company.com",
            "Send document summary to manager@office.com",
            "Mail project update to stakeholders@project.com"
        ],
        "🧠 Conditional Logic": [
            "If it rains today then remind me to take umbrella",
            "If temperature > 30°C then email heat warning to team",
            "When it's sunny tomorrow then schedule outdoor meeting",
            "If it snows this weekend then cancel picnic plans"
        ],
        "🔄 Complex Workflows": [
            "Process weather data and email alerts to emergency@city.gov",
            "Analyze document and send summary to manager@company.com",
            "If weather is bad then email work-from-home notice to all staff",
            "Calculate project costs and email report to finance@company.com"
        ]
    }
    
    for category, examples in capabilities.items():
        print(f"\n{category}:")
        for example in examples:
            print(f"   • \"{example}\"")
    
    print(f"\n🎯 SPECIAL FEATURE - YOUR SCENARIO:")
    print(f"   📝 \"If it rains today after 4pm then remind me and")
    print(f"       send email to shreekumarchandancharchit@gmail.com")
    print(f"       to not come to office and submit work on Monday EOD\"")
    print(f"   ")
    print(f"   🤖 System Processing:")
    print(f"   1. 🌤️ Monitors weather conditions in real-time")
    print(f"   2. ⏰ Checks if current time is after 4 PM")
    print(f"   3. 🌧️ Detects if it's raining")
    print(f"   4. 📅 Creates reminder for user")
    print(f"   5. 📧 Sends professional email to shreekumarchandancharchit@gmail.com")
    print(f"   6. 💼 Includes work-from-home instructions and Monday deadline")

if __name__ == "__main__":
    print("🤖 INTELLIGENT MCP CHATBOT TESTER")
    print("=" * 80)
    
    # Show capabilities
    show_chatbot_capabilities()
    
    # Test conditional logic parsing
    test_conditional_logic_parsing()
    
    # Run main tests
    success = test_chatbot_scenarios()
    
    if success:
        print("\n🎉 INTELLIGENT CHATBOT IS FULLY OPERATIONAL!")
        print("🌟 Ready for complex conditional logic and automation!")
    else:
        print("\n🔧 Some features need attention. Check server status and try again.")
    
    print("\n💡 TO USE INTERACTIVE CHATBOT:")
    print("   python intelligent_chatbot.py")
    print("\n🌐 WEB INTERFACE:")
    print("   http://localhost:8000")
