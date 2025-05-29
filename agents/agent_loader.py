#!/usr/bin/env python3
"""
Agent Loader System - Load and manage agents for the MCP server
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import agent discovery
from . import discover_agents, load_all_agents, load_agent_from_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agents.agent_loader")

class MCPAgentLoader:
    """Agent loader for the MCP server system."""
    
    def __init__(self, mcp_server=None):
        self.mcp_server = mcp_server
        self.discovered_agents = {}
        self.loaded_agents = {}
        self.failed_agents = {}
        self.load_statistics = {
            "total_discovered": 0,
            "total_loaded": 0,
            "total_failed": 0,
            "last_load_time": None
        }
    
    def load_all_agents(self) -> Dict[str, Any]:
        """Load all agents from the agents folder structure."""
        logger.info("Loading all agents...")
        
        # Discover agents
        self.discovered_agents = discover_agents()
        self.load_statistics["total_discovered"] = len(self.discovered_agents)
        
        logger.info(f"Loading {len(self.discovered_agents)} discovered agents...")
        
        # Load agents in priority order
        sorted_agents = sorted(
            self.discovered_agents.items(),
            key=lambda x: x[1].get("priority", 5)
        )
        
        for agent_id, agent_info in sorted_agents:
            try:
                if agent_info.get("auto_load", True):
                    agent = load_agent_from_info(agent_info)
                    if agent:
                        self.loaded_agents[agent_id] = {
                            "agent": agent,
                            "info": agent_info,
                            "loaded_at": datetime.now().isoformat()
                        }
                        
                        # Register with MCP server if available
                        if self.mcp_server:
                            self.mcp_server.register_agent(agent_id, agent)
                        
                        logger.info(f"Loaded agent: {agent_id} ({agent_info['name']})")
                    else:
                        self.failed_agents[agent_id] = {
                            "info": agent_info,
                            "error": "Failed to instantiate agent",
                            "failed_at": datetime.now().isoformat()
                        }
                        logger.error(f"Failed to load agent: {agent_id}")
                else:
                    logger.info(f"Skipping agent {agent_id} (auto_load=False)")
                    
            except Exception as e:
                self.failed_agents[agent_id] = {
                    "info": agent_info,
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
                logger.error(f"Error loading agent {agent_id}: {e}")
        
        # Update statistics
        self.load_statistics.update({
            "total_loaded": len(self.loaded_agents),
            "total_failed": len(self.failed_agents),
            "last_load_time": datetime.now().isoformat()
        })
        
        logger.info(f"Successfully loaded {len(self.loaded_agents)} agents")
        if self.failed_agents:
            logger.warning(f"Failed to load {len(self.failed_agents)} agents")
        
        return self.loaded_agents
    
    def load_agent_by_id(self, agent_id: str) -> Optional[Any]:
        """Load a specific agent by ID."""
        if agent_id in self.loaded_agents:
            logger.info(f"Agent {agent_id} already loaded")
            return self.loaded_agents[agent_id]["agent"]
        
        # Check if agent was discovered
        if agent_id not in self.discovered_agents:
            # Re-discover agents
            self.discovered_agents = discover_agents()
        
        if agent_id in self.discovered_agents:
            try:
                agent_info = self.discovered_agents[agent_id]
                agent = load_agent_from_info(agent_info)
                
                if agent:
                    self.loaded_agents[agent_id] = {
                        "agent": agent,
                        "info": agent_info,
                        "loaded_at": datetime.now().isoformat()
                    }
                    
                    # Register with MCP server if available
                    if self.mcp_server:
                        self.mcp_server.register_agent(agent_id, agent)
                    
                    logger.info(f"Loaded agent: {agent_id}")
                    return agent
                else:
                    logger.error(f"Failed to instantiate agent: {agent_id}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error loading agent {agent_id}: {e}")
                return None
        else:
            logger.error(f"Agent {agent_id} not found in discovered agents")
            return None
    
    def unload_agent(self, agent_id: str) -> bool:
        """Unload a specific agent."""
        if agent_id in self.loaded_agents:
            try:
                # Unregister from MCP server if available
                if self.mcp_server:
                    self.mcp_server.unregister_agent(agent_id)
                
                del self.loaded_agents[agent_id]
                logger.info(f"Unloaded agent: {agent_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error unloading agent {agent_id}: {e}")
                return False
        else:
            logger.warning(f"Agent {agent_id} not loaded")
            return False
    
    def reload_all_agents(self) -> Dict[str, Any]:
        """Reload all agents (hot reload)."""
        logger.info("Reloading all agents...")
        
        # Unload all current agents
        for agent_id in list(self.loaded_agents.keys()):
            self.unload_agent(agent_id)
        
        # Clear caches
        self.discovered_agents.clear()
        self.failed_agents.clear()
        
        # Reload all agents
        return self.load_all_agents()
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get detailed status of all agents."""
        # Get category statistics
        categories = {}
        for agent_id, agent_data in self.discovered_agents.items():
            category = agent_data.get("category", "unknown")
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            "total_discovered": len(self.discovered_agents),
            "total_loaded": len(self.loaded_agents),
            "total_failed": len(self.failed_agents),
            "categories": categories,
            "loaded_agents": {
                agent_id: {
                    "name": data["info"]["name"],
                    "version": data["info"].get("version", "unknown"),
                    "category": data["info"].get("category", "unknown"),
                    "loaded_at": data["loaded_at"]
                }
                for agent_id, data in self.loaded_agents.items()
            },
            "failed_agents": {
                agent_id: {
                    "name": data["info"]["name"],
                    "error": data["error"],
                    "failed_at": data["failed_at"]
                }
                for agent_id, data in self.failed_agents.items()
            },
            "load_statistics": self.load_statistics
        }

def initialize_agent_loader(mcp_server=None) -> MCPAgentLoader:
    """Initialize the agent loader system."""
    loader = MCPAgentLoader(mcp_server)
    return loader
