#!/usr/bin/env python3
import json
import re
import sys
import asyncio

from fastmcp import Client
from llama_cpp import Llama

MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
RPC_ENDPOINT = "http://127.0.0.1:8000/mcp/"  # matches your fastmcp run command

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
      – omit “extension” unless the user explicitly asks
  • find_ply_files(path: str = ".") -> list[str]
  • visualize_pointcloud(path: str) -> dict
      – opens an Open3D window or offscreen renders to an image

If the user’s request requires one of these tools, call it. Otherwise, answer normally.
"""

def ask_llm(prompt: str, stop=None, max_tokens=256) -> str:
    params = {"prompt": prompt, "temperature": 0.0, "max_tokens": max_tokens}
    if stop:
        params["stop"] = stop
    return llm.create_completion(**params)["choices"][0]["text"].strip()

def extract_tool_call(text: str):
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
            if "tool" in obj:
                # clean up empty extension for list_files
                if obj["tool"] == "list_files":
                    args = obj.get("args", {})
                    if args.get("extension") in (None, "", "null"):
                        args.pop("extension", None)
                    obj["args"] = args
                return obj
        except json.JSONDecodeError:
            continue
    return None

def unwrap(response):
    # Convert any TextContent or nested structure to plain Python types
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
            # Ask the LLM how to proceed
            reply = ask_llm(history, stop=["\n"])
            print("LLM:", reply)
            history += " " + reply

            call = extract_tool_call(reply)
            if not call:
                continue

            # Invoke the tool via fastmcp.Client
            raw_result = await client.call_tool(call["tool"], call.get("args", {}))
            result = unwrap(raw_result)
            print("[Tool result]", result)

            # Feed the result back to the LLM for a final natural-language answer
            history += f"\n{json.dumps(result)}\nAssistant:"
            final = ask_llm(history, stop=["\nUser:"])
            print("Assistant:", final)
            history += " " + final

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

