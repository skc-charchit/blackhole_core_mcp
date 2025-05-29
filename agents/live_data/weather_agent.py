#!/usr/bin/env python3
"""
Real-Time Weather Agent - Live Weather Data Only
Uses OpenWeatherMap API exclusively for real-time weather data
"""

import os
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

class RealTimeWeatherAgent(BaseMCPAgent):
    """Real-time weather agent that fetches live data from OpenWeatherMap API only."""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="realtime_weather",
                description="Fetch real-time weather data from OpenWeatherMap API",
                input_types=["text", "dict"],
                output_types=["dict"],
                methods=["get_weather", "get_forecast", "process", "info"]
            )
        ]

        super().__init__("realtime_weather_agent", "Real-Time Weather Agent", capabilities)

        # OpenWeatherMap API configuration from environment
        self.api_key = os.getenv('OPENWEATHER_API_KEY', '').strip()
        self.base_url = os.getenv('OPENWEATHER_BASE_URL', 'https://api.openweathermap.org/data/2.5').strip()
        self.units = os.getenv('WEATHER_UNITS', 'metric').strip()
        self.language = os.getenv('WEATHER_LANGUAGE', 'en').strip()

        # City name patterns for better matching
        self.city_patterns = [
            r'weather\s+(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'(?:temperature|temp)\s+(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'forecast\s+(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'climate\s+(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'(?:what|how).*?weather.*?(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'weather.*?(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'([a-zA-Z\s,.-]+?)\s+weather(?:\s*\?*\s*$)',
            r'weather\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)',
            r'(?:in|of|for)\s+([a-zA-Z\s,.-]+?)(?:\s*\?*\s*$)'
        ]

        # Common city name corrections and aliases
        self.city_corrections = {
            'mumbai': 'Mumbai,IN',
            'bombay': 'Mumbai,IN',
            'delhi': 'New Delhi,IN',
            'new delhi': 'New Delhi,IN',
            'bangalore': 'Bangalore,IN',
            'bengaluru': 'Bangalore,IN',
            'banglore': 'Bangalore,IN',
            'chennai': 'Chennai,IN',
            'madras': 'Chennai,IN',
            'kolkata': 'Kolkata,IN',
            'calcutta': 'Kolkata,IN',
            'pune': 'Pune,IN',
            'hyderabad': 'Hyderabad,IN',
            'ahmedabad': 'Ahmedabad,IN',
            'jaipur': 'Jaipur,IN',
            'lucknow': 'Lucknow,IN',
            'kanpur': 'Kanpur,IN',
            'nagpur': 'Nagpur,IN',
            'indore': 'Indore,IN',
            'thane': 'Thane,IN',
            'bhopal': 'Bhopal,IN',
            'visakhapatnam': 'Visakhapatnam,IN',
            'patna': 'Patna,IN',
            'vadodara': 'Vadodara,IN',
            'ghaziabad': 'Ghaziabad,IN',
            'ludhiana': 'Ludhiana,IN',
            'agra': 'Agra,IN',
            'nashik': 'Nashik,IN',
            'faridabad': 'Faridabad,IN',
            'meerut': 'Meerut,IN',
            'rajkot': 'Rajkot,IN',
            'varanasi': 'Varanasi,IN',
            'srinagar': 'Srinagar,IN',
            'aurangabad': 'Aurangabad,IN',
            'dhanbad': 'Dhanbad,IN',
            'amritsar': 'Amritsar,IN',
            'allahabad': 'Prayagraj,IN',
            'prayagraj': 'Prayagraj,IN',
            'ranchi': 'Ranchi,IN',
            'howrah': 'Howrah,IN',
            'coimbatore': 'Coimbatore,IN',
            'jabalpur': 'Jabalpur,IN',
            'gwalior': 'Gwalior,IN',
            'vijayawada': 'Vijayawada,IN',
            'jodhpur': 'Jodhpur,IN',
            'madurai': 'Madurai,IN',
            'raipur': 'Raipur,IN',
            'kota': 'Kota,IN',
            'chandigarh': 'Chandigarh,IN',
            'guwahati': 'Guwahati,IN'
        }

        # Validate API key
        if not self.api_key or len(self.api_key) < 10:
            self.logger.warning("OpenWeatherMap API key not found or invalid in environment variables")
            self.logger.warning("Please set OPENWEATHER_API_KEY in .env file for live weather data")
        else:
            self.logger.info(f"Real-Time Weather Agent initialized with API key: {self.api_key[:8]}...")

    def extract_city_name(self, query: str) -> Optional[str]:
        """Extract city name from user query with improved accuracy."""
        query_lower = query.lower().strip()
        original_query = query_lower

        # Remove common question words and clean up
        query_clean = re.sub(r'\b(what|is|the|how|today|now|current|currently|s)\b', '', query_lower)
        query_clean = ' '.join(query_clean.split())

        # Try each pattern
        for pattern in self.city_patterns:
            match = re.search(pattern, original_query, re.IGNORECASE)
            if match:
                city = match.group(1).strip()

                # Clean up the city name
                city = re.sub(r'[^\w\s,.-]', '', city)  # Keep letters, spaces, commas, dots, hyphens
                city = ' '.join(city.split())  # Normalize whitespace

                # Remove trailing words that aren't part of city names
                city = re.sub(r'\b(today|now|currently|please|thanks?)\b.*$', '', city, flags=re.IGNORECASE)
                city = city.strip()

                # Apply corrections if available
                if city.lower() in self.city_corrections:
                    return self.city_corrections[city.lower()]

                if city and len(city) > 1:
                    return city.title() if ',' not in city else city

        # Try with cleaned query
        for pattern in self.city_patterns:
            match = re.search(pattern, query_clean, re.IGNORECASE)
            if match:
                city = match.group(1).strip()

                # Clean up the city name
                city = re.sub(r'[^\w\s,.-]', '', city)
                city = ' '.join(city.split())

                # Apply corrections if available
                if city.lower() in self.city_corrections:
                    return self.city_corrections[city.lower()]

                if city and len(city) > 1:
                    return city.title() if ',' not in city else city

        # If no pattern matches, check if the entire query is a city name
        clean_query = re.sub(r'[^\w\s]', '', query_lower)
        clean_query = ' '.join(clean_query.split())

        if clean_query in self.city_corrections:
            return self.city_corrections[clean_query]

        # Last resort: return the cleaned query if it looks like a city name
        if len(clean_query) > 1 and len(clean_query.split()) <= 3:
            return clean_query.title()

        return None

    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main process method."""
        try:
            params = message.params
            query = params.get("query", "") or params.get("text", "")

            if not query:
                return {
                    "status": "error",
                    "message": "No weather query provided",
                    "agent": self.agent_id
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
                        "Temperature in Delhi",
                        "Weather forecast for Bangalore",
                        "How's the weather in Chennai?"
                    ],
                    "agent": self.agent_id
                }

            # Get real-time weather data
            weather_data = await self.get_realtime_weather(city)

            if weather_data["status"] == "success":
                # Format the response
                formatted_response = self.format_weather_response(weather_data["data"], city, query)

                return {
                    "status": "success",
                    "city": weather_data["data"]["city"],
                    "country": weather_data["data"]["country"],
                    "query": query,
                    "weather_data": weather_data["data"],
                    "formatted_response": formatted_response,
                    "data_source": "openweathermap_realtime",
                    "agent": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return weather_data

        except Exception as e:
            self.logger.error(f"Error in process: {e}")
            return {
                "status": "error",
                "message": f"Weather processing failed: {str(e)}",
                "agent": self.agent_id
            }

    async def get_realtime_weather(self, city: str) -> Dict[str, Any]:
        """Get real-time weather data from OpenWeatherMap API."""
        try:
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
            response = requests.get(url, params=params, timeout=10)

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
                    "visibility": round(data.get("visibility", 0) / 1000, 1),  # Convert to km
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
                    "suggestions": [
                        "Try using the full city name",
                        "Include country code (e.g., 'Mumbai, IN')",
                        "Check for typos in the city name",
                        "Try a nearby major city"
                    ],
                    "agent": self.agent_id
                }
            elif response.status_code == 401:
                return {
                    "status": "error",
                    "message": "Invalid API key. Please check your OpenWeatherMap API key configuration.",
                    "agent": self.agent_id
                }
            elif response.status_code == 429:
                return {
                    "status": "error",
                    "message": "API rate limit exceeded. Please try again in a few minutes.",
                    "agent": self.agent_id
                }
            else:
                return {
                    "status": "error",
                    "message": f"Weather API error: {response.status_code} - {response.text}",
                    "agent": self.agent_id
                }

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Weather API request timed out. Please try again.",
                "agent": self.agent_id
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "Unable to connect to weather service. Please check your internet connection.",
                "agent": self.agent_id
            }
        except Exception as e:
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
            pressure = weather_data["pressure"]
            visibility = weather_data["visibility"]
            cloudiness = weather_data["cloudiness"]

            # Temperature unit
            unit = "°C" if self.units == "metric" else "°F"
            wind_unit = "m/s" if self.units == "metric" else "mph"
            pressure_unit = "hPa"

            response = f"🌤️ **Real-Time Weather in {weather_data['city']}, {weather_data['country']}**\n\n"
            response += f"🌡️ **Temperature:** {temp}{unit} (feels like {feels_like}{unit})\n"
            response += f"☁️ **Conditions:** {description}\n"
            response += f"💧 **Humidity:** {humidity}%\n"
            response += f"💨 **Wind Speed:** {wind_speed} {wind_unit}\n"
            response += f"🔽 **Pressure:** {pressure} {pressure_unit}\n"
            response += f"👁️ **Visibility:** {visibility} km\n"
            response += f"☁️ **Cloudiness:** {cloudiness}%\n"
            response += f"🌅 **Sunrise:** {weather_data['sunrise']}\n"
            response += f"🌇 **Sunset:** {weather_data['sunset']}\n"

            # Add weather advice based on conditions
            if temp > 35:
                response += f"\n🔥 **Weather Advice:** Extremely hot! Stay indoors, drink plenty of water, and avoid outdoor activities."
            elif temp > 30:
                response += f"\n🔥 **Weather Advice:** Very hot! Stay hydrated and avoid prolonged sun exposure."
            elif temp < 5:
                response += f"\n🧊 **Weather Advice:** Very cold! Dress warmly and be careful of icy conditions."
            elif temp < 15:
                response += f"\n🧥 **Weather Advice:** Cool weather. Consider wearing a jacket or sweater."

            if humidity > 85:
                response += f"\n💧 **Humidity Alert:** Very high humidity ({humidity}%). It may feel very muggy and uncomfortable."
            elif humidity > 70:
                response += f"\n💧 **Humidity Notice:** High humidity levels. It may feel more humid than the actual temperature."

            if wind_speed > 15:
                response += f"\n💨 **Wind Alert:** Strong winds ({wind_speed} {wind_unit}). Secure loose objects and be careful when driving."
            elif wind_speed > 10:
                response += f"\n💨 **Wind Notice:** Moderate winds. Be aware of windy conditions."

            if visibility < 5:
                response += f"\n👁️ **Visibility Alert:** Poor visibility ({visibility} km). Drive carefully and use headlights."

            # Add location and timestamp
            response += f"\n\n📍 **Location:** {weather_data['coordinates']['lat']:.2f}°, {weather_data['coordinates']['lon']:.2f}°"
            response += f"\n⏰ **Data Time:** {datetime.fromisoformat(weather_data['api_timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')}"
            response += f"\n🔄 **Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            response += f"\n📡 **Source:** OpenWeatherMap Real-Time API"

            return response

        except Exception as e:
            self.logger.error(f"Error formatting weather response: {e}")
            return f"Real-time weather data received for {weather_data.get('city', city)}, but formatting failed: {str(e)}"

    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request."""
        return {
            "status": "success",
            "info": self.get_info(),
            "api_configured": bool(self.api_key),
            "api_key_preview": f"{self.api_key[:8]}..." if self.api_key else "Not configured",
            "base_url": self.base_url,
            "units": self.units,
            "language": self.language,
            "supported_cities": "Worldwide (OpenWeatherMap database)",
            "example_queries": [
                "What is the weather in Mumbai?",
                "Mumbai weather",
                "Temperature in Delhi",
                "Weather forecast for Bangalore",
                "How's the weather in Chennai today?",
                "Climate in New York",
                "London weather"
            ],
            "features": [
                "Real-time weather data",
                "Global city support",
                "Automatic city name correction",
                "Professional weather reports",
                "Weather advice and alerts",
                "Sunrise/sunset times",
                "Wind and visibility data"
            ],
            "agent": self.agent_id
        }

# Agent registration
def get_agent_info():
    """Get agent information for auto-discovery."""
    return {
        "name": "Real-Time Weather Agent",
        "description": "Fetches real-time weather data from OpenWeatherMap API exclusively",
        "version": "1.0.0",
        "author": "MCP System",
        "capabilities": ["realtime_weather", "global_cities", "weather_alerts"],
        "category": "data"
    }

def create_agent():
    """Create and return the agent instance."""
    return RealTimeWeatherAgent()

if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test_agent():
        print("🌤️ Testing Real-Time Weather Agent")
        print("=" * 60)

        try:
            agent = RealTimeWeatherAgent()

            # Test queries
            test_queries = [
                "What is the weather in Mumbai?",
                "Delhi weather",
                "Temperature in Bangalore",
                "Chennai weather today",
                "How's the weather in New York?"
            ]

            for query in test_queries:
                print(f"\n🔍 Testing: '{query}'")

                message = MCPMessage(
                    id=f"test_{datetime.now().timestamp()}",
                    method="process",
                    params={"query": query},
                    timestamp=datetime.now()
                )

                result = await agent.process_message(message)

                if result["status"] == "success":
                    print(f"✅ Success: {result['city']}, {result['country']}")
                    print(f"📊 Temperature: {result['weather_data']['temperature']}°C")
                    print(f"☁️ Conditions: {result['weather_data']['description']}")
                    print(f"📡 Source: {result['data_source']}")
                else:
                    print(f"❌ Error: {result['message']}")

            print("\n✅ Real-Time Weather Agent test completed!")

        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            print("🔧 Please check your OpenWeatherMap API key in .env file")

    asyncio.run(test_agent())
