#!/usr/bin/env python3
"""
Document Processor Agent - Core agent for processing documents
"""

import asyncio
import json
import re
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

# MongoDB integration
try:
    from mcp_mongodb_integration import MCPMongoDBIntegration
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Agent metadata for auto-discovery
AGENT_METADATA = {
    "id": "document_processor",
    "name": "Document Processor Agent",
    "version": "1.0.0",
    "author": "MCP System",
    "description": "Extract text, detect authors, process PDFs and images",
    "dependencies": [],
    "auto_load": True,
    "priority": 1
}

class DocumentProcessorAgent(BaseMCPAgent):
    """MCP Agent for processing documents with inter-agent communication."""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="document_processing",
                description="Extract text, detect authors, process PDFs and images",
                input_types=["pdf", "image", "text"],
                output_types=["text", "dict"],
                methods=["process", "extract_text", "detect_authors", "extract_metadata"],
                can_call_agents=["text_analyzer"]
            )
        ]
        super().__init__("document_processor", "Document Processor Agent", capabilities)

        # Initialize MongoDB integration
        self.mongodb_integration = None
        if MONGODB_AVAILABLE:
            try:
                import asyncio
                self.mongodb_integration = MCPMongoDBIntegration()
                asyncio.create_task(self._init_mongodb())
            except Exception as e:
                self.logger.error(f"Failed to initialize MongoDB: {e}")

    async def _init_mongodb(self):
        """Initialize MongoDB connection."""
        if self.mongodb_integration:
            try:
                connected = await self.mongodb_integration.connect()
                if connected:
                    self.logger.info("Document Agent connected to MongoDB")
                else:
                    self.logger.warning("Document Agent failed to connect to MongoDB")
            except Exception as e:
                self.logger.error(f"Document Agent MongoDB initialization error: {e}")

    async def _store_document_result(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Store document processing result in MongoDB with force storage."""
        if self.mongodb_integration:
            try:
                # Primary storage method
                mongodb_id = await self.mongodb_integration.save_agent_output(
                    "document_agent",
                    input_data,
                    result,
                    {"storage_type": "document_processing", "processing_type": "document_analysis"}
                )
                self.logger.info(f"✅ Document result stored in MongoDB: {mongodb_id}")

                # Also force store as backup
                await self.mongodb_integration.force_store_result(
                    "document_agent",
                    input_data.get("user_input", "document_processing"),
                    result
                )
                self.logger.info("✅ Document result force stored as backup")

            except Exception as e:
                self.logger.error(f"❌ Failed to store document result: {e}")

                # Try force storage as fallback
                try:
                    await self.mongodb_integration.force_store_result(
                        "document_agent",
                        input_data.get("user_input", "document_processing"),
                        result
                    )
                    self.logger.info("✅ Document result fallback storage successful")
                except Exception as e2:
                    self.logger.error(f"❌ Document result fallback storage failed: {e2}")

    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Process documents and collaborate with other agents."""
        params = message.params
        user_input = params.get("user_input", "")
        context = params.get("context", {})
        documents = context.get("documents_context", [])

        if not documents:
            return {
                "status": "no_documents",
                "message": "No documents provided for processing",
                "agent": self.agent_id
            }

        # Process each document
        processed_docs = []
        all_authors = []
        all_content = []

        for doc in documents:
            processed_doc = await self.process_single_document(doc)
            processed_docs.append(processed_doc)

            if processed_doc.get("authors"):
                all_authors.extend(processed_doc["authors"])

            if processed_doc.get("content"):
                all_content.append(processed_doc["content"])

        # If user is asking about authors, collaborate with text analyzer
        if "author" in user_input.lower():
            try:
                text_analysis = await self.call_agent(
                    "text_analyzer",
                    "find_authors",
                    {"content": " ".join(all_content), "detected_authors": all_authors}
                )

                return {
                    "status": "success",
                    "processed_documents": processed_docs,
                    "author_analysis": text_analysis,
                    "collaboration": ["text_analyzer"],
                    "agent": self.agent_id
                }
            except Exception as e:
                self.log_error(f"Author collaboration error: {e}")

        # Default processing
        result = {
            "status": "success",
            "processed_documents": processed_docs,
            "total_documents": len(processed_docs),
            "authors_found": list(set(all_authors)),
            "agent": self.agent_id
        }

        # Store in MongoDB
        await self._store_document_result(params, result)

        return result

    async def process_single_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document."""
        filename = doc.get("filename", "unknown")
        content = doc.get("content", "")
        doc_type = doc.get("type", "unknown")

        # Extract authors from content
        authors = self.extract_authors_from_content(content)

        # Extract metadata
        metadata = {
            "filename": filename,
            "type": doc_type,
            "size": len(content),
            "word_count": len(content.split()) if content else 0,
            "processed_at": datetime.now().isoformat()
        }

        return {
            "filename": filename,
            "content": content,
            "authors": authors,
            "metadata": metadata,
            "processed_by": self.agent_id
        }

    def extract_authors_from_content(self, content: str) -> List[str]:
        """Extract authors from document content."""
        authors = []

        # Look for explicit author mentions
        author_patterns = [
            r"Authors?:\s*([^\n]+)",
            r"Detected Authors?:\s*([^\n]+)",
            r"By:\s*([^\n]+)",
            r"Written by:\s*([^\n]+)"
        ]

        for pattern in author_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Split by commas and clean up
                author_names = [name.strip() for name in match.split(",")]
                authors.extend(author_names)

        # Remove duplicates and empty strings
        authors = list(set([author for author in authors if author]))

        return authors

    async def handle_extract_text(self, message: MCPMessage) -> Dict[str, Any]:
        """Extract text from documents."""
        params = message.params
        documents = params.get("documents", [])

        extracted_texts = []
        for doc in documents:
            content = doc.get("content", "")
            extracted_texts.append({
                "filename": doc.get("filename", "unknown"),
                "text": content,
                "word_count": len(content.split()) if content else 0
            })

        return {
            "status": "success",
            "extracted_texts": extracted_texts,
            "total_documents": len(documents),
            "agent": self.agent_id
        }

    async def handle_detect_authors(self, message: MCPMessage) -> Dict[str, Any]:
        """Detect authors in documents."""
        params = message.params
        content = params.get("content", "")
        documents = params.get("documents", [])

        all_authors = []

        # Process content directly
        if content:
            authors = self.extract_authors_from_content(content)
            all_authors.extend(authors)

        # Process documents
        for doc in documents:
            doc_content = doc.get("content", "")
            authors = self.extract_authors_from_content(doc_content)
            all_authors.extend(authors)

        # Remove duplicates
        unique_authors = list(set(all_authors))

        return {
            "status": "success",
            "authors": unique_authors,
            "total_authors": len(unique_authors),
            "agent": self.agent_id
        }

    async def handle_extract_metadata(self, message: MCPMessage) -> Dict[str, Any]:
        """Extract metadata from documents."""
        params = message.params
        documents = params.get("documents", [])

        metadata_list = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = {
                "filename": doc.get("filename", "unknown"),
                "type": doc.get("type", "unknown"),
                "size": len(content),
                "word_count": len(content.split()) if content else 0,
                "character_count": len(content),
                "line_count": len(content.split('\n')) if content else 0,
                "extracted_at": datetime.now().isoformat()
            }
            metadata_list.append(metadata)

        return {
            "status": "success",
            "metadata": metadata_list,
            "total_documents": len(documents),
            "agent": self.agent_id
        }

# Agent registration functions
def get_agent_info():
    """Get agent information for auto-discovery."""
    return {
        "name": "Document Processor Agent",
        "description": "Extract text, detect authors, process PDFs and images with inter-agent communication",
        "version": "1.0.0",
        "author": "MCP System",
        "capabilities": ["document_processing", "text_extraction", "author_detection", "metadata_extraction"],
        "category": "core"
    }

def create_agent():
    """Create and return the agent instance."""
    return DocumentProcessorAgent()

if __name__ == "__main__":
    # Test the Document Processor agent
    print("📄 Testing Document Processor Agent")
    print("=" * 40)

    agent = DocumentProcessorAgent()
    print(f"Created agent: {agent}")
    print(f"Capabilities: {[cap.name for cap in agent.capabilities]}")
    print(f"Methods: {list(agent.message_handlers.keys())}")

    print("\n✅ Document Processor agent ready!")
    print("🎯 Perfect for processing documents and collaborating with other agents!")
