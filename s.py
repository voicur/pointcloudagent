from fastmcp import FastMCP
import sys

mcp = FastMCP(name="Demo")

@mcp.tool
def greet(name: str = "world") -> str:
    print(f"[debug] greet called with {name}", file=sys.stderr, flush=True)
    return f"Hello, {name}!"

if __name__ == "__main__":
    print("[debug] MCP server starting", file=sys.stderr, flush=True)
    mcp.run()
