#!/usr/bin/env python3
"""
PointCloudAgent demo client
───────────────────────────
• Assistant’s name is “V” (case-insensitive).
• Prints **only** V’s final replies (in green).
• Prints raw server/tool “message” in red (no JSON).
• Intercepts greetings so no JSON/tool calls ever get printed.
• Calls MCP tools only when you explicitly mention a filepath or tool args.
• Gracefully handles tool errors without crashing.
"""



import json
import re
import sys
import asyncio

from fastmcp import Client
from fastmcp.exceptions import ToolError
from llama_cpp import Llama
from colorama import init, Fore, Style   # pip install colorama

#!/usr/bin/env python3
from colorama import init, Fore, Style

init(autoreset=True)

print("\n\nIts the year of Agentic AI (Sense, Decide, Act and Interact) With new releases and capabilities like MCP it is now possible to call tools and provide...")

print(Fore.RED + "Machine: Executing tool chains at red-hot speed." + Style.RESET_ALL)
print(Fore.GREEN + "LLM: Ready to interact with users and MCP’s.\n\n" + Style.RESET_ALL)


# ── Configuration ────────────────────────────────────────────────────────────
MODEL_PATH   = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
RPC_ENDPOINT = "http://127.0.0.1:8000/mcp/"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=8192,
    temperature=0.0,
    verbose=False,
    log_level="error"
)

SYSTEM_PROMPT = """\
Your name is V. Respond to “V” or “v”.
You respond as normal for greetings, chit-chat, questions—reply normally in plain text.
Only call an MCP tool when the user explicitly provides:
  • a filepath (e.g. .ply, .obj) or
  • clear tool-specific parameters.

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
  • animate_view(path: str, axis: str, duration_sec: float)
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
  • scan_room()
  • compute_fpfh(path: str,
                 voxel_size: float,
                 radius_normal: float,
                 radius_feature: float)

When calling a tool, emit **exactly one** JSON object on its own line:
{"tool": "tool_name", "args": {"arg": "value"}}
No markdown, no code fences.
"""

# Regex to detect JSON in LLM output
JSON_RE     = re.compile(r"\{")
# Regex to detect simple greetings to V
GREETING_RE = re.compile(r"^\s*(?:hi|hello|hey)(?:\s+v)?[!?.]?\s*$", re.IGNORECASE)

# Initialize colorama
init(autoreset=True)
def red(txt: str)   -> str: return f"{Fore.RED}{txt}{Style.RESET_ALL}"
def green(txt: str) -> str: return f"{Fore.GREEN}{txt}{Style.RESET_ALL}"

def ask_llm(prompt: str, stop=None, max_tokens=256) -> str:
    params = {"prompt": prompt, "temperature": 0.0, "max_tokens": max_tokens}
    if stop:
        params["stop"] = stop
    return llm.create_completion(**params)["choices"][0]["text"].strip()

def extract_tool_call(text: str):
    decoder = json.JSONDecoder()
    for match in JSON_RE.finditer(text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
            if isinstance(obj, dict) and "tool" in obj:
                return obj
        except json.JSONDecodeError:
            continue
    return None

def unwrap(resp):
    if hasattr(resp, "text"):
        txt = resp.text
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            return txt
    if isinstance(resp, list):
        return [unwrap(r) for r in resp]
    if isinstance(resp, dict):
        return {k: unwrap(v) for k, v in resp.items()}
    return resp

async def main():
    history = SYSTEM_PROMPT
    client  = Client(RPC_ENDPOINT)

    async with client:
        while True:
            user = input(">>> ").strip()
            history += f"\nUser: {user}\nAssistant:"

            # 1) Pure greetings → direct LLM reply
            if GREETING_RE.match(user):
                reply = ask_llm(history, stop=["\n"])
                print(green(reply))
                history += " " + reply
                continue

            # 2) Ask LLM for draft (may emit JSON tool call)
            # draft = ask_llm(history, stop=["\n"])
            draft = ask_llm(history)
            call  = extract_tool_call(draft)

            if call:
                # Perform the tool call
                try:
                    raw    = await client.call_tool(call["tool"], call.get("args", {}))
                    result = unwrap(raw)
                except ToolError as e:
                    result = {"error": str(e)}
                except Exception as e:
                    result = {"error": f"Unexpected: {e}"}

                # 3) Print only the 'message' field in red
                message = None
                if isinstance(result, dict) and "message" in result:
                    message = result["message"]
                elif isinstance(result, list) and result and isinstance(result[0], dict) and "message" in result[0]:
                    message = result[0]["message"]
                else:
                    message = str(result)
                print(red(message))

                # 4) Feed full result back to LLM for wrap-up
                history += f"\n{json.dumps(result, ensure_ascii=False)}\nAssistant:"
                final = ask_llm(history, stop=["\n"])
                # print(green(final))
                history += " " + final

            else:
                # 5) Direct plain-text reply
                # print(green(draft))
                history += " " + draft

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
