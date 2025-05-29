#!/usr/bin/env python3
"""
Intelligent MCP Chatbot with Conditional Logic
Handles complex scenarios with weather monitoring, calendar reminders, and email automation
"""

import os
import re
import json
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("intelligent_chatbot")

class IntelligentMCPChatbot:
    """Intelligent chatbot with conditional logic and multi-agent coordination."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        self.mcp_server_url = mcp_server_url.rstrip('/')
        self.conversation_history = []
        self.active_conditions = []  # Store active conditional statements
        self.user_preferences = {}
        
        # Conditional logic patterns
        self.condition_patterns = {
            'weather_condition': r'if\s+it\s+(rains?|snows?|is\s+sunny|is\s+cloudy|is\s+hot|is\s+cold)',
            'time_condition': r'if\s+.*?(after|before|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            'temperature_condition': r'if\s+.*?temperature.*?(above|below|over|under)\s+(\d+)',
            'date_condition': r'if\s+.*?(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
        }
        
        # Action patterns
        self.action_patterns = {
            'reminder': r'remind\s+me|set\s+reminder|alert\s+me',
            'email': r'send\s+email|email\s+to|mail\s+to',
            'calculation': r'calculate|compute|what\s+is|solve',
            'weather_query': r'weather|temperature|forecast'
        }
        
        logger.info("Intelligent MCP Chatbot initialized")
    
    async def start_interactive_session(self):
        """Start interactive chatbot session."""
        print("🤖 INTELLIGENT MCP CHATBOT")
        print("=" * 60)
        print("💡 I can handle complex scenarios with conditions!")
        print("📝 Example: 'If it rains today after 4pm then remind me and email john@example.com'")
        print("🔢 I can also do math: 'What is 15% of 200?'")
        print("🌤️ Weather queries: 'What's the weather in Mumbai?'")
        print("📅 Reminders: 'Remind me to call John at 3 PM'")
        print("❌ Type 'quit' to exit")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n🎯 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye! Have a great day!")
                    break
                
                if not user_input:
                    continue
                
                # Process user input
                response = await self.process_user_input(user_input)
                
                # Display response
                self.display_response(response)
                
                # Add to conversation history
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "user_input": user_input,
                    "bot_response": response
                })
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input and determine appropriate response."""
        try:
            # Check if it's a conditional statement
            if self.is_conditional_statement(user_input):
                return await self.handle_conditional_statement(user_input)
            
            # Check for mathematical expressions
            elif self.is_math_query(user_input):
                return await self.handle_math_query(user_input)
            
            # Check for weather queries
            elif self.is_weather_query(user_input):
                return await self.handle_weather_query(user_input)
            
            # Check for calendar/reminder requests
            elif self.is_calendar_query(user_input):
                return await self.handle_calendar_query(user_input)
            
            # Check for email requests
            elif self.is_email_query(user_input):
                return await self.handle_email_query(user_input)
            
            # General conversation
            else:
                return await self.handle_general_query(user_input)
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return {
                "type": "error",
                "message": f"Sorry, I encountered an error: {str(e)}",
                "suggestions": [
                    "Try rephrasing your request",
                    "Check if the MCP server is running",
                    "Use simpler language"
                ]
            }
    
    def is_conditional_statement(self, text: str) -> bool:
        """Check if the text contains conditional logic."""
        text_lower = text.lower()
        conditional_keywords = ['if', 'when', 'whenever', 'in case', 'should']
        action_keywords = ['then', 'remind', 'email', 'send', 'alert', 'notify']
        
        has_condition = any(keyword in text_lower for keyword in conditional_keywords)
        has_action = any(keyword in text_lower for keyword in action_keywords)
        
        return has_condition and has_action
    
    def is_math_query(self, text: str) -> bool:
        """Check if the text is a mathematical query."""
        math_indicators = [
            'calculate', 'compute', 'what is', 'solve', 'math',
            '+', '-', '*', '/', '%', 'percent', 'area', 'volume'
        ]
        return any(indicator in text.lower() for indicator in math_indicators)
    
    def is_weather_query(self, text: str) -> bool:
        """Check if the text is a weather query."""
        weather_indicators = ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy']
        return any(indicator in text.lower() for indicator in weather_indicators)
    
    def is_calendar_query(self, text: str) -> bool:
        """Check if the text is a calendar/reminder query."""
        calendar_indicators = ['remind', 'reminder', 'schedule', 'meeting', 'appointment', 'calendar']
        return any(indicator in text.lower() for indicator in calendar_indicators)
    
    def is_email_query(self, text: str) -> bool:
        """Check if the text is an email query."""
        email_indicators = ['email', 'send', 'mail to', '@']
        return any(indicator in text.lower() for indicator in email_indicators)
    
    async def handle_conditional_statement(self, statement: str) -> Dict[str, Any]:
        """Handle conditional statements like 'If it rains then remind me'."""
        try:
            # Parse the conditional statement
            condition_part, action_part = self.parse_conditional_statement(statement)
            
            if not condition_part or not action_part:
                return {
                    "type": "error",
                    "message": "Could not parse the conditional statement",
                    "example": "Try: 'If it rains today after 4pm then remind me and email john@example.com'",
                    "parsed": {
                        "condition": condition_part,
                        "action": action_part
                    }
                }
            
            # Create conditional logic entry
            conditional_entry = {
                "id": f"condition_{len(self.active_conditions) + 1}",
                "original_statement": statement,
                "condition": condition_part,
                "action": action_part,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "triggered": False
            }
            
            # Add to active conditions
            self.active_conditions.append(conditional_entry)
            
            # If it's a weather condition, check current weather
            if 'weather' in condition_part.lower() or any(word in condition_part.lower() for word in ['rain', 'sunny', 'cloudy']):
                weather_check = await self.check_weather_condition(condition_part, action_part)
                conditional_entry.update(weather_check)
            
            return {
                "type": "conditional_logic",
                "message": "✅ Conditional statement created successfully!",
                "conditional": conditional_entry,
                "explanation": f"I'll monitor: '{condition_part}' and execute: '{action_part}'",
                "active_conditions": len(self.active_conditions)
            }
            
        except Exception as e:
            logger.error(f"Error handling conditional statement: {e}")
            return {
                "type": "error",
                "message": f"Failed to process conditional statement: {str(e)}"
            }
    
    def parse_conditional_statement(self, statement: str) -> tuple:
        """Parse conditional statement into condition and action parts."""
        try:
            statement_lower = statement.lower()
            
            # Find condition part (after 'if' and before 'then')
            if_match = re.search(r'if\s+(.*?)(?:\s+then|\s+do|\s+remind|\s+email|\s+send)', statement_lower)
            condition_part = if_match.group(1).strip() if if_match else ""
            
            # Find action part (after 'then', 'remind', 'email', etc.)
            action_keywords = ['then', 'remind', 'email', 'send', 'alert', 'notify']
            action_part = ""
            
            for keyword in action_keywords:
                if keyword in statement_lower:
                    parts = statement_lower.split(keyword, 1)
                    if len(parts) > 1:
                        action_part = parts[1].strip()
                        break
            
            return condition_part, action_part
            
        except Exception as e:
            logger.error(f"Error parsing conditional statement: {e}")
            return "", ""
    
    async def check_weather_condition(self, condition: str, action: str) -> Dict[str, Any]:
        """Check weather condition and execute action if met."""
        try:
            # Extract location from condition or use default
            location = self.extract_location_from_text(condition) or "Mumbai"
            
            # Get current weather
            weather_response = await self.call_mcp_server("/api/mcp/command", {
                "command": f"What is the weather in {location}?"
            })
            
            if weather_response.get("status") == "success":
                weather_data = weather_response.get("weather_data", {})
                current_conditions = weather_data.get("description", "").lower()
                
                # Check if condition is met
                condition_met = False
                
                if "rain" in condition.lower() and "rain" in current_conditions:
                    condition_met = True
                elif "sunny" in condition.lower() and "clear" in current_conditions:
                    condition_met = True
                elif "cloudy" in condition.lower() and "cloud" in current_conditions:
                    condition_met = True
                
                # Check time condition
                time_condition_met = self.check_time_condition(condition)
                
                if condition_met and time_condition_met:
                    # Execute action
                    action_result = await self.execute_conditional_action(action)
                    
                    return {
                        "condition_met": True,
                        "weather_checked": True,
                        "current_weather": current_conditions,
                        "location": location,
                        "action_executed": True,
                        "action_result": action_result,
                        "triggered_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "condition_met": False,
                        "weather_checked": True,
                        "current_weather": current_conditions,
                        "location": location,
                        "reason": "Weather or time condition not met"
                    }
            else:
                return {
                    "condition_met": False,
                    "weather_checked": False,
                    "error": "Could not check weather"
                }
                
        except Exception as e:
            logger.error(f"Error checking weather condition: {e}")
            return {
                "condition_met": False,
                "error": str(e)
            }
    
    def check_time_condition(self, condition: str) -> bool:
        """Check if time condition is met."""
        try:
            current_time = datetime.now()
            
            # Extract time from condition
            time_match = re.search(r'after\s+(\d{1,2})(?::(\d{2}))?\s*(pm|am)?', condition.lower())
            
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3)
                
                # Convert to 24-hour format
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                
                condition_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if "after" in condition.lower():
                    return current_time > condition_time
                elif "before" in condition.lower():
                    return current_time < condition_time
                else:
                    return True  # No specific time condition
            
            return True  # No time condition found
            
        except Exception as e:
            logger.error(f"Error checking time condition: {e}")
            return True
    
    def extract_location_from_text(self, text: str) -> Optional[str]:
        """Extract location from text."""
        # Simple location extraction - in production, use NLP
        common_cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 'pune', 'hyderabad']
        
        text_lower = text.lower()
        for city in common_cities:
            if city in text_lower:
                return city.title()
        
        return None
    
    async def execute_conditional_action(self, action: str) -> Dict[str, Any]:
        """Execute the action part of conditional statement."""
        try:
            results = []
            
            # Check for reminder action
            if "remind" in action.lower():
                reminder_result = await self.create_reminder_from_action(action)
                results.append({"type": "reminder", "result": reminder_result})
            
            # Check for email action
            if "email" in action.lower() or "@" in action:
                email_result = await self.send_email_from_action(action)
                results.append({"type": "email", "result": email_result})
            
            return {
                "status": "success",
                "actions_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error executing conditional action: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def create_reminder_from_action(self, action: str) -> Dict[str, Any]:
        """Create reminder from action text."""
        try:
            # Use calendar agent to create reminder
            response = await self.call_mcp_server("/api/mcp/command", {
                "command": f"Remind me: {action}"
            })
            
            return response
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def send_email_from_action(self, action: str) -> Dict[str, Any]:
        """Send email from action text."""
        try:
            # Extract email address
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', action)
            
            if email_match:
                email_address = email_match.group(0)
                
                # Create email content
                email_content = f"Weather Alert: Conditional statement triggered.\n\nAction: {action}\n\nTriggered at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Use workflow engine to send email
                response = await self.call_mcp_server("/api/mcp/workflow", {
                    "documents": [
                        {
                            "filename": "weather_alert.txt",
                            "content": email_content,
                            "type": "text"
                        }
                    ],
                    "query": f"Send this weather alert to {email_address}",
                    "rag_mode": True
                })
                
                return response
            else:
                return {"status": "error", "message": "No email address found in action"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def handle_math_query(self, query: str) -> Dict[str, Any]:
        """Handle mathematical queries."""
        try:
            response = await self.call_mcp_server("/api/mcp/command", {
                "command": query
            })
            
            return {
                "type": "math",
                "query": query,
                "response": response
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def handle_weather_query(self, query: str) -> Dict[str, Any]:
        """Handle weather queries."""
        try:
            response = await self.call_mcp_server("/api/mcp/command", {
                "command": query
            })
            
            return {
                "type": "weather",
                "query": query,
                "response": response
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def handle_calendar_query(self, query: str) -> Dict[str, Any]:
        """Handle calendar/reminder queries."""
        try:
            response = await self.call_mcp_server("/api/mcp/command", {
                "command": query
            })
            
            return {
                "type": "calendar",
                "query": query,
                "response": response
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def handle_email_query(self, query: str) -> Dict[str, Any]:
        """Handle email queries."""
        try:
            response = await self.call_mcp_server("/api/mcp/workflow", {
                "documents": [],
                "query": query,
                "rag_mode": True
            })
            
            return {
                "type": "email",
                "query": query,
                "response": response
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries."""
        try:
            response = await self.call_mcp_server("/api/mcp/command", {
                "command": query
            })
            
            return {
                "type": "general",
                "query": query,
                "response": response
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def call_mcp_server(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP server endpoint."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_server_url}{endpoint}",
                    json=data,
                    timeout=30
                ) as response:
                    return await response.json()
                    
        except ImportError:
            # Fallback to requests (synchronous)
            response = requests.post(
                f"{self.mcp_server_url}{endpoint}",
                json=data,
                timeout=30
            )
            return response.json()
            
        except Exception as e:
            logger.error(f"Error calling MCP server: {e}")
            return {"status": "error", "message": str(e)}
    
    def display_response(self, response: Dict[str, Any]):
        """Display chatbot response."""
        response_type = response.get("type", "unknown")
        
        print(f"\n🤖 Bot: ", end="")
        
        if response_type == "conditional_logic":
            print("✅ Conditional statement processed!")
            print(f"   📋 Condition: {response['conditional']['condition']}")
            print(f"   🎯 Action: {response['conditional']['action']}")
            print(f"   📊 Active conditions: {response['active_conditions']}")
            
            if response['conditional'].get('condition_met'):
                print(f"   🎉 Condition was met and action executed!")
            else:
                print(f"   ⏳ Monitoring condition...")
        
        elif response_type == "math":
            math_response = response.get("response", {})
            if math_response.get("status") == "success":
                result = math_response.get("result", math_response.get("formatted_result", "N/A"))
                print(f"🔢 {result}")
                if "explanation" in math_response:
                    print(f"   📝 {math_response['explanation']}")
            else:
                print(f"❌ {math_response.get('message', 'Math calculation failed')}")
        
        elif response_type == "weather":
            weather_response = response.get("response", {})
            if weather_response.get("status") == "success":
                city = weather_response.get("city", "Unknown")
                weather_data = weather_response.get("weather_data", {})
                temp = weather_data.get("temperature", "N/A")
                desc = weather_data.get("description", "N/A")
                print(f"🌤️ {city}: {temp}°C, {desc}")
            else:
                print(f"❌ {weather_response.get('message', 'Weather query failed')}")
        
        elif response_type == "error":
            print(f"❌ {response.get('message', 'Unknown error')}")
            suggestions = response.get("suggestions", [])
            if suggestions:
                print("   💡 Suggestions:")
                for suggestion in suggestions:
                    print(f"      • {suggestion}")
        
        else:
            # General response
            general_response = response.get("response", {})
            if isinstance(general_response, dict):
                message = general_response.get("message", general_response.get("weather_response", "Response received"))
                print(message)
            else:
                print(str(general_response))

async def main():
    """Main function to start the chatbot."""
    chatbot = IntelligentMCPChatbot()
    await chatbot.start_interactive_session()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting chatbot: {e}")
        print("💡 Make sure the MCP server is running: python start_mcp.py")
