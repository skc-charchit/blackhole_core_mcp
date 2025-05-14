#blachkhole_core.agents.my_agent.py

from blackhole_core.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def plan(self, input_data):
        return f"MyAgent received: {input_data}"
