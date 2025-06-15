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
def list_files(path: str = ".", extension: str | None = None) -> list[str]:
    """List files in the directory.

    If *extension* is provided, only return files ending with that
    extension (case-insensitive) and include the full path to each
    entry.
    """
    entries = os.listdir(path)
    if extension:
        extension = extension.lstrip(".").lower()
        entries = [os.path.join(path, e)
                   for e in entries if e.lower().endswith(f".{extension}")]
    return entries

@mcp.tool
def find_ply_files(path: str = ".") -> list[str]:
    """Recursively find .ply files under the given path."""
    return pct.find_ply_files(path)

if __name__ == "__main__":
    mcp.run()        # FastMCP prints exactly one JSON line per call

