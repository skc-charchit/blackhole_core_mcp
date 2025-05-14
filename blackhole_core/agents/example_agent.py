#blachkhole_core.agents.example_agent.py

from .base_agent import BaseAgent

class ExampleAgent(BaseAgent):
    def plan(self, input_data):
        return f"Example plan for: {input_data}"
