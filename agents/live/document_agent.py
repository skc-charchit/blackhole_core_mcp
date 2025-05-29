#!/usr/bin/env python3
"""
Document Agent - Production Ready
Live agent for document processing with full MCP compliance
"""

import asyncio
import json
import re
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

# MongoDB integration
try:
    from mcp_mongodb_integration import MCPMongoDBIntegration
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Agent metadata for auto-discovery
AGENT_METADATA = {
    "id": "document_agent",
    "name": "Document Agent",
    "version": "2.0.0",
    "author": "MCP System",
    "description": "Document processing, text analysis, and content extraction",
    "category": "processing",
    "status": "live",
    "dependencies": ["pymongo"],
    "auto_load": True,
    "priority": 3,
    "health_check_interval": 60,
    "max_failures": 3,
    "recovery_timeout": 120
}

class DocumentAgent(BaseMCPAgent):
    """Production-ready Document Agent with enhanced capabilities."""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="document_processing",
                description="Process documents, extract text, detect authors, and analyze content",
                input_types=["pdf", "image", "text", "dict"],
                output_types=["text", "dict"],
                methods=["process", "extract_text", "detect_authors", "extract_metadata", "info"],
                version="2.0.0"
            )
        ]
        
        super().__init__("document_agent", "Document Agent", capabilities)

        # Production configuration
        self.max_document_size = 10 * 1024 * 1024  # 10MB
        self.max_documents_per_request = 10
        self.processing_timeout = 60
        self.failure_count = 0
        self.last_health_check = datetime.now()

        # Initialize MongoDB integration
        self.mongodb_integration = None
        if MONGODB_AVAILABLE:
            try:
                self.mongodb_integration = MCPMongoDBIntegration()
                asyncio.create_task(self._init_mongodb())
            except Exception as e:
                self.logger.error(f"Failed to initialize MongoDB: {e}")

        self.logger.info("Document Agent initialized with production configuration")

    async def _init_mongodb(self):
        """Initialize MongoDB connection."""
        if self.mongodb_integration:
            try:
                connected = await self.mongodb_integration.connect()
                if connected:
                    self.logger.info("Document Agent connected to MongoDB")
                else:
                    self.logger.warning("Document Agent failed to connect to MongoDB")
                    self.failure_count += 1
            except Exception as e:
                self.logger.error(f"Document Agent MongoDB initialization error: {e}")
                self.failure_count += 1

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for production monitoring."""
        try:
            # Test basic document processing
            test_doc = {
                "filename": "test.txt",
                "content": "This is a test document for health check.",
                "type": "text"
            }
            
            test_result = await self.process_single_document(test_doc)
            
            health_status = {
                "agent_id": self.agent_id,
                "status": "healthy" if test_result.get("processed_by") == self.agent_id else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "failure_count": self.failure_count,
                "mongodb_connected": self.mongodb_integration is not None,
                "uptime": (datetime.now() - self.last_health_check).total_seconds(),
                "test_processing": "success" if test_result.get("processed_by") else "failed",
                "version": AGENT_METADATA["version"]
            }
            
            self.last_health_check = datetime.now()
            
            # Reset failure count on successful health check
            if health_status["status"] == "healthy":
                self.failure_count = 0
            
            return health_status
            
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Document health check failed: {e}")
            return {
                "agent_id": self.agent_id,
                "status": "unhealthy",
                "error": str(e),
                "failure_count": self.failure_count,
                "last_check": datetime.now().isoformat()
            }

    async def _store_document_result(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Store document processing result in MongoDB with enhanced error handling."""
        if self.mongodb_integration:
            try:
                # Primary storage method
                mongodb_id = await self.mongodb_integration.save_agent_output(
                    "document_agent",
                    input_data,
                    result,
                    {
                        "storage_type": "document_processing",
                        "processing_type": "document_analysis",
                        "agent_version": AGENT_METADATA["version"]
                    }
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
                self.failure_count += 1
                
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
                    self.failure_count += 1

    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle document processing with enhanced error handling."""
        try:
            params = message.params
            user_input = params.get("user_input", "") or params.get("query", "")
            context = params.get("context", {})
            documents = context.get("documents_context", [])

            # If no documents provided, try to process text input
            if not documents and user_input:
                # Create a virtual document from text input
                documents = [{
                    "filename": "text_input.txt",
                    "content": user_input,
                    "type": "text"
                }]

            if not documents:
                return {
                    "status": "no_documents",
                    "message": "No documents provided for processing. Please provide document content or text to analyze.",
                    "agent": self.agent_id,
                    "version": AGENT_METADATA["version"],
                    "examples": [
                        "Analyze this text: Your text here",
                        "Process document with content in context",
                        "Extract information from provided documents"
                    ]
                }

            # Validate document limits
            if len(documents) > self.max_documents_per_request:
                return {
                    "status": "error",
                    "message": f"Too many documents. Maximum {self.max_documents_per_request} documents per request.",
                    "agent": self.agent_id
                }

            # Process each document
            processed_docs = []
            all_authors = []
            all_content = []

            for doc in documents:
                # Validate document size
                content_size = len(str(doc.get("content", "")))
                if content_size > self.max_document_size:
                    self.logger.warning(f"Document too large: {content_size} bytes")
                    continue

                processed_doc = await self.process_single_document(doc)
                processed_docs.append(processed_doc)

                if processed_doc.get("authors"):
                    all_authors.extend(processed_doc["authors"])

                if processed_doc.get("content"):
                    all_content.append(processed_doc["content"])

            # Compile results
            result = {
                "status": "success",
                "processed_documents": processed_docs,
                "total_documents": len(processed_docs),
                "authors_found": list(set(all_authors)),
                "total_content_length": sum(len(content) for content in all_content),
                "processing_summary": {
                    "documents_processed": len(processed_docs),
                    "authors_detected": len(set(all_authors)),
                    "total_words": sum(len(content.split()) for content in all_content),
                    "processing_time": datetime.now().isoformat()
                },
                "agent": self.agent_id,
                "version": AGENT_METADATA["version"]
            }

            # Store in MongoDB
            await self._store_document_result(params, result)

            return result

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Error in document agent process: {e}")
            return {
                "status": "error",
                "message": f"Document processing failed: {str(e)}",
                "agent": self.agent_id,
                "failure_count": self.failure_count
            }

    async def process_single_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document with enhanced analysis."""
        try:
            filename = doc.get("filename", "unknown")
            content = doc.get("content", "")
            doc_type = doc.get("type", "unknown")

            # Extract authors from content
            authors = self.extract_authors_from_content(content)

            # Perform content analysis
            analysis = self.analyze_content(content)

            # Extract metadata
            metadata = {
                "filename": filename,
                "type": doc_type,
                "size": len(content),
                "word_count": len(content.split()) if content else 0,
                "character_count": len(content),
                "line_count": len(content.split('\n')) if content else 0,
                "processed_at": datetime.now().isoformat(),
                "analysis": analysis
            }

            return {
                "filename": filename,
                "content": content,
                "authors": authors,
                "metadata": metadata,
                "analysis": analysis,
                "processed_by": self.agent_id,
                "processing_version": AGENT_METADATA["version"]
            }

        except Exception as e:
            self.logger.error(f"Error processing single document: {e}")
            return {
                "filename": doc.get("filename", "unknown"),
                "error": str(e),
                "processed_by": self.agent_id,
                "status": "failed"
            }

    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Perform enhanced content analysis."""
        if not content:
            return {"error": "No content to analyze"}

        try:
            words = content.split()
            sentences = content.split('.')
            paragraphs = content.split('\n\n')

            # Basic statistics
            analysis = {
                "word_count": len(words),
                "sentence_count": len([s for s in sentences if s.strip()]),
                "paragraph_count": len([p for p in paragraphs if p.strip()]),
                "character_count": len(content),
                "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
                "average_sentence_length": len(words) / len(sentences) if sentences else 0
            }

            # Content type detection
            if any(keyword in content.lower() for keyword in ['abstract', 'introduction', 'conclusion', 'references']):
                analysis["content_type"] = "academic_paper"
            elif any(keyword in content.lower() for keyword in ['dear', 'sincerely', 'regards']):
                analysis["content_type"] = "letter"
            elif any(keyword in content.lower() for keyword in ['chapter', 'section']):
                analysis["content_type"] = "book_or_manual"
            else:
                analysis["content_type"] = "general_text"

            # Language detection (basic)
            if content:
                analysis["language"] = "english"  # Simplified for now

            return analysis

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def extract_authors_from_content(self, content: str) -> List[str]:
        """Extract authors from document content with enhanced patterns."""
        authors = []

        if not content:
            return authors

        try:
            # Enhanced author patterns
            author_patterns = [
                r"Authors?:\s*([^\n]+)",
                r"Detected Authors?:\s*([^\n]+)",
                r"By:\s*([^\n]+)",
                r"Written by:\s*([^\n]+)",
                r"Author\(s\):\s*([^\n]+)",
                r"Created by:\s*([^\n]+)",
                r"Authored by:\s*([^\n]+)"
            ]

            for pattern in author_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Split by commas and clean up
                    author_names = [name.strip() for name in match.split(",")]
                    authors.extend(author_names)

            # Remove duplicates and empty strings
            authors = list(set([author for author in authors if author and len(author) > 1]))

            return authors

        except Exception as e:
            self.logger.error(f"Error extracting authors: {e}")
            return []

    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request with production metadata."""
        return {
            "status": "success",
            "info": self.get_info(),
            "metadata": AGENT_METADATA,
            "health": await self.health_check(),
            "capabilities": [cap.name for cap in self.capabilities],
            "supported_formats": ["text", "pdf", "image"],
            "processing_limits": {
                "max_document_size": f"{self.max_document_size / (1024*1024):.1f}MB",
                "max_documents_per_request": self.max_documents_per_request,
                "processing_timeout": f"{self.processing_timeout}s"
            },
            "agent": self.agent_id
        }

# Agent registration functions for auto-discovery
def get_agent_metadata():
    """Get agent metadata for auto-discovery."""
    return AGENT_METADATA

def create_agent():
    """Create and return the agent instance."""
    return DocumentAgent()

def get_agent_info():
    """Get agent information for compatibility."""
    return {
        "name": "Document Agent",
        "description": "Production-ready document processing and text analysis",
        "version": "2.0.0",
        "author": "MCP System",
        "capabilities": ["document_processing", "text_analysis", "author_detection", "content_analysis"],
        "category": "processing"
    }
