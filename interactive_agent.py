"""
Interactive Agent with LLM-powered query routing.

This script allows you to chat with an LLM that intelligently routes queries
to the appropriate MCP tools (GeoServer, RoutingServer, WeatherMapServer).
"""

import os
import json
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Import servers
from servers.geo_server import GeoServer
from servers.routing_server import RoutingServer
from servers.weather_server import WeatherMapServer


class InteractiveAgent:
    """Interactive agent that uses LLM to route queries to MCP tools."""
    
    def __init__(self):
        """Initialize the agent with all servers and OpenAI client."""
        # Initialize servers
        self.geo_server = GeoServer()
        self.routing_server = RoutingServer()
        self.weather_server = WeatherMapServer()
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.client = OpenAI(api_key=api_key)
        
        # Define tools for OpenAI function calling
        self.tools = self._define_tools()
        
        print("[OK] Initialized GeoServer (Real API)")
        print("[OK] Initialized RoutingServer (Mock)")
        print("[OK] Initialized WeatherMapServer (Mock)")
        print("[OK] Initialized OpenAI client")
        print()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define tools for OpenAI function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "geocode",
                    "description": "Convert an address to latitude and longitude coordinates. Use this when user asks for coordinates of a location or wants to geocode an address.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "The address to geocode (e.g., 'AUB, Beirut, Lebanon')"
                            }
                        },
                        "required": ["address"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reverse_geocode",
                    "description": "Convert latitude and longitude coordinates to a formatted address. Use this when user provides coordinates and wants to know the address.",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_poi",
                    "description": "Search for points of interest (POIs) near a location. Use this when user wants to find cafes, restaurants, parks, hotels, or other places near a location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (e.g., 'cafe', 'restaurant', 'park', 'hotel')"
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_route",
                    "description": "Get a route between two points with distance and estimated time. Use this when user wants directions or a route between two locations.",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_distance",
                    "description": "Calculate the straight-line distance between two points. Use this when user asks for distance between two locations or coordinates.",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fastest_route",
                    "description": "Find the fastest route between two locations (can be addresses or coordinates). Use this when user asks for fastest/quickest route.",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather conditions for a location. Use this when user asks about weather in a place.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location name or address (e.g., 'Beirut, Lebanon')"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_temperature",
                    "description": "Get temperature at specific coordinates. Use this when user asks for temperature at coordinates.",
                    "parameters": {
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
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call the appropriate tool based on name."""
        print(f"\n[TOOL] Calling tool: {tool_name}")
        print(f"[ARGS] Arguments: {json.dumps(arguments, indent=2)}")
        
        try:
            if tool_name == "geocode":
                result = await self.geo_server._geocode(arguments["address"])
            elif tool_name == "reverse_geocode":
                result = await self.geo_server._reverse_geocode(arguments["lat"], arguments["lon"])
            elif tool_name == "search_poi":
                result = await self.geo_server._search_poi(
                    arguments["query"], arguments["lat"], arguments["lon"]
                )
            elif tool_name == "get_route":
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
            elif tool_name == "get_weather":
                result = await self.weather_server._get_weather(arguments["location"])
            elif tool_name == "get_temperature":
                result = await self.weather_server._get_temperature(
                    arguments["lat"], arguments["lon"]
                )
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            print(f"[OK] Tool result: {json.dumps(result, indent=2)[:200]}...")  # Truncate for display
            return result
        except Exception as e:
            error_result = {"error": str(e)}
            print(f"[ERROR] Tool error: {error_result}")
            return error_result
    
    async def chat(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Send message to LLM and handle tool calls."""
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Keep calling tools until we get a final response
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get response from LLM
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # or "gpt-4" for better results
                messages=conversation_history,
                tools=self.tools,
                tool_choice="auto"  # Let LLM decide when to use tools
            )
            
            message = response.choices[0].message
            
            # Add assistant message to history (but don't include tool_calls in the dict if we're going to handle them)
            assistant_message = {
                "role": "assistant",
                "content": message.content
            }
            if message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            conversation_history.append(assistant_message)
            
            # Handle tool calls
            if message.tool_calls:
                print(f"\n[LLM] Decided to use {len(message.tool_calls)} tool(s):")
                for tool_call in message.tool_calls:
                    print(f"   -> {tool_call.function.name}")
                
                # Execute all tool calls
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Call the tool
                    tool_result = await self.call_tool(tool_name, arguments)
                    
                    # Add tool result to conversation
                    conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(tool_result)
                    })
                
                # Continue loop to get final response with tool results
                continue
            else:
                # No tool calls, we have the final response
                if message.content:
                    return message.content
                else:
                    return "I processed your request but didn't get a response. Please try rephrasing your question."
        
        # If we've done too many iterations, return an error
        return "I'm having trouble processing your request. Please try again with a simpler question."
    
    async def run(self):
        """Run the interactive chat loop."""
        print("="*70)
        print("Interactive Map Services Agent with LLM Routing")
        print("="*70)
        print("\nYou can ask questions like:")
        print("  - 'Find cafes near AUB'")
        print("  - 'What are the coordinates of American University of Beirut?'")
        print("  - 'Get the distance between Beirut and Tripoli'")
        print("  - 'What's the weather in Beirut?'")
        print("\nType 'quit' or 'exit' to stop.\n")
        
        conversation_history = [
            {
                "role": "system",
                "content": """You are a helpful assistant that can help users with geocoding, routing, and weather queries.
You have access to several tools:
- GeoServer: geocode addresses, reverse geocode coordinates, search for points of interest (REAL DATA from OpenStreetMap)
- RoutingServer: get routes, calculate distances, find fastest routes (MOCK DATA - but distance calculations are accurate)
- WeatherMapServer: get weather and temperature (MOCK DATA)

IMPORTANT INSTRUCTIONS:
1. When a user asks about a location by name (like "AUB", "Beirut", "Tripoli"), you may need to geocode it first to get coordinates
2. For POI searches, you need coordinates - if the user gives a location name, geocode it first, then search for POIs
3. For routing between locations, geocode both locations first, then call get_route or get_distance
4. Always use the tools when appropriate - don't just guess or make up information
5. After calling tools, provide a clear, helpful response based on the actual results

Example workflow:
- User: "Find cafes near AUB"
- Step 1: Call geocode("AUB") to get coordinates
- Step 2: Call search_poi("cafe", lat, lon) with the coordinates from step 1
- Step 3: Present the results to the user"""
            }
        ]
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break
                
                # Process with LLM
                print("\n[Thinking...]")
                response = await self.chat(user_input, conversation_history)
                
                # Display response
                print(f"\nAssistant: {response}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n[ERROR] Error: {str(e)}")
                import traceback
                traceback.print_exc()


async def main():
    """Main entry point."""
    try:
        agent = InteractiveAgent()
        await agent.run()
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Created a .env file with OPENAI_API_KEY=your_key")
        print("  2. Installed python-dotenv: pip install python-dotenv")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

