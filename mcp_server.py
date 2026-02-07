"""
MCP Server for AntiGravity IDE Bridge
=====================================
This is the MCP (Model Context Protocol) server that provides tools to the AI IDE.
It communicates with the Bridge Server via HTTP to get browser state and send commands.

This file is spawned by the IDE (e.g., via stdio) when it needs to use the browser tools.
"""

import asyncio
import json
from typing import Optional

import requests
from bs4 import BeautifulSoup
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Bridge Server base URL
BRIDGE_URL = "http://127.0.0.1:8000"


def get_browser_state_from_bridge():
    """Fetch current browser state from the Bridge Server."""
    try:
        response = requests.get(f"{BRIDGE_URL}/state", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def send_command_to_bridge(command: dict):
    """Send a command to the browser via the Bridge Server."""
    try:
        response = requests.post(f"{BRIDGE_URL}/command", json=command, timeout=5)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# MCP SERVER
# =============================================================================

mcp_server = Server("antigravity-bridge")


@mcp_server.list_tools()
async def list_tools():
    """List all available tools for the AI Agent."""
    return [
        Tool(
            name="get_browser_state",
            description="Get the current state of the connected browser including URL, console errors, network failures, and DOM snapshot.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="click_element",
            description="Click on an element in the browser using a CSS selector.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to click"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="type_text",
            description="Type text into an input element in the browser.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the input element"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type into the element"
                    }
                },
                "required": ["selector", "text"]
            }
        ),
        Tool(
            name="verify_fix",
            description="Verify that a fix was applied by checking DOM for element presence/absence and content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to verify"
                    },
                    "expected_text": {
                        "type": "string",
                        "description": "Optional text that should be present in the element"
                    },
                    "should_exist": {
                        "type": "boolean",
                        "description": "True to verify element exists, False to verify it does NOT exist",
                        "default": True
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="verify_api_cors",
            description="Test if an API endpoint is reachable from Python (bypassing browser) to diagnose CORS issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The API endpoint URL to test"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, DELETE)",
                        "enum": ["GET", "POST", "PUT", "DELETE"]
                    },
                    "payload": {
                        "type": "string",
                        "description": "Optional JSON payload for POST/PUT requests"
                    }
                },
                "required": ["url", "method"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls from the AI Agent."""
    
    if name == "get_browser_state":
        return await tool_get_browser_state()
    elif name == "click_element":
        return await tool_click_element(arguments.get("selector", ""))
    elif name == "type_text":
        return await tool_type_text(arguments.get("selector", ""), arguments.get("text", ""))
    elif name == "verify_fix":
        return await tool_verify_fix(
            arguments.get("selector", ""),
            arguments.get("expected_text"),
            arguments.get("should_exist", True)
        )
    elif name == "verify_api_cors":
        return await tool_verify_api_cors(
            arguments.get("url", ""),
            arguments.get("method", "GET"),
            arguments.get("payload")
        )
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================

async def tool_get_browser_state():
    """Get current browser state from Bridge Server."""
    state = get_browser_state_from_bridge()
    
    if state is None:
        return [TextContent(
            type="text",
            text="⚠️ Cannot connect to Bridge Server. Make sure it's running (Start Server in Chrome extension)."
        )]
    
    if not state.get("connected"):
        return [TextContent(
            type="text",
            text="⚠️ Browser extension is not connected. Click 'Connect' in the Chrome extension."
        )]
    
    errors_text = "None" if not state["console_logs"] else "\n".join(
        f"  - {err}" for err in state["console_logs"][-5:]
    )
    network_text = "None" if not state["network_logs"] else "\n".join(
        f"  - {log}" for log in state["network_logs"][-5:]
    )
    dom_snippet = state["dom_summary"][:2000] + "..." if len(state["dom_summary"]) > 2000 else state["dom_summary"]
    
    result = f"""
📊 BROWSER STATE
================

🔗 Current URL: {state["url"] or "N/A"}

🚨 Recent Console Errors:
{errors_text}

🌐 Recent Network Failures:
{network_text}

📄 DOM Snapshot (truncated):
{dom_snippet if dom_snippet else "No DOM data available"}
"""
    return [TextContent(type="text", text=result.strip())]


async def tool_click_element(selector: str):
    """Send click command to browser."""
    if not selector:
        return [TextContent(type="text", text="❌ Error: No selector provided.")]
    
    result = send_command_to_bridge({"type": "click", "selector": selector})
    
    if result.get("success"):
        return [TextContent(type="text", text=f"✅ Click command sent for '{selector}'")]
    else:
        return [TextContent(type="text", text=f"❌ Failed: {result.get('error', 'Unknown error')}")]


async def tool_type_text(selector: str, text: str):
    """Send type command to browser."""
    if not selector:
        return [TextContent(type="text", text="❌ Error: No selector provided.")]
    
    result = send_command_to_bridge({"type": "type", "selector": selector, "text": text})
    
    if result.get("success"):
        return [TextContent(type="text", text=f"✅ Type command sent: '{text}' into '{selector}'")]
    else:
        return [TextContent(type="text", text=f"❌ Failed: {result.get('error', 'Unknown error')}")]


async def tool_verify_fix(selector: str, expected_text: Optional[str], should_exist: bool):
    """Verify DOM state using BeautifulSoup."""
    state = get_browser_state_from_bridge()
    
    if state is None:
        return [TextContent(type="text", text="⚠️ Cannot connect to Bridge Server.")]
    
    if not state.get("connected"):
        return [TextContent(type="text", text="⚠️ Browser extension is not connected.")]
    
    dom_summary = state.get("dom_summary", "")
    if not dom_summary:
        return [TextContent(type="text", text="⚠️ No DOM data available.")]
    
    try:
        soup = BeautifulSoup(dom_summary, "html.parser")
        elements = soup.select(selector)
        element_found = len(elements) > 0
        
        if should_exist:
            if not element_found:
                return [TextContent(type="text", text=f"❌ FAILURE: Element '{selector}' was NOT found.")]
            
            if expected_text:
                element_text = elements[0].get_text(strip=True)
                if expected_text in element_text:
                    return [TextContent(type="text", text=f"✅ SUCCESS: Element '{selector}' contains '{expected_text}'.")]
                else:
                    return [TextContent(type="text", text=f"❌ FAILURE: Text '{expected_text}' not found. Actual: '{element_text[:200]}'")]
            
            return [TextContent(type="text", text=f"✅ SUCCESS: Element '{selector}' exists.")]
        else:
            if element_found:
                return [TextContent(type="text", text=f"❌ FAILURE: Element '{selector}' still exists (expected removed).")]
            return [TextContent(type="text", text=f"✅ SUCCESS: Element '{selector}' does NOT exist (as expected).")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error parsing DOM: {str(e)}")]


async def tool_verify_api_cors(url: str, method: str, payload: Optional[str]):
    """Test API directly from Python to diagnose CORS issues."""
    state = get_browser_state_from_bridge()
    network_logs = state.get("network_logs", []) if state else []
    browser_blocked = any(url in str(log) for log in network_logs)
    
    try:
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            data = json.loads(payload) if payload else {}
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            data = json.loads(payload) if payload else {}
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return [TextContent(type="text", text=f"❌ Unsupported method: {method}")]
        
        python_success = response.status_code < 400
        
        if python_success and browser_blocked:
            return [TextContent(type="text", text=f"""
🔍 CORS ISSUE DETECTED

This is a **CORS issue**. Backend reachable by Python but blocked in Browser.

📡 Python: Status {response.status_code}
🌐 Browser: Blocked

💡 Solution: Add 'Access-Control-Allow-Origin' header on backend.
""")]
        elif python_success:
            return [TextContent(type="text", text=f"✅ API reachable - Status: {response.status_code}")]
        else:
            return [TextContent(type="text", text=f"❌ API Error (not CORS) - Status: {response.status_code}")]
    
    except requests.exceptions.ConnectionError:
        return [TextContent(type="text", text=f"❌ Connection Error: Cannot reach {url}")]
    except requests.exceptions.Timeout:
        return [TextContent(type="text", text=f"❌ Timeout: Request timed out")]
    except json.JSONDecodeError:
        return [TextContent(type="text", text=f"❌ Invalid JSON payload")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


# =============================================================================
# MAIN
# =============================================================================

async def run():
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
