import os
import sys
import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay

def _ensure_exists(path: str) -> str:
    """
    1) Try the given path.
    2) Otherwise, search the entire tree for any file whose name contains the basename.
       Return the first match (first found).
    Debug prints will go to stderr so you can see resolution steps.
    """
    print(f"[debug] ensure_exists called with path: '{path}'", file=sys.stderr, flush=True)
    # exact match
    if os.path.exists(path):
        print(f"[debug] found exact path: '{path}'", file=sys.stderr, flush=True)
        return path

    key = os.path.basename(path).lower()
    print(f"[debug] file not found, searching for any file containing: '{key}'", file=sys.stderr, flush=True)
    for root, _, files in os.walk('.'):
        for name in files:
            if key in name.lower():
                resolved = os.path.join(root, name)
                print(f"[warn] '{path}' not found—using '{resolved}'", file=sys.stderr, flush=True)
                return resolved

    print(f"[error] no matches found for '{path}' → raising FileNotFoundError", file=sys.stderr, flush=True)
    raise FileNotFoundError(f"File not found: {path}")

# ─── Core tools ───────────────────────────────────────────────────────────────────

def scan_room() -> dict:
    """
    Placeholder for a “scan the room” tool.
    TODO: replace this stub with your real room-scanning logic.
    """
    return {
        "status": "scan_room executed",
        "message": "I can’t scan the room just yet, but I’ll be able to soon!"
    }

def count_points(path: str) -> int:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    return len(pc.points)

def get_bounding_box(path: str) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    bbox = pc.get_axis_aligned_bounding_box()
    return {"min": bbox.min_bound.tolist(), "max": bbox.max_bound.tolist()}

def find_ply_files(path: str = ".") -> list[str]:
    matches = []
    for root, _, files in os.walk(path):
        for name in files:
            if name.lower().endswith(".ply"):
                matches.append(os.path.join(root, name))
    return matches

def list_files(path: str = ".", extension: str | None = None) -> list[str]:
    if not os.path.isdir(path):
        path = _ensure_exists(path)
    entries = []
    for name in os.listdir(path):
        if extension:
            if name.lower().endswith(extension.lower()):
                entries.append(os.path.join(path, name))
        else:
            entries.append(os.path.join(path, name))
    return entries

def visualize_pointcloud(path: str) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    o3d.visualization.draw_geometries([pc])
    return {"status": "point cloud displayed"}

# ─── Nice visuals ────────────────────────────────────────────────────────────────

def color_by_height(path: str, colormap: str = "viridis") -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    pts = np.asarray(pc.points)
    z = pts[:, 2]
    norm = (z - z.min()) / (z.max() - z.min())
    cmap = plt.get_cmap(colormap)
    pc.colors = o3d.utility.Vector3dVector(cmap(norm)[:, :3])
    o3d.visualization.draw_geometries([pc])
    return {"status": "colored by height", "colormap": colormap}

def show_oriented_bounding_box(path: str) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    obb = pc.get_oriented_bounding_box()
    obb.color = (1, 0, 0)
    o3d.visualization.draw_geometries([pc, obb])
    return {"status": "oriented bounding box displayed"}

def visualize_voxel_grid(path: str, voxel_size: float = 0.05) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    vg = o3d.geometry.VoxelGrid.create_from_point_cloud(pc, voxel_size=voxel_size)
    o3d.visualization.draw_geometries([vg])
    return {"status": "voxel grid displayed", "voxel_size": voxel_size}

def segment_plane_colormap(
    path: str,
    distance_threshold: float = 0.01,
    ransac_n: int = 3,
    num_iterations: int = 1000,
    colormap: str = "plasma"
) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    model, inliers = pc.segment_plane(distance_threshold, ransac_n, num_iterations)
    inlier_cloud  = pc.select_by_index(inliers)             # points on the plane
    outlier_cloud = pc.select_by_index(inliers, invert=True)  # everything else
    inlier_cloud.paint_uniform_color([1.0, 0.0, 0.0])   # red
    outlier_cloud.paint_uniform_color([0.0, 1.0, 0.0])  # green
    a, b, c, d = model
    pts = np.asarray(pc.points)
    dist = np.abs((pts @ np.array([a, b, c]) + d)) / np.linalg.norm([a, b, c])
    norm = (dist - dist.min()) / (dist.max() - dist.min())
    cmap = plt.get_cmap(colormap)
    pc.colors = o3d.utility.Vector3dVector(cmap(norm)[:, :3])
    o3d.visualization.draw_geometries([pc])
    o3d.visualization.draw_geometries([inlier_cloud])
    o3d.visualization.draw_geometries([outlier_cloud])
    return {"status": "plane segmented & heatmapped", "plane_model": model}

