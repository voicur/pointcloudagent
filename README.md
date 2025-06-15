# PointCloud Agent

This demo lets you chat with an assistant that can analyze point cloud files using a few MCP tools.

## Running

Run the client with:

```bash
python client.py
```

The client allocates up to 256 tokens for each LLM reply so that tool
requests are not truncated.

The assistant may choose to call tools automatically based on your questions. Tool requests are printed in the terminal along with their results.

## Finding PLY files

Use the `find_ply_files` tool to search for `.ply` files recursively. For example you can ask:

```
What PLY files are under the `data` folder?
```

The assistant will call `find_ply_files` and respond with the list of matching file paths.
