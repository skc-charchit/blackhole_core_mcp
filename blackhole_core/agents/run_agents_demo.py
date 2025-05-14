# from blackhole_core.agents.loader import load_agent
# from blackhole_core.data_source.mongodb import get_agent_outputs_collection
# from datetime import datetime

# def run_demo():
#     print("🚀 Running ArchiveSearchAgent demo...")

#     ArchiveSearchAgentClass = load_agent("archive_search_agent")
#     agent = ArchiveSearchAgentClass(memory=[], source="csv")
#     result = agent.plan({"document_text": "bitcoin"})
#     print("\n📊 ArchiveSearchAgent Result:\n", result)

#     try:
#         collection = get_agent_outputs_collection()
#         result.pop("_id", None)  # 👈 Remove _id if exists to avoid duplicate key error
#         collection.insert_one(result)
#         print("✅ ArchiveSearchAgent result saved to MongoDB.")
#     except Exception as e:
#         print(f"Error saving ArchiveSearchAgent result to MongoDB: {e}")

#     print("\n🚀 Running LiveDataAgent demo...")

#     LiveDataAgentClass = load_agent("live_data_agent")
#     agent = LiveDataAgentClass(memory=[], api_url="https://wttr.in/London?format=j1")
#     result = agent.plan({"query": "London weather"})
#     print("\n📊 LiveDataAgent Result:\n", result)

#     try:
#         result.pop("_id", None)
#         collection.insert_one(result)
#         print("✅ LiveDataAgent result saved to MongoDB.")
#     except Exception as e:
#         print(f"Error saving LiveDataAgent result to MongoDB: {e}")

# if __name__ == "__main__":
#     run_demo()

#blachkhole_core.agents.run_agents_demo.py
import sys
import os

# Add parent directory to system path so imports work smoothly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
# from blackhole_core.agents.live_data_agent import LiveDataAgent  # Uncomment to test LiveDataAgent

def test_archive_search_agent():
    print("\n🔍 Testing ArchiveSearchAgent...")
    agent = ArchiveSearchAgent()
    test_query = {"document_text": "nothing is black or white"}
    result = agent.plan(test_query)
    print("\n📊 ArchiveSearchAgent Output:\n", result)

# def test_live_data_agent():
#     print("\n🌐 Testing LiveDataAgent...")
#     agent = LiveDataAgent()
#     result = agent.plan("bitcoin")
#     print("\n📊 LiveDataAgent Output:\n", result)

if __name__ == "__main__":
    test_archive_search_agent()
    # test_live_data_agent()  # Uncomment to run LiveDataAgent test
