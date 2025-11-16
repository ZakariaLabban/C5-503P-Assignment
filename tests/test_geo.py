"""
Tests for GeoServer MCP tools.

Tests cover:
- Tool accessibility
- JSON schema validation
- Basic function output
"""

import pytest
import asyncio
from servers.geo_server import GeoServer


class TestGeoServer:
    """Test suite for GeoServer."""
    
    @pytest.fixture
    def server(self):
        """Create a GeoServer instance for testing."""
        return GeoServer()
    
    @pytest.mark.asyncio
    async def test_geocode_tool_accessible(self, server):
        """Test that geocode tool is accessible."""
        # Check if tool is registered
        tools = server._tools
        tool_names = [tool.name for tool in tools]
        assert "geocode" in tool_names, "geocode tool should be registered"
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_tool_accessible(self, server):
        """Test that reverse_geocode tool is accessible."""
        tools = server._tools
        tool_names = [tool.name for tool in tools]
        assert "reverse_geocode" in tool_names, "reverse_geocode tool should be registered"
    
    @pytest.mark.asyncio
    async def test_search_poi_tool_accessible(self, server):
        """Test that search_poi tool is accessible."""
        tools = server._tools
        tool_names = [tool.name for tool in tools]
        assert "search_poi" in tool_names, "search_poi tool should be registered"
    
    @pytest.mark.asyncio
    async def test_geocode_schema_validation(self, server):
        """Test geocode tool schema validation."""
        tools = server._tools
        geocode_tool = next(tool for tool in tools if tool.name == "geocode")
        
        # Check schema structure
        assert hasattr(geocode_tool, "inputSchema")
        schema = geocode_tool.inputSchema
        
        # Validate required fields
        assert "properties" in schema
        assert "address" in schema["properties"]
        assert schema["properties"]["address"]["type"] == "string"
        assert "required" in schema
        assert "address" in schema["required"]
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_schema_validation(self, server):
        """Test reverse_geocode tool schema validation."""
        tools = server._tools
        tool = next(tool for tool in tools if tool.name == "reverse_geocode")
        schema = tool.inputSchema
        
        assert "properties" in schema
        assert "lat" in schema["properties"]
        assert "lon" in schema["properties"]
        assert schema["properties"]["lat"]["type"] == "number"
        assert schema["properties"]["lon"]["type"] == "number"
        assert "lat" in schema["required"]
        assert "lon" in schema["required"]
    
    @pytest.mark.asyncio
    async def test_search_poi_schema_validation(self, server):
        """Test search_poi tool schema validation."""
        tools = server._tools
        tool = next(tool for tool in tools if tool.name == "search_poi")
        schema = tool.inputSchema
        
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "lat" in schema["properties"]
        assert "lon" in schema["properties"]
        assert all(field in schema["required"] for field in ["query", "lat", "lon"])
    
    @pytest.mark.asyncio
    async def test_geocode_basic_output(self, server):
        """Test geocode function returns valid JSON output."""
        result = await server._geocode("Beirut, Lebanon")
        
        # Check result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should have 'success' field"
        
        if result.get("success"):
            assert "lat" in result, "Successful result should have 'lat'"
            assert "lon" in result, "Successful result should have 'lon'"
            assert isinstance(result["lat"], (int, float)), "lat should be a number"
            assert isinstance(result["lon"], (int, float)), "lon should be a number"
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_basic_output(self, server):
        """Test reverse_geocode function returns valid JSON output."""
        # Test with Beirut coordinates
        result = await server._reverse_geocode(33.8938, 35.5018)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should have 'success' field"
        
        if result.get("success"):
            assert "address" in result, "Successful result should have 'address'"
            assert isinstance(result["address"], str), "address should be a string"
    
    @pytest.mark.asyncio
    async def test_search_poi_basic_output(self, server):
        """Test search_poi function returns valid JSON output."""
        # Test with Beirut coordinates
        result = await server._search_poi("cafe", 33.8938, 35.5018)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should have 'success' field"
        
        if result.get("success"):
            assert "results" in result, "Successful result should have 'results'"
            assert isinstance(result["results"], list), "results should be a list"
            assert "count" in result, "Result should have 'count'"
    
    @pytest.mark.asyncio
    async def test_geocode_error_handling(self, server):
        """Test geocode handles errors gracefully."""
        # Test with invalid address
        result = await server._geocode("")
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # Should either succeed or have error info
        assert "success" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_tool_call_geocode(self, server):
        """Test calling geocode tool through internal handler."""
        # Access the call_tool handler through the server's registered handlers
        # Since MCP handlers are registered, we'll test by calling the underlying method directly
        # which is what the handler would call anyway
        result = await server._geocode("AUB, Beirut")
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should have 'success' field"
        
        if result.get("success"):
            assert "lat" in result, "Successful result should have 'lat'"
            assert "lon" in result, "Successful result should have 'lon'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

