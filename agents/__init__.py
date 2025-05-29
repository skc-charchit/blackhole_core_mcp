"""
MCP Agents Package
Production agents for the Model Context Protocol system
"""

# Production agents auto-discovery
PRODUCTION_AGENTS = [
    "realtime_weather_agent",
    "math_agent", 
    "calendar_agent",
    "real_gmail_agent",
    "document_processor"
]

def get_production_agents():
    """Get list of production agent names."""
    return PRODUCTION_AGENTS

def is_production_agent(agent_name):
    """Check if an agent is a production agent."""
    return agent_name in PRODUCTION_AGENTS
