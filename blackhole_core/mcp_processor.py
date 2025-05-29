#!/usr/bin/env python3
"""
BlackHole Core MCP - Model Context Protocol Processor
Intelligent command processing and agent routing system
Maintains your perspective while enabling general MCP functionality
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from .mcp_config import mcp_config
from .response_formatter import response_formatter
from .chat_history import chat_history
from .universal_connector import universal_connector
from .agent_registry import agent_registry
from .agent_orchestrator import agent_orchestrator
from .backend_agent_manager import backend_agent_manager
from .agents.archive_search_agent import ArchiveSearchAgent
from .agents.live_data_agent import LiveDataAgent
from .agents.document_processor_agent import DocumentProcessorAgent
from .data_source.mongodb import get_mongo_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPProcessor:
    """
    BlackHole Core MCP Processor
    Routes user commands to appropriate agents using your configuration
    Maintains your perspective while enabling general MCP functionality
    """

    def __init__(self):
        """Initialize the MCP processor with your agents and configuration."""

        # Your agent architecture (prioritized by your needs)
        self.agents = {
            'document_processor': DocumentProcessorAgent(),  # Your primary focus
            'archive_search': ArchiveSearchAgent(),         # Your data retrieval
            'live_data': LiveDataAgent(),                   # Your external integration
        }

        # Use your command patterns from configuration
        self.command_patterns = mcp_config.get_command_patterns()

        # Your system information
        self.system_info = {
            'name': mcp_config.system_name,
            'description': mcp_config.system_description,
            'version': mcp_config.version,
            'primary_focus': mcp_config.primary_focus,
            'capabilities': mcp_config.core_capabilities
        }

        # MongoDB client for logging
        self.mongo_client = get_mongo_client()
        self.db = self.mongo_client["blackhole_db"]
        self.commands_collection = self.db["mcp_commands"]

        # Initialize external agents through universal connector
        self._initialize_external_agents()

        # Load backend agents automatically
        self._initialize_backend_agents()

    def _initialize_external_agents(self) -> None:
        """Initialize external agents through the universal connector."""
        try:
            # Get enabled agent configurations
            enabled_agents = agent_registry.get_enabled_agents()

            for agent_id, config in enabled_agents.items():
                success = universal_connector.register_agent(config)
                if success:
                    logger.info(f"Successfully connected external agent: {agent_id}")
                else:
                    logger.warning(f"Failed to connect external agent: {agent_id}")

        except Exception as e:
            logger.error(f"Error initializing external agents: {e}")

    def _initialize_backend_agents(self) -> None:
        """Initialize backend agents automatically."""
        try:
            logger.info("Initializing backend agents for inter-agent collaboration...")
            result = backend_agent_manager.load_backend_agents()

            logger.info(f"Backend agents loaded: {result['connected']} connected, {result['failed']} failed")

            # Log collaboration capabilities
            capabilities = backend_agent_manager.get_collaboration_capabilities()
            logger.info(f"Collaboration capabilities available from {len(capabilities)} agents")

        except Exception as e:
            logger.error(f"Error initializing backend agents: {e}")

    def parse_command(self, user_input: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Parse user command and determine the appropriate agent and parameters.

        Returns:
            Tuple of (agent_name, command_type, parameters)
        """
        user_input = user_input.strip().lower()

        # Check each command pattern
        for command_type, config in self.command_patterns.items():
            for pattern in config['patterns']:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    # Extract parameters from the match
                    params = {
                        'query': match.group(1) if match.groups() else user_input,
                        'original_input': user_input,
                        'command_type': command_type
                    }
                    return config['agent'], command_type, params

        # Default to archive search if no pattern matches
        return 'archive_search', 'search', {
            'query': user_input,
            'original_input': user_input,
            'command_type': 'general'
        }

    def execute_command(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """
        Execute a user command with collaborative agent support and clean responses.

        Args:
            user_input: The user's command/query
            session_id: Optional session ID for chat history

        Returns:
            Clean, focused response from single agent or collaborative agents
        """
        start_time = datetime.now()

        try:
            # Create session if not provided
            if not session_id:
                session_id = chat_history.create_session()

            logger.info(f"Processing command: '{user_input}'")

            # Check if this requires collaborative processing
            collaborative_response = self._try_collaborative_processing(user_input, session_id)

            if collaborative_response:
                # Collaborative agents handled the request
                processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                # Add processing time to response
                collaborative_response['processing_time_ms'] = processing_time_ms
                collaborative_response['session_id'] = session_id

                # Add to chat history
                chat_history.add_message(
                    session_id, user_input, collaborative_response, 'collaborative', processing_time_ms
                )

                return collaborative_response

            # Fall back to single agent processing
            return self._execute_single_agent_command(user_input, session_id, start_time)

        except Exception as e:
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            error_response = {
                'type': 'error',
                'status': 'error',
                'message': f'Error processing command: {str(e)}',
                'command': user_input,
                'session_id': session_id or 'unknown',
                'processing_time_ms': processing_time_ms,
                'timestamp': datetime.now().isoformat()
            }

            # Add to chat history if session exists
            if session_id:
                chat_history.add_message(session_id, user_input, error_response, 'error', processing_time_ms)

            self._log_command(user_input, error_response)
            return error_response

    def _try_collaborative_processing(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """Try to process the request using collaborative agents."""
        try:
            # Check if collaborative processing is beneficial
            import asyncio

            # Run the collaborative processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                collaborative_result = loop.run_until_complete(
                    agent_orchestrator.process_collaborative_request(
                        user_input, {'session_id': session_id}
                    )
                )
            finally:
                loop.close()

            # Check if collaboration was actually used
            if collaborative_result.get('collaboration_used', False):
                return {
                    'type': 'collaborative',
                    'status': 'success',
                    'collaboration_info': {
                        'agents_involved': collaborative_result.get('agents_involved', []),
                        'workflow_id': collaborative_result.get('workflow_id'),
                        'processing_approach': collaborative_result.get('processing_approach')
                    },
                    'result': collaborative_result.get('result', {}),
                    'summary': self._create_collaboration_summary(collaborative_result),
                    'timestamp': datetime.now().isoformat()
                }

            return None  # No collaboration needed

        except Exception as e:
            logger.warning(f"Collaborative processing failed, falling back to single agent: {e}")
            return None

    def _execute_single_agent_command(self, user_input: str, session_id: str, start_time: datetime) -> Dict[str, Any]:
        """Execute command using single agent (original logic)."""
        # Parse the command
        agent_name, command_type, params = self.parse_command(user_input)

        logger.info(f"Single agent processing: Agent: {agent_name}, Type: {command_type}")

        # Handle special commands
        if agent_name == 'help':
            help_response = self._generate_help_response()

            # Add to chat history
            chat_history.add_message(
                session_id, user_input, help_response, 'help',
                int((datetime.now() - start_time).total_seconds() * 1000)
            )

            return help_response

        # Execute through appropriate agent
        if agent_name in self.agents:
            # Internal agent execution
            agent = self.agents[agent_name]

            # Prepare agent input based on command type
            if command_type == 'search' or command_type == 'archive_search':
                agent_input = {'document_text': params['query']}
            elif command_type == 'live_data':
                agent_input = {'query': params['query']}
            elif command_type == 'document_processing':
                agent_input = {'document_text': params['query']}
            else:
                agent_input = {'document_text': params['query']}

            # Execute agent
            raw_result = agent.plan(agent_input)

            # Calculate processing time
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Create raw response for logging
            raw_response = {
                'status': 'success',
                'command': user_input,
                'command_type': command_type,
                'agent_used': agent_name,
                'result': raw_result,
                'timestamp': datetime.now().isoformat(),
                'processing_time_ms': processing_time_ms
            }

            # Format response based on command type
            if command_type == 'live_data' and any(word in user_input.lower() for word in ['weather', 'temperature', 'climate']):
                clean_response = response_formatter.format_weather_response(raw_response, user_input)
                response_type = 'weather'
            elif command_type == 'search' or command_type == 'archive_search':
                clean_response = response_formatter.format_search_response(raw_response, user_input)
                response_type = 'search'
            elif command_type == 'document_processing':
                clean_response = response_formatter.format_document_response(raw_response, user_input)
                response_type = 'document_analysis'
            else:
                # Default clean response
                clean_response = {
                    'type': 'general',
                    'response': raw_result.get('output', 'Command processed successfully'),
                    'agent_used': agent_name,
                    'processing_time_ms': processing_time_ms,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                }
                response_type = 'general'

            # Add session info
            clean_response['session_id'] = session_id

            # Add to chat history
            chat_history.add_message(
                session_id, user_input, clean_response, response_type, processing_time_ms
            )

            # Log the command execution (raw response)
            self._log_command(user_input, raw_response)

            return clean_response

        else:
            # Try external agents through universal connector
            external_response = universal_connector.route_request(user_input, {'session_id': session_id})

            if external_response.get('status') == 'success':
                # External agent handled the request
                processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                # Format external response
                clean_response = {
                    'type': 'external_agent',
                    'result': external_response.get('result'),
                    'agent_used': external_response.get('routing_info', {}).get('selected_agent', 'external'),
                    'routing_info': external_response.get('routing_info', {}),
                    'processing_time_ms': processing_time_ms,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'session_id': session_id
                }

                # Add to chat history
                chat_history.add_message(
                    session_id, user_input, clean_response, 'external_agent', processing_time_ms
                )

                # Log the command execution
                self._log_command(user_input, external_response)

                return clean_response

            else:
                # No agent could handle the request
                error_response = {
                    'type': 'error',
                    'status': 'error',
                    'message': f'No agent available to handle: {user_input}',
                    'command': user_input,
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat(),
                    'available_agents': list(self.agents.keys()) + list(universal_connector.connected_agents.keys())
                }

                # Add to chat history
                chat_history.add_message(session_id, user_input, error_response, 'error')

                return error_response

    def _create_collaboration_summary(self, collaborative_result: Dict[str, Any]) -> str:
        """Create a summary of the collaboration process."""
        try:
            result_data = collaborative_result.get('result', {})
            agents_involved = collaborative_result.get('agents_involved', [])

            if 'collaboration_summary' in result_data:
                return result_data['collaboration_summary']

            # Create default summary
            agent_count = len(agents_involved)
            if agent_count > 1:
                return f"Collaborative response from {agent_count} agents: {', '.join(agents_involved)}"
            else:
                return f"Processed by agent: {agents_involved[0] if agents_involved else 'unknown'}"

        except Exception as e:
            logger.warning(f"Error creating collaboration summary: {e}")
            return "Collaborative processing completed"

    def _generate_help_response(self) -> Dict[str, Any]:
        """Generate help response reflecting your BlackHole Core perspective."""
        commands_help = []

        # Prioritize commands based on your focus
        priority_order = ['document_processing', 'archive_search', 'live_data', 'help']

        for command_type in priority_order:
            if command_type in self.command_patterns and command_type != 'help':
                config = self.command_patterns[command_type]
                examples = config.get('examples', config['patterns'][:2])
                commands_help.append({
                    'command': command_type,
                    'description': config['description'],
                    'examples': examples,
                    'agent': config['agent'],
                    'priority': priority_order.index(command_type) + 1
                })

        return {
            'status': 'success',
            'command': 'help',
            'result': {
                'system': self.system_info,
                'message': f'{self.system_info["name"]} - Your Intelligent Document Processing Assistant',
                'primary_focus': 'Document processing and analysis with AI-powered insights',
                'commands': commands_help,
                'usage': 'Describe what you want in natural language - I understand your intent and route to the right expert.',
                'your_capabilities': self.system_info['capabilities'],
                'examples': [
                    'analyze this document about machine learning',
                    'search for documents about artificial intelligence',
                    'process this PDF with LLM analysis',
                    'get live weather data for research',
                    'extract insights from uploaded files'
                ],
                'supported_formats': list(mcp_config.supported_formats.keys()),
                'processing_options': list(mcp_config.processing_options.keys())
            },
            'timestamp': datetime.now().isoformat()
        }

    def _log_command(self, command: str, response: Dict[str, Any]) -> None:
        """Log command execution to MongoDB."""
        try:
            log_entry = {
                'command': command,
                'response': response,
                'timestamp': datetime.now(),
                'session_id': None  # Can be enhanced with session tracking
            }
            self.commands_collection.insert_one(log_entry)
        except Exception as e:
            logger.warning(f"Failed to log command: {e}")

    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history."""
        try:
            history = list(self.commands_collection.find(
                {},
                {'_id': 0}
            ).sort('timestamp', -1).limit(limit))
            return history
        except Exception as e:
            logger.error(f"Failed to get command history: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all available agents."""
        status = {}

        for agent_name, agent in self.agents.items():
            try:
                # Test agent with a simple query
                test_result = agent.plan({'document_text': 'test'})
                status[agent_name] = {
                    'status': 'available',
                    'class': agent.__class__.__name__,
                    'test_successful': True
                }
            except Exception as e:
                status[agent_name] = {
                    'status': 'error',
                    'class': agent.__class__.__name__,
                    'error': str(e),
                    'test_successful': False
                }

        return {
            'total_agents': len(self.agents),
            'available_agents': len([s for s in status.values() if s['status'] == 'available']),
            'agents': status,
            'timestamp': datetime.now().isoformat()
        }

# Global MCP processor instance
mcp_processor = MCPProcessor()

def process_user_command(command: str) -> Dict[str, Any]:
    """
    Main entry point for processing user commands.

    Args:
        command: User's natural language command

    Returns:
        Structured response from the appropriate agent
    """
    return mcp_processor.execute_command(command)
