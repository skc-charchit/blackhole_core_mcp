#blachkhole_core.agents.live_data_agent.py

import requests
from datetime import datetime
from bson import ObjectId
from blackhole_core.data_source.mongodb import get_mongo_client

class LiveDataAgent:
    def __init__(self, memory=None, api_url=None):
        self.memory = memory
        self.api_url = api_url or "https://wttr.in/London?format=j1"
        self.client = get_mongo_client()
        self.db = self.client["blackhole_db"]

    def plan(self, query):
        try:
            response = requests.get(self.api_url, timeout=10)
            data = response.json()
            result = {
                "agent": "LiveDataAgent",
                "input": query,
                "output": data,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"api_url": self.api_url}
            }
        except Exception as e:
            result = {
                "agent": "LiveDataAgent",
                "input": query,
                "output": f"Error fetching data: {e}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"api_url": self.api_url}
            }

        return result
