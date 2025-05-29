#!/usr/bin/env python3
"""
Simple Interactive Chatbot Demo
Demonstrates the intelligent chatbot with conditional logic and multi-agent coordination
"""

import requests
import json
from datetime import datetime

class SimpleChatbotDemo:
    """Simple chatbot demo for testing scenarios."""
    
    def __init__(self):
        self.server_url = "http://localhost:8000"
        self.conversation_history = []
    
    def start_demo(self):
        """Start the chatbot demo."""
        print("🤖 INTELLIGENT MCP CHATBOT DEMO")
        print("=" * 60)
        print("💡 I can handle complex scenarios with conditions!")
        print("🔢 Math: 'What is 15% of 200?'")
        print("🌤️ Weather: 'What's the weather in Mumbai?'")
        print("📅 Reminders: 'Remind me to call John at 3 PM'")
        print("🧠 Conditional: 'If it rains then email john@example.com'")
        print("❌ Type 'quit' to exit")
        print("=" * 60)
        
        # Show your specific scenario
        print("\n🎯 YOUR SCENARIO EXAMPLE:")
        print("📝 Try: 'If it rains today after 4pm then remind me and")
        print("      send email to shreekumarchandancharchit@gmail.com")
        print("      to not come to office and submit work on Monday EOD'")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n🎯 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye! Have a great day!")
                    break
                
                if not user_input:
                    continue
                
                # Process the input
                response = self.process_input(user_input)
                self.display_response(response)
                
                # Add to history
                self.conversation_history.append({
                    "user": user_input,
                    "bot": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def process_input(self, user_input):
        """Process user input and get response."""
        try:
            # Check if it's a conditional statement
            if self.is_conditional(user_input):
                return self.handle_conditional(user_input)
            
            # Send to MCP server
            response = requests.post(
                f"{self.server_url}/api/mcp/command",
                json={"command": user_input},
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "message": f"Server error: {response.status_code}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "Cannot connect to MCP server. Is it running?",
                "suggestion": "Run: python start_mcp.py"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def is_conditional(self, text):
        """Check if text contains conditional logic."""
        conditional_words = ['if', 'when', 'whenever']
        action_words = ['then', 'remind', 'email', 'send']
        
        text_lower = text.lower()
        has_condition = any(word in text_lower for word in conditional_words)
        has_action = any(word in text_lower for word in action_words)
        
        return has_condition and has_action
    
    def handle_conditional(self, statement):
        """Handle conditional statements."""
        try:
            # Parse the statement
            condition, action = self.parse_conditional(statement)
            
            if not condition or not action:
                return {
                    "status": "error",
                    "message": "Could not parse conditional statement",
                    "example": "Try: 'If it rains then remind me'"
                }
            
            # Simulate conditional processing
            result = {
                "status": "success",
                "type": "conditional",
                "message": "✅ Conditional statement processed!",
                "condition": condition,
                "action": action,
                "explanation": f"I'll monitor: '{condition}' and execute: '{action}'"
            }
            
            # Check if it's weather-related
            if any(word in condition.lower() for word in ['rain', 'sunny', 'cloudy', 'weather']):
                # Get current weather for demonstration
                weather_response = self.get_weather_for_condition(condition)
                result["weather_check"] = weather_response
                
                # Check if condition might be met
                if weather_response.get("status") == "success":
                    weather_desc = weather_response.get("weather_data", {}).get("description", "").lower()
                    
                    if "rain" in condition.lower() and "rain" in weather_desc:
                        result["condition_status"] = "MET - It's currently raining!"
                        result["action_triggered"] = True
                        
                        # Simulate action execution
                        if "email" in action.lower():
                            result["email_simulation"] = self.simulate_email_action(action)
                    else:
                        result["condition_status"] = "NOT MET - Monitoring continues..."
                        result["action_triggered"] = False
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing conditional: {str(e)}"
            }
    
    def parse_conditional(self, statement):
        """Parse conditional statement into condition and action."""
        statement_lower = statement.lower()
        
        # Find condition (after 'if' and before action words)
        condition = ""
        action = ""
        
        if "if " in statement_lower:
            parts = statement_lower.split("if ", 1)
            if len(parts) > 1:
                rest = parts[1]
                
                # Find where action starts
                action_words = ["then", "remind", "email", "send", "alert"]
                for word in action_words:
                    if word in rest:
                        condition_action = rest.split(word, 1)
                        if len(condition_action) == 2:
                            condition = condition_action[0].strip()
                            action = condition_action[1].strip()
                            break
        
        return condition, action
    
    def get_weather_for_condition(self, condition):
        """Get weather data for condition checking."""
        try:
            # Extract city or use default
            city = "Mumbai"  # Default city
            
            response = requests.post(
                f"{self.server_url}/api/mcp/command",
                json={"command": f"What is the weather in {city}?"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": "Could not get weather"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def simulate_email_action(self, action):
        """Simulate email action execution."""
        # Extract email address
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', action)
        
        if email_match:
            email_address = email_match.group(0)
            
            return {
                "status": "simulated",
                "email_to": email_address,
                "subject": "Weather Alert - Work From Home Notice",
                "content": "Due to current weather conditions (rain detected), please work from home today and submit your work by Monday EOD.",
                "message": f"📧 Email would be sent to {email_address}"
            }
        else:
            return {
                "status": "error",
                "message": "No email address found in action"
            }
    
    def display_response(self, response):
        """Display the chatbot response."""
        print(f"\n🤖 Bot: ", end="")
        
        if response.get("status") == "success":
            response_type = response.get("type", "general")
            
            if response_type == "conditional":
                print("✅ Conditional statement processed!")
                print(f"   📋 Condition: {response.get('condition', 'N/A')}")
                print(f"   🎯 Action: {response.get('action', 'N/A')}")
                print(f"   💡 {response.get('explanation', '')}")
                
                # Show weather check if available
                weather_check = response.get("weather_check", {})
                if weather_check.get("status") == "success":
                    weather_data = weather_check.get("weather_data", {})
                    city = weather_check.get("city", "Unknown")
                    temp = weather_data.get("temperature", "N/A")
                    desc = weather_data.get("description", "N/A")
                    print(f"   🌤️ Current weather in {city}: {temp}°C, {desc}")
                
                # Show condition status
                condition_status = response.get("condition_status")
                if condition_status:
                    print(f"   📊 Condition status: {condition_status}")
                
                # Show email simulation
                email_sim = response.get("email_simulation", {})
                if email_sim.get("status") == "simulated":
                    print(f"   📧 Email simulation: {email_sim.get('message', '')}")
                    print(f"   📝 Subject: {email_sim.get('subject', '')}")
                    print(f"   💌 Content preview: {email_sim.get('content', '')[:100]}...")
            
            else:
                # Handle other response types
                if "weather_data" in response:
                    # Weather response
                    city = response.get("city", "Unknown")
                    weather_data = response.get("weather_data", {})
                    temp = weather_data.get("temperature", "N/A")
                    desc = weather_data.get("description", "N/A")
                    print(f"🌤️ {city}: {temp}°C, {desc}")
                
                elif "result" in response or "formatted_result" in response:
                    # Math response
                    result = response.get("result", response.get("formatted_result", "N/A"))
                    print(f"🔢 {result}")
                
                else:
                    # General response
                    message = response.get("message", response.get("weather_response", "Response received"))
                    print(message)
        
        else:
            # Error response
            print(f"❌ {response.get('message', 'Unknown error')}")
            
            suggestion = response.get("suggestion")
            if suggestion:
                print(f"   💡 {suggestion}")

def main():
    """Main function."""
    print("🚀 Starting Simple Chatbot Demo...")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ MCP Server is running!")
        else:
            print("❌ MCP Server is not responding properly")
            return
    except:
        print("❌ Cannot connect to MCP Server")
        print("💡 Please start the server first: python start_mcp.py")
        return
    
    # Start the demo
    demo = SimpleChatbotDemo()
    demo.start_demo()

if __name__ == "__main__":
    main()
