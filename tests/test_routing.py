"""
Tests for RoutingServer MCP tools.

Tests cover:
- Tool accessibility
- JSON schema validation
- Basic function output
"""

import pytest
import asyncio
from servers.routing_server import RoutingServer


class TestRoutingServer:
    """Test suite for RoutingServer."""
    
    @pytest.fixture
    def server(self):
        """Create a RoutingServer instance for testing."""
        return RoutingServer()
    
    @pytest.mark.asyncio
    async def test_get_route_tool_accessible(self, server):
        """Test that get_route tool is accessible."""
        tools = server._tools
        tool_names = [tool.name for tool in tools]
        assert "get_route" in tool_names, "get_route tool should be registered"
    
    @pytest.mark.asyncio
    async def test_get_distance_tool_accessible(self, server):
        """Test that get_distance tool is accessible."""
        tools = server._tools
        tool_names = [tool.name for tool in tools]
        assert "get_distance" in tool_names, "get_distance tool should be registered"
    
    @pytest.mark.asyncio
    async def test_fastest_route_tool_accessible(self, server):
        """Test that fastest_route tool is accessible."""
        tools = server._tools
        tool_names = [tool.name for tool in tools]
        assert "fastest_route" in tool_names, "fastest_route tool should be registered"
    
    @pytest.mark.asyncio
    async def test_get_route_schema_validation(self, server):
        """Test get_route tool schema validation."""
        tools = server._tools
        tool = next(tool for tool in tools if tool.name == "get_route")
        schema = tool.inputSchema
        
        assert "properties" in schema
        required_fields = ["start_lat", "start_lon", "end_lat", "end_lon"]
        for field in required_fields:
            assert field in schema["properties"]
            assert schema["properties"][field]["type"] == "number"
        assert all(field in schema["required"] for field in required_fields)
    
    @pytest.mark.asyncio
    async def test_get_distance_schema_validation(self, server):
        """Test get_distance tool schema validation."""
        tools = server._tools
        tool = next(tool for tool in tools if tool.name == "get_distance")
        schema = tool.inputSchema
        
        assert "properties" in schema
        required_fields = ["start_lat", "start_lon", "end_lat", "end_lon"]
        for field in required_fields:
            assert field in schema["properties"]
        assert all(field in schema["required"] for field in required_fields)
    
    @pytest.mark.asyncio
    async def test_fastest_route_schema_validation(self, server):
        """Test fastest_route tool schema validation."""
        tools = server._tools
        tool = next(tool for tool in tools if tool.name == "fastest_route")
        schema = tool.inputSchema
        
        assert "properties" in schema
        assert "start" in schema["properties"]
        assert "end" in schema["properties"]
        assert schema["properties"]["start"]["type"] == "string"
        assert schema["properties"]["end"]["type"] == "string"
        assert "start" in schema["required"]
        assert "end" in schema["required"]
    
    @pytest.mark.asyncio
    async def test_get_route_basic_output(self, server):
        """Test get_route function returns valid JSON output."""
        # Test with Beirut to Tripoli
        result = await server._get_route(33.8938, 35.5018, 34.4344, 35.8444)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should have 'success' field"
        
        if result.get("success"):
            assert "distance_km" in result, "Result should have 'distance_km'"
            assert "start" in result, "Result should have 'start coordinates"
            assert "end" in result, "Result should have end coordinates"
            assert isinstance(result["distance_km"], (int, float)), "distance_km should be a number"
    
    @pytest.mark.asyncio
    async def test_get_distance_basic_output(self, server):
        """Test get_distance function returns valid JSON output."""
        # Test with Beirut to Tripoli
        result = await server._get_distance(33.8938, 35.5018, 34.4344, 35.8444)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should have 'success' field"
        
        if result.get("success"):
            assert "distance_km" in result, "Result should have 'distance_km'"
            assert "distance_miles" in result, "Result should have 'distance_miles'"
            assert isinstance(result["distance_km"], (int, float)), "distance_km should be a number"
            assert result["distance_km"] > 0, "Distance should be positive"
    
    @pytest.mark.asyncio
    async def test_fastest_route_basic_output(self, server):
        """Test fastest_route function returns valid JSON output."""
        result = await server._fastest_route("Beirut", "Tripoli")
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result or "error" in result, "Result should have success or error"
        
        if result.get("success"):
            assert "distance_km" in result, "Result should have 'distance_km'"
    
    @pytest.mark.asyncio
    async def test_haversine_distance_calculation(self, server):
        """Test haversine distance calculation."""
        # Known distance: Beirut to Tripoli is approximately 85 km
        distance = server._haversine_distance(33.8938, 35.5018, 34.4344, 35.8444)
        
        assert isinstance(distance, (int, float)), "Distance should be a number"
        assert distance > 0, "Distance should be positive"
        # Should be roughly 80-90 km
        assert 50 < distance < 150, f"Distance should be reasonable (got {distance} km)"
    
    @pytest.mark.asyncio
    async def test_get_route_error_handling(self, server):
        """Test get_route handles errors gracefully."""
        # Test with invalid coordinates
        result = await server._get_route(0, 0, 0, 0)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # Should handle gracefully (distance would be 0, but should still return valid structure)
        assert "success" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_tool_call_get_distance(self, server):
        """Test calling get_distance tool through internal handler."""
        # Test by calling the underlying method directly
        result = await server._get_distance(33.8938, 35.5018, 34.4344, 35.8444)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should have 'success' field"
        
        if result.get("success"):
            assert "distance_km" in result, "Result should have 'distance_km'"
            assert isinstance(result["distance_km"], (int, float)), "distance_km should be a number"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

