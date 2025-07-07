#!/usr/bin/env python3

import logging
import asyncio
import json
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError as e:
    logger.error(f"Error: {e}")
    import sys
    sys.exit(1)

# Robot state
robot_state = {
    "position": {"x": 0, "y": 0},
    "direction": "north",
    "battery": 100,
    "status": "idle"
}

# Initialize FastMCP server
mcp = FastMCP("Robot MCP Server")

@mcp.tool()
def move_forward(distance: float = 1.0) -> str:
    """Move the robot forward by specified distance in meters"""
    global robot_state
    
    robot_state["status"] = "moving"
    
    # Update position based on direction
    if robot_state["direction"] == "north":
        robot_state["position"]["y"] += distance
    elif robot_state["direction"] == "south":
        robot_state["position"]["y"] -= distance
    elif robot_state["direction"] == "east":
        robot_state["position"]["x"] += distance
    elif robot_state["direction"] == "west":
        robot_state["position"]["x"] -= distance
    
    robot_state["battery"] -= distance * 2
    robot_state["battery"] = max(0, robot_state["battery"])
    robot_state["status"] = "idle"
    
    return f"🤖 Robot moved forward {distance}m. New position: ({robot_state['position']['x']:.1f}, {robot_state['position']['y']:.1f}). Battery: {robot_state['battery']:.1f}%"

@mcp.tool()
def move_backward(distance: float = 1.0) -> str:
    """Move the robot backward by specified distance in meters"""
    global robot_state
    
    robot_state["status"] = "moving"
    
    # Update position based on direction (opposite)
    if robot_state["direction"] == "north":
        robot_state["position"]["y"] -= distance
    elif robot_state["direction"] == "south":
        robot_state["position"]["y"] += distance
    elif robot_state["direction"] == "east":
        robot_state["position"]["x"] -= distance
    elif robot_state["direction"] == "west":
        robot_state["position"]["x"] += distance
    
    robot_state["battery"] -= distance * 2
    robot_state["battery"] = max(0, robot_state["battery"])
    robot_state["status"] = "idle"
    
    return f"🤖 Robot moved backward {distance}m. New position: ({robot_state['position']['x']:.1f}, {robot_state['position']['y']:.1f}). Battery: {robot_state['battery']:.1f}%"

