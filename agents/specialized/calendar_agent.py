#!/usr/bin/env python3
"""
Calendar Agent - Google Calendar Integration and Reminder Management
Handles calendar events, reminders, and scheduling
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

class CalendarAgent(BaseMCPAgent):
    """Calendar agent for managing events and reminders."""
    
    def __init__(self):
        capabilities = [
            AgentCapability(
                name="calendar_management",
                description="Manage calendar events and reminders",
                input_types=["dict", "text"],
                output_types=["dict"],
                methods=["create_reminder", "schedule_event", "check_events", "process", "info"]
            )
        ]
        
        super().__init__("calendar_agent", "Calendar Agent", capabilities)
        
        # In-memory storage for reminders (in production, use database)
        self.reminders = []
        self.events = []
        
        # Calendar configuration
        self.timezone = os.getenv('TIMEZONE', 'UTC')
        
        self.logger.info("Calendar Agent initialized")
    
    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main process method."""
        try:
            params = message.params
            action = params.get("action", "")
            
            if action == "create_reminder":
                return await self.handle_create_reminder(message)
            elif action == "schedule_event":
                return await self.handle_schedule_event(message)
            elif action == "check_events":
                return await self.handle_check_events(message)
            else:
                # Parse natural language request
                query = params.get("query", "") or params.get("text", "")
                return await self.parse_calendar_request(query)
                
        except Exception as e:
            self.logger.error(f"Error in process: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent": self.agent_id
            }
    
    async def parse_calendar_request(self, query: str) -> Dict[str, Any]:
        """Parse natural language calendar requests."""
        try:
            query_lower = query.lower()
            
            # Check for reminder keywords
            if any(word in query_lower for word in ["remind", "reminder", "alert", "notify"]):
                return await self.create_reminder_from_text(query)
            
            # Check for event keywords
            elif any(word in query_lower for word in ["schedule", "meeting", "appointment", "event"]):
                return await self.create_event_from_text(query)
            
            # Check for query keywords
            elif any(word in query_lower for word in ["check", "show", "list", "what", "when"]):
                return await self.list_events_and_reminders()
            
            else:
                return {
                    "status": "error",
                    "message": "Could not understand calendar request",
                    "examples": [
                        "Remind me to call John at 3 PM",
                        "Schedule meeting with team tomorrow at 10 AM",
                        "Check my events for today"
                    ],
                    "agent": self.agent_id
                }
                
        except Exception as e:
            self.logger.error(f"Error parsing calendar request: {e}")
            return {
                "status": "error",
                "message": f"Failed to parse request: {str(e)}",
                "agent": self.agent_id
            }
    
    async def create_reminder_from_text(self, text: str) -> Dict[str, Any]:
        """Create reminder from natural language text."""
        try:
            # Extract time and message from text
            # This is a simplified parser - in production, use NLP libraries
            
            reminder_data = {
                "id": f"reminder_{len(self.reminders) + 1}",
                "text": text,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "type": "reminder"
            }
            
            # Try to extract time information
            if "at" in text.lower():
                # Simple time extraction
                parts = text.lower().split("at")
                if len(parts) > 1:
                    time_part = parts[1].strip()
                    reminder_data["time"] = time_part
            
            # Try to extract date information
            if "today" in text.lower():
                reminder_data["date"] = datetime.now().strftime("%Y-%m-%d")
            elif "tomorrow" in text.lower():
                reminder_data["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            self.reminders.append(reminder_data)
            
            return {
                "status": "success",
                "message": "Reminder created successfully",
                "reminder": reminder_data,
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error creating reminder: {e}")
            return {
                "status": "error",
                "message": f"Failed to create reminder: {str(e)}",
                "agent": self.agent_id
            }
    
    async def create_event_from_text(self, text: str) -> Dict[str, Any]:
        """Create event from natural language text."""
        try:
            event_data = {
                "id": f"event_{len(self.events) + 1}",
                "title": text,
                "created_at": datetime.now().isoformat(),
                "status": "scheduled",
                "type": "event"
            }
            
            # Simple parsing for demo
            if "meeting" in text.lower():
                event_data["category"] = "meeting"
            elif "appointment" in text.lower():
                event_data["category"] = "appointment"
            else:
                event_data["category"] = "general"
            
            self.events.append(event_data)
            
            return {
                "status": "success",
                "message": "Event scheduled successfully",
                "event": event_data,
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error creating event: {e}")
            return {
                "status": "error",
                "message": f"Failed to create event: {str(e)}",
                "agent": self.agent_id
            }
    
    async def list_events_and_reminders(self) -> Dict[str, Any]:
        """List all events and reminders."""
        try:
            return {
                "status": "success",
                "reminders": self.reminders,
                "events": self.events,
                "total_reminders": len(self.reminders),
                "total_events": len(self.events),
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error listing events: {e}")
            return {
                "status": "error",
                "message": f"Failed to list events: {str(e)}",
                "agent": self.agent_id
            }
    
    async def handle_create_reminder(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle create reminder request."""
        try:
            params = message.params
            
            reminder_data = {
                "id": f"reminder_{len(self.reminders) + 1}",
                "title": params.get("title", ""),
                "description": params.get("description", ""),
                "datetime": params.get("datetime", ""),
                "email_notification": params.get("email_notification", False),
                "email_address": params.get("email_address", ""),
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "type": "reminder"
            }
            
            self.reminders.append(reminder_data)
            
            return {
                "status": "success",
                "message": "Reminder created successfully",
                "reminder": reminder_data,
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error creating reminder: {e}")
            return {
                "status": "error",
                "message": f"Failed to create reminder: {str(e)}",
                "agent": self.agent_id
            }
    
    async def handle_schedule_event(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle schedule event request."""
        try:
            params = message.params
            
            event_data = {
                "id": f"event_{len(self.events) + 1}",
                "title": params.get("title", ""),
                "description": params.get("description", ""),
                "start_time": params.get("start_time", ""),
                "end_time": params.get("end_time", ""),
                "attendees": params.get("attendees", []),
                "created_at": datetime.now().isoformat(),
                "status": "scheduled",
                "type": "event"
            }
            
            self.events.append(event_data)
            
            return {
                "status": "success",
                "message": "Event scheduled successfully",
                "event": event_data,
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error scheduling event: {e}")
            return {
                "status": "error",
                "message": f"Failed to schedule event: {str(e)}",
                "agent": self.agent_id
            }
    
    async def handle_check_events(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle check events request."""
        try:
            params = message.params
            date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
            
            # Filter events and reminders for the specified date
            filtered_events = []
            filtered_reminders = []
            
            for event in self.events:
                if date in event.get("start_time", "") or date in event.get("created_at", ""):
                    filtered_events.append(event)
            
            for reminder in self.reminders:
                if date in reminder.get("datetime", "") or date in reminder.get("date", ""):
                    filtered_reminders.append(reminder)
            
            return {
                "status": "success",
                "date": date,
                "events": filtered_events,
                "reminders": filtered_reminders,
                "total_events": len(filtered_events),
                "total_reminders": len(filtered_reminders),
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error checking events: {e}")
            return {
                "status": "error",
                "message": f"Failed to check events: {str(e)}",
                "agent": self.agent_id
            }
    
    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request."""
        return {
            "status": "success",
            "info": self.get_info(),
            "total_reminders": len(self.reminders),
            "total_events": len(self.events),
            "timezone": self.timezone,
            "features": [
                "Create reminders",
                "Schedule events",
                "Natural language parsing",
                "Email notifications",
                "Event management"
            ],
            "agent": self.agent_id
        }

# Agent registration
def get_agent_info():
    """Get agent information for auto-discovery."""
    return {
        "name": "Calendar Agent",
        "description": "Manages calendar events, reminders, and scheduling with natural language support",
        "version": "1.0.0",
        "author": "MCP System",
        "capabilities": ["calendar_management", "reminders", "events", "scheduling"],
        "category": "specialized"
    }

def create_agent():
    """Create and return the agent instance."""
    return CalendarAgent()

if __name__ == "__main__":
    # Test the agent
    import asyncio
    
    async def test_agent():
        print("📅 Testing Calendar Agent")
        print("=" * 40)
        
        agent = CalendarAgent()
        
        # Test reminder creation
        reminder_message = MCPMessage(
            id="test_reminder",
            method="process",
            params={
                "query": "Remind me to call John at 3 PM today"
            },
            timestamp=datetime.now()
        )
        
        result = await agent.process_message(reminder_message)
        print(f"Reminder test: {result['status']}")
        
        # Test event scheduling
        event_message = MCPMessage(
            id="test_event",
            method="process",
            params={
                "query": "Schedule meeting with team tomorrow at 10 AM"
            },
            timestamp=datetime.now()
        )
        
        result = await agent.process_message(event_message)
        print(f"Event test: {result['status']}")
        
        # Test listing
        list_message = MCPMessage(
            id="test_list",
            method="process",
            params={
                "query": "Show my events and reminders"
            },
            timestamp=datetime.now()
        )
        
        result = await agent.process_message(list_message)
        print(f"List test: {result['status']}")
        print(f"Total items: {result.get('total_reminders', 0) + result.get('total_events', 0)}")
        
        print("\n✅ Calendar Agent test completed!")
    
    asyncio.run(test_agent())
