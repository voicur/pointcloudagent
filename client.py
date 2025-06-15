# client.py
import subprocess, json, shutil, re, sys
from llama_cpp import Llama

MODEL_PATH = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"

server_proc = subprocess.Popen(
    [shutil.which("python3"), "-u", "server.py"],   #  ←  -u = unbuffered
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)

llm = Llama(model_path=MODEL_PATH, n_ctx=4096, verbose=False, log_level="error")

SYSTEM_PROMPT = """You are an assistant that can call MCP tools. To invoke a
tool you must emit a single line of JSON like:
    {"tool": "tool_name", "args": {"arg": "value"}}
Wait for the tool result before continuing your reply.

Available tools:
  • count_points(path: str) -> int
        Return the number of points in a point cloud file.
  • get_bounding_box(path: str) -> dict
        Return the axis-aligned bounding box of a point cloud file.
  • list_files(path: str = ".") -> list[str]
        List files and folders in the directory.
  • find_ply_files(path: str = ".") -> list[str]
        Recursively search for files ending with ".ply".

If the user request requires file information, call a tool. Otherwise, just
answer as a normal chat assistant."""

def ask_llm(message: str) -> str:
    resp = llm.create_completion(
        prompt=f"{SYSTEM_PROMPT}\n\nUser: {message}\nAssistant:",
        temperature=0.0,
        max_tokens=256,
        stop=["\nUser:"]
    )
    return resp["choices"][0]["text"].strip()

def extract_json(txt: str):
    """Return first JSON object found in the text or ``None`` if parsing fails."""

    # Look for fenced blocks like ```json ... ```
    fence = re.search(r"```\s*json\s*(\{.*?\})\s*```", txt, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        snippet = fence.group(1)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError as e:
            print(f"[error] failed to parse fenced JSON: {e}", file=sys.stderr)

    decoder = json.JSONDecoder()
    # Scan the text for the first valid JSON object
    for idx, ch in enumerate(txt):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(txt[idx:])
            return obj
        except json.JSONDecodeError:
            continue

    print(f"[error] failed to parse JSON from: {txt!r}", file=sys.stderr)
    return None

def call_tool(request_json: dict) -> dict:
    server_proc.stdin.write(json.dumps(request_json) + "\n")
    server_proc.stdin.flush()

    # read lines until one parses as JSON
    for line in server_proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            # everything else (debug prints, etc.) is ignored
            continue
    raise RuntimeError("MCP server connection closed unexpectedly")

if __name__ == "__main__":
    print("Ask me about your point cloud or files (Ctrl-C to quit)")
    try:
        while True:
            user_msg = input(">> ").strip()
            raw = ask_llm(user_msg)
            print("Raw LLM reply:", repr(raw))

            tool_req = extract_json(raw)
            if tool_req:
                result = call_tool(tool_req)
                print(f"[Tool result] {json.dumps(result)}")
            else:
                print(raw)                    
    except KeyboardInterrupt:
        pass
    finally:
        server_proc.terminate()