@mcp.tool()
def turn_left(degrees: float = 90) -> str:
    """Turn the robot left by specified degrees"""
    global robot_state
    
    robot_state["status"] = "turning"
    
    # Update direction
    directions = ["north", "west", "south", "east"]
    current_idx = directions.index(robot_state["direction"])
    turns = int(degrees // 90)
    new_idx = (current_idx + turns) % 4
    robot_state["direction"] = directions[new_idx]
    
    robot_state["battery"] -= 1
    robot_state["battery"] = max(0, robot_state["battery"])
    robot_state["status"] = "idle"
    
    return f"🤖 Robot turned left {degrees}°. Now facing: {robot_state['direction']}. Battery: {robot_state['battery']:.1f}%"

@mcp.tool()
def turn_right(degrees: float = 90) -> str:
    """Turn the robot right by specified degrees"""
    global robot_state
    
    robot_state["status"] = "turning"
    
    # Update direction
    directions = ["north", "east", "south", "west"]
    current_idx = directions.index(robot_state["direction"])
    turns = int(degrees // 90)
    new_idx = (current_idx + turns) % 4
    robot_state["direction"] = directions[new_idx]
    
    robot_state["battery"] -= 1
    robot_state["battery"] = max(0, robot_state["battery"])
    robot_state["status"] = "idle"
    
    return f"🤖 Robot turned right {degrees}°. Now facing: {robot_state['direction']}. Battery: {robot_state['battery']:.1f}%"

@mcp.tool()
def get_status() -> str:
    """Get current robot status and position"""
    return f"🤖 Robot Status:\n" + \
           f"Position: ({robot_state['position']['x']:.1f}, {robot_state['position']['y']:.1f})\n" + \
           f"Direction: {robot_state['direction']}\n" + \
           f"Battery: {robot_state['battery']:.1f}%\n" + \
           f"Status: {robot_state['status']}"

@mcp.tool()
def stop() -> str:
    """Stop all robot movement"""
    global robot_state
    robot_state["status"] = "stopped"
    return "🤖 Robot stopped. All movement halted."

@mcp.tool()
def charge_battery(amount: float = 25) -> str:
    """Simulate charging the robot battery by specified amount (1-100)"""
    global robot_state
    
    amount = min(amount, 100 - robot_state["battery"])
    robot_state["battery"] += amount
    robot_state["battery"] = min(robot_state["battery"], 100)
    
    return f"🔋 Battery charged by {amount}%. Current battery: {robot_state['battery']:.1f}%"

@mcp.tool()
def reset_robot() -> str:
    """Reset robot to initial state"""
    global robot_state
    robot_state = {
        "position": {"x": 0, "y": 0},
        "direction": "north",
        "battery": 100,
        "status": "idle"
    }
    return "🔄 Robot reset to initial state: Position (0,0), facing north, battery 100%"

# Create FastAPI app
app = FastAPI(title="Robot MCP Server", description="MCP Server for Robot Commands")

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP requests over HTTP"""
    try:
        body = await request.json()
        logger.info(f"Received MCP request: {body}")
        
        # Handle MCP method calls
        if body.get("method") == "initialize":
            # Handle MCP initialization
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "Robot MCP Server",
                        "version": "1.0.0"
                    }
                }
            })
        
        elif body.get("method") == "tools/list":
            # Return list of available tools
            tools = []
            for tool_name, tool_func in mcp._tools.items():
                # Get function signature for better schema
                import inspect
                sig = inspect.signature(tool_func)
                properties = {}
                required = []
                
                for param_name, param in sig.parameters.items():
                    if param_name != 'self':
                        param_type = "string"
                        if param.annotation == float:
                            param_type = "number"
                        elif param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == bool:
                            param_type = "boolean"
                        
                        properties[param_name] = {
                            "type": param_type,
                            "description": f"Parameter {param_name}"
                        }
                        
                        if param.default == inspect.Parameter.empty:
                            required.append(param_name)
                
                tools.append({
                    "name": tool_name,
                    "description": tool_func.__doc__ or f"Tool: {tool_name}",
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                })
            
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "tools": tools
                }
            })
        
        elif body.get("method") == "notifications/initialized":
            # Handle post-initialization notification
            logger.info("Client initialized successfully")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {}
            })
        
        elif body.get("method") == "ping":
            # Handle ping requests
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {}
            })
        
        elif body.get("method") == "tools/call":
            # Execute tool
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name in mcp._tools:
                try:
                    result = mcp._tools[tool_name](**arguments)
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": str(result)
                                }
                            ]
                        }
                    })
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution error: {str(e)}"
                        }
                    })
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {body.get('method')}"
                }
            })
            
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id") if hasattr(body, 'get') else None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        })

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Robot MCP Server is running",
        "status": "healthy",
        "robot_state": robot_state,
        "mcp_endpoint": "/mcp"
    }

@app.post("/")
async def root_post_redirect(request: Request):
    """Handle POST requests to root - redirect to proper MCP endpoint"""
    try:
        body = await request.json()
        logger.warning(f"POST request sent to '/' instead of '/mcp'. Redirecting... Request: {body}")
        
        # Forward the request to the proper MCP endpoint
        return await mcp_endpoint(request)
        
    except Exception as e:
        logger.error(f"Error handling POST to root: {e}")
        return JSONResponse({
            "error": "Invalid request to root endpoint",
            "message": "MCP requests should be sent to /mcp endpoint",
            "correct_endpoint": "/mcp"
        }, status_code=400)

@app.get("/status")
async def robot_status():
    """Get robot status via REST endpoint"""
    return robot_state

if __name__ == "__main__":
    logger.info("🚀 Starting Robot MCP Server on Jetson...")
    logger.info(f"Initial robot state: {robot_state}")
    logger.info("📡 Server will be accessible at http://0.0.0.0:8000/mcp")
    
    # Run FastAPI server with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
