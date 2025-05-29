#!/usr/bin/env python3
"""
BlackHole Core Chat History Manager
Manages conversation history and context for better user experience
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid

from .data_source.mongodb import get_mongo_client

@dataclass
class ChatMessage:
    """Represents a single chat message."""
    id: str
    session_id: str
    user_message: str
    system_response: Dict[str, Any]
    timestamp: datetime
    response_type: str  # 'weather', 'search', 'document_analysis', etc.
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class ChatHistoryManager:
    """
    Manages conversation history and provides context-aware responses.
    """
    
    def __init__(self):
        """Initialize the chat history manager."""
        self.mongo_client = get_mongo_client()
        self.db = self.mongo_client["blackhole_db"]
        self.chat_collection = self.db["chat_history"]
        self.sessions_collection = self.db["chat_sessions"]
        
        # Create indexes for better performance
        try:
            self.chat_collection.create_index([("session_id", 1), ("timestamp", -1)])
            self.sessions_collection.create_index([("session_id", 1)])
        except Exception:
            pass  # Indexes might already exist
    
    def create_session(self, user_id: str = "default") -> str:
        """
        Create a new chat session.
        
        Args:
            user_id: User identifier
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0,
            'status': 'active'
        }
        
        try:
            self.sessions_collection.insert_one(session_data)
        except Exception as e:
            print(f"Error creating session: {e}")
        
        return session_id
    
    def add_message(self, session_id: str, user_message: str, system_response: Dict[str, Any], 
                   response_type: str = "general", processing_time_ms: int = 0) -> str:
        """
        Add a message to chat history.
        
        Args:
            session_id: Session identifier
            user_message: User's input message
            system_response: System's response
            response_type: Type of response (weather, search, etc.)
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        
        message = ChatMessage(
            id=message_id,
            session_id=session_id,
            user_message=user_message,
            system_response=system_response,
            timestamp=datetime.now(),
            response_type=response_type,
            processing_time_ms=processing_time_ms
        )
        
        try:
            # Store message
            self.chat_collection.insert_one(message.to_dict())
            
            # Update session
            self.sessions_collection.update_one(
                {'session_id': session_id},
                {
                    '$set': {'last_activity': datetime.now()},
                    '$inc': {'message_count': 1}
                }
            )
            
        except Exception as e:
            print(f"Error adding message: {e}")
        
        return message_id
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of chat messages
        """
        try:
            messages = list(
                self.chat_collection.find(
                    {'session_id': session_id}
                ).sort('timestamp', -1).limit(limit)
            )
            
            # Convert to chat format and reverse to chronological order
            chat_history = []
            for msg in reversed(messages):
                chat_history.append({
                    'id': msg['id'],
                    'user': msg['user_message'],
                    'assistant': self._format_response_for_chat(msg['system_response'], msg['response_type']),
                    'timestamp': msg['timestamp'],
                    'type': msg['response_type'],
                    'processing_time': msg.get('processing_time_ms', 0)
                })
            
            return chat_history
            
        except Exception as e:
            print(f"Error getting session history: {e}")
            return []
    
    def get_recent_context(self, session_id: str, context_window: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation context for better responses.
        
        Args:
            session_id: Session identifier
            context_window: Number of recent messages to include
            
        Returns:
            Recent conversation context
        """
        try:
            recent_messages = list(
                self.chat_collection.find(
                    {'session_id': session_id}
                ).sort('timestamp', -1).limit(context_window)
            )
            
            context = []
            for msg in reversed(recent_messages):
                context.append({
                    'user_message': msg['user_message'],
                    'response_type': msg['response_type'],
                    'timestamp': msg['timestamp']
                })
            
            return context
            
        except Exception as e:
            print(f"Error getting context: {e}")
            return []
    
    def search_history(self, session_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search through chat history.
        
        Args:
            session_id: Session identifier
            query: Search query
            limit: Maximum results to return
            
        Returns:
            Matching chat messages
        """
        try:
            # Simple text search in user messages and responses
            search_filter = {
                'session_id': session_id,
                '$or': [
                    {'user_message': {'$regex': query, '$options': 'i'}},
                    {'system_response.summary': {'$regex': query, '$options': 'i'}},
                    {'system_response.location': {'$regex': query, '$options': 'i'}}
                ]
            }
            
            results = list(
                self.chat_collection.find(search_filter)
                .sort('timestamp', -1)
                .limit(limit)
            )
            
            return [self._format_search_result(msg) for msg in results]
            
        except Exception as e:
            print(f"Error searching history: {e}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a chat session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics
        """
        try:
            # Get session info
            session = self.sessions_collection.find_one({'session_id': session_id})
            if not session:
                return {}
            
            # Get message statistics
            pipeline = [
                {'$match': {'session_id': session_id}},
                {'$group': {
                    '_id': '$response_type',
                    'count': {'$sum': 1},
                    'avg_processing_time': {'$avg': '$processing_time_ms'}
                }}
            ]
            
            type_stats = list(self.chat_collection.aggregate(pipeline))
            
            # Calculate total stats
            total_messages = sum(stat['count'] for stat in type_stats)
            avg_processing_time = sum(stat['avg_processing_time'] or 0 for stat in type_stats) / len(type_stats) if type_stats else 0
            
            return {
                'session_id': session_id,
                'created_at': session['created_at'],
                'last_activity': session['last_activity'],
                'total_messages': total_messages,
                'message_types': {stat['_id']: stat['count'] for stat in type_stats},
                'avg_processing_time_ms': round(avg_processing_time, 2),
                'session_duration': str(session['last_activity'] - session['created_at'])
            }
            
        except Exception as e:
            print(f"Error getting session stats: {e}")
            return {}
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Clean up old chat sessions.
        
        Args:
            days_old: Delete sessions older than this many days
            
        Returns:
            Number of sessions deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Get old sessions
            old_sessions = list(
                self.sessions_collection.find(
                    {'last_activity': {'$lt': cutoff_date}}
                )
            )
            
            session_ids = [session['session_id'] for session in old_sessions]
            
            if session_ids:
                # Delete messages
                self.chat_collection.delete_many({'session_id': {'$in': session_ids}})
                
                # Delete sessions
                result = self.sessions_collection.delete_many({'session_id': {'$in': session_ids}})
                
                return result.deleted_count
            
            return 0
            
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return 0
    
    def _format_response_for_chat(self, response: Dict[str, Any], response_type: str) -> str:
        """Format system response for chat display."""
        try:
            if response_type == 'weather':
                if 'summary' in response:
                    return response['summary']
                elif 'current' in response:
                    current = response['current']
                    location = response.get('location', 'Unknown')
                    temp = current.get('temperature', 'N/A')
                    condition = current.get('condition', 'N/A')
                    return f"Weather in {location}: {temp}, {condition}"
            
            elif response_type == 'search':
                count = response.get('results_count', 0)
                query = response.get('query', 'your search')
                return f"Found {count} results for '{query}'"
            
            elif response_type == 'document_analysis':
                return response.get('analysis', 'Document analyzed successfully')
            
            # Fallback
            return response.get('summary', str(response))
            
        except Exception:
            return "Response processed"
    
    def _format_search_result(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Format search result for display."""
        return {
            'id': message['id'],
            'user_message': message['user_message'],
            'response_summary': self._format_response_for_chat(message['system_response'], message['response_type']),
            'timestamp': message['timestamp'],
            'type': message['response_type']
        }

# Global chat history manager
chat_history = ChatHistoryManager()
