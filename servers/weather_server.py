"""
WeatherMapServer - MCP server for weather and map overlay operations.

This server provides tools for:
- Getting weather for a location
- Getting temperature at coordinates
- Weather overlay for map tiles
"""

import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx


class WeatherMapServer:
    """MCP server for weather and map overlay services."""
    
    def __init__(self):
        """Initialize the WeatherMapServer."""
        self.server = Server("weather-server")
        self._register_tools()
        # Using OpenWeatherMap API (free tier available)
        # For demo, we'll use mock data but provide real API structure
        self.use_mock = True  # Set to False to use real API (requires API key)
        self.api_key = None  # Set your OpenWeatherMap API key here if using real API
    
    def _register_tools(self):
        """Register all MCP tools for this server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            return [
                Tool(
                    name="get_weather",
                    description="Get current weather conditions for a location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location name or address (e.g., 'Beirut, Lebanon')"
                            }
                        },
                        "required": ["location"]
                    }
                ),
                Tool(
                    name="get_temperature",
                    description="Get temperature at specific coordinates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lat": {
                                "type": "number",
                                "description": "Latitude coordinate"
                            },
                            "lon": {
                                "type": "number",
                                "description": "Longitude coordinate"
                            }
                        },
                        "required": ["lat", "lon"]
                    }
                ),
                Tool(
                    name="weather_overlay",
                    description="Get weather overlay data for a map tile",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tile_x": {
                                "type": "integer",
                                "description": "Tile X coordinate"
                            },
                            "tile_y": {
                                "type": "integer",
                                "description": "Tile Y coordinate"
                            },
                            "zoom": {
                                "type": "integer",
                                "description": "Zoom level (0-18)"
                            }
                        },
                        "required": ["tile_x", "tile_y", "zoom"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_weather":
                    location = arguments.get("location")
                    if not location:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "Location parameter is required"}, indent=2)
                        )]
                    result = await self._get_weather(location)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "get_temperature":
                    lat = arguments.get("lat")
                    lon = arguments.get("lon")
                    if lat is None or lon is None:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "Lat and lon parameters are required"}, indent=2)
                        )]
                    result = await self._get_temperature(lat, lon)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "weather_overlay":
                    tile_x = arguments.get("tile_x")
                    tile_y = arguments.get("tile_y")
                    zoom = arguments.get("zoom")
                    if None in [tile_x, tile_y, zoom]:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "Tile_x, tile_y, and zoom parameters are required"}, indent=2)
                        )]
                    result = await self._weather_overlay(tile_x, tile_y, zoom)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    async def _get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather conditions for a location.
        
        Args:
            location: Location name or address
            
        Returns:
            Dictionary with weather information
        """
        try:
            if self.use_mock:
                # Mock weather data
                import random
                conditions = ["sunny", "cloudy", "rainy", "partly cloudy"]
                condition = random.choice(conditions)
                
                return {
                    "success": True,
                    "location": location,
                    "condition": condition,
                    "temperature_c": round(random.uniform(15, 30), 1),
                    "temperature_f": round(random.uniform(59, 86), 1),
                    "humidity": random.randint(40, 80),
                    "wind_speed_kmh": round(random.uniform(5, 25), 1),
                    "note": "Mock weather data - use real API for actual conditions"
                }
            else:
                # Real API implementation (requires API key)
                async with httpx.AsyncClient() as client:
                    # First geocode the location
                    geo_response = await client.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={"q": location, "format": "json", "limit": 1},
                        headers={"User-Agent": "WeatherServer-MCP/1.0"}
                    )
                    geo_data = geo_response.json()
                    
                    if not geo_data:
                        return {
                            "success": False,
                            "error": "Location not found",
                            "location": location
                        }
                    
                    lat = float(geo_data[0]["lat"])
                    lon = float(geo_data[0]["lon"])
                    
                    # Get weather
                    weather_response = await client.get(
                        "https://api.openweathermap.org/data/2.5/weather",
                        params={
                            "lat": lat,
                            "lon": lon,
                            "appid": self.api_key,
                            "units": "metric"
                        }
                    )
                    weather_response.raise_for_status()
                    weather_data = weather_response.json()
                    
                    return {
                        "success": True,
                        "location": location,
                        "condition": weather_data["weather"][0]["main"],
                        "description": weather_data["weather"][0]["description"],
                        "temperature_c": round(weather_data["main"]["temp"], 1),
                        "temperature_f": round(weather_data["main"]["temp"] * 9/5 + 32, 1),
                        "humidity": weather_data["main"]["humidity"],
                        "wind_speed_kmh": round(weather_data["wind"]["speed"] * 3.6, 1),
                        "pressure": weather_data["main"]["pressure"]
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Weather retrieval error: {str(e)}",
                "location": location
            }
    
    async def _get_temperature(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get temperature at specific coordinates.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Dictionary with temperature information
        """
        try:
            if self.use_mock:
                # Mock temperature data
                import random
                temp_c = round(random.uniform(10, 35), 1)
                
                return {
                    "success": True,
                    "lat": lat,
                    "lon": lon,
                    "temperature_c": temp_c,
                    "temperature_f": round(temp_c * 9/5 + 32, 1),
                    "note": "Mock temperature data - use real API for actual conditions"
                }
            else:
                # Real API implementation
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openweathermap.org/data/2.5/weather",
                        params={
                            "lat": lat,
                            "lon": lon,
                            "appid": self.api_key,
                            "units": "metric"
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    return {
                        "success": True,
                        "lat": lat,
                        "lon": lon,
                        "temperature_c": round(data["main"]["temp"], 1),
                        "temperature_f": round(data["main"]["temp"] * 9/5 + 32, 1),
                        "feels_like_c": round(data["main"]["feels_like"], 1),
                        "min_temp_c": round(data["main"]["temp_min"], 1),
                        "max_temp_c": round(data["main"]["temp_max"], 1)
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Temperature retrieval error: {str(e)}",
                "lat": lat,
                "lon": lon
            }
    
    async def _weather_overlay(self, tile_x: int, tile_y: int, zoom: int) -> Dict[str, Any]:
        """
        Get weather overlay data for a map tile.
        
        Args:
            tile_x: Tile X coordinate
            tile_y: Tile Y coordinate
            zoom: Zoom level
            
        Returns:
            Dictionary with weather overlay information
        """
        try:
            # Convert tile coordinates to lat/lon bounds
            def tile_to_latlon(tile_x, tile_y, zoom):
                n = 2.0 ** zoom
                lon_deg = tile_x / n * 360.0 - 180.0
                lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_y / n)))
                lat_deg = math.degrees(lat_rad)
                return lat_deg, lon_deg
            
            import math
            lat1, lon1 = tile_to_latlon(tile_x, tile_y, zoom)
            lat2, lon2 = tile_to_latlon(tile_x + 1, tile_y + 1, zoom)
            
            if self.use_mock:
                # Mock overlay data
                import random
                return {
                    "success": True,
                    "tile": {"x": tile_x, "y": tile_y, "zoom": zoom},
                    "bounds": {
                        "north": round(lat1, 6),
                        "south": round(lat2, 6),
                        "east": round(lon2, 6),
                        "west": round(lon1, 6)
                    },
                    "weather_data": {
                        "condition": random.choice(["clear", "cloudy", "rainy"]),
                        "temperature_avg": round(random.uniform(15, 30), 1),
                        "precipitation": random.choice([True, False])
                    },
                    "note": "Mock overlay data - use real API for actual weather tiles"
                }
            else:
                # Real API implementation would fetch weather tile data
                # This is a simplified version
                return {
                    "success": True,
                    "tile": {"x": tile_x, "y": tile_y, "zoom": zoom},
                    "bounds": {
                        "north": round(lat1, 6),
                        "south": round(lat2, 6),
                        "east": round(lon2, 6),
                        "west": round(lon1, 6)
                    },
                    "weather_data": {
                        "note": "Real weather overlay requires specialized weather tile service"
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Weather overlay error: {str(e)}",
                "tile": {"x": tile_x, "y": tile_y, "zoom": zoom}
            }
    
    async def run(self):
        """Run the server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="weather-server",
                    server_version="1.0.0"
                )
            )


if __name__ == "__main__":
    import asyncio
    server = WeatherMapServer()
    asyncio.run(server.run())

