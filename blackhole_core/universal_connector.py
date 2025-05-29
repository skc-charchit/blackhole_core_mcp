#!/usr/bin/env python3
"""
Universal Agent Connector - USB-like interface for external agents
Connects to any external agent without modifying their code
"""

import requests
import json
import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UniversalAgentConnector:
    """
    Universal connector that can interface with any external agent.
    Works like a USB - plug and play without code modifications.
    """
    
    def __init__(self):
        """Initialize the universal connector."""
        self.connected_agents = {}
        self.agent_capabilities = {}
        self.routing_patterns = {}
        self.connection_methods = {
            'http_api': self._connect_http_api,
            'python_module': self._connect_python_module,
            'function_call': self._connect_function,
            'class_instance': self._connect_class_instance,
            'websocket': self._connect_websocket,
            'grpc': self._connect_grpc
        }
    
    def register_agent(self, agent_config: Dict[str, Any]) -> bool:
        """
        Register an external agent with the MCP system.
        
        Args:
            agent_config: Configuration for the external agent
            
        Returns:
            True if successfully registered
        """
        try:
            agent_id = agent_config['id']
            connection_type = agent_config['connection_type']
            
            # Validate connection type
            if connection_type not in self.connection_methods:
                logger.error(f"Unsupported connection type: {connection_type}")
                return False
            
            # Connect to the agent
            connector_func = self.connection_methods[connection_type]
            agent_interface = connector_func(agent_config)
            
            if agent_interface:
                # Store agent connection
                self.connected_agents[agent_id] = {
                    'interface': agent_interface,
                    'config': agent_config,
                    'connection_type': connection_type,
                    'status': 'connected',
                    'last_ping': datetime.now()
                }
                
                # Extract capabilities
                capabilities = self._extract_capabilities(agent_config, agent_interface)
                self.agent_capabilities[agent_id] = capabilities
                
                # Update routing patterns
                self._update_routing_patterns(agent_id, capabilities)
                
                logger.info(f"Successfully registered agent: {agent_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_config.get('id', 'unknown')}: {e}")
            return False
    
    def route_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Automatically route user request to the most appropriate agent.
        
        Args:
            user_input: User's natural language request
            context: Additional context for routing
            
        Returns:
            Response from the selected agent
        """
        try:
            # Analyze request to determine best agent
            selected_agent = self._select_agent(user_input, context)
            
            if not selected_agent:
                return {
                    'status': 'error',
                    'message': 'No suitable agent found for this request',
                    'user_input': user_input
                }
            
            # Execute request through selected agent
            response = self._execute_request(selected_agent, user_input, context)
            
            # Add routing metadata
            response['routing_info'] = {
                'selected_agent': selected_agent,
                'routing_confidence': self._calculate_confidence(user_input, selected_agent),
                'available_agents': list(self.connected_agents.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error routing request: {e}")
            return {
                'status': 'error',
                'message': f'Routing error: {str(e)}',
                'user_input': user_input
            }
    
    def _connect_http_api(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Connect to HTTP API based agent."""
        try:
            base_url = config['endpoint']
            headers = config.get('headers', {})
            auth = config.get('auth', {})
            
            # Test connection
            health_endpoint = config.get('health_check', f"{base_url}/health")
            response = requests.get(health_endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    'type': 'http_api',
                    'base_url': base_url,
                    'headers': headers,
                    'auth': auth,
                    'methods': config.get('methods', ['POST']),
                    'endpoints': config.get('endpoints', {})
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to connect to HTTP API: {e}")
            return None
    
    def _connect_python_module(self, config: Dict[str, Any]) -> Optional[Any]:
        """Connect to Python module based agent."""
        try:
            module_path = config['module_path']
            class_name = config.get('class_name')
            
            # Import the module
            module = importlib.import_module(module_path)
            
            if class_name:
                # Get class from module
                agent_class = getattr(module, class_name)
                # Initialize with config parameters
                init_params = config.get('init_params', {})
                agent_instance = agent_class(**init_params)
                return agent_instance
            else:
                # Return module directly
                return module
                
        except Exception as e:
            logger.error(f"Failed to connect to Python module: {e}")
            return None
    
    def _connect_function(self, config: Dict[str, Any]) -> Optional[Callable]:
        """Connect to function based agent."""
        try:
            module_path = config['module_path']
            function_name = config['function_name']
            
            # Import module and get function
            module = importlib.import_module(module_path)
            function = getattr(module, function_name)
            
            return function
            
        except Exception as e:
            logger.error(f"Failed to connect to function: {e}")
            return None
    
    def _connect_class_instance(self, config: Dict[str, Any]) -> Optional[Any]:
        """Connect to existing class instance."""
        try:
            # This would connect to an already instantiated class
            # Implementation depends on how the instance is provided
            instance_ref = config.get('instance_reference')
            
            if instance_ref:
                # Could be a global variable, singleton, etc.
                return instance_ref
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to connect to class instance: {e}")
            return None
    
    def _connect_websocket(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Connect to WebSocket based agent."""
        try:
            # WebSocket connection setup
            ws_url = config['websocket_url']
            
            return {
                'type': 'websocket',
                'url': ws_url,
                'protocols': config.get('protocols', []),
                'headers': config.get('headers', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return None
    
    def _connect_grpc(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Connect to gRPC based agent."""
        try:
            # gRPC connection setup
            grpc_endpoint = config['grpc_endpoint']
            
            return {
                'type': 'grpc',
                'endpoint': grpc_endpoint,
                'service': config.get('service'),
                'methods': config.get('methods', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to connect to gRPC: {e}")
            return None
    
    def _extract_capabilities(self, config: Dict[str, Any], interface: Any) -> Dict[str, Any]:
        """Extract capabilities from the connected agent."""
        capabilities = {
            'keywords': config.get('keywords', []),
            'description': config.get('description', ''),
            'input_types': config.get('input_types', ['text']),
            'output_types': config.get('output_types', ['json']),
            'methods': [],
            'confidence_patterns': config.get('patterns', [])
        }
        
        # Auto-detect methods if it's a Python object
        if hasattr(interface, '__dict__'):
            methods = [method for method in dir(interface) 
                      if not method.startswith('_') and callable(getattr(interface, method))]
            capabilities['methods'] = methods
        
        return capabilities
    
    def _update_routing_patterns(self, agent_id: str, capabilities: Dict[str, Any]) -> None:
        """Update routing patterns based on agent capabilities."""
        patterns = capabilities.get('confidence_patterns', [])
        keywords = capabilities.get('keywords', [])
        
        # Add keyword-based patterns
        for keyword in keywords:
            if keyword not in self.routing_patterns:
                self.routing_patterns[keyword] = []
            self.routing_patterns[keyword].append(agent_id)
        
        # Add regex patterns
        for pattern in patterns:
            if pattern not in self.routing_patterns:
                self.routing_patterns[pattern] = []
            self.routing_patterns[pattern].append(agent_id)
    
    def _select_agent(self, user_input: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Select the most appropriate agent for the request."""
        user_input_lower = user_input.lower()
        agent_scores = {}
        
        # Score agents based on keyword matching
        for keyword, agent_ids in self.routing_patterns.items():
            if keyword.lower() in user_input_lower:
                for agent_id in agent_ids:
                    if agent_id not in agent_scores:
                        agent_scores[agent_id] = 0
                    agent_scores[agent_id] += 1
        
        # Score based on capabilities
        for agent_id, capabilities in self.agent_capabilities.items():
            description = capabilities.get('description', '').lower()
            if any(word in description for word in user_input_lower.split()):
                if agent_id not in agent_scores:
                    agent_scores[agent_id] = 0
                agent_scores[agent_id] += 0.5
        
        # Return agent with highest score
        if agent_scores:
            return max(agent_scores, key=agent_scores.get)
        
        return None
    
    def _calculate_confidence(self, user_input: str, agent_id: str) -> float:
        """Calculate confidence score for agent selection."""
        if agent_id not in self.agent_capabilities:
            return 0.0
        
        capabilities = self.agent_capabilities[agent_id]
        keywords = capabilities.get('keywords', [])
        
        matches = sum(1 for keyword in keywords if keyword.lower() in user_input.lower())
        total_keywords = len(keywords) if keywords else 1
        
        return min(matches / total_keywords, 1.0)
    
    def _execute_request(self, agent_id: str, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute request through the selected agent."""
        if agent_id not in self.connected_agents:
            return {
                'status': 'error',
                'message': f'Agent {agent_id} not connected'
            }
        
        agent_info = self.connected_agents[agent_id]
        interface = agent_info['interface']
        connection_type = agent_info['connection_type']
        
        try:
            if connection_type == 'http_api':
                return self._execute_http_request(interface, user_input, context)
            elif connection_type == 'python_module':
                return self._execute_python_request(interface, user_input, context)
            elif connection_type == 'function_call':
                return self._execute_function_request(interface, user_input, context)
            elif connection_type == 'class_instance':
                return self._execute_instance_request(interface, user_input, context)
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported connection type: {connection_type}'
                }
                
        except Exception as e:
            logger.error(f"Error executing request through agent {agent_id}: {e}")
            return {
                'status': 'error',
                'message': f'Execution error: {str(e)}',
                'agent_id': agent_id
            }
    
    def _execute_http_request(self, interface: Dict[str, Any], user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request through HTTP API."""
        try:
            base_url = interface['base_url']
            headers = interface['headers']
            
            # Prepare request payload
            payload = {
                'input': user_input,
                'context': context or {}
            }
            
            # Use configured endpoint or default
            endpoint = interface.get('endpoints', {}).get('process', '/process')
            url = f"{base_url}{endpoint}"
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'result': response.json(),
                    'agent_type': 'http_api'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP {response.status_code}: {response.text}',
                    'agent_type': 'http_api'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'HTTP request failed: {str(e)}',
                'agent_type': 'http_api'
            }
    
    def _execute_python_request(self, interface: Any, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request through Python module/class."""
        try:
            # Try common method names
            method_names = ['process', 'execute', 'run', 'handle', 'plan']
            
            for method_name in method_names:
                if hasattr(interface, method_name):
                    method = getattr(interface, method_name)
                    
                    # Call with appropriate parameters
                    if callable(method):
                        # Try different parameter combinations
                        try:
                            result = method(user_input)
                        except TypeError:
                            try:
                                result = method({'input': user_input, 'context': context})
                            except TypeError:
                                result = method(user_input, context)
                        
                        return {
                            'status': 'success',
                            'result': result,
                            'agent_type': 'python_module',
                            'method_used': method_name
                        }
            
            return {
                'status': 'error',
                'message': 'No suitable method found in Python module',
                'agent_type': 'python_module'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Python execution failed: {str(e)}',
                'agent_type': 'python_module'
            }
    
    def _execute_function_request(self, interface: Callable, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request through function call."""
        try:
            # Get function signature to determine parameters
            sig = inspect.signature(interface)
            params = list(sig.parameters.keys())
            
            if len(params) == 1:
                result = interface(user_input)
            elif len(params) == 2:
                result = interface(user_input, context)
            else:
                # Try with keyword arguments
                result = interface(input=user_input, context=context)
            
            return {
                'status': 'success',
                'result': result,
                'agent_type': 'function_call'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Function execution failed: {str(e)}',
                'agent_type': 'function_call'
            }
    
    def _execute_instance_request(self, interface: Any, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request through class instance."""
        return self._execute_python_request(interface, user_input, context)
    
    def get_connected_agents(self) -> Dict[str, Any]:
        """Get information about all connected agents."""
        return {
            agent_id: {
                'status': info['status'],
                'connection_type': info['connection_type'],
                'capabilities': self.agent_capabilities.get(agent_id, {}),
                'last_ping': info['last_ping'].isoformat()
            }
            for agent_id, info in self.connected_agents.items()
        }
    
    def disconnect_agent(self, agent_id: str) -> bool:
        """Disconnect an agent from the system."""
        if agent_id in self.connected_agents:
            del self.connected_agents[agent_id]
            if agent_id in self.agent_capabilities:
                del self.agent_capabilities[agent_id]
            
            # Remove from routing patterns
            for pattern, agents in self.routing_patterns.items():
                if agent_id in agents:
                    agents.remove(agent_id)
            
            logger.info(f"Disconnected agent: {agent_id}")
            return True
        
        return False

# Global universal connector instance
universal_connector = UniversalAgentConnector()
