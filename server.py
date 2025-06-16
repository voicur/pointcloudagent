#!/usr/bin/env python3
import os
import pointcloud_tools as pct
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "PointCloudDemo",
    stateless_http=True,
    host="127.0.0.1",
    port=8080
)

DEFAULT_PATH = "data/bunny.ply"

@mcp.tool()
def count_points(path: str = DEFAULT_PATH) -> int | dict:
    return pct.count_points(path)

@mcp.tool()
def get_bounding_box(path: str = DEFAULT_PATH) -> dict:
    return pct.get_bounding_box(path)

@mcp.tool()
def list_files(path: str = ".", extension: str | None = None):
    return pct.list_files(path, extension)

@mcp.tool()
def find_ply_files(path: str = ".") -> list[str]:
    return pct.find_ply_files(path)

@mcp.tool()
def visualize_pointcloud(path: str = DEFAULT_PATH) -> dict:
    """MCP tool to pop up an Open3D window for the given .ply file."""
    return pct.visualize_pointcloud(path)

if __name__ == "__main__":
    # Serve over SSE/HTTP with JSON responses
    mcp.run(transport="streamable-http")

