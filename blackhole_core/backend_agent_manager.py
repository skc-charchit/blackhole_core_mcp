#!/usr/bin/env python3
"""
Backend Agent Manager - Automatically connects agents defined in configuration
Agents are connected in the backend, not through frontend interface
"""

import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

from .universal_connector import universal_connector
from .agent_registry import agent_registry

logger = logging.getLogger(__name__)

class BackendAgentManager:
    """
    Manages agents that are configured and connected automatically in the backend.
    No frontend interaction needed - agents are defined in configuration files.
    """
    
    def __init__(self, config_dir: str = "agent_configs"):
        """Initialize the backend agent manager."""
        self.config_dir = config_dir
        self.backend_agents = {}
        self.auto_connect_enabled = True
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Create default backend agent configurations
        self._create_default_backend_configs()
    
    def _create_default_backend_configs(self):
        """Create default backend agent configurations."""
        default_configs = {
            # Text Analysis Agent
            "text_analyzer.json": {
                "id": "text_analyzer",
                "name": "Text Analysis Agent",
                "description": "Advanced text analysis and NLP processing",
                "connection_type": "python_module",
                "module_path": "example_agents.simple_agent",
                "class_name": "SimpleAgent",
                "init_params": {
                    "agent_name": "TextAnalyzer"
                },
                "keywords": ["analyze", "text", "nlp", "sentiment", "language"],
                "patterns": [r"analyze\s+(.+)", r"sentiment\s+(.+)", r"text\s+analysis"],
                "capabilities": {
                    "text_processing": True,
                    "sentiment_analysis": True,
                    "language_detection": True,
                    "keyword_extraction": True
                },
                "collaboration_roles": ["analyzer", "processor"],
                "enabled": True,
                "auto_connect": True
            },
            
            # Data Processor Agent
            "data_processor.json": {
                "id": "data_processor",
                "name": "Data Processing Agent",
                "description": "Processes and transforms various data formats",
                "connection_type": "python_module",
                "module_path": "example_agents.simple_agent",
                "class_name": "DataProcessor",
                "keywords": ["data", "process", "transform", "convert", "format"],
                "patterns": [r"process\s+data", r"transform\s+(.+)", r"convert\s+(.+)"],
                "capabilities": {
                    "data_transformation": True,
                    "format_conversion": True,
                    "data_validation": True,
                    "batch_processing": True
                },
                "collaboration_roles": ["processor", "transformer"],
                "enabled": True,
                "auto_connect": True
            },
            
            # Research Agent
            "research_agent.json": {
                "id": "research_agent",
                "name": "Research Agent",
                "description": "Conducts comprehensive research and information gathering",
                "connection_type": "function_call",
                "module_path": "example_agents.simple_agent",
                "function_name": "advanced_processor",
                "keywords": ["research", "investigate", "gather", "information", "study"],
                "patterns": [r"research\s+(.+)", r"investigate\s+(.+)", r"study\s+(.+)"],
                "capabilities": {
                    "information_gathering": True,
                    "source_verification": True,
                    "comprehensive_analysis": True,
                    "report_generation": True
                },
                "collaboration_roles": ["researcher", "investigator"],
                "enabled": True,
                "auto_connect": True
            },
            
            # Summary Agent
            "summary_agent.json": {
                "id": "summary_agent",
                "name": "Summary Agent",
                "description": "Creates summaries and extracts key insights",
                "connection_type": "function_call",
                "module_path": "example_agents.simple_agent",
                "function_name": "quick_processor",
                "keywords": ["summary", "summarize", "key points", "insights", "overview"],
                "patterns": [r"summarize\s+(.+)", r"summary\s+of\s+(.+)", r"key\s+points"],
                "capabilities": {
                    "text_summarization": True,
                    "key_point_extraction": True,
                    "insight_generation": True,
                    "content_condensation": True
                },
                "collaboration_roles": ["summarizer", "synthesizer"],
                "enabled": True,
                "auto_connect": True
            },
            
            # Validation Agent
            "validation_agent.json": {
                "id": "validation_agent",
                "name": "Validation Agent",
                "description": "Validates and verifies information accuracy",
                "connection_type": "python_module",
                "module_path": "example_agents.simple_agent",
                "class_name": "SimpleAgent",
                "init_params": {
                    "agent_name": "Validator"
                },
                "keywords": ["validate", "verify", "check", "confirm", "accuracy"],
                "patterns": [r"validate\s+(.+)", r"verify\s+(.+)", r"check\s+(.+)"],
                "capabilities": {
                    "fact_checking": True,
                    "data_validation": True,
                    "accuracy_verification": True,
                    "quality_assurance": True
                },
                "collaboration_roles": ["validator", "checker"],
                "enabled": True,
                "auto_connect": True
            }
        }
        
        # Save default configurations
        for filename, config in default_configs.items():
            config_path = os.path.join(self.config_dir, filename)
            if not os.path.exists(config_path):
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Created default backend agent config: {filename}")
    
    def load_backend_agents(self):
        """Load and connect all backend agents from configuration files."""
        if not self.auto_connect_enabled:
            logger.info("Auto-connect disabled, skipping backend agent loading")
            return
        
        logger.info("Loading backend agents from configuration files...")
        
        # Load all JSON configuration files
        config_files = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
        
        connected_count = 0
        failed_count = 0
        
        for config_file in config_files:
            config_path = os.path.join(self.config_dir, config_file)
            
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check if agent should be auto-connected
                if not config.get('auto_connect', True) or not config.get('enabled', True):
                    logger.info(f"Skipping agent {config.get('id', config_file)}: auto_connect or enabled is False")
                    continue
                
                # Register and connect the agent
                success = self._connect_backend_agent(config)
                
                if success:
                    connected_count += 1
                    self.backend_agents[config['id']] = {
                        'config': config,
                        'config_file': config_file,
                        'connected_at': datetime.now(),
                        'status': 'connected'
                    }
                    logger.info(f"Successfully connected backend agent: {config['id']}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to connect backend agent: {config.get('id', config_file)}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error loading agent config {config_file}: {e}")
        
        logger.info(f"Backend agent loading complete: {connected_count} connected, {failed_count} failed")
        
        return {
            'connected': connected_count,
            'failed': failed_count,
            'total_configs': len(config_files)
        }
    
    def _connect_backend_agent(self, config: Dict[str, Any]) -> bool:
        """Connect a single backend agent."""
        try:
            # Add to agent registry
            registry_success = agent_registry.add_agent_config(config)
            if not registry_success:
                logger.warning(f"Failed to add agent {config['id']} to registry")
                return False
            
            # Connect through universal connector
            connector_success = universal_connector.register_agent(config)
            if not connector_success:
                logger.warning(f"Failed to connect agent {config['id']} through universal connector")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting backend agent {config.get('id', 'unknown')}: {e}")
            return False
    
    def add_backend_agent(self, agent_config: Dict[str, Any], save_to_file: bool = True) -> bool:
        """Add a new backend agent configuration."""
        try:
            agent_id = agent_config['id']
            
            # Connect the agent
            success = self._connect_backend_agent(agent_config)
            
            if success and save_to_file:
                # Save configuration to file
                config_file = f"{agent_id}.json"
                config_path = os.path.join(self.config_dir, config_file)
                
                with open(config_path, 'w') as f:
                    json.dump(agent_config, f, indent=2)
                
                # Track in backend agents
                self.backend_agents[agent_id] = {
                    'config': agent_config,
                    'config_file': config_file,
                    'connected_at': datetime.now(),
                    'status': 'connected'
                }
                
                logger.info(f"Added and saved backend agent: {agent_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding backend agent: {e}")
            return False
    
    def remove_backend_agent(self, agent_id: str, delete_file: bool = True) -> bool:
        """Remove a backend agent."""
        try:
            # Disconnect from universal connector
            universal_connector.disconnect_agent(agent_id)
            
            # Remove from registry
            agent_registry.remove_agent_config(agent_id)
            
            # Remove from backend tracking
            if agent_id in self.backend_agents:
                agent_info = self.backend_agents[agent_id]
                
                # Delete configuration file if requested
                if delete_file and 'config_file' in agent_info:
                    config_path = os.path.join(self.config_dir, agent_info['config_file'])
                    if os.path.exists(config_path):
                        os.remove(config_path)
                        logger.info(f"Deleted config file for agent {agent_id}")
                
                del self.backend_agents[agent_id]
            
            logger.info(f"Removed backend agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing backend agent {agent_id}: {e}")
            return False
    
    def get_backend_agents(self) -> Dict[str, Any]:
        """Get information about all backend agents."""
        return {
            agent_id: {
                'name': info['config'].get('name', agent_id),
                'description': info['config'].get('description', ''),
                'connection_type': info['config'].get('connection_type', 'unknown'),
                'keywords': info['config'].get('keywords', []),
                'capabilities': info['config'].get('capabilities', {}),
                'collaboration_roles': info['config'].get('collaboration_roles', []),
                'connected_at': info['connected_at'].isoformat(),
                'status': info['status']
            }
            for agent_id, info in self.backend_agents.items()
        }
    
    def reload_backend_agents(self):
        """Reload all backend agents from configuration files."""
        logger.info("Reloading backend agents...")
        
        # Disconnect existing backend agents
        for agent_id in list(self.backend_agents.keys()):
            universal_connector.disconnect_agent(agent_id)
        
        self.backend_agents.clear()
        
        # Reload from files
        return self.load_backend_agents()
    
    def enable_auto_connect(self):
        """Enable automatic connection of backend agents."""
        self.auto_connect_enabled = True
        logger.info("Backend agent auto-connect enabled")
    
    def disable_auto_connect(self):
        """Disable automatic connection of backend agents."""
        self.auto_connect_enabled = False
        logger.info("Backend agent auto-connect disabled")
    
    def get_collaboration_capabilities(self) -> Dict[str, List[str]]:
        """Get collaboration capabilities of all backend agents."""
        capabilities = {}
        
        for agent_id, info in self.backend_agents.items():
            agent_capabilities = info['config'].get('capabilities', {})
            collaboration_roles = info['config'].get('collaboration_roles', [])
            
            capabilities[agent_id] = {
                'capabilities': list(agent_capabilities.keys()),
                'collaboration_roles': collaboration_roles,
                'keywords': info['config'].get('keywords', [])
            }
        
        return capabilities

# Global backend agent manager
backend_agent_manager = BackendAgentManager()
