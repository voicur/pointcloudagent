#!/usr/bin/env python3
import json
import re
import sys
import asyncio

from fastmcp import Client
from llama_cpp import Llama

MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
RPC_ENDPOINT = "http://127.0.0.1:8000/mcp/"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=8192,           # use full capacity of the model
    temperature=0.0,
    verbose=False,
    log_level="error"
)

SYSTEM_PROMPT = """You are a minimal assistant that ONLY calls MCP tools when needed.
When you call a tool, emit EXACTLY one JSON object on its own line, with no extra text:

{"tool": "tool_name", "args": {"arg": "value"}}

Then stop. Do NOT wrap in fences or markdown.

Available tools:
  • count_points(path: str)
  • get_bounding_box(path: str)
  • find_ply_files(path: str)
  • list_files(path: str, extension: str | None)
  • visualize_pointcloud(path: str)
  • color_by_height(path: str, colormap: str)
  • show_oriented_bounding_box(path: str)
  • visualize_voxel_grid(path: str, voxel_size: float)
  • voxel_downsample(path: str, voxel_size: float)
  • segment_plane_colormap(path: str,
                           distance_threshold: float,
                           ransac_n: int,
                           num_iterations: int,
                           colormap: str)
  • cluster_dbscan(path: str, eps: float, min_points: int)
  • detect_iss_keypoints(path: str,
                         salient_radius: float,
                         non_max_radius: float)
  • show_mesh_with_texture(mesh_path: str, texture_path: str)
  • animate_view(path: str, axis: str, n_frames: int, output_folder: str)
  • show_hybrid(path_pc: str, path_mesh: str)
  • segment_plane(path: str,
                  distance_threshold: float,
                  ransac_n: int,
                  num_iterations: int)
  • slice_cloud(path: str, axis: str, num_slices: int)
  • poisson_mesh_reconstruction(path: str, depth: int)
  • mesh_poisson_compare(path: str, depth1: int, depth2: int)
  • ball_pivot_mesh(path: str, radii: list[float])
  • delaunay_mesh(path: str)
  • compute_fpfh(path: str,
                 voxel_size: float,
                 radius_normal: float,
                 radius_feature: float)

If the user’s request requires one of these tools, call it. Otherwise, answer normally.
"""

def ask_llm(prompt: str, stop=None, max_tokens=256) -> str:
    params = {
        "prompt": prompt,
        "temperature": 0.0,
        "max_tokens": max_tokens
    }
    if stop:
        params["stop"] = stop
    return llm.create_completion(**params)["choices"][0]["text"].strip()

def extract_tool_call(text: str):
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
            if "tool" in obj:
                return obj
        except json.JSONDecodeError:
            continue
    return None

def unwrap(response):
    if hasattr(response, "text"):
        return response.text
    if isinstance(response, list):
        return [unwrap(item) for item in response]
    if isinstance(response, dict):
        return {k: unwrap(v) for k, v in response.items()}
    return response

async def main():
    history = SYSTEM_PROMPT
    print("PointCloudAgent (Ctrl-C to quit)")
    client = Client(RPC_ENDPOINT)
    async with client:
        while True:
            user_input = input(">> ").strip()
            history += f"\nUser: {user_input}\nAssistant:"
            reply = ask_llm(history, stop=["\n"])
            print("LLM:", reply)
            history += " " + reply

            call = extract_tool_call(reply)
            if not call:
                continue

            raw_result = await client.call_tool(call["tool"], call.get("args", {}))
            result = unwrap(raw_result)
            print("[Tool result]", result)

            history += f"\n{json.dumps(result)}\nAssistant:"
            final = ask_llm(history, stop=["\nUser:"])
            print("Assistant:", final)
            history += " " + final

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