def cluster_dbscan(path: str, eps: float = 0.02, min_points: int = 10) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    # eps - radius, min_point - minimum number of point to form core
    labels = np.array(pc.cluster_dbscan(eps=eps, min_points=min_points))
    max_label = labels.max()
    colors = plt.get_cmap("tab20")(labels / (max_label if max_label > 0 else 1))
    colors[labels < 0] = (0, 0, 0, 1)
    pc.colors = o3d.utility.Vector3dVector(colors[:, :3])
    o3d.visualization.draw_geometries([pc])
    return {"status": "DBSCAN clustering displayed", "clusters": int(max_label + 1)}

def detect_iss_keypoints(path: str, salient_radius: float = 0.005, non_max_radius: float = 0.005) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    #Intrinsic Shape Signature (more in lectures) looks how anisotropic (difference) the neightbor within a salient radius by checking the eigenvalues of the covariance matrix of those neighbors
    keypts = o3d.geometry.keypoint.compute_iss_keypoints(
        pc, salient_radius=salient_radius, non_max_radius=non_max_radius
    )
    spheres = []
    for p in keypts.points:
        s = o3d.geometry.TriangleMesh.create_sphere(radius=salient_radius * 0.5)
        s.translate(p)
        s.paint_uniform_color((1, 0, 0))
        spheres.append(s)
    pc.paint_uniform_color((0.5, 0.7, 1.0))
    o3d.visualization.draw_geometries([pc, *spheres])
    return {"status": "ISS keypoints detected", "num_keypoints": len(keypts.points)}

#Not functional yet working on this:
def show_mesh_with_texture(mesh_path: str, texture_path: str) -> dict:
    mesh_path = _ensure_exists(mesh_path)
    texture_path = _ensure_exists(texture_path)
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    mesh.textures = [o3d.io.read_image(texture_path)]
    o3d.visualization.draw_geometries([mesh])
    return {"status": "textured mesh displayed"}

import time
import open3d as o3d
import os


def animate_view(path: str, axis: str = "x", duration_sec: float = 10.0) -> dict:
    """
    Open a window, rotate the point cloud or mesh automatically for duration_sec seconds.
    """
    path = _ensure_exists(path)
    if path.lower().endswith((".ply", ".obj")):
        geom = o3d.io.read_triangle_mesh(path) if path.lower().endswith((".obj",)) \
               else o3d.io.read_point_cloud(path)
    else:
        geom = o3d.io.read_point_cloud(path)

    vis = o3d.visualization.Visualizer()
    vis.create_window()
    vis.add_geometry(geom)
    ctr = vis.get_view_control()

    start = time.time()
    while time.time() - start < duration_sec:
        if axis.lower() == "x":
            ctr.rotate(1.0, 0.0)
        else:
            ctr.rotate(0.0, 1.0)
        vis.poll_events()
        vis.update_renderer()
        time.sleep(0.01)

    vis.destroy_window()
    return {"status": f"rotated {os.path.basename(path)} for {duration_sec} seconds"}


#Not functional yet working on this:
def show_hybrid(path_pc: str, path_mesh: str) -> dict:
    path_pc = _ensure_exists(path_pc)
    path_mesh = _ensure_exists(path_mesh)
    pc = o3d.io.read_point_cloud(path_pc)
    mesh = o3d.io.read_triangle_mesh(path_mesh)
    mesh.compute_vertex_normals()
    o3d.visualization.draw_geometries([pc, mesh])
    return {"status": "hybrid scene displayed"}

# ─── Reconstruction & Segmentation ────────────────────────────────────────────────

def segment_plane(path: str,
                  distance_threshold: float = 0.01,
                  ransac_n: int = 3,
                  num_iterations: int = 1000) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    model, inliers = pc.segment_plane(distance_threshold, ransac_n, num_iterations)
    inlier_cloud = pc.select_by_index(inliers)
    outlier_cloud = pc.select_by_index(inliers, invert=True)
    inlier_cloud.paint_uniform_color((0, 1, 0))
    outlier_cloud.paint_uniform_color((1, 0, 0))
    o3d.visualization.draw_geometries([inlier_cloud, outlier_cloud])
    return {
        "status": "plane segmented (inliers green, outliers red)",
        "plane_model": model,
        "inliers": len(inliers),
        "outliers": len(pc.points) - len(inliers)
    }

