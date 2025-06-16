# PointCloud Agent

This demo lets you chat with an assistant that can analyze point cloud files using a few MCP tools.

## Running

Run the client with:

```bash
python client.py
```

The client allocates up to 256 tokens for each LLM reply so that tool
requests are not truncated.  Generation stops whenever the model begins a
new `User:` line, allowing you to continue issuing commands without long
delays.

The assistant may choose to call tools automatically based on your questions. Tool requests are printed in the terminal along with their results.
After a tool finishes, the client sends its output back to the model so the
assistant can complete its response before you enter another command.

## Troubleshooting

If the server process terminates unexpectedly (for example because a Python
dependency like `open3d` is missing), the client prints the server's stderr
output before raising an error. This output often contains the exact import
failure or traceback so you can install the missing package and try again.

## Finding PLY files

Use the `find_ply_files` tool to search for `.ply` files recursively. For example you can ask:

```
What PLY files are under the `data` folder?
```

The assistant will call `find_ply_files` and respond with the list of matching file paths.
