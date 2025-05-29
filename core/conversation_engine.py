#!/usr/bin/env python3
"""
Conversation Engine
Intelligent conversational AI with MongoDB search-first approach
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import re
import asyncio

from database.mongodb_manager import mongodb_manager

class ConversationEngine:
    """Intelligent conversation engine with MongoDB integration."""

    def __init__(self):
        self.logger = logging.getLogger("conversation_engine")
        self.mongodb = mongodb_manager

        # Conversation settings
        self.search_threshold = 0.7  # Similarity threshold for using cached responses
        self.max_context_length = 5  # Number of previous messages to consider
        self.enable_cache = True

        # Agent routing patterns
        self.agent_patterns = {
            'weather': [
                r'weather', r'temperature', r'rain', r'sunny', r'cloudy', r'forecast',
                r'climate', r'humidity', r'wind', r'storm', r'snow'
            ],
            'math': [
                r'calculate', r'math', r'percentage', r'multiply', r'divide', r'add',
                r'subtract', r'equation', r'formula', r'sum', r'average', r'square'
            ],
            'image_ocr': [
                r'extract text', r'read image', r'ocr', r'scan', r'image text',
                r'photo text', r'screenshot text', r'document scan'
            ],
            'document': [
                r'analyze document', r'pdf', r'document', r'summarize', r'extract',
                r'file analysis', r'text analysis', r'content analysis'
            ],
            'email': [
                r'send email', r'email', r'mail', r'notify', r'message',
                r'contact', r'inform', r'alert'
            ],
            'calendar': [
                r'remind', r'schedule', r'calendar', r'appointment', r'meeting',
                r'event', r'time', r'date', r'deadline'
            ]
        }

        self.logger.info("Conversation Engine initialized")

    async def process_query(self, user_id: str, session_id: str, query: str,
                          context: List[Dict] = None) -> Dict[str, Any]:
        """Process user query with MongoDB search-first approach."""
        try:
            self.logger.info(f"Processing query for user {user_id}: {query[:50]}...")

            # Step 1: Search MongoDB first
            mongodb_result = await self._search_mongodb_first(query, user_id)

            if mongodb_result:
                self.logger.info("Found relevant data in MongoDB")
                response = await self._generate_conversational_response(
                    query, mongodb_result, "mongodb_search"
                )

                # Store this interaction
                await self.mongodb.store_conversation(
                    user_id, session_id, query, response["message"],
                    "mongodb_search", {"source": "cached_data"}
                )

                return response

            # Step 2: Route to appropriate agent(s)
            self.logger.info("No relevant data found, routing to agents")
            agent_response = await self._route_to_agents(query, user_id, session_id)

            # Step 3: Store new data and response
            if agent_response.get("status") == "success":
                await self._store_agent_response(
                    user_id, session_id, query, agent_response
                )

            return agent_response

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "status": "error",
                "message": f"I encountered an error processing your request: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _search_mongodb_first(self, query: str, user_id: str) -> Optional[Dict]:
        """Search MongoDB for relevant existing data."""
        try:
            # Search conversations
            conversations = await self.mongodb.search_conversations(query, user_id, limit=5)

            # Search extracted data
            extracted_data = await self.mongodb.search_extracted_data(query, limit=5)

            # Check query cache
            query_hash = self._generate_query_hash(query)
            cached_response = await self.mongodb.get_cached_response(query_hash)

            if cached_response:
                return {
                    "type": "cached_response",
                    "data": cached_response,
                    "relevance": "high"
                }

            if conversations or extracted_data:
                return {
                    "type": "search_results",
                    "conversations": conversations,
                    "extracted_data": extracted_data,
                    "relevance": "medium"
                }

            return None

        except Exception as e:
            self.logger.error(f"Error searching MongoDB: {e}")
            return None

    async def _generate_conversational_response(self, query: str, mongodb_result: Dict,
                                              source: str) -> Dict[str, Any]:
        """Generate conversational response from MongoDB data."""
        try:
            if mongodb_result["type"] == "cached_response":
                cached = mongodb_result["data"]
                return {
                    "status": "success",
                    "message": f"Based on previous analysis: {cached['response'].get('message', 'No message available')}",
                    "source": "cached_data",
                    "agent_used": cached.get("agent_used", "unknown"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": True
                }

            elif mongodb_result["type"] == "search_results":
                # Combine relevant information
                response_parts = []

                # From conversations
                if mongodb_result.get("conversations"):
                    conv = mongodb_result["conversations"][0]  # Most recent
                    response_parts.append(f"From previous conversation: {conv['response'][:200]}...")

                # From extracted data
                if mongodb_result.get("extracted_data"):
                    data = mongodb_result["extracted_data"][0]  # Most relevant
                    response_parts.append(f"From extracted data: {data['extracted_text'][:200]}...")

                combined_response = "\n\n".join(response_parts)

                return {
                    "status": "success",
                    "message": f"Based on stored information:\n\n{combined_response}",
                    "source": "mongodb_search",
                    "agent_used": "conversation_engine",
                    "timestamp": datetime.utcnow().isoformat(),
                    "search_results": True
                }

        except Exception as e:
            self.logger.error(f"Error generating conversational response: {e}")
            return {
                "status": "error",
                "message": "I found some relevant information but couldn't process it properly.",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _route_to_agents(self, query: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Route query to appropriate agent(s)."""
        try:
            # Determine which agent(s) to use
            target_agents = self._identify_target_agents(query)

            if not target_agents:
                return {
                    "status": "error",
                    "message": "I'm not sure how to help with that request. Could you please rephrase or be more specific?",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # For now, use the first identified agent
            # TODO: Implement multi-agent coordination
            primary_agent = target_agents[0]

            self.logger.info(f"Routing to agent: {primary_agent}")

            # Import and call the appropriate agent
            agent_response = await self._call_agent(primary_agent, query, user_id, session_id)

            return agent_response

        except Exception as e:
            self.logger.error(f"Error routing to agents: {e}")
            return {
                "status": "error",
                "message": f"I encountered an error while processing your request: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _identify_target_agents(self, query: str) -> List[str]:
        """Identify which agents should handle the query."""
        query_lower = query.lower()
        target_agents = []

        # Enhanced multi-agent detection for complex queries
        for agent_type, patterns in self.agent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    if agent_type not in target_agents:
                        target_agents.append(agent_type)
                    break

        # Additional detection for complex queries
        if not target_agents:
            # Check for file extensions or specific indicators
            if any(ext in query_lower for ext in ['.pdf', '.png', '.jpg', '.jpeg', '.webp']):
                if 'text' in query_lower or 'extract' in query_lower:
                    target_agents.append('image_ocr')
                else:
                    target_agents.append('document')
            elif any(word in query_lower for word in ['calculate', 'math', '%', '+', '-', '*', '/']):
                target_agents.append('math')
            elif '@' in query and 'email' in query_lower:
                target_agents.append('email')

        # Special handling for multi-part queries
        if len(target_agents) > 1:
            self.logger.info(f"Multi-agent query detected: {target_agents}")

        return target_agents

    async def _call_agent(self, agent_type: str, query: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Call the specified agent."""
        try:
            # This is a placeholder for agent calling
            # In the actual implementation, you would import and call the specific agent

            if agent_type == "weather":
                return await self._call_weather_agent(query)
            elif agent_type == "math":
                return await self._call_math_agent(query)
            elif agent_type == "image_ocr":
                return await self._call_image_ocr_agent(query)
            elif agent_type == "document":
                return await self._call_document_agent(query)
            elif agent_type == "email":
                return await self._call_email_agent(query)
            elif agent_type == "calendar":
                return await self._call_calendar_agent(query)
            else:
                return {
                    "status": "error",
                    "message": f"Agent type '{agent_type}' not implemented yet.",
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Error calling agent {agent_type}: {e}")
            return {
                "status": "error",
                "message": f"Error calling {agent_type} agent: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    # Placeholder agent calling methods
    async def _call_weather_agent(self, query: str) -> Dict[str, Any]:
        """Call weather agent."""
        # TODO: Import and call actual weather agent
        return {
            "status": "success",
            "message": "Weather agent would be called here",
            "agent_used": "weather_agent",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _call_math_agent(self, query: str) -> Dict[str, Any]:
        """Call math agent."""
        # TODO: Import and call actual math agent
        return {
            "status": "success",
            "message": "Math agent would be called here",
            "agent_used": "math_agent",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _call_image_ocr_agent(self, query: str) -> Dict[str, Any]:
        """Call image OCR agent."""
        # TODO: Import and call actual OCR agent
        return {
            "status": "success",
            "message": "Image OCR agent would be called here",
            "agent_used": "image_ocr_agent",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _call_document_agent(self, query: str) -> Dict[str, Any]:
        """Call document agent."""
        # TODO: Import and call actual document agent
        return {
            "status": "success",
            "message": "Document agent would be called here",
            "agent_used": "document_agent",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _call_email_agent(self, query: str) -> Dict[str, Any]:
        """Call email agent."""
        # TODO: Import and call actual email agent
        return {
            "status": "success",
            "message": "Email agent would be called here",
            "agent_used": "email_agent",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _call_calendar_agent(self, query: str) -> Dict[str, Any]:
        """Call calendar agent."""
        # TODO: Import and call actual calendar agent
        return {
            "status": "success",
            "message": "Calendar agent would be called here",
            "agent_used": "calendar_agent",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _store_agent_response(self, user_id: str, session_id: str,
                                  query: str, response: Dict):
        """Store agent response in MongoDB."""
        try:
            # Store conversation
            await self.mongodb.store_conversation(
                user_id, session_id, query, response.get("message", ""),
                response.get("agent_used"), response
            )

            # Cache the response if successful
            if response.get("status") == "success" and self.enable_cache:
                query_hash = self._generate_query_hash(query)
                await self.mongodb.cache_query_response(
                    query_hash, query, response, response.get("agent_used", "unknown")
                )

            # Store extracted data if available
            if response.get("extracted_text"):
                await self.mongodb.store_extracted_data(
                    response.get("agent_used", "unknown"),
                    response.get("source_file", "unknown"),
                    response.get("source_type", "text"),
                    response["extracted_text"],
                    response
                )

        except Exception as e:
            self.logger.error(f"Error storing agent response: {e}")

    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for query caching."""
        # Normalize query for better cache hits
        normalized = re.sub(r'\s+', ' ', query.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()

    async def get_conversation_context(self, user_id: str, session_id: str) -> List[Dict]:
        """Get recent conversation context."""
        try:
            return await self.mongodb.get_conversation_history(
                user_id, session_id, limit=self.max_context_length
            )
        except Exception as e:
            self.logger.error(f"Error getting conversation context: {e}")
            return []

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get conversation engine statistics."""
        try:
            db_stats = await self.mongodb.get_database_stats()

            return {
                "database_stats": db_stats,
                "conversation_engine": {
                    "search_threshold": self.search_threshold,
                    "max_context_length": self.max_context_length,
                    "cache_enabled": self.enable_cache,
                    "supported_agents": list(self.agent_patterns.keys())
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}

# Global instance
conversation_engine = ConversationEngine()
