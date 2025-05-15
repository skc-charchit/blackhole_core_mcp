import sys
import os
import traceback
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

try:
    from blackhole_core.agents.loader import load_agent
    from blackhole_core.data_source.mongodb import get_agent_outputs_collection
    from blackhole_core.agents.archive_search_agent import ArchiveSearchAgent
    from blackhole_core.agents.live_data_agent import LiveDataAgent
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️ Make sure you're running this script from the project root directory.")
    sys.exit(1)

def run_archive_search_agent_demo():
    print("🚀 Running ArchiveSearchAgent demo...")

    try:
        # Direct instantiation instead of using loader
        agent = ArchiveSearchAgent(memory=[], source="csv")
        result = agent.plan({"document_text": "bitcoin"})
        print("\n📊 ArchiveSearchAgent Result:\n", result)

        try:
            collection = get_agent_outputs_collection()
            if isinstance(result, dict):
                result.pop("_id", None)  # 👈 Remove _id if exists to avoid duplicate key error
                collection.insert_one(result)
                print("✅ ArchiveSearchAgent result saved to MongoDB.")
            else:
                print("❌ Result is not a dictionary, cannot save to MongoDB.")
        except Exception as e:
            print(f"⚠️ Error saving ArchiveSearchAgent result to MongoDB: {e}")
            print("⚠️ Continuing without saving to database...")
    except Exception as e:
        print(f"❌ Error running ArchiveSearchAgent: {e}")
        traceback.print_exc()

def run_live_data_agent_demo():
    print("\n🚀 Running LiveDataAgent demo...")

    try:
        # Direct instantiation instead of using loader
        agent = LiveDataAgent(memory=[], api_url="https://wttr.in/London?format=j1")
        result = agent.plan({"query": "London weather"})
        print("\n📊 LiveDataAgent Result:\n", result)

        try:
            collection = get_agent_outputs_collection()
            if isinstance(result, dict):
                result.pop("_id", None)
                collection.insert_one(result)
                print("✅ LiveDataAgent result saved to MongoDB.")
            else:
                print("❌ Result is not a dictionary, cannot save to MongoDB.")
        except Exception as e:
            print(f"⚠️ Error saving LiveDataAgent result to MongoDB: {e}")
            print("⚠️ Continuing without saving to database...")
    except Exception as e:
        print(f"❌ Error running LiveDataAgent: {e}")
        traceback.print_exc()

def run_demo():
    try:
        run_archive_search_agent_demo()
        run_live_data_agent_demo()
    except Exception as e:
        print(f"❌ Unhandled error in run_demo: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
