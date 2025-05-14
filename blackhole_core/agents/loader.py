#blachkhole_core.agents.loader.py

import importlib
import sys
import os

# Ensure that Python can find the 'blackhole_core' directory for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def load_agent(agent_name):
    """
    Dynamically import and return an agent class by its name.
    Example: load_agent('my_agent') imports agents/my_agent.py and returns MyAgent class.
    """
    try:
        module = importlib.import_module(f"blackhole_core.agents.{agent_name}")
        class_name = ''.join([part.capitalize() for part in agent_name.split('_')])
        agent_class = getattr(module, class_name)
        return agent_class
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"Could not load agent '{agent_name}': {e}")

# Test block
if __name__ == "__main__":
    try:
        AgentClass = load_agent('my_agent')
        agent = AgentClass(memory=[], source="api")
        print(agent)
    except Exception as e:
        print(e)
