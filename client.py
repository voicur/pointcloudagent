#!/usr/bin/env python3
import json
import re
import sys

import requests
from llama_cpp import Llama

MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
SERVER_URL = "http://127.0.0.1:8080/mcp/"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    temperature=0.0,
    verbose=False,
    log_level="error"
)

SYSTEM_PROMPT = """You are a minimal assistant that ONLY calls MCP tools when needed.
When you call a tool, emit EXACTLY one JSON object on its own line, with no extra text:

{"tool": "tool_name", "args": {"arg": "value"}}

Then stop. Do NOT wrap in fences or markdown.

Available tools:
  • count_points(path: str) -> int or {{ "error": str }}
  • get_bounding_box(path: str) -> dict or {{ "error": str }}
  • list_files(path: str = ".", extension: str | None = None) -> list[str]
      – omit “extension” unless the user explicitly asks for a file type
  • find_ply_files(path: str = ".") -> list[str]
  • visualize_pointcloud(path: str) -> dict
      – opens an Open3D window to visualize the .ply and returns status when closed

If the user’s request requires one of these tools, call it. Otherwise, answer normally.
"""

def ask_llm(prompt: str, stop=None, max_tokens=256) -> str:
    params = {"prompt": prompt, "temperature": 0.0, "max_tokens": max_tokens}
    if stop is not None:
        params["stop"] = stop
    resp = llm.create_completion(**params)
    return resp["choices"][0]["text"].strip()

def extract_tool_call(text: str):
    decoder = json.JSONDecoder()
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[m.start():])
            if "tool" in obj:
                # Remove empty or None extensions for list_files
                if obj["tool"] == "list_files":
                    args = obj.get("args", {})
                    if args.get("extension") in (None, "", "null"):
                        args.pop("extension", None)
                    obj["args"] = args
                return obj
        except json.JSONDecodeError:
            continue
    return None

def call_tool(request_json: dict):
    rpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": request_json["tool"],
            "arguments": request_json.get("args", {})
        }
    }
    resp = requests.post(SERVER_URL, json=rpc, headers=HEADERS, stream=True)
    resp.raise_for_status()
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        msg = json.loads(payload)
        if "result" in msg:
            return msg["result"]
        if "error" in msg:
            raise RuntimeError(msg["error"])
    raise RuntimeError("No result from MCP")

if __name__ == "__main__":
    history = SYSTEM_PROMPT
    print("PointCloudAgent LLM client (Ctrl-C to quit)")
    try:
        while True:
            user_input = input(">> ").strip()
            history += f"\nUser: {user_input}\nAssistant:"
            reply = ask_llm(history, stop=["\n"])
            print("LLM:", reply)
            history += " " + reply

            tool_call = extract_tool_call(reply)
            if tool_call:
                result = call_tool(tool_call)
                print("[Tool result]", result)
                history += f"\n{json.dumps(result)}\nAssistant:"
                final = ask_llm(history, stop=["\nUser:"])
                print("Assistant:", final)
                history += " " + final
    except KeyboardInterrupt:
        sys.exit(0)

