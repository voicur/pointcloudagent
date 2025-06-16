import open3d as o3d
import os
import sys

def _ensure_exists(path: str) -> None:
    """Raise FileNotFoundError if path does not exist."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

def count_points(path: str) -> int:
    _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    print(f"[debug] processed {path}  →  {len(pc.points)} points",
          file=sys.stderr, flush=True)
    return len(pc.points)

def get_bounding_box(path: str) -> dict:
    _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    bbox = pc.get_axis_aligned_bounding_box()
    return {"min": bbox.min_bound.tolist(), "max": bbox.max_bound.tolist()}

def find_ply_files(path: str = ".") -> list[str]:
    """Recursively search path for .ply files."""
    matches = []
    for root, _, files in os.walk(path):
        for name in files:
            if name.lower().endswith(".ply"):
                matches.append(os.path.join(root, name))
    print(f"[debug] searched {path}  →  {len(matches)} matches",
          file=sys.stderr, flush=True)
    return matches

def list_files(path: str = ".", extension: str | None = None) -> list[str]:
    """
    List all files and folders in *path*. If *extension* is provided,
    only return entries ending with that extension (case-insensitive).
    Always returns full paths.
    """
    _ensure_exists(path)
    entries = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if extension:
            ext = extension.lstrip(".").lower()
            if name.lower().endswith(f".{ext}"):
                entries.append(full)
        else:
            entries.append(full)
    return entries

def visualize_pointcloud(path: str) -> dict:
    """
    Load the point cloud at *path* and open an Open3D visualizer.
    Blocks until you close the window.
    Returns a status dict.
    """
    _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    if pc.is_empty():
        return {"error": "Point cloud is empty or failed to load."}
    # Launch the GUI; blocks until window is closed
    o3d.visualization.draw_geometries([pc])
    return {"status": "visualization complete"}

