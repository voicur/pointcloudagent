from fastmcp import FastMCP
import pointcloud_tools as pct
import os     

mcp = FastMCP(name="PointCloud Demo")

@mcp.tool
def count_points(path: str) -> int:
    """Return number of points in the file."""
    return pct.count_points(path)

@mcp.tool
def get_bounding_box(path: str) -> dict:
    """Return axis-aligned bounding box."""
    return pct.get_bounding_box(path)

@mcp.tool
def list_files(path: str = ".") -> list[str]:
    """List files and folders in the directory."""
    return os.listdir(path)

if __name__ == "__main__":
    mcp.run()        # FastMCP prints exactly one JSON line per call

