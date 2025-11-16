"""
Main Assistant Agent that integrates all map servers.

This agent routes user queries to the appropriate MCP server and formats results.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional


class AssistantAgent:
    """Main agent that routes queries to appropriate map servers."""
    
    def __init__(self):
        """Initialize the AssistantAgent with all map servers."""
        self.servers = {}
        self._initialize_servers()
    
    def _initialize_servers(self):
        """Initialize connections to all MCP servers."""
        # Note: In a real implementation, these would be separate processes
        # For this assignment, we'll use direct imports for simplicity
        from servers.geo_server import GeoServer
        from servers.routing_server import RoutingServer
        from servers.weather_server import WeatherMapServer
        
        self.geo_server = GeoServer()
        self.routing_server = RoutingServer()
        self.weather_server = WeatherMapServer()
        
        print("✓ Initialized GeoServer")
        print("✓ Initialized RoutingServer")
        print("✓ Initialized WeatherMapServer")
    
    async def _call_geo_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the GeoServer."""
        try:
            if tool_name == "geocode":
                result = await self.geo_server._geocode(arguments["address"])
            elif tool_name == "reverse_geocode":
                result = await self.geo_server._reverse_geocode(
                    arguments["lat"], arguments["lon"]
                )
            elif tool_name == "search_poi":
                result = await self.geo_server._search_poi(
                    arguments["query"], arguments["lat"], arguments["lon"]
                )
            else:
                result = {"error": f"Unknown geo tool: {tool_name}"}
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def _call_routing_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the RoutingServer."""
        try:
            if tool_name == "get_route":
                result = await self.routing_server._get_route(
                    arguments["start_lat"], arguments["start_lon"],
                    arguments["end_lat"], arguments["end_lon"]
                )
            elif tool_name == "get_distance":
                result = await self.routing_server._get_distance(
                    arguments["start_lat"], arguments["start_lon"],
                    arguments["end_lat"], arguments["end_lon"]
                )
            elif tool_name == "fastest_route":
                result = await self.routing_server._fastest_route(
                    arguments["start"], arguments["end"]
                )
            else:
                result = {"error": f"Unknown routing tool: {tool_name}"}
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def _call_weather_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the WeatherMapServer."""
        try:
            if tool_name == "get_weather":
                result = await self.weather_server._get_weather(arguments["location"])
            elif tool_name == "get_temperature":
                result = await self.weather_server._get_temperature(
                    arguments["lat"], arguments["lon"]
                )
            elif tool_name == "weather_overlay":
                result = await self.weather_server._weather_overlay(
                    arguments["tile_x"], arguments["tile_y"], arguments["zoom"]
                )
            else:
                result = {"error": f"Unknown weather tool: {tool_name}"}
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _route_query(self, query: str) -> tuple[str, Dict[str, Any]]:
        """
        Route a user query to the appropriate server and tool.
        
        Args:
            query: User's natural language query
            
        Returns:
            Tuple of (server_name, tool_name, arguments)
        """
        query_lower = query.lower()
        
        # GeoServer routing
        if any(word in query_lower for word in ["geocode", "address to", "coordinates of", "where is"]):
            if "reverse" in query_lower or "coordinates to address" in query_lower:
                # Extract coordinates (simplified)
                return "geo", "reverse_geocode", self._extract_coords(query)
            else:
                # Extract address
                address = self._extract_address(query)
                return "geo", "geocode", {"address": address}
        
        if any(word in query_lower for word in ["find", "search", "near", "poi", "cafe", "restaurant", "park"]):
            # POI search
            location = self._extract_location_for_poi(query)
            return "geo", "search_poi", location
        
        # RoutingServer routing
        if any(word in query_lower for word in ["route", "directions", "how to get", "navigate", "distance"]):
            if "fastest" in query_lower or "quickest" in query_lower:
                locations = self._extract_two_locations(query)
                return "routing", "fastest_route", locations
            elif "distance" in query_lower:
                # Check if query contains coordinate pairs
                import re
                coord_pattern = r'(-?\d+\.?\d*)\s*[,]\s*(-?\d+\.?\d*)'
                coords_found = re.findall(coord_pattern, query)
                if len(coords_found) >= 2:
                    # Extract two coordinate pairs
                    coords = {
                        "start_lat": float(coords_found[0][0]),
                        "start_lon": float(coords_found[0][1]),
                        "end_lat": float(coords_found[1][0]),
                        "end_lon": float(coords_found[1][1])
                    }
                    return "routing", "get_distance", coords
                else:
                    coords = self._extract_two_coords(query)
                    return "routing", "get_distance", coords
            else:
                coords = self._extract_two_coords(query)
                return "routing", "get_route", coords
        
        # WeatherMapServer routing
        if any(word in query_lower for word in ["weather", "temperature", "forecast"]):
            if "overlay" in query_lower or "tile" in query_lower:
                tile_info = self._extract_tile_info(query)
                return "weather", "weather_overlay", tile_info
            elif any(char.isdigit() for char in query) and "," in query:
                # Likely coordinates
                coords = self._extract_coords(query)
                return "weather", "get_temperature", coords
            else:
                location = self._extract_location(query)
                return "weather", "get_weather", {"location": location}
        
        # Default to geocoding if unclear
        return "geo", "geocode", {"address": query}
    
    def _extract_address(self, query: str) -> str:
        """Extract address from query (simplified)."""
        # Remove common prefixes
        prefixes = ["find", "geocode", "where is", "address of", "coordinates of"]
        for prefix in prefixes:
            if query.lower().startswith(prefix):
                return query[len(prefix):].strip()
        return query.strip()
    
    def _extract_location(self, query: str) -> str:
        """Extract location from query."""
        prefixes = ["weather in", "weather at", "temperature in", "temperature at"]
        for prefix in prefixes:
            if prefix in query.lower():
                idx = query.lower().index(prefix)
                return query[idx + len(prefix):].strip()
        return query.strip()
    
    def _extract_coords(self, query: str) -> Dict[str, float]:
        """Extract coordinates from query (simplified)."""
        # Look for lat,lon pattern
        import re
        pattern = r'(-?\d+\.?\d*)\s*[,]\s*(-?\d+\.?\d*)'
        match = re.search(pattern, query)
        if match:
            return {"lat": float(match.group(1)), "lon": float(match.group(2))}
        return {"lat": 33.8938, "lon": 35.5018}  # Default to Beirut
    
    def _extract_location_for_poi(self, query: str) -> Dict[str, Any]:
        """Extract location info for POI search."""
        # Try to find a known location or use default
        location = self._extract_location(query)
        
        # Try to geocode it (simplified - in real implementation would call geocode)
        # For now, use default coordinates
        coords = self._extract_coords(query)
        
        # Extract POI type
        poi_types = ["cafe", "restaurant", "park", "hotel", "museum", "hospital"]
        query_type = None
        for poi_type in poi_types:
            if poi_type in query.lower():
                query_type = poi_type
                break
        
        return {
            "query": query_type or "place",
            "lat": coords["lat"],
            "lon": coords["lon"]
        }
    
    def _extract_two_locations(self, query: str) -> Dict[str, str]:
        """Extract two locations from query."""
        # Simplified - look for "from X to Y" pattern
        import re
        pattern = r'from\s+(.+?)\s+to\s+(.+)'
        match = re.search(pattern, query.lower())
        if match:
            return {"start": match.group(1).strip(), "end": match.group(2).strip()}
        return {"start": "Beirut", "end": "Tripoli"}
    
    def _extract_two_coords(self, query: str) -> Dict[str, float]:
        """Extract two coordinate pairs from query."""
        # Simplified - use defaults
        return {
            "start_lat": 33.8938, "start_lon": 35.5018,  # Beirut
            "end_lat": 34.4344, "end_lon": 35.8444  # Tripoli
        }
    
    def _extract_tile_info(self, query: str) -> Dict[str, int]:
        """Extract tile information from query."""
        import re
        # Look for tile_x, tile_y, zoom pattern
        pattern = r'tile[_\s]*(\d+)[,\s]+(\d+)[,\s]+zoom[_\s]*(\d+)'
        match = re.search(pattern, query.lower())
        if match:
            return {
                "tile_x": int(match.group(1)),
                "tile_y": int(match.group(2)),
                "zoom": int(match.group(3))
            }
        return {"tile_x": 10, "tile_y": 7, "zoom": 5}
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query and return formatted results.
        
        Args:
            query: User's natural language query
            
        Returns:
            Formatted result dictionary
        """
        print(f"\n🔍 Processing query: '{query}'")
        
        # Route the query
        server_name, tool_name, arguments = self._route_query(query)
        print(f"📡 Routing to {server_name} server, tool: {tool_name}")
        print(f"📋 Arguments: {arguments}")
        
        # Call the appropriate tool
        try:
            if server_name == "geo":
                result = await self._call_geo_tool(tool_name, arguments)
            elif server_name == "routing":
                result = await self._call_routing_tool(tool_name, arguments)
            elif server_name == "weather":
                result = await self._call_weather_tool(tool_name, arguments)
            else:
                result = {"error": f"Unknown server: {server_name}"}
            
            return {
                "query": query,
                "server": server_name,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            return {
                "query": query,
                "error": str(e)
            }
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format a result for pretty printing.
        
        Args:
            result: Result dictionary from process_query
            
        Returns:
            Formatted string
        """
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        server = result.get("server", "unknown")
        tool = result.get("tool", "unknown")
        data = result.get("result", {})
        
        output = f"\n{'='*60}\n"
        output += f"Server: {server.upper()} | Tool: {tool}\n"
        output += f"{'='*60}\n"
        output += json.dumps(data, indent=2)
        output += f"\n{'='*60}\n"
        
        return output


async def main():
    """Main function with example interactions."""
    agent = AssistantAgent()
    
    print("\n" + "="*60)
    print("🗺️  Map Services Assistant Agent")
    print("="*60)
    
    # Example queries
    example_queries = [
        "Find cafes near AUB",
        "Geocode American University of Beirut",
        "What's the weather in Beirut?",
        "Get route from Beirut to Tripoli",
        "What's the distance between 33.8938,35.5018 and 34.4344,35.8444?",
        "Temperature at 33.8938, 35.5018"
    ]
    
    print("\n📝 Running example queries...\n")
    
    for query in example_queries:
        result = await agent.process_query(query)
        formatted = agent.format_result(result)
        print(formatted)
        print()


if __name__ == "__main__":
    asyncio.run(main())

