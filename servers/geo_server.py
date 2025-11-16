"""
GeoServer - MCP server for geocoding and location-based operations.

This server provides tools for:
- Geocoding addresses to coordinates
- Reverse geocoding coordinates to addresses
- Searching for points of interest (POI)
"""

import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx


class GeoServer:
    """MCP server for geocoding and location services."""
    
    def __init__(self):
        """Initialize the GeoServer."""
        self.server = Server("geo-server")
        # Store tools for testing
        self._tools = []
        self._register_tools()
        # Using Nominatim API (free, no key required)
        self.nominatim_base = "https://nominatim.openstreetmap.org"
    
    def _register_tools(self):
        """Register all MCP tools for this server."""
        
        # Define tools
        tools_list = [
                Tool(
                    name="geocode",
                    description="Convert an address to latitude and longitude coordinates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "The address to geocode (e.g., 'AUB, Beirut, Lebanon')"
                            }
                        },
                        "required": ["address"]
                    }
                ),
                Tool(
                    name="reverse_geocode",
                    description="Convert latitude and longitude coordinates to an address",
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
                    name="search_poi",
                    description="Search for points of interest near a location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (e.g., 'cafe', 'restaurant', 'park')"
                            },
                            "lat": {
                                "type": "number",
                                "description": "Latitude of the search center"
                            },
                            "lon": {
                                "type": "number",
                                "description": "Longitude of the search center"
                            }
                        },
                        "required": ["query", "lat", "lon"]
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
                if name == "geocode":
                    address = arguments.get("address")
                    if not address:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "Address parameter is required"}, indent=2)
                        )]
                    result = await self._geocode(address)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "reverse_geocode":
                    lat = arguments.get("lat")
                    lon = arguments.get("lon")
                    if lat is None or lon is None:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "Lat and lon parameters are required"}, indent=2)
                        )]
                    result = await self._reverse_geocode(lat, lon)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
                elif name == "search_poi":
                    query = arguments.get("query")
                    lat = arguments.get("lat")
                    lon = arguments.get("lon")
                    if not query or lat is None or lon is None:
                        return [TextContent(
                            type="text",
                            text=json.dumps({"error": "Query, lat, and lon parameters are required"}, indent=2)
                        )]
                    result = await self._search_poi(query, lat, lon)
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
    
    async def _geocode(self, address: str) -> Dict[str, Any]:
        """
        Geocode an address to coordinates.
        
        Args:
            address: The address to geocode
            
        Returns:
            Dictionary with lat, lon, and formatted address
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.nominatim_base}/search",
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 1
                    },
                    headers={"User-Agent": "GeoServer-MCP/1.0"}
                )
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    return {
                        "success": False,
                        "error": "Address not found",
                        "address": address
                    }
                
                result = data[0]
                return {
                    "success": True,
                    "address": result.get("display_name", address),
                    "lat": float(result.get("lat", 0)),
                    "lon": float(result.get("lon", 0)),
                    "type": result.get("type", "unknown")
                }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "address": address
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Geocoding error: {str(e)}",
                "address": address
            }
    
    async def _reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to an address.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Dictionary with formatted address
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.nominatim_base}/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json"
                    },
                    headers={"User-Agent": "GeoServer-MCP/1.0"}
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    return {
                        "success": False,
                        "error": data.get("error", "Reverse geocoding failed"),
                        "lat": lat,
                        "lon": lon
                    }
                
                return {
                    "success": True,
                    "address": data.get("display_name", "Unknown address"),
                    "lat": lat,
                    "lon": lon,
                    "type": data.get("type", "unknown")
                }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "lat": lat,
                "lon": lon
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Reverse geocoding error: {str(e)}",
                "lat": lat,
                "lon": lon
            }
    
    async def _search_poi(self, query: str, lat: float, lon: float) -> Dict[str, Any]:
        """
        Search for points of interest near a location.
        
        Args:
            query: Search query (e.g., 'cafe', 'restaurant')
            lat: Latitude of search center
            lon: Longitude of search center
            
        Returns:
            Dictionary with list of POIs found
        """
        try:
            async with httpx.AsyncClient() as client:
                # Search near the location
                search_query = f"{query} near {lat},{lon}"
                response = await client.get(
                    f"{self.nominatim_base}/search",
                    params={
                        "q": search_query,
                        "format": "json",
                        "limit": 10,
                        "lat": lat,
                        "lon": lon
                    },
                    headers={"User-Agent": "GeoServer-MCP/1.0"}
                )
                response.raise_for_status()
                data = response.json()
                
                pois = []
                for item in data:
                    pois.append({
                        "name": item.get("display_name", "Unknown"),
                        "lat": float(item.get("lat", 0)),
                        "lon": float(item.get("lon", 0)),
                        "type": item.get("type", "unknown"),
                        "category": item.get("category", "unknown")
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "center": {"lat": lat, "lon": lon},
                    "count": len(pois),
                    "results": pois
                }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "query": query
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"POI search error: {str(e)}",
                "query": query
            }
    
    async def run(self):
        """Run the server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="geo-server",
                    server_version="1.0.0"
                )
            )


if __name__ == "__main__":
    import asyncio
    server = GeoServer()
    asyncio.run(server.run())