def slice_cloud(path: str,
                axis: str = "z",
                num_slices: int = 5) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    pts = np.asarray(pc.points)
    idx = {"x": 0, "y": 1, "z": 2}.get(axis.lower(), 2)
    vals = pts[:, idx]
    mins, maxs = vals.min(), vals.max()
    thresholds = np.linspace(mins, maxs, num_slices + 1)
    colors = np.zeros_like(pts)
    cmap = plt.get_cmap("tab10")
    for i in range(num_slices):
        mask = (vals >= thresholds[i]) & (vals < thresholds[i + 1])
        colors[mask] = cmap(i / num_slices)[:3]
    pc.colors = o3d.utility.Vector3dVector(colors)
    o3d.visualization.draw_geometries([pc])
    return {"status": f"cloud sliced into {num_slices} along {axis}-axis", "num_slices": num_slices}

def poisson_mesh_reconstruction(path: str, depth: int = 9) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    pc.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30))
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pc, depth=depth)
    mesh.compute_vertex_normals()
    o3d.visualization.draw_geometries([mesh])
    return {"status": "poisson mesh reconstructed", "vertices": len(mesh.vertices), "triangles": len(mesh.triangles), "depth": depth}

#not functional. 
def mesh_poisson_compare(path: str,
                         depth1: int = 8,
                         depth2: int = 12) -> dict:
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    pc.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30))
    m1, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pc, depth=depth1)
    m2, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pc, depth=depth2)
    m1.paint_uniform_color((1, 0, 0))
    m2.paint_uniform_color((0, 0, 1))
    o3d.visualization.draw_geometries([m1, m2])
    return {"status": "poisson compare displayed (red=depth1, blue=depth2)", "depths": [depth1, depth2], "counts": [len(m1.triangles), len(m2.triangles)]}

def ball_pivot_mesh(path: str, radii: list[float] = [0.005, 0.01, 0.02]) -> dict:
    """
    Ball-pivoting mesh reconstruction (watertight).
    """
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    pc.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.05, max_nn=30))
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pc, o3d.utility.DoubleVector(radii)
    )
    mesh.compute_vertex_normals()
    o3d.visualization.draw_geometries([mesh])
    return {"status": "ball-pivot mesh displayed", "radii": radii}

def delaunay_mesh(path: str) -> dict:
    """
    Project to XY, do 2D Delaunay, and build a mesh.
    """
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    pts = np.asarray(pc.points)
    pts2d = pts[:, :2]
    tri = Delaunay(pts2d)
    mesh = o3d.geometry.TriangleMesh(
        vertices=o3d.utility.Vector3dVector(pts),
        triangles=o3d.utility.Vector3iVector(tri.simplices)
    )
    mesh.compute_vertex_normals()
    o3d.visualization.draw_geometries([mesh])
    return {"status": "delaunay mesh displayed", "triangles": len(tri.simplices)}

def compute_fpfh(path: str,
                 voxel_size: float = 0.05,
                 radius_normal: float = 0.1,
                 radius_feature: float = 0.25) -> dict:
    #Fast Point Feature Histogram feature dimention tell how many histogram bins
    #num point how many point survived the voxel downsample
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    down = pc.voxel_down_sample(voxel_size)
    down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100)
    )
    data = np.asarray(fpfh.data)
    return {"status": "fpfh computed", "feature_dimension": data.shape[0], "num_points": data.shape[1]}

def voxel_downsample(path: str, voxel_size: float = 0.05) -> dict:
    """
    Downsample the point cloud by a regular grid of size `voxel_size`
    and display the reduced cloud.
    """
    path = _ensure_exists(path)
    pc = o3d.io.read_point_cloud(path)
    before = len(pc.points)
    down = pc.voxel_down_sample(voxel_size)
    after = len(down.points)
    o3d.visualization.draw_geometries([down])
    return {
        "status": "point cloud voxel-downsampled and displayed",
        "voxel_size": voxel_size,
        "before": before,
        "after": after
    }

