#!/usr/bin/env python3
"""
Weather Agent - Production Ready
Live agent for real-time weather data with full MCP compliance
"""

import os
import requests
import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
import sys
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
    "id": "weather_agent",
    "name": "Weather Agent",
    "version": "2.0.0",
    "author": "MCP System",
    "description": "Real-time weather data with OpenWeatherMap API integration",
    "category": "data",
    "status": "live",
    "dependencies": ["requests", "pymongo"],
    "auto_load": True,
    "priority": 2,
    "health_check_interval": 60,
    "max_failures": 5,
    "recovery_timeout": 120,
    "api_requirements": ["OPENWEATHER_API_KEY"]
}

class WeatherAgent(BaseMCPAgent):
    """Production-ready Weather Agent with enhanced capabilities."""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="realtime_weather",
                description="Fetch real-time weather data from OpenWeatherMap API",
                input_types=["text", "dict"],
                output_types=["dict"],
                methods=["process", "get_weather", "get_forecast", "info"],
                version="2.0.0"
            )
        ]

        super().__init__("weather_agent", "Weather Agent", capabilities)

        # Production configuration
        self.api_key = os.getenv('OPENWEATHER_API_KEY', '').strip()
        self.base_url = os.getenv('OPENWEATHER_BASE_URL', 'https://api.openweathermap.org/data/2.5').strip()
        self.units = os.getenv('WEATHER_UNITS', 'metric').strip()
        self.language = os.getenv('WEATHER_LANGUAGE', 'en').strip()
        self.request_timeout = 10
        self.cache_duration = 300  # 5 minutes
        self.failure_count = 0
        self.last_health_check = datetime.now()
        self.weather_cache = {}

        # Initialize MongoDB integration
        self.mongodb_integration = None
        if MONGODB_AVAILABLE:
            try:
                self.mongodb_integration = MCPMongoDBIntegration()
                asyncio.create_task(self._init_mongodb())
            except Exception as e:
                self.logger.error(f"Failed to initialize MongoDB: {e}")

        # City name patterns and corrections
        self.city_patterns = [
            r'weather\s+(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'(?:temperature|temp)\s+(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'forecast\s+(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'(?:what|how).*?weather.*?(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'weather.*?(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'([a-zA-Z\s,.-]+?)\s+weather(?:\s*\?*\s*$)',
            r'weather\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)'
        ]

        self.city_corrections = {
            'mumbai': 'Mumbai,IN', 'bombay': 'Mumbai,IN',
            'delhi': 'New Delhi,IN', 'new delhi': 'New Delhi,IN',
            'bangalore': 'Bangalore,IN', 'bengaluru': 'Bangalore,IN', 'banglore': 'Bangalore,IN',
            'chennai': 'Chennai,IN', 'madras': 'Chennai,IN',
            'kolkata': 'Kolkata,IN', 'calcutta': 'Kolkata,IN',
            'pune': 'Pune,IN', 'hyderabad': 'Hyderabad,IN'
        }

        # Validate API key
        if not self.api_key or len(self.api_key) < 10:
            self.logger.warning("OpenWeatherMap API key not found or invalid")
            self.failure_count += 1
        else:
            self.logger.info(f"Weather Agent initialized with API key: {self.api_key[:8]}...")

    async def _init_mongodb(self):
        """Initialize MongoDB connection."""
        if self.mongodb_integration:
            try:
                connected = await self.mongodb_integration.connect()
                if connected:
                    self.logger.info("Weather Agent connected to MongoDB")
                else:
                    self.logger.warning("Weather Agent failed to connect to MongoDB")
                    self.failure_count += 1
            except Exception as e:
                self.logger.error(f"Weather Agent MongoDB initialization error: {e}")
                self.failure_count += 1

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for production monitoring."""
        try:
            # Test API connectivity
            test_city = "London"
            api_status = "healthy"
            
            if self.api_key:
                try:
                    url = f"{self.base_url}/weather"
                    params = {
                        "q": test_city,
                        "appid": self.api_key,
                        "units": self.units
                    }
                    response = requests.get(url, params=params, timeout=5)
                    if response.status_code != 200:
                        api_status = "unhealthy"
                        self.failure_count += 1
                except:
                    api_status = "unhealthy"
                    self.failure_count += 1
            else:
                api_status = "no_api_key"

            health_status = {
                "agent_id": self.agent_id,
                "status": "healthy" if api_status == "healthy" else "unhealthy",
                "api_status": api_status,
                "api_key_configured": bool(self.api_key),
                "last_check": datetime.now().isoformat(),
                "failure_count": self.failure_count,
                "mongodb_connected": self.mongodb_integration is not None,
                "cache_entries": len(self.weather_cache),
                "uptime": (datetime.now() - self.last_health_check).total_seconds(),
                "version": AGENT_METADATA["version"]
            }

            self.last_health_check = datetime.now()

            # Reset failure count on successful health check
            if health_status["status"] == "healthy":
                self.failure_count = 0

            return health_status

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Weather health check failed: {e}")
            return {
                "agent_id": self.agent_id,
                "status": "unhealthy",
                "error": str(e),
                "failure_count": self.failure_count,
                "last_check": datetime.now().isoformat()
            }

    def extract_city_name(self, query: str) -> Optional[str]:
        """Extract city name from user query with improved accuracy."""
        query_lower = query.lower().strip()
        
        # Try each pattern
        for pattern in self.city_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                city = re.sub(r'[^\w\s,.-]', '', city)
                city = ' '.join(city.split())
                
                # Apply corrections if available
                if city.lower() in self.city_corrections:
                    return self.city_corrections[city.lower()]
                
                if city and len(city) > 1:
                    return city.title() if ',' not in city else city

        return None

    async def _store_weather_data(self, query: str, city: str, weather_data: Dict[str, Any], result: Dict[str, Any]):
        """Store weather data in MongoDB with enhanced error handling."""
        if self.mongodb_integration:
            try:
                # Primary storage method
                mongodb_id = await self.mongodb_integration.save_agent_output(
                    "weather_agent",
                    {"query": query, "city": city, "type": "weather_request"},
                    result,
                    {
                        "weather_data": weather_data,
                        "storage_type": "weather_data",
                        "api_source": "openweathermap",
                        "agent_version": AGENT_METADATA["version"]
                    }
                )
                self.logger.info(f"✅ Weather data stored in MongoDB: {mongodb_id}")
                
                # Also force store as backup
                await self.mongodb_integration.force_store_result(
                    "weather_agent",
                    query,
                    result
                )
                self.logger.info("✅ Weather data force stored as backup")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to store weather data: {e}")
                self.failure_count += 1
                
                # Try force storage as fallback
                try:
                    await self.mongodb_integration.force_store_result(
                        "weather_agent",
                        query,
                        result
                    )
                    self.logger.info("✅ Weather data fallback storage successful")
                except Exception as e2:
                    self.logger.error(f"❌ Weather data fallback storage failed: {e2}")
                    self.failure_count += 1

    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main process method with enhanced error handling."""
        try:
            params = message.params
            query = params.get("query", "") or params.get("text", "")

            if not query:
                return {
                    "status": "error",
                    "message": "No weather query provided",
                    "agent": self.agent_id,
                    "version": AGENT_METADATA["version"]
                }

            # Extract city name from query
            city = self.extract_city_name(query)

            if not city:
                return {
                    "status": "error",
                    "message": "Could not identify city name in query. Please specify a city clearly.",
                    "examples": [
                        "What is the weather in Mumbai?",
                        "Mumbai weather",
                        "Temperature in Delhi"
                    ],
                    "agent": self.agent_id
                }

            # Check cache first
            cache_key = f"{city.lower()}_{self.units}"
            if cache_key in self.weather_cache:
                cached_data = self.weather_cache[cache_key]
                if (datetime.now() - cached_data["timestamp"]).seconds < self.cache_duration:
                    self.logger.info(f"Returning cached weather data for {city}")
                    cached_data["data"]["cached"] = True
                    return cached_data["data"]

            # Get real-time weather data
            weather_data = await self.get_realtime_weather(city)

            if weather_data["status"] == "success":
                # Cache the result
                self.weather_cache[cache_key] = {
                    "data": weather_data,
                    "timestamp": datetime.now()
                }

                # Format the response
                formatted_response = self.format_weather_response(weather_data["data"], city, query)

                result = {
                    "status": "success",
                    "city": weather_data["data"]["city"],
                    "country": weather_data["data"]["country"],
                    "query": query,
                    "weather_data": weather_data["data"],
                    "formatted_response": formatted_response,
                    "data_source": "openweathermap_realtime",
                    "agent": self.agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "cached": False
                }

                # Store in MongoDB
                await self._store_weather_data(query, city, weather_data["data"], result)

                return result
            else:
                return weather_data

        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Error in weather agent process: {e}")
            return {
                "status": "error",
                "message": f"Weather processing failed: {str(e)}",
                "agent": self.agent_id,
                "failure_count": self.failure_count
            }

    async def get_realtime_weather(self, city: str) -> Dict[str, Any]:
        """Get real-time weather data from OpenWeatherMap API."""
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "message": "OpenWeatherMap API key not configured",
                    "agent": self.agent_id
                }

            # Build API URL
            url = f"{self.base_url}/weather"
            params = {
                "q": city,
                "appid": self.api_key,
                "units": self.units,
                "lang": self.language
            }

            self.logger.info(f"Fetching real-time weather for {city} from OpenWeatherMap...")

            # Make API request
            response = requests.get(url, params=params, timeout=self.request_timeout)

            if response.status_code == 200:
                data = response.json()

                # Parse weather data
                weather_info = {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": round(data["main"]["temp"], 1),
                    "feels_like": round(data["main"]["feels_like"], 1),
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "main": data["weather"][0]["main"],
                    "icon": data["weather"][0]["icon"],
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "wind_direction": data.get("wind", {}).get("deg", 0),
                    "visibility": round(data.get("visibility", 0) / 1000, 1),
                    "cloudiness": data["clouds"]["all"],
                    "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M"),
                    "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M"),
                    "timezone": data["timezone"],
                    "coordinates": {
                        "lat": data["coord"]["lat"],
                        "lon": data["coord"]["lon"]
                    },
                    "api_timestamp": datetime.fromtimestamp(data["dt"]).isoformat()
                }

                self.logger.info(f"Successfully retrieved weather for {weather_info['city']}, {weather_info['country']}")

                return {
                    "status": "success",
                    "data": weather_info,
                    "agent": self.agent_id
                }

            elif response.status_code == 404:
                return {
                    "status": "error",
                    "message": f"City '{city}' not found. Please check the spelling or try a different city name.",
                    "agent": self.agent_id
                }
            elif response.status_code == 401:
                self.failure_count += 1
                return {
                    "status": "error",
                    "message": "Invalid API key. Please check your OpenWeatherMap API key configuration.",
                    "agent": self.agent_id
                }
            else:
                self.failure_count += 1
                return {
                    "status": "error",
                    "message": f"Weather API error: {response.status_code}",
                    "agent": self.agent_id
                }

        except requests.exceptions.Timeout:
            self.failure_count += 1
            return {
                "status": "error",
                "message": "Weather API request timed out. Please try again.",
                "agent": self.agent_id
            }
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"Error fetching weather: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "agent": self.agent_id
            }

    def format_weather_response(self, weather_data: Dict[str, Any], city: str, query: str) -> str:
        """Format weather data into a human-readable response."""
        try:
            temp = weather_data["temperature"]
            feels_like = weather_data["feels_like"]
            description = weather_data["description"].title()
            humidity = weather_data["humidity"]
            wind_speed = weather_data["wind_speed"]

            unit = "°C" if self.units == "metric" else "°F"
            wind_unit = "m/s" if self.units == "metric" else "mph"

            response = f"🌤️ **Real-Time Weather in {weather_data['city']}, {weather_data['country']}**\n\n"
            response += f"🌡️ **Temperature:** {temp}{unit} (feels like {feels_like}{unit})\n"
            response += f"☁️ **Conditions:** {description}\n"
            response += f"💧 **Humidity:** {humidity}%\n"
            response += f"💨 **Wind Speed:** {wind_speed} {wind_unit}\n"
            response += f"🌅 **Sunrise:** {weather_data['sunrise']}\n"
            response += f"🌇 **Sunset:** {weather_data['sunset']}\n"
            response += f"\n📡 **Source:** OpenWeatherMap Real-Time API"

            return response

        except Exception as e:
            self.logger.error(f"Error formatting weather response: {e}")
            return f"Weather data received for {weather_data.get('city', city)}, but formatting failed."

    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request with production metadata."""
        return {
            "status": "success",
            "info": self.get_info(),
            "metadata": AGENT_METADATA,
            "health": await self.health_check(),
            "api_configured": bool(self.api_key),
            "cache_size": len(self.weather_cache),
            "supported_cities": "Worldwide (OpenWeatherMap database)",
            "agent": self.agent_id
        }

# Agent registration functions for auto-discovery
def get_agent_metadata():
    """Get agent metadata for auto-discovery."""
    return AGENT_METADATA

def create_agent():
    """Create and return the agent instance."""
    return WeatherAgent()

def get_agent_info():
    """Get agent information for compatibility."""
    return {
        "name": "Weather Agent",
        "description": "Production-ready real-time weather data with OpenWeatherMap API",
        "version": "2.0.0",
        "author": "MCP System",
        "capabilities": ["realtime_weather", "weather_forecasting", "global_cities"],
        "category": "data"
    }
