#!/usr/bin/env python3
"""
Robot MCP Client demo
─────────────────────
• Assistant's name is "V" (case-insensitive).
• Prints **only** V's final replies (in green).
• Prints raw server/tool "message" in red (no JSON).
• Intercepts greetings so no JSON/tool calls ever get printed.
• Calls MCP tools only when you explicitly mention robot commands.
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

print(Fore.RED + "Machine: Executing robot commands at red-hot speed." + Style.RESET_ALL)
print(Fore.GREEN + "LLM: Ready to interact with users and control robots via MCP.\n\n" + Style.RESET_ALL)

# ── Configuration ────────────────────────────────────────────────────────────
MODEL_PATH   = "./models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
RPC_ENDPOINT = "stdio+ssh://user@jetson-ip:python /path/to/simplemcp.py"  # Adjust this for your setup

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=8192,
    temperature=0.0,
    verbose=False,
    log_level="error"
)

SYSTEM_PROMPT = """\
Your name is V. Respond to "V" or "v".
You respond as normal for greetings, chit-chat, questions—reply normally in plain text.
Only call an MCP tool when the user explicitly requests robot actions or commands.

Available robot tools:
  • move_forward(distance: float = 1.0) - Move robot forward by distance in meters
  • move_backward(distance: float = 1.0) - Move robot backward by distance in meters
  • turn_left(degrees: float = 90) - Turn robot left by degrees
  • turn_right(degrees: float = 90) - Turn robot right by degrees
  • get_status() - Get current robot status and position
  • stop() - Stop all robot movement
  • charge_battery(amount: float = 25) - Charge robot battery by amount (1-100)
  • reset_robot() - Reset robot to initial state

Examples of when to call tools:
- "move forward 2 meters" → {"tool": "move_forward", "args": {"distance": 2.0}}
- "turn left" → {"tool": "turn_left", "args": {}}
- "check robot status" → {"tool": "get_status", "args": {}}
- "charge the battery" → {"tool": "charge_battery", "args": {}}

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
    """Extract the actual response message from MCP response"""
    if hasattr(resp, "text"):
        txt = resp.text
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            return txt
    if isinstance(resp, list):
        if len(resp) > 0 and hasattr(resp[0], "text"):
            return resp[0].text
        return [unwrap(r) for r in resp]
    if isinstance(resp, dict):
        return {k: unwrap(v) for k, v in resp.items()}
    return resp

async def main():
    history = SYSTEM_PROMPT
    client  = Client(RPC_ENDPOINT)

    print(green("🤖 Robot MCP Client ready! Try commands like:"))
    print(green("   • 'move forward 2 meters'"))
    print(green("   • 'turn left 90 degrees'"))
    print(green("   • 'check status'"))
    print(green("   • 'charge battery'"))
    print(green("   • 'stop robot'\n"))

    async with client:
        while True:
            user = input(">>> ").strip()
            if not user:
                continue
                
            history += f"\nUser: {user}\nAssistant:"

            # 1) Pure greetings → direct LLM reply
            if GREETING_RE.match(user):
                reply = ask_llm(history, stop=["\n"])
                print(green(reply))
                history += " " + reply
                continue

            # 2) Ask LLM for draft (may emit JSON tool call)
            draft = ask_llm(history)
            call  = extract_tool_call(draft)

            if call:
                # Perform the robot tool call
                try:
                    print(f"🔧 Calling tool: {call['tool']} with args: {call.get('args', {})}")
                    raw    = await client.call_tool(call["tool"], call.get("args", {}))
                    result = unwrap(raw)
                    
                    # Print robot response in red
                    if isinstance(result, str):
                        message = result
                    elif isinstance(result, list) and len(result) > 0:
                        message = str(result[0])
                    else:
                        message = str(result)
                        
                    print(red(message))

                    # 3) Feed result back to LLM for wrap-up
                    history += f"\nTool result: {message}\nAssistant:"
                    final = ask_llm(history, stop=["\n"])
                    if final.strip():
                        print(green(final))
                    history += " " + final

                except ToolError as e:
                    error_msg = f"❌ Tool error: {str(e)}"
                    print(red(error_msg))
                    history += f"\nTool error: {error_msg}\nAssistant:"
                    final = ask_llm(history, stop=["\n"])
                    if final.strip():
                        print(green(final))
                    history += " " + final
                    
                except Exception as e:
                    error_msg = f"❌ Unexpected error: {str(e)}"
                    print(red(error_msg))
                    history += f"\nUnexpected error: {error_msg}\nAssistant:"
                    final = ask_llm(history, stop=["\n"])
                    if final.strip():
                        print(green(final))
                    history += " " + final

            else:
                # 4) Direct plain-text reply
                print(green(draft))
                history += " " + draft

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(green("\n👋 Goodbye!"))
        sys.exit(0)
