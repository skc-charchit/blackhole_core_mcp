#!/usr/bin/env python3
"""
BlackHole Core Response Formatter
Provides clean, focused responses without unnecessary details
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime

class ResponseFormatter:
    """
    Formats responses to be clean and focused on user's specific request.
    Removes unnecessary technical details and provides only relevant information.
    """

    def __init__(self):
        """Initialize the response formatter."""
        self.weather_keywords = ['weather', 'temperature', 'temp', 'climate', 'forecast']
        self.location_patterns = [
            r'weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)',
            r'temperature\s+(?:in|for|at)\s+([a-zA-Z\s]+)',
            r'(?:in|for|at)\s+([a-zA-Z\s]+)\s+weather',
        ]

    def format_weather_response(self, raw_response: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """
        Format weather response to show only essential weather information.

        Args:
            raw_response: Raw response from weather API
            user_query: Original user query

        Returns:
            Clean, focused weather response
        """
        try:
            # Extract location from user query
            location = self._extract_location(user_query)

            # Extract weather data from raw response
            weather_data = self._extract_weather_data(raw_response)

            if not weather_data:
                return {
                    'type': 'weather',
                    'location': location or 'Unknown',
                    'status': 'error',
                    'message': f"Sorry, I couldn't get weather data for {location or 'that location'}.",
                    'timestamp': datetime.now().isoformat()
                }

            # Create clean response
            clean_response = {
                'type': 'weather',
                'location': weather_data.get('location', location),
                'current': {
                    'temperature': weather_data.get('temperature'),
                    'condition': weather_data.get('condition'),
                    'humidity': weather_data.get('humidity'),
                    'wind_speed': weather_data.get('wind_speed'),
                    'feels_like': weather_data.get('feels_like')
                },
                'summary': self._create_weather_summary(weather_data),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }

            # Remove None values
            clean_response = self._remove_none_values(clean_response)

            return clean_response

        except Exception as e:
            return {
                'type': 'weather',
                'location': location or 'Unknown',
                'status': 'error',
                'message': f"Error getting weather data: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def format_search_response(self, raw_response: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """
        Format search response to show only relevant search results.

        Args:
            raw_response: Raw search response
            user_query: Original user query

        Returns:
            Clean, focused search response
        """
        try:
            # Extract search term
            search_term = self._extract_search_term(user_query)

            # Extract results from raw response
            results = self._extract_search_results(raw_response)

            clean_response = {
                'type': 'search',
                'query': search_term,
                'results_count': len(results),
                'results': results[:5],  # Limit to top 5 results
                'summary': f"Found {len(results)} documents related to '{search_term}'",
                'timestamp': datetime.now().isoformat(),
                'status': 'success' if results else 'no_results'
            }

            if not results:
                clean_response['message'] = f"No documents found for '{search_term}'. Try different keywords."

            return clean_response

        except Exception as e:
            return {
                'type': 'search',
                'query': search_term or user_query,
                'status': 'error',
                'message': f"Search error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def format_document_response(self, raw_response: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """
        Format document analysis response to show only key insights.

        Args:
            raw_response: Raw document processing response
            user_query: Original user query

        Returns:
            Clean, focused document response
        """
        try:
            # Extract key information
            analysis = self._extract_document_analysis(raw_response)

            clean_response = {
                'type': 'document_analysis',
                'analysis': analysis.get('summary', 'Document processed successfully'),
                'key_points': analysis.get('key_points', []),
                'word_count': analysis.get('word_count'),
                'processing_time': analysis.get('processing_time'),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }

            # Remove None values
            clean_response = self._remove_none_values(clean_response)

            return clean_response

        except Exception as e:
            return {
                'type': 'document_analysis',
                'status': 'error',
                'message': f"Document processing error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from user query."""
        query_lower = query.lower()

        for pattern in self.location_patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                return location.title()

        # Fallback: look for common location indicators
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in ['in', 'for', 'at'] and i + 1 < len(words):
                return words[i + 1].title()

        return None

    def _extract_weather_data(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weather data from raw API response."""
        try:
            # Handle different response formats
            if 'result' in raw_response and 'output' in raw_response['result']:
                weather_output = raw_response['result']['output']

                # Get the requested location from the agent response
                requested_location = raw_response['result'].get('location_requested', 'Unknown')

                if isinstance(weather_output, dict):
                    # Direct weather data
                    if 'current_condition' in weather_output:
                        current = weather_output['current_condition'][0]

                        # Use requested location instead of API location
                        actual_location = weather_output.get('nearest_area', [{}])[0].get('areaName', [{}])[0].get('value', requested_location)

                        return {
                            'location': requested_location,  # Use the location user asked for
                            'actual_location': actual_location,  # API's detected location
                            'temperature': f"{current.get('temp_C', 'N/A')}°C",
                            'condition': current.get('weatherDesc', [{}])[0].get('value', 'N/A'),
                            'humidity': f"{current.get('humidity', 'N/A')}%",
                            'wind_speed': f"{current.get('windspeedKmph', 'N/A')} km/h",
                            'feels_like': f"{current.get('FeelsLikeC', 'N/A')}°C"
                        }

                elif isinstance(weather_output, str):
                    # Parse string response
                    parsed_data = self._parse_weather_string(weather_output)
                    parsed_data['location'] = requested_location
                    return parsed_data

            return {}

        except Exception as e:
            print(f"Error extracting weather data: {e}")
            return {}

    def _parse_weather_string(self, weather_str: str) -> Dict[str, Any]:
        """Parse weather information from string response."""
        try:
            # Extract temperature
            temp_match = re.search(r'(\d+)°?[CF]', weather_str)
            temperature = f"{temp_match.group(1)}°C" if temp_match else "N/A"

            # Extract condition
            condition_patterns = [
                r'condition[:\s]+([^,\n]+)',
                r'weather[:\s]+([^,\n]+)',
                r'(sunny|cloudy|rainy|clear|overcast|partly cloudy)',
            ]

            condition = "N/A"
            for pattern in condition_patterns:
                match = re.search(pattern, weather_str, re.IGNORECASE)
                if match:
                    condition = match.group(1).strip()
                    break

            return {
                'temperature': temperature,
                'condition': condition,
                'humidity': 'N/A',
                'wind_speed': 'N/A'
            }

        except Exception:
            return {'temperature': 'N/A', 'condition': 'N/A'}

    def _create_weather_summary(self, weather_data: Dict[str, Any]) -> str:
        """Create a concise weather summary."""
        location = weather_data.get('location', 'the location')
        temp = weather_data.get('temperature', 'N/A')
        condition = weather_data.get('condition', 'N/A')

        return f"Current weather in {location}: {temp}, {condition}"

    def _extract_search_term(self, query: str) -> str:
        """Extract search term from user query."""
        # Remove common search prefixes
        search_patterns = [
            r'search\s+for\s+(.+)',
            r'find\s+(.+)',
            r'look\s+for\s+(.+)',
            r'show\s+me\s+(.+)',
        ]

        for pattern in search_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return query.strip()

    def _extract_search_results(self, raw_response: Dict[str, Any]) -> list:
        """Extract search results from raw response."""
        try:
            if 'result' in raw_response and 'output' in raw_response['result']:
                output = raw_response['result']['output']

                if isinstance(output, list):
                    return output[:5]  # Limit to 5 results
                elif isinstance(output, str) and 'No matches found' not in output:
                    return [{'content': output}]

            return []

        except Exception:
            return []

    def _extract_document_analysis(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract document analysis from raw response."""
        try:
            if 'result' in raw_response:
                result = raw_response['result']

                analysis = {}

                if 'llm_analysis' in result:
                    analysis['summary'] = result['llm_analysis']

                if 'text_length' in result:
                    analysis['word_count'] = f"{result['text_length']} characters"

                if 'processing_time_ms' in raw_response:
                    analysis['processing_time'] = f"{raw_response['processing_time_ms']}ms"

                return analysis

            return {}

        except Exception:
            return {}

    def _remove_none_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove None values from dictionary."""
        if isinstance(data, dict):
            return {k: self._remove_none_values(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self._remove_none_values(item) for item in data if item is not None]
        else:
            return data

# Global formatter instance
response_formatter = ResponseFormatter()
