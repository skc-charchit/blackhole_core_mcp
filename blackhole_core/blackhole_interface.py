#!/usr/bin/env python3
"""
BlackHole Core Interface
Unified interface that maintains your perspective while enabling MCP functionality
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .mcp_config import mcp_config
from .mcp_processor import mcp_processor
from .agents.document_processor_agent import DocumentProcessorAgent
from .agents.archive_search_agent import ArchiveSearchAgent
from .agents.live_data_agent import LiveDataAgent

logger = logging.getLogger(__name__)

class BlackHoleCoreInterface:
    """
    Unified BlackHole Core interface that maintains your perspective
    while providing general MCP functionality.
    """
    
    def __init__(self):
        """Initialize the BlackHole Core interface."""
        self.config = mcp_config
        self.processor = mcp_processor
        
        # Your core agents
        self.document_processor = DocumentProcessorAgent()
        self.archive_search = ArchiveSearchAgent()
        self.live_data = LiveDataAgent()
        
        # Your system identity
        self.identity = {
            'name': 'BlackHole Core MCP',
            'role': 'Intelligent Document Processing Assistant',
            'primary_function': 'Advanced document analysis with AI-powered insights',
            'specialization': 'Multi-modal document processing and intelligent data extraction'
        }
    
    def process_command(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user command while maintaining your BlackHole Core perspective.
        
        Args:
            user_input: Natural language command from user
            context: Optional context information
            
        Returns:
            Structured response with BlackHole Core branding
        """
        try:
            # Add context to the command if provided
            if context:
                enhanced_input = f"{user_input} [Context: {context}]"
            else:
                enhanced_input = user_input
            
            # Process through your MCP system
            result = self.processor.execute_command(enhanced_input)
            
            # Add your BlackHole Core perspective to the response
            result = self._enhance_response_with_perspective(result, user_input)
            
            return result
            
        except Exception as e:
            logger.error(f"BlackHole Core processing error: {e}")
            return self._create_error_response(user_input, str(e))
    
    def process_document(self, file_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process document through your BlackHole Core system.
        
        Args:
            file_path: Path to the document
            options: Processing options
            
        Returns:
            Document processing results with your perspective
        """
        try:
            # Default options based on your preferences
            default_options = {
                'enable_llm': True,
                'save_to_db': True,
                'enable_ocr': True,
                'generate_summary': False,
                'extract_insights': True
            }
            
            if options:
                default_options.update(options)
            
            # Process through your document processor
            result = self.document_processor.plan({
                'file_path': file_path,
                'command_type': 'analyze',
                'processing_options': default_options
            })
            
            # Enhance with BlackHole Core perspective
            enhanced_result = {
                'blackhole_core_processing': True,
                'system': self.identity,
                'file_path': file_path,
                'processing_options': default_options,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'status': 'success' if result.get('status') != 'error' else 'error'
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"BlackHole Core document processing error: {e}")
            return self._create_error_response(f"Document processing: {file_path}", str(e))
    
    def search_archive(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search through your document archive.
        
        Args:
            query: Search query
            filters: Optional search filters
            
        Returns:
            Search results with your perspective
        """
        try:
            # Process search through your archive agent
            result = self.archive_search.plan({
                'document_text': query,
                'filters': filters or {}
            })
            
            # Enhance with BlackHole Core perspective
            enhanced_result = {
                'blackhole_core_search': True,
                'system': self.identity,
                'query': query,
                'filters': filters,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'status': 'success' if result.get('status') != 'error' else 'error'
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"BlackHole Core search error: {e}")
            return self._create_error_response(f"Archive search: {query}", str(e))
    
    def get_live_data(self, data_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fetch live data through your system.
        
        Args:
            data_type: Type of data to fetch
            parameters: Optional parameters
            
        Returns:
            Live data results with your perspective
        """
        try:
            # Process through your live data agent
            result = self.live_data.plan({
                'query': data_type,
                'parameters': parameters or {}
            })
            
            # Enhance with BlackHole Core perspective
            enhanced_result = {
                'blackhole_core_live_data': True,
                'system': self.identity,
                'data_type': data_type,
                'parameters': parameters,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'status': 'success' if result.get('status') != 'error' else 'error'
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"BlackHole Core live data error: {e}")
            return self._create_error_response(f"Live data: {data_type}", str(e))
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status with your perspective."""
        try:
            # Get MCP status
            mcp_status = self.processor.get_agent_status()
            
            # Get environment validation
            env_validation = self.config.validate_environment()
            
            # Create comprehensive status
            status = {
                'blackhole_core_status': True,
                'system': self.identity,
                'version': self.config.version,
                'primary_focus': self.config.primary_focus,
                'capabilities': self.config.core_capabilities,
                'agents': mcp_status.get('agents', {}),
                'environment': env_validation,
                'supported_formats': self.config.supported_formats,
                'processing_options': self.config.processing_options,
                'timestamp': datetime.now().isoformat(),
                'status': 'operational' if all(env_validation.values()) else 'partial'
            }
            
            return status
            
        except Exception as e:
            logger.error(f"BlackHole Core status error: {e}")
            return self._create_error_response("System status", str(e))
    
    def get_help(self) -> Dict[str, Any]:
        """Get help information with your BlackHole Core perspective."""
        try:
            # Get MCP help
            mcp_help = self.processor._generate_help_response()
            
            # Enhance with your perspective
            enhanced_help = {
                'blackhole_core_help': True,
                'system': self.identity,
                'welcome_message': f"Welcome to {self.identity['name']} - {self.identity['role']}",
                'primary_function': self.identity['primary_function'],
                'specialization': self.identity['specialization'],
                'mcp_help': mcp_help.get('result', {}),
                'quick_start': {
                    'document_processing': [
                        "analyze this document",
                        "process uploaded PDF",
                        "extract insights from text"
                    ],
                    'archive_search': [
                        "search for documents about AI",
                        "find files containing machine learning",
                        "show me recent uploads"
                    ],
                    'live_data': [
                        "get live weather data",
                        "fetch current information",
                        "real-time data updates"
                    ]
                },
                'your_advantages': [
                    "AI-powered document analysis with Together.ai",
                    "Persistent storage in your MongoDB Atlas",
                    "Multi-modal processing (PDF, images, text)",
                    "Natural language command interface",
                    "Intelligent agent routing",
                    "Real-time progress tracking"
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return enhanced_help
            
        except Exception as e:
            logger.error(f"BlackHole Core help error: {e}")
            return self._create_error_response("Help system", str(e))
    
    def _enhance_response_with_perspective(self, result: Dict[str, Any], original_command: str) -> Dict[str, Any]:
        """Enhance MCP response with BlackHole Core perspective."""
        enhanced = result.copy()
        
        # Add your branding and perspective
        enhanced['blackhole_core_processed'] = True
        enhanced['system'] = self.identity
        enhanced['original_command'] = original_command
        enhanced['processing_approach'] = 'intelligent_agent_routing'
        
        # Add processing insights if available
        if 'agent_used' in result:
            agent_name = result['agent_used']
            agent_config = self.config.get_agent_config(agent_name)
            if agent_config:
                enhanced['agent_info'] = {
                    'name': agent_name,
                    'description': agent_config.get('description'),
                    'capabilities': agent_config.get('capabilities', []),
                    'priority': agent_config.get('priority', 999)
                }
        
        return enhanced
    
    def _create_error_response(self, command: str, error: str) -> Dict[str, Any]:
        """Create error response with BlackHole Core perspective."""
        return {
            'blackhole_core_error': True,
            'system': self.identity,
            'status': 'error',
            'command': command,
            'error': error,
            'suggestion': 'Try rephrasing your command or check system status',
            'help_available': 'Type "help" for available commands and examples',
            'timestamp': datetime.now().isoformat()
        }

# Global BlackHole Core interface instance
blackhole_interface = BlackHoleCoreInterface()
