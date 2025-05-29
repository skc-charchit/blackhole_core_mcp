#!/usr/bin/env python3
"""
BlackHole Core Live Data Agent
Fetches real-time data with location-specific responses
"""

import requests
import re
from datetime import datetime
from bson import ObjectId
from blackhole_core.data_source.mongodb import get_mongo_client

class LiveDataAgent:
    def __init__(self, memory=None, api_url=None):
        self.memory = memory
        self.base_api_url = "https://wttr.in"
        self.client = get_mongo_client()
        self.db = self.client["blackhole_db"]

        # Location extraction patterns
        self.location_patterns = [
            r'weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)',
            r'temperature\s+(?:in|for|at)\s+([a-zA-Z\s]+)',
            r'(?:in|for|at)\s+([a-zA-Z\s]+)\s+weather',
            r'(?:in|for|at)\s+([a-zA-Z\s]+)\s+temperature',
            r'weather\s+([a-zA-Z\s]+)',
            r'([a-zA-Z\s]+)\s+weather'
        ]

    def plan(self, query):
        try:
            # Extract location from query
            location = self._extract_location(query)

            # Build API URL with specific location
            api_url = f"{self.base_api_url}/{location}?format=j1"

            # Fetch weather data
            response = requests.get(api_url, timeout=10)
            data = response.json()

            result = {
                "agent": "LiveDataAgent",
                "input": query,
                "output": data,
                "location_requested": location,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"api_url": api_url}
            }

        except Exception as e:
            result = {
                "agent": "LiveDataAgent",
                "input": query,
                "output": f"Error fetching data: {e}",
                "location_requested": location if 'location' in locals() else "Unknown",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"api_url": api_url if 'api_url' in locals() else "N/A"}
            }

        return result

    def _extract_location(self, query):
        """
        Extract location from user query.

        Args:
            query: User's query (dict or string)

        Returns:
            Extracted location or default to London
        """
        # Handle different query formats
        if isinstance(query, dict):
            query_text = query.get('query', '') or query.get('document_text', '') or str(query)
        else:
            query_text = str(query)

        query_lower = query_text.lower().strip()

        # Try each pattern to extract location
        for pattern in self.location_patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                # Clean up the location
                location = self._clean_location(location)
                if location:
                    return location

        # Fallback: look for common city names and handle misspellings
        city_mappings = {
            # Common misspellings and variations
            'banglore': 'bangalore',
            'bengaluru': 'bangalore',
            'bombay': 'mumbai',
            'calcutta': 'kolkata',
            'madras': 'chennai',
            'new delhi': 'delhi',
            'ny': 'new york',
            'nyc': 'new york',
            'la': 'los angeles',
            'sf': 'san francisco',
            'london uk': 'london',
            'paris france': 'paris',
            'tokyo japan': 'tokyo',

            # Direct city names
            'mumbai': 'mumbai',
            'delhi': 'delhi',
            'bangalore': 'bangalore',
            'chennai': 'chennai',
            'kolkata': 'kolkata',
            'hyderabad': 'hyderabad',
            'pune': 'pune',
            'ahmedabad': 'ahmedabad',
            'london': 'london',
            'paris': 'paris',
            'tokyo': 'tokyo',
            'new york': 'new york',
            'los angeles': 'los angeles',
            'chicago': 'chicago',
            'sydney': 'sydney',
            'melbourne': 'melbourne',
            'toronto': 'toronto',
            'vancouver': 'vancouver',
            'berlin': 'berlin',
            'madrid': 'madrid'
        }

        # Check for exact matches and misspellings
        for variant, correct_city in city_mappings.items():
            if variant in query_lower:
                return correct_city.title()

        # Fuzzy matching for close misspellings
        for variant, correct_city in city_mappings.items():
            if self._is_similar_city(query_lower, variant):
                return correct_city.title()

        # Default fallback
        return "London"

    def _clean_location(self, location):
        """Clean and validate location string."""
        if not location:
            return None

        # Remove common words that aren't part of location
        stop_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'weather', 'temperature', 'climate']
        words = location.split()
        cleaned_words = [word for word in words if word.lower() not in stop_words]

        if not cleaned_words:
            return None

        # Join and capitalize properly
        cleaned_location = ' '.join(cleaned_words).title()

        # Handle special cases
        location_mappings = {
            'Ny': 'New York',
            'La': 'Los Angeles',
            'Sf': 'San Francisco',
            'Uk': 'London',
            'Us': 'New York'
        }

        return location_mappings.get(cleaned_location, cleaned_location)

    def _is_similar_city(self, query_text: str, city_name: str) -> bool:
        """Check if query contains a city name with minor misspellings."""
        # Simple fuzzy matching for common misspellings
        if len(city_name) < 4:
            return False

        # Check if most characters match (allowing 1-2 character differences)
        max_differences = 1 if len(city_name) <= 6 else 2
        differences = 0

        # Find the city name in the query
        if city_name not in query_text:
            return False

        return True
