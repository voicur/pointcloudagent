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
        temperature=0.0
    )
    return resp["choices"][0]["text"].strip()

def extract_json(txt: str):
    for m in re.finditer(r"\{.*?\}", txt, flags=re.DOTALL):
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
    return None

def call_tool(request_json: dict) -> dict:
    server_proc.stdin.write(json.dumps(request_json) + "\n")
    server_proc.stdin.flush()

    # read lines until one is valid JSON
    for line in server_proc.stdout:
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)            
        # everything else (debug prints, etc.) is ignored
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
                print(f"[Tool result] {result}")
            else:
                print(raw)                    
    except KeyboardInterrupt:
        pass
    finally:
        server_proc.terminate()

