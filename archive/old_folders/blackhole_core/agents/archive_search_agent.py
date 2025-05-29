#blachkhole_core.agents.archive_search_agent.py
import pandas as pd
from datetime import datetime, timezone
from bson import ObjectId
from blackhole_core.data_source.mongodb import get_mongo_client
import os
from rapidfuzz import fuzz

class ArchiveSearchAgent:
    def __init__(self, memory=None, source=None):
        """Initialize ArchiveSearchAgent with optional memory and source, and setup MongoDB client."""
        self.memory = memory
        self.source = source or "csv"
        self.client = get_mongo_client()
        self.db = self.client["blackhole_db"]

        # Dynamically resolve archive CSV path
        self.archive_path = os.path.join(os.path.dirname(__file__), '..', 'data_source', 'sample_archive.csv')
        if not os.path.exists(self.archive_path):
            raise FileNotFoundError(f"Sample archive not found at {self.archive_path}")

    def plan(self, query):
        """Search for approximate matches in the archive CSV based on document_text in query."""
        document_text = query.get('document_text', "")
        if not document_text:
            return {"error": "No document_text provided."}

        df = pd.read_csv(self.archive_path)

        matches = []
        threshold = 60  # Similarity threshold (0-100)

        for _, row in df.iterrows():
            # Check each column individually for better matching
            for col, value in row.items():
                # Skip empty values
                if pd.isna(value) or str(value).strip() == "":
                    continue

                # Convert to string and lowercase for comparison
                value_str = str(value).lower()
                doc_text_lower = document_text.lower()

                # Try different fuzzy matching methods
                token_ratio = fuzz.token_set_ratio(doc_text_lower, value_str)
                partial_ratio = fuzz.partial_ratio(doc_text_lower, value_str)

                # Use the higher of the two scores
                similarity = max(token_ratio, partial_ratio)

                if similarity >= threshold:
                    # Only add each row once
                    match_entry = {
                        "match_score": similarity,
                        "matched_on": col,
                        "matched_value": value,
                        **row.to_dict()
                    }

                    # Check if this row is already in matches
                    if not any(m.get('title') == row['title'] for m in matches):
                        matches.append(match_entry)
                    break  # Move to next row once we find a match

        result = {
            "agent": "ArchiveSearchAgent",
            "input": query,
            "output": matches if matches else "No matches found.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source_file": self.archive_path}
        }
        return result

    def run(self, query):
        """Alias for the plan() method for compatibility with pipelines."""
        return self.plan(query)
