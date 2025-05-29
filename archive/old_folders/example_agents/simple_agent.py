#!/usr/bin/env python3
"""
Example External Agent - Simple Python Class
Demonstrates how your existing agents can be connected without modification
"""

import json
from datetime import datetime
from typing import Dict, Any

class SimpleAgent:
    """
    Example of your existing agent that can be connected to MCP
    without any code modifications.
    """
    
    def __init__(self, agent_name: str = "SimpleAgent"):
        """Initialize the agent."""
        self.agent_name = agent_name
        self.capabilities = ["text processing", "simple analysis", "data formatting"]
        print(f"✅ {self.agent_name} initialized with capabilities: {self.capabilities}")
    
    def process(self, input_data: str) -> Dict[str, Any]:
        """
        Main processing method - this is what MCP will call.
        Your existing method signature doesn't need to change.
        """
        try:
            # Your existing processing logic
            result = self._analyze_text(input_data)
            
            return {
                'status': 'success',
                'agent': self.agent_name,
                'input': input_data,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'capabilities_used': ['text processing', 'analysis']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'agent': self.agent_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Your existing text analysis logic."""
        words = text.split()
        
        analysis = {
            'word_count': len(words),
            'character_count': len(text),
            'sentence_count': text.count('.') + text.count('!') + text.count('?'),
            'contains_question': '?' in text,
            'contains_exclamation': '!' in text,
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'summary': f"Text analysis: {len(words)} words, {len(text)} characters"
        }
        
        # Add sentiment analysis (simple)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        analysis['sentiment'] = sentiment
        analysis['positive_indicators'] = positive_count
        analysis['negative_indicators'] = negative_count
        
        return analysis
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status - optional method."""
        return {
            'agent': self.agent_name,
            'status': 'active',
            'capabilities': self.capabilities,
            'timestamp': datetime.now().isoformat()
        }

class DataProcessor:
    """
    Another example agent for data processing.
    """
    
    def __init__(self):
        self.name = "DataProcessor"
        print(f"✅ {self.name} initialized")
    
    def execute(self, data: Any) -> Dict[str, Any]:
        """
        Different method name - MCP will auto-detect this.
        """
        try:
            if isinstance(data, str):
                # Try to parse as JSON
                try:
                    parsed_data = json.loads(data)
                    result = self._process_json(parsed_data)
                except json.JSONDecodeError:
                    result = self._process_text(data)
            else:
                result = self._process_data(data)
            
            return {
                'status': 'success',
                'processor': self.name,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'processor': self.name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process JSON data."""
        return {
            'type': 'json_processing',
            'keys': list(data.keys()) if isinstance(data, dict) else [],
            'structure': type(data).__name__,
            'summary': f"Processed JSON with {len(data)} items" if isinstance(data, (dict, list)) else "Processed JSON data"
        }
    
    def _process_text(self, text: str) -> Dict[str, Any]:
        """Process text data."""
        return {
            'type': 'text_processing',
            'length': len(text),
            'lines': text.count('\n') + 1,
            'summary': f"Processed text with {len(text)} characters"
        }
    
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """Process other data types."""
        return {
            'type': 'data_processing',
            'data_type': type(data).__name__,
            'summary': f"Processed {type(data).__name__} data"
        }

# Example function-based agent
def quick_processor(input_text: str) -> Dict[str, Any]:
    """
    Example function that can be connected as an agent.
    No class needed - just a simple function.
    """
    try:
        # Quick processing logic
        result = {
            'processed_text': input_text.upper(),
            'reversed_text': input_text[::-1],
            'word_count': len(input_text.split()),
            'processing_type': 'quick_function'
        }
        
        return {
            'status': 'success',
            'function': 'quick_processor',
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'function': 'quick_processor',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Example with different parameter signature
def advanced_processor(input_data: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Function with context parameter - MCP will auto-detect signature.
    """
    try:
        context = context or {}
        
        # Use context if provided
        processing_mode = context.get('mode', 'standard')
        
        if processing_mode == 'detailed':
            result = {
                'detailed_analysis': True,
                'input_length': len(input_data),
                'input_type': type(input_data).__name__,
                'context_provided': bool(context),
                'processing_mode': processing_mode
            }
        else:
            result = {
                'simple_analysis': True,
                'processed': f"Processed: {input_data[:50]}..."
            }
        
        return {
            'status': 'success',
            'function': 'advanced_processor',
            'result': result,
            'context_used': context,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'function': 'advanced_processor',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test the agents locally
    print("🧪 Testing Example Agents")
    print("=" * 40)
    
    # Test SimpleAgent
    agent = SimpleAgent("TestAgent")
    result = agent.process("This is a great example of text processing!")
    print(f"SimpleAgent result: {json.dumps(result, indent=2)}")
    
    # Test DataProcessor
    processor = DataProcessor()
    result = processor.execute('{"test": "data", "count": 5}')
    print(f"DataProcessor result: {json.dumps(result, indent=2)}")
    
    # Test function agents
    result = quick_processor("Hello World")
    print(f"Quick processor result: {json.dumps(result, indent=2)}")
    
    result = advanced_processor("Advanced processing test", {"mode": "detailed"})
    print(f"Advanced processor result: {json.dumps(result, indent=2)}")
    
    print("✅ All example agents working correctly!")
