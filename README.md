# Map Services MCP Server Project

A comprehensive map services system built with OpenAI Agents SDK and Model Context Protocol (MCP). This project provides geocoding, routing, and weather services through MCP-compatible servers, integrated with an intelligent assistant agent.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Servers](#servers)
- [Testing](#testing)
- [Example Queries](#example-queries)

## 🎯 Project Overview

This project implements 3 custom MCP servers that expose map-related operations as tools:

1. **GeoServer** - Geocoding and location services
2. **RoutingServer** - Route calculation and navigation
3. **WeatherMapServer** - Weather information and overlays

All servers are integrated with a main `AssistantAgent` that automatically routes user queries to the appropriate server and tool.

## ✨ Features

- **MCP-Compatible Servers**: All servers follow the Model Context Protocol standard
- **Async/Await Support**: Fully asynchronous implementation for better performance
- **JSON Schema Validation**: Strict input/output schemas for all tools
- **Error Handling**: Graceful error handling with informative messages
- **Automatic Routing**: Intelligent query routing in the assistant agent
- **Comprehensive Tests**: Test suite covering tool accessibility, schema validation, and basic functionality

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Step 1: Clone or Navigate to Project Directory

```bash
cd C5-503-Assignment
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note on MCP Package**: The MCP (Model Context Protocol) package may need to be installed separately depending on your environment. If you encounter import errors, try:

```bash
# Option 1: Install from PyPI (if available)
pip install mcp

# Option 2: Install from GitHub
pip install git+https://github.com/modelcontextprotocol/python-sdk.git

# Option 3: If using a different MCP implementation, adjust imports in server files accordingly
```

### Step 3: Verify Installation

```bash
python --version  # Should be 3.10+
pip list | grep mcp  # Should show mcp package
```

## 📁 Project Structure

```
project/
│── servers/
│    ├── geo_server.py          # GeoServer MCP implementation
│    ├── routing_server.py       # RoutingServer MCP implementation
│    └── weather_server.py       # WeatherMapServer MCP implementation
│── agent.py                     # Main AssistantAgent integration
│── interactive_agent.py         # Interactive LLM-powered agent with chat interface
│── tests/
│    ├── __init__.py
│    ├── test_geo.py             # Tests for GeoServer
│    └── test_routing.py         # Tests for RoutingServer
│── requirements.txt             # Python dependencies
│── README.md                    # This file
```

## 🚀 Usage

### Running Individual Servers

Each server can be run independently:

#### GeoServer

```bash
python servers/geo_server.py
```

#### RoutingServer

```bash
python servers/routing_server.py
```

#### WeatherMapServer

```bash
python servers/weather_server.py
```

### Running the Main Agent

The main agent integrates all servers and provides a unified interface:

```bash
python agent.py
```

This will run example queries and demonstrate the routing capabilities.

### Running the Interactive Agent

The interactive agent provides an LLM-powered chat interface that intelligently routes queries to the appropriate MCP tools:

```bash
python interactive_agent.py
```

**Prerequisites for Interactive Agent:**

1. **OpenAI API Key**: You need an OpenAI API key to use the interactive agent
   - Create a `.env` file in the project root
   - Add your API key: `OPENAI_API_KEY=your_key_here`
   - The agent uses `gpt-4o-mini` by default (can be changed in code)

2. **Install python-dotenv** (if not already installed):
   ```bash
   pip install python-dotenv
   ```

**Features:**
- Natural language conversation interface
- Intelligent query routing using LLM function calling
- Automatic tool selection based on user queries
- Multi-step workflows (e.g., geocoding a location before searching for POIs)
- Real-time tool execution feedback

**Example Interaction:**
```
You: Find cafes near AUB
[LLM] Decided to use 2 tool(s):
   -> geocode
   -> search_poi
[TOOL] Calling tool: geocode
[TOOL] Calling tool: search_poi
Assistant: I found 5 cafes near AUB (American University of Beirut)...
```

### Programmatic Usage

You can also use the agent programmatically:

```python
import asyncio
from agent import AssistantAgent

async def main():
    agent = AssistantAgent()
    result = await agent.process_query("Find cafes near AUB")
    print(agent.format_result(result))

asyncio.run(main())
```

## 🛠️ Servers

### 1. GeoServer

**Location**: `servers/geo_server.py`

**Tools**:

#### `geocode(address: string)`
Converts an address to latitude and longitude coordinates.

**Example**:
```python
result = await geo_server._geocode("American University of Beirut")
# Returns: {"success": True, "lat": 33.8938, "lon": 35.5018, "address": "..."}
```

#### `reverse_geocode(lat: float, lon: float)`
Converts coordinates to a formatted address.

**Example**:
```python
result = await geo_server._reverse_geocode(33.8938, 35.5018)
# Returns: {"success": True, "address": "Beirut, Lebanon", ...}
```

#### `search_poi(query: string, lat: float, lon: float)`
Searches for points of interest near a location.

**Example**:
```python
result = await geo_server._search_poi("cafe", 33.8938, 35.5018)
# Returns: {"success": True, "count": 5, "results": [...]}
```

**API Used**: OpenStreetMap Nominatim (free, no API key required)

---

### 2. RoutingServer

**Location**: `servers/routing_server.py`

**Tools**:

#### `get_route(start_lat, start_lon, end_lat, end_lon)`
Calculates a route between two points with distance and estimated time.

**Example**:
```python
result = await routing_server._get_route(33.8938, 35.5018, 34.4344, 35.8444)
# Returns: {"success": True, "distance_km": 85.2, "estimated_time_minutes": 102.4, ...}
```

#### `get_distance(start_lat, start_lon, end_lat, end_lon)`
Calculates the straight-line (Haversine) distance between two points.

**Example**:
```python
result = await routing_server._get_distance(33.8938, 35.5018, 34.4344, 35.8444)
# Returns: {"success": True, "distance_km": 85.2, "distance_miles": 52.9}
```

#### `fastest_route(start, end)`
Finds the fastest route between two locations (can be addresses or coordinates).

**Example**:
```python
result = await routing_server._fastest_route("Beirut", "Tripoli")
# Returns: {"success": True, "distance_km": 85.2, "route_type": "fastest", ...}
```

**Note**: Currently uses mock implementation. Set `use_mock = False` and provide API key for real routing via OpenRouteService.

---

### 3. WeatherMapServer

**Location**: `servers/weather_server.py`

**Tools**:

#### `get_weather(location)`
Gets current weather conditions for a location.

**Example**:
```python
result = await weather_server._get_weather("Beirut, Lebanon")
# Returns: {"success": True, "condition": "sunny", "temperature_c": 25.3, ...}
```

#### `get_temperature(lat, lon)`
Gets temperature at specific coordinates.

**Example**:
```python
result = await weather_server._get_temperature(33.8938, 35.5018)
# Returns: {"success": True, "temperature_c": 25.3, "temperature_f": 77.5}
```

#### `weather_overlay(tile_x, tile_y, zoom)`
Gets weather overlay data for a map tile.

**Example**:
```python
result = await weather_server._weather_overlay(10, 7, 5)
# Returns: {"success": True, "bounds": {...}, "weather_data": {...}}
```

**Note**: Currently uses mock data. Set `use_mock = False` and provide OpenWeatherMap API key for real weather data.

---

## 🧪 Testing

### Running Tests

Run all tests:

```bash
pytest tests/ -v
```

Run specific test file:

```bash
# Test GeoServer
python tests/test_geo.py

# Test RoutingServer
python tests/test_routing.py
```

Or using pytest:

```bash
pytest tests/test_geo.py -v
pytest tests/test_routing.py -v
```

### Test Coverage

Tests verify:

- ✅ **Tool Accessibility**: All tools are registered and accessible
- ✅ **JSON Schema Validation**: Input schemas are properly defined
- ✅ **Basic Function Output**: Functions return valid JSON structures
- ✅ **Error Handling**: Errors are handled gracefully

### Test Structure

- `test_geo.py`: Tests for GeoServer (geocode, reverse_geocode, search_poi)
- `test_routing.py`: Tests for RoutingServer (get_route, get_distance, fastest_route)

## 💡 Example Queries

The assistant agent can handle natural language queries and route them to the appropriate server:

### Geocoding Examples

```python
# Find coordinates of an address
"Geocode American University of Beirut"
"Where is AUB?"
"Find coordinates of Beirut, Lebanon"

# Reverse geocoding
"Reverse geocode 33.8938, 35.5018"
"What address is at coordinates 33.8938, 35.5018?"

# POI Search
"Find cafes near AUB"
"Search for restaurants near Beirut"
"Find parks near 33.8938, 35.5018"
```

### Routing Examples

```python
# Get route
"Get route from Beirut to Tripoli"
"Route from 33.8938,35.5018 to 34.4344,35.8444"

# Distance calculation
"What's the distance between Beirut and Tripoli?"
"Distance from 33.8938,35.5018 to 34.4344,35.8444"

# Fastest route
"Fastest route from Beirut to Tripoli"
"Quickest way from AUB to downtown Beirut"
```

### Weather Examples

```python
# Weather by location
"What's the weather in Beirut?"
"Weather at American University of Beirut"

# Temperature by coordinates
"Temperature at 33.8938, 35.5018"
"Get temperature for coordinates 33.8938, 35.5018"

# Weather overlay
"Weather overlay for tile 10, 7, zoom 5"
```

## 🔧 Configuration

### Interactive Agent Setup

To use the interactive agent, you need to set up your OpenAI API key:

1. Create a `.env` file in the project root directory
2. Add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. Make sure `python-dotenv` is installed: `pip install python-dotenv`

The interactive agent uses OpenAI's function calling feature to intelligently route queries to the appropriate MCP tools. It supports:
- Multi-turn conversations
- Automatic tool selection
- Multi-step workflows (e.g., geocoding before POI search)
- Real-time tool execution

### Using Real APIs

To use real APIs instead of mocks:

1. **OpenRouteService** (for routing):
   - Sign up at https://openrouteservice.org/
   - Get API key
   - In `servers/routing_server.py`, set `use_mock = False` and add `self.api_key = "your_key"`

2. **OpenWeatherMap** (for weather):
   - Sign up at https://openweathermap.org/api
   - Get API key
   - In `servers/weather_server.py`, set `use_mock = False` and add `self.api_key = "your_key"`

**Note**: OpenStreetMap Nominatim (used by GeoServer) is free and requires no API key.

## 📝 Code Standards

- ✅ **Docstrings**: All functions have docstrings
- ✅ **Type Hints**: Full type annotation support
- ✅ **Async/Await**: All I/O operations are asynchronous
- ✅ **JSON Schemas**: Strict input/output validation
- ✅ **Error Handling**: Comprehensive error handling
- ✅ **Clean Code**: Easy to read and understand

## 🐛 Troubleshooting

### Import Errors

If you get import errors, make sure:
- All dependencies are installed: `pip install -r requirements.txt`
- You're using Python 3.10+
- You're in the project root directory

### API Errors

- **Nominatim (GeoServer)**: Free but has rate limits. If you hit limits, wait a few seconds.
- **Mock Data**: Some servers use mock data by default. Check `use_mock` flag in server files.

### Test Failures

- Make sure all dependencies are installed
- Some tests require internet connection (for API calls)
- Run tests with `-v` flag for verbose output

## 📚 Additional Resources

- [OpenAI Agents SDK Documentation](https://github.com/openai/openai-python)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [OpenStreetMap Nominatim](https://nominatim.org/)
- [OpenRouteService](https://openrouteservice.org/)
- [OpenWeatherMap API](https://openweathermap.org/api)

## 👤 Author

Engineering Course - Part 2 Assignment

## 📄 License

This project is for educational purposes.

---

**Happy Mapping! 🗺️**

