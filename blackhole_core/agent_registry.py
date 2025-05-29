#!/usr/bin/env python3
"""
Agent Registry - Configuration and management for external agents
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime

class AgentRegistry:
    """
    Registry for managing external agent configurations.
    Provides templates and examples for different agent types.
    """
    
    def __init__(self, config_file: str = "agent_configs.json"):
        """Initialize the agent registry."""
        self.config_file = config_file
        self.agent_configs = {}
        self.load_configurations()
    
    def load_configurations(self) -> None:
        """Load agent configurations from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.agent_configs = json.load(f)
            except Exception as e:
                print(f"Error loading agent configs: {e}")
                self.agent_configs = {}
        else:
            # Create default configurations
            self.create_default_configurations()
    
    def save_configurations(self) -> None:
        """Save agent configurations to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.agent_configs, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving agent configs: {e}")
    
    def create_default_configurations(self) -> None:
        """Create default agent configuration templates."""
        self.agent_configs = {
            "example_http_agent": {
                "id": "example_http_agent",
                "name": "Example HTTP API Agent",
                "description": "Example agent accessible via HTTP API",
                "connection_type": "http_api",
                "endpoint": "http://localhost:8001",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer your-token-here"
                },
                "health_check": "http://localhost:8001/health",
                "endpoints": {
                    "process": "/process",
                    "status": "/status"
                },
                "keywords": ["example", "demo", "test"],
                "patterns": [r"example\s+(.+)", r"demo\s+(.+)"],
                "input_types": ["text", "json"],
                "output_types": ["json"],
                "enabled": False
            },
            
            "python_module_agent": {
                "id": "python_module_agent",
                "name": "Python Module Agent",
                "description": "Agent implemented as Python module",
                "connection_type": "python_module",
                "module_path": "your_agents.example_agent",
                "class_name": "ExampleAgent",
                "init_params": {
                    "config_param": "value"
                },
                "keywords": ["python", "module", "local"],
                "patterns": [r"python\s+(.+)", r"local\s+(.+)"],
                "input_types": ["text", "dict"],
                "output_types": ["dict", "json"],
                "enabled": False
            },
            
            "function_agent": {
                "id": "function_agent",
                "name": "Function-based Agent",
                "description": "Agent implemented as a simple function",
                "connection_type": "function_call",
                "module_path": "your_agents.functions",
                "function_name": "process_request",
                "keywords": ["function", "simple", "quick"],
                "patterns": [r"function\s+(.+)", r"quick\s+(.+)"],
                "input_types": ["text"],
                "output_types": ["text", "dict"],
                "enabled": False
            },
            
            "websocket_agent": {
                "id": "websocket_agent",
                "name": "WebSocket Agent",
                "description": "Real-time agent via WebSocket",
                "connection_type": "websocket",
                "websocket_url": "ws://localhost:8002/ws",
                "protocols": ["agent-protocol"],
                "headers": {},
                "keywords": ["realtime", "websocket", "live"],
                "patterns": [r"realtime\s+(.+)", r"live\s+(.+)"],
                "input_types": ["text", "json"],
                "output_types": ["json", "stream"],
                "enabled": False
            },
            
            "grpc_agent": {
                "id": "grpc_agent",
                "name": "gRPC Agent",
                "description": "High-performance agent via gRPC",
                "connection_type": "grpc",
                "grpc_endpoint": "localhost:50051",
                "service": "AgentService",
                "methods": {
                    "Process": "process_request",
                    "Status": "get_status"
                },
                "keywords": ["grpc", "performance", "fast"],
                "patterns": [r"grpc\s+(.+)", r"fast\s+(.+)"],
                "input_types": ["protobuf", "json"],
                "output_types": ["protobuf", "json"],
                "enabled": False
            }
        }
        
        self.save_configurations()
    
    def add_agent_config(self, config: Dict[str, Any]) -> bool:
        """Add a new agent configuration."""
        try:
            agent_id = config['id']
            self.agent_configs[agent_id] = config
            self.save_configurations()
            return True
        except Exception as e:
            print(f"Error adding agent config: {e}")
            return False
    
    def update_agent_config(self, agent_id: str, config: Dict[str, Any]) -> bool:
        """Update an existing agent configuration."""
        try:
            if agent_id in self.agent_configs:
                self.agent_configs[agent_id].update(config)
                self.save_configurations()
                return True
            return False
        except Exception as e:
            print(f"Error updating agent config: {e}")
            return False
    
    def remove_agent_config(self, agent_id: str) -> bool:
        """Remove an agent configuration."""
        try:
            if agent_id in self.agent_configs:
                del self.agent_configs[agent_id]
                self.save_configurations()
                return True
            return False
        except Exception as e:
            print(f"Error removing agent config: {e}")
            return False
    
    def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        return self.agent_configs.get(agent_id, {})
    
    def get_enabled_agents(self) -> Dict[str, Any]:
        """Get all enabled agent configurations."""
        return {
            agent_id: config 
            for agent_id, config in self.agent_configs.items() 
            if config.get('enabled', False)
        }
    
    def get_all_agents(self) -> Dict[str, Any]:
        """Get all agent configurations."""
        return self.agent_configs.copy()
    
    def enable_agent(self, agent_id: str) -> bool:
        """Enable an agent."""
        if agent_id in self.agent_configs:
            self.agent_configs[agent_id]['enabled'] = True
            self.save_configurations()
            return True
        return False
    
    def disable_agent(self, agent_id: str) -> bool:
        """Disable an agent."""
        if agent_id in self.agent_configs:
            self.agent_configs[agent_id]['enabled'] = False
            self.save_configurations()
            return True
        return False
    
    def create_http_agent_config(self, agent_id: str, name: str, endpoint: str, 
                                keywords: List[str], description: str = "") -> Dict[str, Any]:
        """Create configuration for HTTP API agent."""
        return {
            "id": agent_id,
            "name": name,
            "description": description,
            "connection_type": "http_api",
            "endpoint": endpoint,
            "headers": {
                "Content-Type": "application/json"
            },
            "health_check": f"{endpoint}/health",
            "endpoints": {
                "process": "/process",
                "status": "/status"
            },
            "keywords": keywords,
            "patterns": [f"{keyword}\\s+(.+)" for keyword in keywords],
            "input_types": ["text", "json"],
            "output_types": ["json"],
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
    
    def create_python_agent_config(self, agent_id: str, name: str, module_path: str,
                                  class_name: str, keywords: List[str], 
                                  description: str = "", init_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create configuration for Python module agent."""
        return {
            "id": agent_id,
            "name": name,
            "description": description,
            "connection_type": "python_module",
            "module_path": module_path,
            "class_name": class_name,
            "init_params": init_params or {},
            "keywords": keywords,
            "patterns": [f"{keyword}\\s+(.+)" for keyword in keywords],
            "input_types": ["text", "dict"],
            "output_types": ["dict", "json"],
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
    
    def create_function_agent_config(self, agent_id: str, name: str, module_path: str,
                                    function_name: str, keywords: List[str],
                                    description: str = "") -> Dict[str, Any]:
        """Create configuration for function-based agent."""
        return {
            "id": agent_id,
            "name": name,
            "description": description,
            "connection_type": "function_call",
            "module_path": module_path,
            "function_name": function_name,
            "keywords": keywords,
            "patterns": [f"{keyword}\\s+(.+)" for keyword in keywords],
            "input_types": ["text"],
            "output_types": ["text", "dict"],
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate agent configuration and return list of errors."""
        errors = []
        
        # Required fields
        required_fields = ['id', 'name', 'connection_type']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Connection type specific validation
        connection_type = config.get('connection_type')
        
        if connection_type == 'http_api':
            if 'endpoint' not in config:
                errors.append("HTTP API agent requires 'endpoint' field")
        
        elif connection_type == 'python_module':
            if 'module_path' not in config:
                errors.append("Python module agent requires 'module_path' field")
        
        elif connection_type == 'function_call':
            if 'module_path' not in config or 'function_name' not in config:
                errors.append("Function agent requires 'module_path' and 'function_name' fields")
        
        elif connection_type == 'websocket':
            if 'websocket_url' not in config:
                errors.append("WebSocket agent requires 'websocket_url' field")
        
        elif connection_type == 'grpc':
            if 'grpc_endpoint' not in config:
                errors.append("gRPC agent requires 'grpc_endpoint' field")
        
        return errors
    
    def get_agent_templates(self) -> Dict[str, Any]:
        """Get agent configuration templates."""
        return {
            "http_api": {
                "id": "your_agent_id",
                "name": "Your Agent Name",
                "description": "Description of what your agent does",
                "connection_type": "http_api",
                "endpoint": "http://your-agent-url:port",
                "headers": {"Content-Type": "application/json"},
                "keywords": ["keyword1", "keyword2"],
                "enabled": True
            },
            "python_module": {
                "id": "your_agent_id",
                "name": "Your Agent Name", 
                "description": "Description of what your agent does",
                "connection_type": "python_module",
                "module_path": "your_module.your_agent",
                "class_name": "YourAgentClass",
                "keywords": ["keyword1", "keyword2"],
                "enabled": True
            },
            "function_call": {
                "id": "your_agent_id",
                "name": "Your Agent Name",
                "description": "Description of what your agent does", 
                "connection_type": "function_call",
                "module_path": "your_module.functions",
                "function_name": "your_function",
                "keywords": ["keyword1", "keyword2"],
                "enabled": True
            }
        }

# Global agent registry instance
agent_registry = AgentRegistry()
