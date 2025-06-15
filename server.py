from fastmcp import FastMCP
import pointcloud_tools as pct
import os

DEFAULT_PATH = "data/bunny.ply"

mcp = FastMCP(name="PointCloud Demo")

@mcp.tool
def count_points(path: str = DEFAULT_PATH) -> int:
    """Return number of points in the file.

    If ``path`` does not exist, the default ``data/bunny.ply`` is used.
    """
    if os.path.exists(path):
        return pct.count_points(path)
    return pct.count_points(DEFAULT_PATH)

@mcp.tool
def get_bounding_box(path: str = DEFAULT_PATH) -> dict:
    """Return axis-aligned bounding box.

    If ``path`` does not exist, the default ``data/bunny.ply`` is used.
    """
    if os.path.exists(path):
        return pct.get_bounding_box(path)
    return pct.get_bounding_box(DEFAULT_PATH)

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

