#!/usr/bin/env python3
"""
BlackHole Core MCP Configuration
Maintains your perspective while enabling general MCP functionality
"""

import os
from typing import Dict, List, Any

class MCPConfig:
    """
    Configuration for BlackHole Core MCP system.
    Maintains your specific approach while enabling general MCP patterns.
    """

    def __init__(self):
        """Initialize MCP configuration with your perspective."""

        # Your BlackHole Core Identity
        self.system_name = "BlackHole Core MCP"
        self.system_description = "Advanced Model Context Protocol system for intelligent document processing and multi-agent workflows"
        self.version = "2.0"

        # Your Perspective: Document-Centric Approach
        self.primary_focus = "document_processing"
        self.core_capabilities = [
            "intelligent_document_analysis",
            "multi_modal_processing",
            "llm_powered_insights",
            "organized_data_storage",
            "natural_language_interaction"
        ]

        # Your Agent Architecture
        self.agent_hierarchy = {
            "primary": {
                "document_processor": {
                    "description": "Core document analysis and processing",
                    "priority": 1,
                    "capabilities": ["pdf_processing", "image_ocr", "llm_analysis", "summarization"]
                }
            },
            "secondary": {
                "archive_search": {
                    "description": "Search through processed documents",
                    "priority": 2,
                    "capabilities": ["mongodb_search", "fuzzy_matching", "metadata_filtering"]
                },
                "live_data": {
                    "description": "Real-time data integration",
                    "priority": 3,
                    "capabilities": ["api_fetching", "weather_data", "external_integration"]
                }
            }
        }

        # Your Command Patterns (Natural Language Understanding)
        self.command_patterns = {
            # Document Processing (Your Primary Focus)
            "document_processing": {
                "patterns": [
                    r"analyze\s+(.+)",
                    r"process\s+(.+)",
                    r"extract\s+(.+)",
                    r"summarize\s+(.+)",
                    r"read\s+(.+)",
                    r"understand\s+(.+)"
                ],
                "agent": "document_processor",
                "description": "Process and analyze documents with AI",
                "examples": [
                    "analyze this document",
                    "process the uploaded PDF",
                    "extract key insights from this text"
                ]
            },

            # Archive Search (Your Data Retrieval)
            "archive_search": {
                "patterns": [
                    r"search\s+for\s+(.+)",
                    r"find\s+(.+)",
                    r"look\s+for\s+(.+)",
                    r"show\s+me\s+(.+)",
                    r"get\s+documents?\s+about\s+(.+)"
                ],
                "agent": "archive_search",
                "description": "Search through your document archive",
                "examples": [
                    "search for documents about AI",
                    "find files containing machine learning",
                    "show me recent uploads"
                ]
            },

            # Live Data (Your External Integration)
            "live_data": {
                "patterns": [
                    r"get\s+live\s+(.+)",
                    r"fetch\s+current\s+(.+)",
                    r"real[- ]?time\s+(.+)",
                    r"current\s+(.+)",
                    r"weather\s+(.+)",
                    r"(.+)\s+weather",
                    r"what\s+is\s+the\s+weather\s+(.+)",
                    r"how\s+is\s+the\s+weather\s+(.+)",
                    r"temperature\s+(.+)",
                    r"(.+)\s+temperature",
                    r"climate\s+(.+)",
                    r"forecast\s+(.+)"
                ],
                "agent": "live_data",
                "description": "Fetch real-time external data",
                "examples": [
                    "get live weather data",
                    "weather in Mumbai",
                    "what is the weather in London",
                    "temperature in New York"
                ]
            },

            # System Help (Your User Guidance)
            "help": {
                "patterns": [
                    r"help",
                    r"what\s+can\s+you\s+do",
                    r"commands?",
                    r"capabilities",
                    r"how\s+to\s+use"
                ],
                "agent": "help_system",
                "description": "Show system capabilities and usage",
                "examples": [
                    "help",
                    "what can you do",
                    "show available commands"
                ]
            }
        }

        # Your Processing Options
        self.processing_options = {
            "llm_analysis": {
                "enabled": True,
                "provider": "together_ai",
                "model": "deepseek-ai/DeepSeek-V3",
                "description": "AI-powered document analysis"
            },
            "ocr_processing": {
                "enabled": True,
                "engine": "tesseract",
                "preprocessing": True,
                "description": "Optical character recognition for images"
            },
            "database_storage": {
                "enabled": True,
                "provider": "mongodb_atlas",
                "auto_save": True,
                "description": "Persistent storage in your MongoDB"
            },
            "file_organization": {
                "enabled": True,
                "structure": "multimodal_folders",
                "timestamping": True,
                "description": "Organized file storage system"
            }
        }

        # Your Supported File Types
        self.supported_formats = {
            "documents": {
                "pdf": {"priority": 1, "processing": "enhanced_extraction"},
                "txt": {"priority": 2, "processing": "direct_analysis"},
                "md": {"priority": 2, "processing": "markdown_parsing"},
                "doc": {"priority": 3, "processing": "office_extraction"},
                "docx": {"priority": 3, "processing": "office_extraction"}
            },
            "images": {
                "png": {"priority": 1, "processing": "ocr_analysis"},
                "jpg": {"priority": 1, "processing": "ocr_analysis"},
                "jpeg": {"priority": 1, "processing": "ocr_analysis"},
                "bmp": {"priority": 2, "processing": "ocr_analysis"},
                "tiff": {"priority": 2, "processing": "ocr_analysis"}
            },
            "data": {
                "csv": {"priority": 2, "processing": "structured_analysis"},
                "json": {"priority": 2, "processing": "structured_analysis"},
                "xml": {"priority": 3, "processing": "structured_analysis"}
            }
        }

        # Your Response Format
        self.response_format = {
            "standard_fields": [
                "status",
                "command",
                "command_type",
                "agent_used",
                "result",
                "timestamp",
                "processing_time_ms"
            ],
            "metadata_fields": [
                "file_info",
                "processing_options",
                "llm_analysis",
                "mongodb_id"
            ],
            "success_indicators": ["success", "completed", "processed"],
            "error_indicators": ["error", "failed", "timeout"]
        }

        # Your Environment Integration
        self.environment = {
            "mongodb_uri": os.getenv("MONGO_URI") or os.getenv("MONGODB_URI"),
            "together_api_key": os.getenv("TOGETHER_API_KEY"),
            "upload_directory": os.getenv("UPLOAD_DIR", "uploads"),
            "multimodal_base": "data/multimodal",
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true"
        }

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        for category in ["primary", "secondary"]:
            if agent_name in self.agent_hierarchy[category]:
                return self.agent_hierarchy[category][agent_name]
        return {}

    def get_command_patterns(self, command_type: str = None) -> Dict[str, Any]:
        """Get command patterns, optionally filtered by type."""
        if command_type:
            return self.command_patterns.get(command_type, {})
        return self.command_patterns

    def get_processing_options(self) -> Dict[str, Any]:
        """Get current processing options."""
        return self.processing_options

    def is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported."""
        if not filename or '.' not in filename:
            return False

        ext = filename.rsplit('.', 1)[1].lower()

        for category in self.supported_formats.values():
            if ext in category:
                return True
        return False

    def get_file_processing_config(self, filename: str) -> Dict[str, Any]:
        """Get processing configuration for a specific file."""
        if not filename or '.' not in filename:
            return {"processing": "unknown", "priority": 999}

        ext = filename.rsplit('.', 1)[1].lower()

        for category in self.supported_formats.values():
            if ext in category:
                return category[ext]

        return {"processing": "generic", "priority": 999}

    def validate_environment(self) -> Dict[str, bool]:
        """Validate that required environment variables are set."""
        validation = {
            "mongodb_configured": bool(self.environment["mongodb_uri"]),
            "llm_configured": bool(self.environment["together_api_key"]),
            "upload_directory_exists": os.path.exists(self.environment["upload_directory"]),
            "multimodal_structure": os.path.exists(self.environment["multimodal_base"])
        }

        return validation

# Global configuration instance
mcp_config = MCPConfig()
