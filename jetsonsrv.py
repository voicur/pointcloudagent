#!/usr/bin/env python3

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP
except ImportError as e:
    logger.error(f"Error: {e}")
    import sys
    sys.exit(1)

robot_state = {
    "x": 0,
    "y": 0,
    "connected": True
}

# Initialize FastMCP server
mcp = FastMCP("Robot Server")

@mcp.tool()
def move_forward(distance: float = 1.0) -> str:
    """Move robot forward by distance"""
    global robot_state
    robot_state["y"] += distance
    return f"Moved forward {distance} units. Position: ({robot_state['x']}, {robot_state['y']})"

@mcp.tool()
def move_backward(distance: float = 1.0) -> str:
    """Move robot backward by distance"""
    global robot_state
    robot_state["y"] -= distance
    return f"Moved backward {distance} units. Position: ({robot_state['x']}, {robot_state['y']})"

@mcp.tool()
def move_left(steps: int = 1) -> str:
    """Move robot left by steps"""
    global robot_state
    robot_state["x"] -= steps
    return f"Moved left {steps} steps. Position: ({robot_state['x']}, {robot_state['y']})"

@mcp.tool()
def move_right(steps: int = 1) -> str:
    """Move robot right by steps"""
    global robot_state
    robot_state["x"] += steps
    return f"Moved right {steps} steps. Position: ({robot_state['x']}, {robot_state['y']})"

@mcp.tool()
def turn_left(degrees: float = 90) -> str:
    """Turn robot left by degrees"""
    global robot_state
    return f"Turned left {degrees} degrees"

@mcp.tool()
def turn_right(degrees: float = 90) -> str:
    """Turn robot right by degrees"""
    global robot_state
    return f"Turned right {degrees} degrees"

@mcp.tool()
def get_status() -> str:
    """Get robot status"""
    status = "connected" if robot_state["connected"] else "disconnected"
    return f"Robot status: {status}, Position: ({robot_state['x']}, {robot_state['y']})"

@mcp.tool()
def reset() -> str:
    """Reset robot to origin"""
    global robot_state
    robot_state["x"] = 0
    robot_state["y"] = 0
    return "Robot reset to position (0, 0)"

if __name__ == "__main__":
    logger.info("Starting Robot MCP Server...")
    logger.info(f"Initial state: {robot_state}")
    logger.info("Server running on http://0.0.0.0:8000")
    
    # Run FastMCP server with HTTP transport
    mcp.run(transport="http", host="0.0.0.0", port=8000)
