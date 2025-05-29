#!/usr/bin/env python3
"""
Math Agent - Production Ready
Live agent for mathematical calculations with full MCP compliance
"""

import os
import re
import math
import operator
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

# MongoDB integration
try:
    from mcp_mongodb_integration import MCPMongoDBIntegration
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Agent metadata for auto-discovery
AGENT_METADATA = {
    "id": "math_agent",
    "name": "Math Agent",
    "version": "2.0.0",
    "author": "MCP System",
    "description": "Advanced mathematical calculations with MongoDB storage",
    "category": "computation",
    "status": "live",
    "dependencies": ["pymongo"],
    "auto_load": True,
    "priority": 1,
    "health_check_interval": 30,
    "max_failures": 3,
    "recovery_timeout": 60
}

class MathAgent(BaseMCPAgent):
    """Production-ready Math Agent with enhanced capabilities."""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="mathematical_computation",
                description="Perform mathematical calculations, percentages, and analysis",
                input_types=["text", "dict"],
                output_types=["dict", "number"],
                methods=["process", "calculate", "analyze", "info"],
                version="2.0.0"
            )
        ]

        super().__init__("math_agent", "Math Agent", capabilities)
        
        # Production configuration
        self.max_expression_length = 1000
        self.calculation_timeout = 30
        self.failure_count = 0
        self.last_health_check = datetime.now()
        
        # Initialize MongoDB integration
        self.mongodb_integration = None
        if MONGODB_AVAILABLE:
            try:
                self.mongodb_integration = MCPMongoDBIntegration()
                asyncio.create_task(self._init_mongodb())
            except Exception as e:
                self.logger.error(f"Failed to initialize MongoDB: {e}")
        
        # Mathematical operations mapping
        self.operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '//': operator.floordiv,
            '%': operator.mod,
            '**': operator.pow,
            '^': operator.xor,
        }
        
        # Mathematical functions
        self.math_functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'ceil': math.ceil,
            'floor': math.floor,
            'pi': math.pi,
            'e': math.e
        }

        self.logger.info("Math Agent initialized with production configuration")

    async def _init_mongodb(self):
        """Initialize MongoDB connection."""
        if self.mongodb_integration:
            try:
                connected = await self.mongodb_integration.connect()
                if connected:
                    self.logger.info("Math Agent connected to MongoDB")
                else:
                    self.logger.warning("Math Agent failed to connect to MongoDB")
                    self.failure_count += 1
            except Exception as e:
                self.logger.error(f"Math Agent MongoDB initialization error: {e}")
                self.failure_count += 1

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for production monitoring."""
        try:
            # Test basic calculation
            test_result = await self.process_math_expression("2 + 2")
            
            health_status = {
                "agent_id": self.agent_id,
                "status": "healthy" if test_result.get("status") == "success" else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "failure_count": self.failure_count,
                "mongodb_connected": self.mongodb_integration is not None,
                "uptime": (datetime.now() - self.last_health_check).total_seconds(),
                "test_calculation": test_result.get("result", "failed"),
                "version": AGENT_METADATA["version"]
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

    async def _store_calculation(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Store calculation result in MongoDB with enhanced error handling."""
        if self.mongodb_integration:
            try:
                # Primary storage method
                mongodb_id = await self.mongodb_integration.save_agent_output(
                    "math_agent",
                    input_data,
                    result,
                    {
                        "calculation_type": result.get("operation", "unknown"),
                        "storage_type": "calculation",
                        "agent_version": AGENT_METADATA["version"]
                    }
                )
                self.logger.info(f"✅ Math calculation stored in MongoDB: {mongodb_id}")
                
                # Also force store as backup
                await self.mongodb_integration.force_store_result(
                    "math_agent",
                    input_data.get("expression", "unknown"),
                    result
                )
                self.logger.info("✅ Math calculation force stored as backup")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to store math calculation: {e}")
                self.failure_count += 1
                
                # Try force storage as fallback
                try:
                    await self.mongodb_integration.force_store_result(
                        "math_agent",
                        input_data.get("expression", "unknown"),
                        result
                    )
                    self.logger.info("✅ Math calculation fallback storage successful")
                except Exception as e2:
                    self.logger.error(f"❌ Math calculation fallback storage failed: {e2}")
                    self.failure_count += 1

    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main process method with enhanced error handling."""
        try:
            params = message.params
            expression = params.get("expression", "") or params.get("query", "")

            if not expression:
                return {
                    "status": "error",
                    "message": "No mathematical expression provided",
                    "agent": self.agent_id,
                    "version": AGENT_METADATA["version"]
                }

            # Validate expression length
            if len(expression) > self.max_expression_length:
                return {
                    "status": "error",
                    "message": f"Expression too long (max {self.max_expression_length} characters)",
                    "agent": self.agent_id
                }

            # Process the mathematical expression
            result = await self.process_math_expression(expression)
            
            # Store in MongoDB if successful
            if result.get("status") == "success":
                await self._store_calculation(
                    {"expression": expression, "query": expression},
                    result
                )
            
            return result

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Error in math agent process: {e}")
            return {
                "status": "error",
                "message": f"Math processing failed: {str(e)}",
                "agent": self.agent_id,
                "failure_count": self.failure_count
            }

    async def process_math_expression(self, expression: str) -> Dict[str, Any]:
        """Process mathematical expression with enhanced capabilities."""
        try:
            # Clean and validate expression
            cleaned_expression = self.clean_expression(expression)
            
            if not cleaned_expression:
                return {
                    "status": "error",
                    "message": "Invalid or empty mathematical expression",
                    "agent": self.agent_id
                }

            # Check for percentage calculations
            if "%" in cleaned_expression and "of" in cleaned_expression.lower():
                return await self.calculate_percentage(cleaned_expression)

            # Evaluate mathematical expression
            try:
                # Create safe evaluation environment
                safe_dict = {
                    "__builtins__": {},
                    **self.math_functions
                }
                
                # Replace common mathematical notation
                cleaned_expression = cleaned_expression.replace("^", "**")
                
                result = eval(cleaned_expression, safe_dict)
                
                return {
                    "status": "success",
                    "result": float(result) if isinstance(result, (int, float)) else result,
                    "expression": expression,
                    "cleaned_expression": cleaned_expression,
                    "operation": "evaluation",
                    "agent": self.agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "version": AGENT_METADATA["version"]
                }

            except ZeroDivisionError:
                return {
                    "status": "error",
                    "message": "Division by zero is not allowed",
                    "expression": expression,
                    "agent": self.agent_id
                }
            except (ValueError, TypeError) as e:
                return {
                    "status": "error",
                    "message": f"Invalid mathematical operation: {str(e)}",
                    "expression": expression,
                    "agent": self.agent_id
                }

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Error processing math expression: {e}")
            return {
                "status": "error",
                "message": f"Mathematical processing failed: {str(e)}",
                "expression": expression,
                "agent": self.agent_id
            }

    def clean_expression(self, expression: str) -> str:
        """Clean and validate mathematical expression."""
        if not expression:
            return ""
        
        # Remove extra whitespace
        cleaned = ' '.join(expression.split())
        
        # Extract mathematical expressions from natural language
        math_patterns = [
            r'calculate\s+(.+)',
            r'compute\s+(.+)',
            r'what\s+is\s+(.+)',
            r'solve\s+(.+)',
            r'(.+\s*[+\-*/]\s*.+)',
            r'(\d+\.?\d*\s*%\s*of\s*\d+\.?\d*)',
        ]
        
        for pattern in math_patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()
                break
        
        # Remove non-mathematical characters but keep operators and numbers
        cleaned = re.sub(r'[^\d+\-*/().%\s\w]', '', cleaned)
        
        return cleaned.strip()

    async def calculate_percentage(self, expression: str) -> Dict[str, Any]:
        """Calculate percentage operations."""
        try:
            # Extract percentage calculation
            percentage_pattern = r'(\d+\.?\d*)\s*%\s*of\s*(\d+\.?\d*)'
            match = re.search(percentage_pattern, expression, re.IGNORECASE)
            
            if match:
                percentage = float(match.group(1))
                value = float(match.group(2))
                result = (percentage / 100) * value
                
                return {
                    "status": "success",
                    "result": round(result, 2),
                    "percentage": percentage,
                    "value": value,
                    "operation": "percentage",
                    "expression": expression,
                    "agent": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Could not parse percentage calculation",
                    "expression": expression,
                    "agent": self.agent_id
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Percentage calculation failed: {str(e)}",
                "expression": expression,
                "agent": self.agent_id
            }

    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request with production metadata."""
        return {
            "status": "success",
            "info": self.get_info(),
            "metadata": AGENT_METADATA,
            "health": await self.health_check(),
            "capabilities": [cap.name for cap in self.capabilities],
            "supported_operations": list(self.operations.keys()),
            "supported_functions": list(self.math_functions.keys()),
            "agent": self.agent_id
        }

