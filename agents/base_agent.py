#!/usr/bin/env python3
"""
Base MCP Agent - Foundation class for all MCP agents
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class AgentCapability:
    """Represents an agent capability."""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    methods: List[str]
    version: str = "1.0.0"
    can_call_agents: Optional[List[str]] = None

@dataclass
class MCPMessage:
    """MCP message structure for agent communication."""
    id: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    sender: Optional[str] = None
    target: Optional[str] = None

class BaseMCPAgent(ABC):
    """Base class for all MCP agents."""
    
    def __init__(self, agent_id: str, name: str, capabilities: List[AgentCapability]):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.logger = self._setup_logging()
        self.message_handlers: Dict[str, Callable] = {}
        self.agent_registry: Optional[Dict[str, 'BaseMCPAgent']] = None
        
        # Register message handlers
        self._register_handlers()
        
        self.logger.info(f"Initialized agent: {self.agent_id} ({self.name})")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent."""
        logger = logging.getLogger(f"agent.{self.agent_id}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.agent_id} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _register_handlers(self):
        """Register message handlers based on capabilities."""
        for capability in self.capabilities:
            for method in capability.methods:
                handler_name = f"handle_{method}"
                if hasattr(self, handler_name):
                    self.message_handlers[method] = getattr(self, handler_name)
                    self.logger.debug(f"Registered handler: {method} -> {handler_name}")
    
    async def process_message(self, message: MCPMessage) -> Dict[str, Any]:
        """Process incoming MCP message."""
        try:
            self.logger.info(f"Processing message: {message.method}")
            
            if message.method in self.message_handlers:
                handler = self.message_handlers[message.method]
                result = await handler(message)
                
                # Add agent metadata to result
                if isinstance(result, dict):
                    result["processed_by"] = self.agent_id
                    result["processed_at"] = datetime.now().isoformat()
                
                return result
            else:
                return {
                    "status": "error",
                    "message": f"Unknown method: {message.method}",
                    "available_methods": list(self.message_handlers.keys()),
                    "agent": self.agent_id
                }
                
        except Exception as e:
            self.logger.error(f"Error processing message {message.method}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent": self.agent_id
            }
    
    async def call_agent(self, agent_id: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call another agent's method."""
        try:
            if not self.agent_registry:
                raise Exception("Agent registry not available")
            
            if agent_id not in self.agent_registry:
                raise Exception(f"Agent {agent_id} not found in registry")
            
            target_agent = self.agent_registry[agent_id]
            
            # Create message
            message = MCPMessage(
                id=f"{self.agent_id}_{datetime.now().timestamp()}",
                method=method,
                params=params,
                timestamp=datetime.now(),
                sender=self.agent_id,
                target=agent_id
            )
            
            self.logger.info(f"Calling agent {agent_id}.{method}")
            result = await target_agent.process_message(message)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calling agent {agent_id}.{method}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent": self.agent_id
            }
    
    def set_agent_registry(self, registry: Dict[str, 'BaseMCPAgent']):
        """Set the agent registry for inter-agent communication."""
        self.agent_registry = registry
        self.logger.info(f"Agent registry set with {len(registry)} agents")
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """Get agent capabilities as dictionaries."""
        return [
            {
                "name": cap.name,
                "description": cap.description,
                "input_types": cap.input_types,
                "output_types": cap.output_types,
                "methods": cap.methods,
                "can_call_agents": cap.can_call_agents or []
            }
            for cap in self.capabilities
        ]
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "id": self.agent_id,
            "name": self.name,
            "capabilities": self.get_capabilities(),
            "available_methods": list(self.message_handlers.keys()),
            "can_call_agents": [
                agent for cap in self.capabilities 
                for agent in (cap.can_call_agents or [])
            ]
        }
    
    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    # Abstract methods that subclasses should implement
    @abstractmethod
    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main 'process' method - should be implemented by subclasses."""
        pass
    
    def __str__(self) -> str:
        return f"MCPAgent({self.agent_id}: {self.name})"
    
    def __repr__(self) -> str:
        return f"MCPAgent(id='{self.agent_id}', name='{self.name}', capabilities={len(self.capabilities)})"

class SimpleMCPAgent(BaseMCPAgent):
    """Simple MCP agent implementation for basic use cases."""
    
    def __init__(self, agent_id: str, name: str, description: str = ""):
        capabilities = [
            AgentCapability(
                name="basic_processing",
                description=description or f"Basic processing for {name}",
                input_types=["text", "dict"],
                output_types=["text", "dict"],
                methods=["process", "info"]
            )
        ]
        super().__init__(agent_id, name, capabilities)
    
    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle basic processing."""
        return {
            "status": "success",
            "message": f"Processed by {self.name}",
            "params": message.params,
            "agent": self.agent_id
        }
    
    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request."""
        return {
            "status": "success",
            "info": self.get_info(),
            "agent": self.agent_id
        }

# Utility functions
def create_simple_agent(agent_id: str, name: str, description: str = "") -> SimpleMCPAgent:
    """Create a simple MCP agent."""
    return SimpleMCPAgent(agent_id, name, description)

def create_message(method: str, params: Dict[str, Any], sender: str = None) -> MCPMessage:
    """Create an MCP message."""
    return MCPMessage(
        id=f"msg_{datetime.now().timestamp()}",
        method=method,
        params=params,
        timestamp=datetime.now(),
        sender=sender
    )

if __name__ == "__main__":
    # Test the base agent
    print("🤖 Testing Base MCP Agent")
    print("=" * 40)
    
    # Create a simple agent
    agent = create_simple_agent("test_agent", "Test Agent", "A simple test agent")
    print(f"Created agent: {agent}")
    print(f"Capabilities: {agent.get_capabilities()}")
    print(f"Methods: {list(agent.message_handlers.keys())}")
    
    # Test message processing
    async def test_agent():
        message = create_message("process", {"test": "data"}, "test_sender")
        result = await agent.process_message(message)
        print(f"Process result: {result}")
        
        info_message = create_message("info", {}, "test_sender")
        info_result = await agent.process_message(info_message)
        print(f"Info result: {info_result}")
    
    asyncio.run(test_agent())
    
    print("\n✅ Base MCP Agent working correctly!")
    print("🎯 Ready for agent development!")
