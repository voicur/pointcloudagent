import os
import sys
import open3d as o3d

# 1) Check that the DISPLAY environment variable is set (X11)
disp = os.environ.get("DISPLAY")
print("DISPLAY =", disp)
if not disp:
    print("⚠️  No DISPLAY—X11 may not be available or you need X11 forwarding.")
    sys.exit(1)

# 2) Try reading a small point cloud (or create a dummy one)
pcd_path = "data/bunny.ply"  # adjust to a real .ply path
if os.path.exists(pcd_path):
    pcd = o3d.io.read_point_cloud(pcd_path)
else:
    print(f"⚠️  {pcd_path} not found, creating a simple point cloud.")
    import numpy as np
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.random.randn(1000,3))

# 3) Attempt to open the visualizer
print("Attempting interactive visualization…")
try:
    o3d.visualization.draw_geometries([pcd])
    print("✅  Interactive window succeeded.")
except Exception as e:
    print("❌  Interactive draw_geometries() failed:")
    print("   ", e)
    sys.exit(1)