# Agent registration functions for auto-discovery
def get_agent_metadata():
    """Get agent metadata for auto-discovery."""
    return AGENT_METADATA

def create_agent():
    """Create and return the agent instance."""
    return MathAgent()

def get_agent_info():
    """Get agent information for compatibility."""
    return {
        "name": "Math Agent",
        "description": "Production-ready mathematical calculations with MongoDB storage",
        "version": "2.0.0",
        "author": "MCP System",
        "capabilities": ["mathematical_computation", "percentage_calculation", "expression_evaluation"],
        "category": "computation"
    }

if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test_agent():
        print("🔢 Testing Production Math Agent")
        print("=" * 50)

        try:
            agent = MathAgent()
            
            # Test health check
            health = await agent.health_check()
            print(f"Health Status: {health['status']}")
            
            # Test calculations
            test_expressions = [
                "Calculate 20% of 500",
                "What is 15 + 25 * 2?",
                "sqrt(16) + log10(100)",
                "sin(pi/2)"
            ]

            for expr in test_expressions:
                print(f"\n🧮 Testing: {expr}")
                
                message = MCPMessage(
                    id=f"test_{datetime.now().timestamp()}",
                    method="process",
                    params={"expression": expr},
                    timestamp=datetime.now()
                )

                result = await agent.process_message(message)
                
                if result["status"] == "success":
                    print(f"✅ Result: {result['result']}")
                else:
                    print(f"❌ Error: {result['message']}")

            print("\n✅ Production Math Agent test completed!")

        except Exception as e:
            print(f"❌ Failed to test agent: {e}")

    asyncio.run(test_agent())
