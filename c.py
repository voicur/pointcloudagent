import subprocess
import json
import sys
import shutil

server_proc = subprocess.Popen([
    shutil.which("python3"), "-u", "s.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)


def call_tool(tool: str, args: dict) -> dict:
    req = {"tool": tool, "args": args}
    print(f"[debug] sending {req}", file=sys.stderr, flush=True)
    server_proc.stdin.write(json.dumps(req) + "\n")
    server_proc.stdin.flush()

    for line in server_proc.stdout:
        line = line.strip()
        if line:
            print(f"[debug] received: {line}", file=sys.stderr, flush=True)
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                print(f"[debug] invalid json: {line}", file=sys.stderr, flush=True)
                continue
    raise RuntimeError("server closed")


if __name__ == "__main__":
    try:
        result = call_tool("greet", {"name": "MCP"})
        print("tool result:", result)
    finally:
        server_proc.terminate()
