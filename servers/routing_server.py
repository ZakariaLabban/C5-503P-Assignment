"""
RoutingServer - MCP server for routing and navigation operations.

This server provides tools for:
- Getting routes between two points
- Calculating distances
- Finding fastest routes
"""

import json
import math
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx


class RoutingServer:
    """MCP server for routing and navigation services."""
    
    def __init__(self):
        """Initialize the RoutingServer."""
        self.server = Server("routing-server")
        # Store tools for testing
        self._tools = []
        self._register_tools()
        # Using OpenRouteService API (free tier available)
        # For demo purposes, we'll use a mock implementation with real API option
        self.ors_base = "https://api.openrouteservice.org/v2"
        self.use_mock = True  # Set to False to use real API (requires API key)
    
    def _register_tools(self):
        """Register all MCP tools for this server."""
        
        # Define tools
        tools_list = [
                Tool(
                    name="get_route",
                    description="Get a route between two points with waypoints and distance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_lat": {
                                "type": "number",
                                "description": "Starting point latitude"
                            },
                            "start_lon": {
                                "type": "number",
                                "description": "Starting point longitude"
                            },
                            "end_lat": {
                                "type": "number",
                                "description": "Destination latitude"
                            },
                            "end_lon": {
                                "type": "number",
                                "description": "Destination longitude"
                            }
                        },
                        "required": ["start_lat", "start_lon", "end_lat", "end_lon"]
                    }
                ),
                Tool(
                    name="get_distance",
                    description="Calculate the straight-line distance between two points",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_lat": {
                                "type": "number",
                                "description": "Starting point latitude"
                            },
                            "start_lon": {
                                "type": "number",
                                "description": "Starting point longitude"
                            },
                            "end_lat": {
                                "type": "number",
                                "description": "Destination latitude"
                            },
                            "end_lon": {
                                "type": "number",
                                "description": "Destination longitude"
                            }
                        },
                        "required": ["start_lat", "start_lon", "end_lat", "end_lon"]
                    }
                ),
                Tool(
                    name="fastest_route",
                    description="Find the fastest route between two points",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "string",
                                "description": "Starting address or 'lat,lon' coordinates"
                            },
                            "end": {
                                "type": "string",
                                "description": "Destination address or 'lat,lon' coordinates"
                            }
                        },
                        "required": ["start", "end"]
                    }
                )
        ]
        
        # Store tools for testing
        self._tools = tools_list
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            return tools_list
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_route":
                    start_lat = arguments.get("start_lat")
                    start_lon = arguments.get("start_lon")
                    end_lat = arguments.get("end_lat")
                    end_lon = arguments.get("end_lon")
                    
                    if None in [start_lat, start_lon, end_lat, end_lon]:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "All coordinates are required"}, indent=2)
                        )]
                    
                    result = await self._get_route(start_lat, start_lon, end_lat, end_lon)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "get_distance":
                    start_lat = arguments.get("start_lat")
                    start_lon = arguments.get("start_lon")
                    end_lat = arguments.get("end_lat")
                    end_lon = arguments.get("end_lon")
                    
                    if None in [start_lat, start_lon, end_lat, end_lon]:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "All coordinates are required"}, indent=2)
                        )]
                    
                    result = await self._get_distance(start_lat, start_lon, end_lat, end_lon)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "fastest_route":
                    start = arguments.get("start")
                    end = arguments.get("end")
                    
                    if not start or not end:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "Start and end parameters are required"}, indent=2)
                        )]
                    
                    result = await self._fastest_route(start, end)
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
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.
        
        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point
            
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    async def _get_route(self, start_lat: float, start_lon: float, 
                        end_lat: float, end_lon: float) -> Dict[str, Any]:
        """
        Get a route between two points.
        
        Args:
            start_lat, start_lon: Starting coordinates
            end_lat, end_lon: Destination coordinates
            
        Returns:
            Dictionary with route information
        """
        try:
            if self.use_mock:
                # Mock implementation
                distance = self._haversine_distance(start_lat, start_lon, end_lat, end_lon)
                # Assume average speed of 50 km/h for mock
                estimated_time = (distance / 50) * 60  # in minutes
                
                return {
                    "success": True,
                    "start": {"lat": start_lat, "lon": start_lon},
                    "end": {"lat": end_lat, "lon": end_lon},
                    "distance_km": round(distance, 2),
                    "estimated_time_minutes": round(estimated_time, 1),
                    "waypoints": [
                        {"lat": start_lat, "lon": start_lon},
                        {"lat": (start_lat + end_lat) / 2, "lon": (start_lon + end_lon) / 2},
                        {"lat": end_lat, "lon": end_lon}
                    ],
                    "note": "Mock route - using straight-line distance estimation"
                }
            else:
                # Real API implementation (requires API key)
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.ors_base}/directions/driving-car",
                        params={
                            "api_key": self.api_key,
                            "start": f"{start_lon},{start_lat}",
                            "end": f"{end_lon},{end_lat}"
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    route = data["features"][0]
                    distance = route["properties"]["segments"][0]["distance"] / 1000  # to km
                    duration = route["properties"]["segments"][0]["duration"] / 60  # to minutes
                    
                    return {
                        "success": True,
                        "start": {"lat": start_lat, "lon": start_lon},
                        "end": {"lat": end_lat, "lon": end_lon},
                        "distance_km": round(distance, 2),
                        "estimated_time_minutes": round(duration, 1),
                        "waypoints": route["geometry"]["coordinates"]
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Route calculation error: {str(e)}",
                "start": {"lat": start_lat, "lon": start_lon},
                "end": {"lat": end_lat, "lon": end_lon}
            }
    
    async def _get_distance(self, start_lat: float, start_lon: float,
                           end_lat: float, end_lon: float) -> Dict[str, Any]:
        """
        Calculate the straight-line distance between two points.
        
        Args:
            start_lat, start_lon: Starting coordinates
            end_lat, end_lon: Destination coordinates
            
        Returns:
            Dictionary with distance information
        """
        try:
            distance = self._haversine_distance(start_lat, start_lon, end_lat, end_lon)
            
            return {
                "success": True,
                "start": {"lat": start_lat, "lon": start_lon},
                "end": {"lat": end_lat, "lon": end_lon},
                "distance_km": round(distance, 2),
                "distance_miles": round(distance * 0.621371, 2)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Distance calculation error: {str(e)}",
                "start": {"lat": start_lat, "lon": start_lon},
                "end": {"lat": end_lat, "lon": end_lon}
            }
    
    async def _fastest_route(self, start: str, end: str) -> Dict[str, Any]:
        """
        Find the fastest route between two points (can be addresses or coordinates).
        
        Args:
            start: Starting address or "lat,lon"
            end: Destination address or "lat,lon"
            
        Returns:
            Dictionary with fastest route information
        """
        try:
            # Parse coordinates or geocode addresses
            async with httpx.AsyncClient() as client:
                # Helper to parse or geocode
                async def get_coords(location: str) -> tuple:
                    if "," in location and location.replace(".", "").replace("-", "").replace(",", "").replace(" ", "").isdigit():
                        # Looks like coordinates
                        parts = location.split(",")
                        return float(parts[0].strip()), float(parts[1].strip())
                    else:
                        # Geocode address
                        response = await client.get(
                            "https://nominatim.openstreetmap.org/search",
                            params={"q": location, "format": "json", "limit": 1},
                            headers={"User-Agent": "RoutingServer-MCP/1.0"}
                        )
                        data = response.json()
                        if data:
                            return float(data[0]["lat"]), float(data[0]["lon"])
                        raise ValueError(f"Could not geocode: {location}")
                
                start_lat, start_lon = await get_coords(start)
                end_lat, end_lon = await get_coords(end)
                
                # Get route
                route_result = await self._get_route(start_lat, start_lon, end_lat, end_lon)
                
                if route_result.get("success"):
                    route_result["start_location"] = start
                    route_result["end_location"] = end
                    route_result["route_type"] = "fastest"
                
                return route_result
        except Exception as e:
            return {
                "success": False,
                "error": f"Fastest route error: {str(e)}",
                "start": start,
                "end": end
            }
    
    async def run(self):
        """Run the server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="routing-server",
                    server_version="1.0.0"
                )
            )


if __name__ == "__main__":
    import asyncio
    server = RoutingServer()
    asyncio.run(server.run())

