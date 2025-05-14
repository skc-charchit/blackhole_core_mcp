#blachkhole_core.agents.base_agent.py

import logging

class BaseAgent:
    def __init__(self, tools=None, memory=None, source=None):
        """
        Base class for agents.

        :param tools: List of tool instances the agent can use.
        :param memory: Memory storage or manager instance.
        :param source: Optional source identifier for the agent.
        """
        self.tools = tools if tools is not None else []
        self.memory = memory
        self.source = source

        # Set up a logger specific to the agent
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO)

    def plan(self, input_data):
        """
        Plan the next steps based on the input.

        :param input_data: Input information for the agent.
        :return: A plan (this is agent-specific and to be implemented by subclasses)
        """
        raise NotImplementedError("Subclasses should implement the plan method.")

    def run(self, input_data):
        """
        Execute the plan and return results.

        :param input_data: Input information for the agent.
        :return: Result of executing the plan.
        """
        self.logger.info(f"Running agent {self.__class__.__name__} with input: {input_data}")
        plan = self.plan(input_data)
        self.logger.info(f"Generated plan: {plan}")
        return plan

    def tag_source(self, data):
        """
        Optionally tag data with the source if provided.

        :param data: Data to tag.
        :return: Tagged data.
        """
        if self.source:
            return {"source": self.source, "data": data}
        return data
