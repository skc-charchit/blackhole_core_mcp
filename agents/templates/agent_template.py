#!/usr/bin/env python3
"""
Agent Template - Production Ready
Template for creating new MCP agents with full compliance and auto-discovery
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

# MongoDB integration (optional)
try:
    from mcp_mongodb_integration import MCPMongoDBIntegration
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Agent metadata for auto-discovery (REQUIRED)
AGENT_METADATA = {
    "id": "template_agent",  # CHANGE THIS: Unique agent identifier
    "name": "Template Agent",  # CHANGE THIS: Human-readable agent name
    "version": "1.0.0",  # CHANGE THIS: Agent version
    "author": "Your Name",  # CHANGE THIS: Agent author
    "description": "Template agent for creating new MCP agents",  # CHANGE THIS: Agent description
    "category": "template",  # CHANGE THIS: Agent category (computation, data, communication, processing, etc.)
    "status": "template",  # CHANGE THIS: live, inactive, future, or template
    "dependencies": [],  # CHANGE THIS: List of required Python packages
    "auto_load": False,  # CHANGE THIS: Whether to auto-load this agent
    "priority": 5,  # CHANGE THIS: Loading priority (1=highest, 10=lowest)
    "health_check_interval": 60,  # CHANGE THIS: Health check interval in seconds
    "max_failures": 3,  # CHANGE THIS: Maximum failures before marking unhealthy
    "recovery_timeout": 120  # CHANGE THIS: Recovery timeout in seconds
}

class TemplateAgent(BaseMCPAgent):
    """Template Agent - Copy and modify this class for new agents."""

    def __init__(self):
        # CHANGE THIS: Define your agent's capabilities
        capabilities = [
            AgentCapability(
                name="template_capability",  # CHANGE THIS: Capability name
                description="Template capability for demonstration",  # CHANGE THIS: Capability description
                input_types=["text", "dict"],  # CHANGE THIS: Supported input types
                output_types=["dict"],  # CHANGE THIS: Supported output types
                methods=["process", "info"],  # CHANGE THIS: Supported methods
                version="1.0.0"  # CHANGE THIS: Capability version
            )
        ]

        # CHANGE THIS: Agent ID and name
        super().__init__("template_agent", "Template Agent", capabilities)
        
        # Production configuration
        self.failure_count = 0
        self.last_health_check = datetime.now()
        
        # CHANGE THIS: Add your agent-specific configuration
        self.max_input_length = 1000
        self.processing_timeout = 30
        
        # Initialize MongoDB integration (optional)
        self.mongodb_integration = None
        if MONGODB_AVAILABLE:
            try:
                self.mongodb_integration = MCPMongoDBIntegration()
                asyncio.create_task(self._init_mongodb())
            except Exception as e:
                self.logger.error(f"Failed to initialize MongoDB: {e}")
        
        self.logger.info("Template Agent initialized")

    async def _init_mongodb(self):
        """Initialize MongoDB connection (optional)."""
        if self.mongodb_integration:
            try:
                connected = await self.mongodb_integration.connect()
                if connected:
                    self.logger.info("Template Agent connected to MongoDB")
                else:
                    self.logger.warning("Template Agent failed to connect to MongoDB")
                    self.failure_count += 1
            except Exception as e:
                self.logger.error(f"Template Agent MongoDB initialization error: {e}")
                self.failure_count += 1

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for production monitoring (REQUIRED)."""
        try:
            # CHANGE THIS: Add your agent-specific health checks
            # Example: Test core functionality
            test_result = await self.test_core_functionality()
            
            health_status = {
                "agent_id": self.agent_id,
                "status": "healthy" if test_result else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "failure_count": self.failure_count,
                "mongodb_connected": self.mongodb_integration is not None,
                "uptime": (datetime.now() - self.last_health_check).total_seconds(),
                "version": AGENT_METADATA["version"],
                # CHANGE THIS: Add your agent-specific health metrics
                "custom_metrics": {
                    "test_functionality": "passed" if test_result else "failed"
                }
            }
            
            self.last_health_check = datetime.now()
            
            # Reset failure count on successful health check
            if health_status["status"] == "healthy":
                self.failure_count = 0
            
            return health_status
            
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Health check failed: {e}")
            return {
                "agent_id": self.agent_id,
                "status": "unhealthy",
                "error": str(e),
                "failure_count": self.failure_count,
                "last_check": datetime.now().isoformat()
            }

    async def test_core_functionality(self) -> bool:
        """Test core functionality for health check (CHANGE THIS)."""
        try:
            # CHANGE THIS: Implement your agent's core functionality test
            # Example: Test basic processing
            test_input = "test"
            result = await self.process_input(test_input)
            return result is not None
        except:
            return False

    async def _store_result(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Store result in MongoDB (optional)."""
        if self.mongodb_integration:
            try:
                # Primary storage method
                mongodb_id = await self.mongodb_integration.save_agent_output(
                    self.agent_id,
                    input_data,
                    result,
                    {
                        "storage_type": "template_processing",  # CHANGE THIS
                        "agent_version": AGENT_METADATA["version"]
                    }
                )
                self.logger.info(f"✅ Result stored in MongoDB: {mongodb_id}")
                
                # Also force store as backup
                await self.mongodb_integration.force_store_result(
                    self.agent_id,
                    input_data.get("query", "unknown"),
                    result
                )
                self.logger.info("✅ Result force stored as backup")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to store result: {e}")
                self.failure_count += 1
                
                # Try force storage as fallback
                try:
                    await self.mongodb_integration.force_store_result(
                        self.agent_id,
                        input_data.get("query", "unknown"),
                        result
                    )
                    self.logger.info("✅ Result fallback storage successful")
                except Exception as e2:
                    self.logger.error(f"❌ Result fallback storage failed: {e2}")
                    self.failure_count += 1

    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main process method (REQUIRED - CHANGE THIS)."""
        try:
            params = message.params
            query = params.get("query", "") or params.get("text", "")

            if not query:
                return {
                    "status": "error",
                    "message": "No input provided",  # CHANGE THIS: Customize error message
                    "agent": self.agent_id,
                    "version": AGENT_METADATA["version"]
                }

            # CHANGE THIS: Validate input according to your agent's requirements
            if len(query) > self.max_input_length:
                return {
                    "status": "error",
                    "message": f"Input too long (max {self.max_input_length} characters)",
                    "agent": self.agent_id
                }

            # CHANGE THIS: Process the input with your agent's logic
            result = await self.process_input(query)
            
            # CHANGE THIS: Format the result according to your agent's output
            formatted_result = {
                "status": "success",
                "result": result,
                "input": query,
                "agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "version": AGENT_METADATA["version"]
            }

            # Store in MongoDB if successful
            if formatted_result.get("status") == "success":
                await self._store_result(
                    {"query": query, "type": "template_processing"},
                    formatted_result
                )
            
            return formatted_result

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Error in template agent process: {e}")
            return {
                "status": "error",
                "message": f"Processing failed: {str(e)}",
                "agent": self.agent_id,
                "failure_count": self.failure_count
            }

    async def process_input(self, input_text: str) -> Any:
        """Process input according to agent logic (CHANGE THIS)."""
        # CHANGE THIS: Implement your agent's core processing logic
        # This is just a template example
        try:
            # Example processing: reverse the input text
            processed = input_text[::-1]
            
            return {
                "original": input_text,
                "processed": processed,
                "processing_type": "template_reverse",
                "length": len(input_text)
            }
        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            raise

    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request with production metadata (REQUIRED)."""
        return {
            "status": "success",
            "info": self.get_info(),
            "metadata": AGENT_METADATA,
            "health": await self.health_check(),
            "capabilities": [cap.name for cap in self.capabilities],
            # CHANGE THIS: Add your agent-specific information
            "configuration": {
                "max_input_length": self.max_input_length,
                "processing_timeout": self.processing_timeout
            },
            "agent": self.agent_id
        }

# Agent registration functions for auto-discovery (REQUIRED)
def get_agent_metadata():
    """Get agent metadata for auto-discovery (REQUIRED)."""
    return AGENT_METADATA

def create_agent():
    """Create and return the agent instance (REQUIRED)."""
    return TemplateAgent()

def get_agent_info():
    """Get agent information for compatibility (REQUIRED)."""
    return {
        "name": AGENT_METADATA["name"],
        "description": AGENT_METADATA["description"],
        "version": AGENT_METADATA["version"],
        "author": AGENT_METADATA["author"],
        "capabilities": ["template_capability"],  # CHANGE THIS
        "category": AGENT_METADATA["category"]
    }

# Test function (optional but recommended)
if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test_agent():
        print(f"🧪 Testing {AGENT_METADATA['name']}")
        print("=" * 50)

        try:
            agent = TemplateAgent()
            
            # Test health check
            health = await agent.health_check()
            print(f"Health Status: {health['status']}")
            
            # Test processing
            test_inputs = [
                "Hello World",
                "Test input",
                "Template agent test"
            ]

            for test_input in test_inputs:
                print(f"\n🔍 Testing: {test_input}")
                
                message = MCPMessage(
                    id=f"test_{datetime.now().timestamp()}",
                    method="process",
                    params={"query": test_input},
                    timestamp=datetime.now()
                )

                result = await agent.process_message(message)
                
                if result["status"] == "success":
                    print(f"✅ Result: {result['result']}")
                else:
                    print(f"❌ Error: {result['message']}")

            print(f"\n✅ {AGENT_METADATA['name']} test completed!")

        except Exception as e:
            print(f"❌ Failed to test agent: {e}")

    asyncio.run(test_agent())

"""
INSTRUCTIONS FOR CREATING NEW AGENTS:

1. Copy this template file to your desired location (live/, inactive/, or future/)
2. Rename the file to your agent's name (e.g., my_agent.py)
3. Search for "CHANGE THIS" comments and modify accordingly:
   - Update AGENT_METADATA with your agent's information
   - Modify the class name and capabilities
   - Implement your agent's core processing logic in process_input()
   - Update health check logic in test_core_functionality()
   - Customize error messages and validation
   - Add any agent-specific configuration

4. Test your agent by running: python your_agent.py
5. Place the agent in the appropriate folder:
   - live/ for active agents
   - inactive/ for disabled agents
   - future/ for planned agents

6. The MCP system will automatically discover and load your agent!

REQUIRED FUNCTIONS:
- get_agent_metadata(): Returns agent metadata for discovery
- create_agent(): Creates and returns agent instance
- get_agent_info(): Returns agent information for compatibility

REQUIRED METHODS:
- health_check(): Production health monitoring
- handle_process(): Main processing logic
- handle_info(): Agent information endpoint

OPTIONAL FEATURES:
- MongoDB integration for data storage
- Custom validation and error handling
- Agent-specific configuration
- Inter-agent communication capabilities
"""
