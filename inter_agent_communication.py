#!/usr/bin/env python3
"""
Inter-Agent Communication System
Establishes unified communication network between all agents with MongoDB integration
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import importlib.util
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

# MongoDB integration
try:
    from mcp_mongodb_integration import MCPMongoDBIntegration
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

class AgentStatus(Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    COMMUNICATING = "communicating"

class MessageType(Enum):
    """Message type enumeration."""
    QUERY = "query"
    RESPONSE = "response"
    REQUEST = "request"
    NOTIFICATION = "notification"
    COLLABORATION = "collaboration"

@dataclass
class InterAgentMessage:
    """Inter-agent message structure."""
    id: str
    sender: str
    receiver: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime
    conversation_id: str
    requires_response: bool = False
    metadata: Dict[str, Any] = None

class AgentCommunicationHub:
    """Central hub for inter-agent communication."""
    
    def __init__(self):
        self.agents = {}
        self.agent_status = {}
        self.message_queue = asyncio.Queue()
        self.conversation_history = {}
        self.mongodb_integration = None
        self.logger = self._setup_logging()
        
        # Define agent capabilities and communication patterns
        self.agent_configs = {
            "math_agent": {
                "path": "agents/specialized/math_agent.py",
                "class_name": "MathAgent",
                "status": AgentStatus.ACTIVE,
                "capabilities": ["calculate", "analyze", "compute", "percentage"],
                "can_communicate_with": ["weather_agent", "document_agent"],
                "data_sharing": ["calculations", "statistics", "analysis"]
            },
            "weather_agent": {
                "path": "agents/data/realtime_weather_agent.py", 
                "class_name": "RealTimeWeatherAgent",
                "status": AgentStatus.ACTIVE,
                "capabilities": ["weather", "forecast", "temperature", "climate"],
                "can_communicate_with": ["math_agent", "document_agent"],
                "data_sharing": ["weather_data", "forecasts", "climate_info"]
            },
            "document_agent": {
                "path": "agents/core/document_processor.py",
                "class_name": "DocumentProcessorAgent", 
                "status": AgentStatus.ACTIVE,
                "capabilities": ["analyze", "process", "extract", "summarize"],
                "can_communicate_with": ["math_agent", "weather_agent"],
                "data_sharing": ["text_analysis", "summaries", "extracted_data"]
            },
            "gmail_agent": {
                "path": "agents/communication/real_gmail_agent.py",
                "class_name": "RealGmailAgent",
                "status": AgentStatus.INACTIVE,  # Currently down
                "capabilities": ["email", "send", "notify"],
                "can_communicate_with": [],  # No communication while down
                "data_sharing": []
            },
            "calendar_agent": {
                "path": "agents/specialized/calendar_agent.py",
                "class_name": "CalendarAgent", 
                "status": AgentStatus.INACTIVE,  # Currently down
                "capabilities": ["schedule", "remind", "calendar"],
                "can_communicate_with": [],  # No communication while down
                "data_sharing": []
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for communication hub."""
        logger = logging.getLogger("inter_agent_communication")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def initialize_system(self) -> bool:
        """Initialize the inter-agent communication system."""
        self.logger.info("🔗 Initializing Inter-Agent Communication System")
        
        # Initialize MongoDB
        if MONGODB_AVAILABLE:
            try:
                self.mongodb_integration = MCPMongoDBIntegration()
                connected = await self.mongodb_integration.connect()
                if connected:
                    self.logger.info("✅ MongoDB connected for inter-agent communication")
                else:
                    self.logger.warning("⚠️ MongoDB connection failed")
            except Exception as e:
                self.logger.error(f"❌ MongoDB initialization error: {e}")
        
        # Load active agents
        active_agents = 0
        for agent_id, config in self.agent_configs.items():
            if config["status"] == AgentStatus.ACTIVE:
                agent = await self._load_agent(agent_id, config)
                if agent:
                    self.agents[agent_id] = agent
                    self.agent_status[agent_id] = AgentStatus.ACTIVE
                    active_agents += 1
                    self.logger.info(f"✅ Loaded active agent: {agent_id}")
                else:
                    self.agent_status[agent_id] = AgentStatus.ERROR
                    self.logger.error(f"❌ Failed to load agent: {agent_id}")
            else:
                self.agent_status[agent_id] = config["status"]
                self.logger.info(f"⚠️ Agent {agent_id} marked as {config['status'].value}")
        
        # Start message processing
        asyncio.create_task(self._process_messages())
        
        self.logger.info(f"🎉 Inter-agent system initialized with {active_agents} active agents")
        return active_agents > 0
    
    async def _load_agent(self, agent_id: str, config: Dict) -> Optional[Any]:
        """Load individual agent with communication capabilities."""
        try:
            agent_path = Path(config["path"])
            if not agent_path.exists():
                return None
            
            spec = importlib.util.spec_from_file_location(agent_id, agent_path)
            if spec is None or spec.loader is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[agent_id] = module
            spec.loader.exec_module(module)
            
            agent_class = getattr(module, config["class_name"], None)
            if agent_class is None:
                return None
            
            # Create agent instance with communication hub reference
            agent = agent_class()
            
            # Inject communication capabilities
            agent.communication_hub = self
            agent.can_communicate_with = set(config["can_communicate_with"])
            agent.data_sharing_capabilities = config["data_sharing"]
            
            return agent
            
        except Exception as e:
            self.logger.error(f"Error loading agent {agent_id}: {e}")
            return None
    
    async def send_message(self, sender: str, receiver: str, message_type: MessageType, 
                          content: Dict[str, Any], conversation_id: str = None) -> str:
        """Send message between agents."""
        if conversation_id is None:
            conversation_id = f"conv_{datetime.now().timestamp()}"
        
        message = InterAgentMessage(
            id=f"msg_{datetime.now().timestamp()}",
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            conversation_id=conversation_id,
            requires_response=message_type in [MessageType.QUERY, MessageType.REQUEST],
            metadata={"routing": "direct"}
        )
        
        await self.message_queue.put(message)
        
        # Store in MongoDB
        if self.mongodb_integration:
            await self._store_inter_agent_message(message)
        
        self.logger.info(f"📤 Message sent: {sender} → {receiver} ({message_type.value})")
        return message.id
    
    async def _process_messages(self):
        """Process inter-agent messages."""
        while True:
            try:
                message = await self.message_queue.get()
                await self._route_message(message)
                self.message_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def _route_message(self, message: InterAgentMessage):
        """Route message to appropriate agent."""
        receiver_agent = self.agents.get(message.receiver)
        
        if not receiver_agent:
            self.logger.warning(f"⚠️ Receiver agent {message.receiver} not available")
            return
        
        if self.agent_status.get(message.receiver) != AgentStatus.ACTIVE:
            self.logger.warning(f"⚠️ Receiver agent {message.receiver} not active")
            return
        
        try:
            # Update agent status
            self.agent_status[message.receiver] = AgentStatus.COMMUNICATING
            
            # Process message with receiver agent
            response = await self._process_agent_message(receiver_agent, message)
            
            # Send response back if required
            if message.requires_response and response:
                await self.send_message(
                    message.receiver,
                    message.sender, 
                    MessageType.RESPONSE,
                    response,
                    message.conversation_id
                )
            
            # Update agent status back to active
            self.agent_status[message.receiver] = AgentStatus.ACTIVE
            
        except Exception as e:
            self.logger.error(f"Error routing message: {e}")
            self.agent_status[message.receiver] = AgentStatus.ACTIVE
    
    async def _process_agent_message(self, agent: Any, message: InterAgentMessage) -> Dict[str, Any]:
        """Process message with specific agent."""
        try:
            # Create agent message format
            from agents.base_agent import MCPMessage
            
            agent_message = MCPMessage(
                id=message.id,
                method="process",
                params={
                    "query": message.content.get("query", ""),
                    "data": message.content.get("data", {}),
                    "context": message.content.get("context", {}),
                    "inter_agent_request": True,
                    "sender_agent": message.sender
                },
                timestamp=message.timestamp
            )
            
            # Process with agent
            result = await agent.process_message(agent_message)
            
            self.logger.info(f"✅ Agent {agent.agent_id} processed inter-agent message")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing agent message: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _store_inter_agent_message(self, message: InterAgentMessage):
        """Store inter-agent message in MongoDB."""
        if not self.mongodb_integration:
            return
        
        try:
            # Store in inter_agent_communications collection
            if not hasattr(self.mongodb_integration, 'db') or not self.mongodb_integration.db:
                return
            
            collection = self.mongodb_integration.db['inter_agent_communications']
            
            document = {
                "message_id": message.id,
                "sender": message.sender,
                "receiver": message.receiver,
                "message_type": message.message_type.value,
                "content": message.content,
                "timestamp": message.timestamp,
                "conversation_id": message.conversation_id,
                "requires_response": message.requires_response,
                "metadata": message.metadata or {}
            }
            
            collection.insert_one(document)
            self.logger.info(f"💾 Stored inter-agent message in MongoDB")
            
        except Exception as e:
            self.logger.error(f"Error storing inter-agent message: {e}")
    
    async def coordinate_multi_agent_task(self, task_description: str, primary_agent: str = None) -> Dict[str, Any]:
        """Coordinate complex task across multiple agents."""
        self.logger.info(f"🎯 Coordinating multi-agent task: {task_description}")
        
        conversation_id = f"multi_task_{datetime.now().timestamp()}"
        
        # Analyze task to determine required agents
        required_agents = self._analyze_task_requirements(task_description)
        
        # Filter only active agents
        active_required_agents = [
            agent for agent in required_agents 
            if self.agent_status.get(agent) == AgentStatus.ACTIVE
        ]
        
        if not active_required_agents:
            return {
                "status": "error",
                "message": "No active agents available for this task",
                "task": task_description
            }
        
        # Execute coordinated workflow
        results = {}
        
        for agent_id in active_required_agents:
            try:
                # Send task to agent
                message_id = await self.send_message(
                    "coordination_hub",
                    agent_id,
                    MessageType.COLLABORATION,
                    {
                        "query": task_description,
                        "context": {"multi_agent_task": True, "other_agents": active_required_agents},
                        "data": results  # Share previous results
                    },
                    conversation_id
                )
                
                # Wait for processing (simplified - in real implementation would be more sophisticated)
                await asyncio.sleep(1)
                
                # Get result from agent
                agent = self.agents.get(agent_id)
                if agent:
                    from agents.base_agent import MCPMessage
                    
                    agent_message = MCPMessage(
                        id=f"coord_{datetime.now().timestamp()}",
                        method="process",
                        params={"query": task_description, "context": {"coordination": True}},
                        timestamp=datetime.now()
                    )
                    
                    result = await agent.process_message(agent_message)
                    results[agent_id] = result
                
            except Exception as e:
                self.logger.error(f"Error coordinating with {agent_id}: {e}")
                results[agent_id] = {"status": "error", "message": str(e)}
        
        # Compile final response
        final_result = {
            "status": "success",
            "task": task_description,
            "conversation_id": conversation_id,
            "participating_agents": active_required_agents,
            "inactive_agents": [agent for agent in required_agents if agent not in active_required_agents],
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store coordination result
        if self.mongodb_integration:
            await self._store_coordination_result(final_result)
        
        return final_result
    
    def _analyze_task_requirements(self, task: str) -> List[str]:
        """Analyze task to determine which agents are needed."""
        task_lower = task.lower()
        required_agents = []
        
        # Check for math-related keywords
        if any(keyword in task_lower for keyword in ["calculate", "compute", "math", "percentage", "cost", "analysis"]):
            required_agents.append("math_agent")
        
        # Check for weather-related keywords  
        if any(keyword in task_lower for keyword in ["weather", "temperature", "forecast", "climate", "heating", "mumbai"]):
            required_agents.append("weather_agent")
        
        # Check for document-related keywords
        if any(keyword in task_lower for keyword in ["document", "text", "analyze", "process", "extract"]):
            required_agents.append("document_agent")
        
        # Check for email-related keywords (but agent is down)
        if any(keyword in task_lower for keyword in ["email", "send", "notify", "mail"]):
            required_agents.append("gmail_agent")  # Will be filtered out as inactive
        
        # Check for calendar-related keywords (but agent is down)
        if any(keyword in task_lower for keyword in ["calendar", "schedule", "remind", "appointment"]):
            required_agents.append("calendar_agent")  # Will be filtered out as inactive
        
        return required_agents
    
    async def _store_coordination_result(self, result: Dict[str, Any]):
        """Store coordination result in MongoDB."""
        if not self.mongodb_integration or not self.mongodb_integration.db:
            return
        
        try:
            collection = self.mongodb_integration.db['multi_agent_coordinations']
            collection.insert_one(result)
            self.logger.info("💾 Stored coordination result in MongoDB")
        except Exception as e:
            self.logger.error(f"Error storing coordination result: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "system": "inter_agent_communication",
            "timestamp": datetime.now().isoformat(),
            "mongodb_connected": self.mongodb_integration is not None,
            "total_agents": len(self.agent_configs),
            "active_agents": len([a for a in self.agent_status.values() if a == AgentStatus.ACTIVE]),
            "inactive_agents": len([a for a in self.agent_status.values() if a == AgentStatus.INACTIVE]),
            "agent_status": {k: v.value for k, v in self.agent_status.items()},
            "communication_capabilities": {
                agent_id: config["can_communicate_with"] 
                for agent_id, config in self.agent_configs.items()
                if config["status"] == AgentStatus.ACTIVE
            }
        }

# Global communication hub instance
communication_hub = None

async def initialize_inter_agent_system() -> AgentCommunicationHub:
    """Initialize the inter-agent communication system."""
    global communication_hub
    
    if communication_hub is None:
        communication_hub = AgentCommunicationHub()
        await communication_hub.initialize_system()
    
    return communication_hub

async def test_inter_agent_communication():
    """Test inter-agent communication capabilities."""
    print("🧪 TESTING INTER-AGENT COMMUNICATION")
    print("=" * 60)
    
    # Initialize system
    hub = await initialize_inter_agent_system()
    
    # Test system status
    status = hub.get_system_status()
    print(f"📊 System Status:")
    print(f"   Active Agents: {status['active_agents']}")
    print(f"   Inactive Agents: {status['inactive_agents']}")
    print(f"   MongoDB Connected: {status['mongodb_connected']}")
    
    # Test multi-agent coordination
    test_tasks = [
        "Calculate the cost of heating based on Mumbai weather",
        "Analyze weather data and provide mathematical insights",
        "Process weather forecast document and calculate trends"
    ]
    
    for task in test_tasks:
        print(f"\n🎯 Testing Task: {task}")
        result = await hub.coordinate_multi_agent_task(task)
        
        print(f"   Status: {result['status']}")
        print(f"   Participating Agents: {result.get('participating_agents', [])}")
        print(f"   Inactive Agents: {result.get('inactive_agents', [])}")
        
        if result['status'] == 'success':
            for agent_id, agent_result in result['results'].items():
                agent_status = agent_result.get('status', 'unknown')
                print(f"   {agent_id}: {agent_status}")

if __name__ == "__main__":
    asyncio.run(test_inter_agent_communication())
