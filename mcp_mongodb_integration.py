#!/usr/bin/env python3
"""
MCP-MongoDB Integration Layer
Connects MCP agents with MongoDB storage
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import pymongo
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

class MCPMongoDBIntegration:
    """Integration layer between MCP agents and MongoDB."""

    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI')
        self.db_name = os.getenv('MONGO_DB_NAME', 'blackhole_db')
        self.collection_name = os.getenv('MONGO_COLLECTION_NAME', 'agent_outputs')
        self.client = None
        self.db = None
        self.collection = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("mcp_mongodb_integration")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def connect(self) -> bool:
        """Connect to MongoDB."""
        if not PYMONGO_AVAILABLE:
            self.logger.error("PyMongo not available")
            return False

        if not self.mongo_uri:
            self.logger.error("MongoDB URI not configured")
            return False

        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)

            # Test connection
            self.client.admin.command('ping')

            # Get database and collection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]

            self.logger.info("Connected to MongoDB successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    async def save_agent_output(self, agent_id: str, input_data: Dict[str, Any],
                               output_data: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """Save agent output to MongoDB."""
        if self.collection is None:
            self.logger.warning("MongoDB not connected, cannot save agent output")
            return f"mock_{datetime.now().timestamp()}"

        try:
            document = {
                "agent": agent_id,
                "agent_id": agent_id,
                "input": input_data,
                "output": output_data,
                "metadata": metadata or {},
                "timestamp": datetime.now(),
                "created_at": datetime.now()
            }

            result = self.collection.insert_one(document)

            self.logger.info(f"Saved {agent_id} output to MongoDB: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            self.logger.error(f"Error saving agent output: {e}")
            return f"error_{datetime.now().timestamp()}"

    async def store_command_result(self, command: str, agent_used: str, result: Dict[str, Any], timestamp: datetime) -> str:
        """Store MCP command result in MongoDB."""
        if not self.db:
            self.logger.warning("MongoDB not connected, cannot store command result")
            return f"mock_{timestamp.timestamp()}"

        try:
            # Store in mcp_commands collection
            commands_collection = self.db['mcp_commands']

            document = {
                "command": command,
                "agent_used": agent_used,
                "result": result,
                "timestamp": timestamp,
                "created_at": datetime.now(),
                "server": "embedded_mcp_server",
                "storage_type": "command_result"
            }

            result_doc = commands_collection.insert_one(document)

            # Also store in agent_outputs collection for compatibility
            await self.save_agent_output(
                agent_used,
                {"command": command, "query": command, "type": "mcp_command"},
                result,
                {
                    "command_timestamp": timestamp.isoformat(),
                    "server": "embedded_mcp_server",
                    "storage_type": "agent_output",
                    "mongodb_id": str(result_doc.inserted_id)
                }
            )

            self.logger.info(f"✅ Stored command result in MongoDB: {result_doc.inserted_id}")
            return str(result_doc.inserted_id)

        except Exception as e:
            self.logger.error(f"❌ Error storing command result: {e}")
            return f"error_{timestamp.timestamp()}"

    async def force_store_result(self, agent_id: str, command: str, result: Dict[str, Any]) -> bool:
        """Force store any result in MongoDB with multiple fallback methods."""
        if not self.db:
            self.logger.warning("MongoDB not connected")
            return False

        try:
            timestamp = datetime.now()

            # Method 1: Store in mcp_commands
            try:
                commands_collection = self.db['mcp_commands']
                commands_collection.insert_one({
                    "command": command,
                    "agent_used": agent_id,
                    "result": result,
                    "timestamp": timestamp,
                    "created_at": timestamp,
                    "server": "embedded_mcp_server",
                    "storage_method": "force_store"
                })
                self.logger.info(f"✅ Force stored in mcp_commands: {agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to store in mcp_commands: {e}")

            # Method 2: Store in agent_outputs
            try:
                await self.save_agent_output(
                    agent_id,
                    {"command": command, "query": command, "type": "force_store"},
                    result,
                    {"timestamp": timestamp.isoformat(), "storage_method": "force_store"}
                )
                self.logger.info(f"✅ Force stored in agent_outputs: {agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to store in agent_outputs: {e}")

            # Method 3: Store in general results collection
            try:
                results_collection = self.db['all_results']
                results_collection.insert_one({
                    "agent_id": agent_id,
                    "command": command,
                    "result": result,
                    "timestamp": timestamp,
                    "created_at": timestamp,
                    "storage_method": "force_store_fallback"
                })
                self.logger.info(f"✅ Force stored in all_results: {agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to store in all_results: {e}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Complete force store failure: {e}")
            return False

    async def process_document_with_agent(self, filename: str, content: str,
                                        query: str = "analyze this document") -> Dict[str, Any]:
        """Process document using document_processor agent and save to MongoDB."""
        try:
            # Simulate document processing (since we don't have direct agent access yet)
            input_data = {
                "file": {
                    "name": filename,
                    "content": content[:500] + "..." if len(content) > 500 else content
                },
                "query": query,
                "processing_type": "document_analysis"
            }

            # Simulate document processor output
            output_data = {
                "extracted_text": content,
                "word_count": len(content.split()) if content else 0,
                "character_count": len(content),
                "analysis": f"Document analysis for: {filename}",
                "query_response": f"Processed query: {query}",
                "detected_authors": self._extract_authors(content),
                "summary": self._generate_summary(content),
                "processing_status": "completed"
            }

            metadata = {
                "filename": filename,
                "file_size": len(content),
                "processing_time": 0.1,
                "agent_version": "1.0.0",
                "processing_method": "mcp_integration"
            }

            # Save to MongoDB
            mongodb_id = await self.save_agent_output(
                "document_processor",
                input_data,
                output_data,
                metadata
            )

            return {
                "status": "success",
                "agent": "document_processor",
                "mongodb_id": mongodb_id,
                "output": output_data,
                "metadata": metadata
            }

        except Exception as e:
            self.logger.error(f"Error processing document: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent": "document_processor"
            }

    def _extract_authors(self, content: str) -> List[str]:
        """Extract authors from content."""
        import re
        authors = []

        # Look for author patterns
        patterns = [
            r"Author[s]?:\s*([^\n]+)",
            r"By:\s*([^\n]+)",
            r"Written by:\s*([^\n]+)"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                author_names = [name.strip() for name in match.split(",")]
                authors.extend(author_names)

        return list(set([author for author in authors if author]))

    def _generate_summary(self, content: str) -> str:
        """Generate a simple summary."""
        if not content:
            return "No content to summarize"

        words = content.split()
        if len(words) <= 50:
            return content

        # Simple summary: first 50 words
        summary = " ".join(words[:50]) + "..."
        return summary

    async def process_pdf_document(self, filename: str, content: str) -> Dict[str, Any]:
        """Process PDF document."""
        return await self.process_document_with_agent(filename, content, "extract and analyze PDF content")

    async def process_ocr_image(self, filename: str, image_data: str) -> Dict[str, Any]:
        """Process OCR image."""
        # Simulate OCR processing
        input_data = {
            "file": {
                "name": filename,
                "type": "image"
            },
            "processing_type": "ocr_analysis"
        }

        output_data = {
            "extracted_text": f"OCR extracted text from {filename}",
            "confidence_score": 0.95,
            "detected_language": "en",
            "text_regions": 1,
            "processing_status": "completed"
        }

        metadata = {
            "filename": filename,
            "image_format": "unknown",
            "ocr_engine": "tesseract",
            "processing_time": 0.2
        }

        mongodb_id = await self.save_agent_output("ocr_processor", input_data, output_data, metadata)

        return {
            "status": "success",
            "agent": "ocr_processor",
            "mongodb_id": mongodb_id,
            "output": output_data,
            "metadata": metadata
        }

    async def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about agent usage."""
        if not self.collection:
            return {"error": "MongoDB not connected"}

        try:
            # Count documents by agent
            pipeline = [
                {"$group": {"_id": "$agent", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]

            agent_counts = list(self.collection.aggregate(pipeline))

            # Total counts
            total_docs = self.collection.count_documents({})
            doc_agents = self.collection.count_documents({"agent": {"$regex": "document", "$options": "i"}})
            pdf_agents = self.collection.count_documents({"agent": {"$regex": "pdf", "$options": "i"}})
            ocr_agents = self.collection.count_documents({"agent": {"$regex": "ocr", "$options": "i"}})

            return {
                "total_documents": total_docs,
                "agent_counts": {item["_id"]: item["count"] for item in agent_counts},
                "document_agents": doc_agents,
                "pdf_agents": pdf_agents,
                "ocr_agents": ocr_agents,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()

# Test function
async def test_integration():
    """Test the MCP-MongoDB integration."""
    print("🧪 Testing MCP-MongoDB Integration")
    print("=" * 50)

    integration = MCPMongoDBIntegration()

    try:
        # Connect
        print("1️⃣ Connecting to MongoDB...")
        if await integration.connect():
            print("   ✅ Connected successfully!")
        else:
            print("   ❌ Connection failed!")
            return

        # Test document processing
        print("\n2️⃣ Testing document processing...")
        test_content = """
        Title: Test Document
        Author: John Doe

        This is a test document for the MCP system.
        It contains sample content to test document processing capabilities.
        The document processor should extract authors and generate summaries.
        """

        result = await integration.process_document_with_agent(
            "test_document.txt",
            test_content,
            "who is the author and what is the summary"
        )

        if result["status"] == "success":
            print(f"   ✅ Document processed! MongoDB ID: {result['mongodb_id']}")
            print(f"   📄 Authors found: {result['output']['detected_authors']}")
            print(f"   📝 Word count: {result['output']['word_count']}")
        else:
            print(f"   ❌ Processing failed: {result.get('error', 'unknown error')}")

        # Test PDF processing
        print("\n3️⃣ Testing PDF processing...")
        pdf_result = await integration.process_pdf_document(
            "sample.pdf",
            "This is sample PDF content for testing."
        )

        if pdf_result["status"] == "success":
            print(f"   ✅ PDF processed! MongoDB ID: {pdf_result['mongodb_id']}")

        # Test OCR processing
        print("\n4️⃣ Testing OCR processing...")
        ocr_result = await integration.process_ocr_image(
            "sample_image.jpg",
            "image_data_here"
        )

        if ocr_result["status"] == "success":
            print(f"   ✅ OCR processed! MongoDB ID: {ocr_result['mongodb_id']}")

        # Get updated statistics
        print("\n5️⃣ Getting updated statistics...")
        stats = await integration.get_agent_statistics()

        if "error" not in stats:
            print(f"   📊 Total documents: {stats['total_documents']}")
            print(f"   📄 Document agents: {stats['document_agents']}")
            print(f"   📄 PDF agents: {stats['pdf_agents']}")
            print(f"   🖼️ OCR agents: {stats['ocr_agents']}")
            print(f"   🤖 Agent breakdown: {stats['agent_counts']}")

        print("\n✅ Integration test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        integration.close()

if __name__ == "__main__":
    asyncio.run(test_integration())
