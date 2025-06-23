#!/usr/bin/env python3
import os
import pointcloud_tools as pct
from fastmcp import FastMCP

mcp = FastMCP(
    "PointCloudDemo",
    stateless_http=True,
    host="127.0.0.1",
    port=8000,
)

# default file for point‐cloud tools
DEFAULT_PLY = "data/bunny.ply"

# ─── Core tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def count_points(path: str = DEFAULT_PLY) -> int:
    return pct.count_points(path)

@mcp.tool()
def get_bounding_box(path: str = DEFAULT_PLY) -> dict:
    return pct.get_bounding_box(path)

@mcp.tool()
def find_ply_files(path: str = ".") -> list[str]:
    return pct.find_ply_files(path)

@mcp.tool()
def list_files(path: str = ".", extension: str | None = None) -> list[str]:
    return pct.list_files(path, extension)

@mcp.tool()
def visualize_pointcloud(path: str = DEFAULT_PLY) -> dict:
    return pct.visualize_pointcloud(path)

# ─── Nice visuals ─────────────────────────────────────────────────────────────

@mcp.tool()
def color_by_height(path: str = DEFAULT_PLY, colormap: str = "viridis") -> dict:
    return pct.color_by_height(path, colormap)

@mcp.tool()
def show_oriented_bounding_box(path: str = DEFAULT_PLY) -> dict:
    return pct.show_oriented_bounding_box(path)

@mcp.tool()
def visualize_voxel_grid(path: str = DEFAULT_PLY, voxel_size: float = 0.05) -> dict:
    return pct.visualize_voxel_grid(path, voxel_size)

@mcp.tool()
def segment_plane_colormap(
    path: str = DEFAULT_PLY,
    distance_threshold: float = 0.01,
    ransac_n: int = 3,
    num_iterations: int = 1000,
    colormap: str = "plasma"
) -> dict:
    return pct.segment_plane_colormap(path, distance_threshold, ransac_n, num_iterations, colormap)

@mcp.tool()
def cluster_dbscan(path: str = DEFAULT_PLY, eps: float = 0.02, min_points: int = 10) -> dict:
    return pct.cluster_dbscan(path, eps, min_points)

@mcp.tool()
def detect_iss_keypoints(path: str = DEFAULT_PLY,
                         salient_radius: float = 0.005,
                         non_max_radius: float = 0.005) -> dict:
    return pct.detect_iss_keypoints(path, salient_radius, non_max_radius)

@mcp.tool()
def show_mesh_with_texture(mesh_path: str, texture_path: str) -> dict:
    return pct.show_mesh_with_texture(mesh_path, texture_path)

@mcp.tool()
def animate_view(path: str = DEFAULT_PLY,
                 axis: str = "y",
                 n_frames: int = 120,
                 output_folder: str = "frames") -> dict:
    return pct.animate_view(path, axis, n_frames, output_folder)

@mcp.tool()
def show_hybrid(path_pc: str = DEFAULT_PLY, path_mesh: str = DEFAULT_PLY) -> dict:
    return pct.show_hybrid(path_pc, path_mesh)

# ─── Reconstruction & Segmentation ────────────────────────────────────────────

@mcp.tool()
def segment_plane(path: str = DEFAULT_PLY,
                  distance_threshold: float = 0.01,
                  ransac_n: int = 3,
                  num_iterations: int = 1000) -> dict:
    return pct.segment_plane(path, distance_threshold, ransac_n, num_iterations)

@mcp.tool()
def slice_cloud(path: str = DEFAULT_PLY,
                axis: str = "z",
                num_slices: int = 5) -> dict:
    return pct.slice_cloud(path, axis, num_slices)

@mcp.tool()
def poisson_mesh_reconstruction(path: str = DEFAULT_PLY, depth: int = 9) -> dict:
    return pct.poisson_mesh_reconstruction(path, depth)

@mcp.tool()
def mesh_poisson_compare(path: str = DEFAULT_PLY,
                         depth1: int = 8,
                         depth2: int = 12) -> dict:
    return pct.mesh_poisson_compare(path, depth1, depth2)

@mcp.tool()
def ball_pivot_mesh(path: str = DEFAULT_PLY,
                    radii: list[float] = [0.005, 0.01, 0.02]) -> dict:
    return pct.ball_pivot_mesh(path, radii)

@mcp.tool()
def delaunay_mesh(path: str = DEFAULT_PLY) -> dict:
    return pct.delaunay_mesh(path)

@mcp.tool()
def voxel_downsample(path: str = DEFAULT_PLY, voxel_size: float = 0.05) -> dict:
    return pct.voxel_downsample(path, voxel_size)

# ─── Features & Registration ────────────────────────────────────────────────────

@mcp.tool()
def compute_fpfh(path: str = DEFAULT_PLY,
                 voxel_size: float = 0.05,
                 radius_normal: float = 0.1,
                 radius_feature: float = 0.25) -> dict:
    return pct.compute_fpfh(path, voxel_size, radius_normal, radius_feature)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", stateless_http=True)

