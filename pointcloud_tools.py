import open3d as o3d
import os
import sys


def count_points(path: str) -> int:
    pc = o3d.io.read_point_cloud(path)
    print(f"[debug] processed {path}  →  {len(pc.points)} points",
          file=sys.stderr, flush=True)
    return len(pc.points)

def get_bounding_box(path: str) -> dict:
    pc = o3d.io.read_point_cloud(path)
    bbox = pc.get_axis_aligned_bounding_box()
    return {"min": bbox.min_bound.tolist(), "max": bbox.max_bound.tolist()}

def find_ply_files(path: str = ".") -> list[str]:
    """Recursively search ``path`` for files ending in ``.ply``."""
    matches = []
    for root, _, files in os.walk(path):
        for name in files:
            if name.lower().endswith(".ply"):
                matches.append(os.path.join(root, name))
    print(f"[debug] searched {path}  →  {len(matches)} matches", file=sys.stderr, flush=True)
    return matches
