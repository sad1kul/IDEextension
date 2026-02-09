"""
MCP Server for Browser Bridge
==============================
Provides tools to the AI IDE for browser interaction with multi-client support.
"""

import asyncio
import json
from typing import Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


BRIDGE_URL = "http://127.0.0.1:8000"


# =============================================================================
# BRIDGE COMMUNICATION
# =============================================================================

def get_browser_state_from_bridge(client_id: Optional[str] = None):
    """Fetch browser state from Bridge Server."""
    try:
        url = f"{BRIDGE_URL}/state/{client_id}" if client_id else f"{BRIDGE_URL}/state"
        response = httpx.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_connected_clients():
    """Get list of connected browser clients."""
    try:
        response = httpx.get(f"{BRIDGE_URL}/clients", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def select_client(client_id: str):
    """Select which browser to control."""
    try:
        response = httpx.post(f"{BRIDGE_URL}/select/{client_id}", timeout=5)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_command_to_bridge(command: dict, target: Optional[str] = None):
    """Send command to browser via Bridge Server."""
    try:
        if target:
            command["target"] = target
        response = httpx.post(f"{BRIDGE_URL}/command", json=command, timeout=5)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# MCP SERVER
# =============================================================================

mcp_server = Server("browser-bridge")


@mcp_server.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        Tool(
            name="list_browsers",
            description="List all connected browser clients. Returns browser type, active URL, and client ID.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="select_browser",
            description="Select which browser to send commands to when multiple are connected.",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "The client ID from list_browsers output"
                    }
                },
                "required": ["client_id"]
            }
        ),
        Tool(
            name="get_browser_state",
            description="Get current state of browser including URL, console errors, network failures, and DOM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Optional: specific client ID (uses active browser if not provided)"
                    }
                },
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
                    },
                    "target": {
                        "type": "string",
                        "description": "Optional: specific client ID to target"
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
                        "description": "Text to type"
                    },
                    "target": {
                        "type": "string",
                        "description": "Optional: specific client ID to target"
                    }
                },
                "required": ["selector", "text"]
            }
        ),
        Tool(
            name="verify_fix",
            description="Verify a fix by checking DOM for element presence/absence.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to verify"
                    },
                    "expected_text": {
                        "type": "string",
                        "description": "Optional text that should be present"
                    },
                    "should_exist": {
                        "type": "boolean",
                        "description": "True to verify exists, False to verify removed",
                        "default": True
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="verify_api_cors",
            description="Test if API is reachable from Python to diagnose CORS issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "API endpoint URL"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method",
                        "enum": ["GET", "POST", "PUT", "DELETE"]
                    },
                    "payload": {
                        "type": "string",
                        "description": "Optional JSON payload"
                    }
                },
                "required": ["url", "method"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    
    if name == "list_browsers":
        return await tool_list_browsers()
    elif name == "select_browser":
        return await tool_select_browser(arguments.get("client_id", ""))
    elif name == "get_browser_state":
        return await tool_get_browser_state(arguments.get("client_id"))
    elif name == "click_element":
        return await tool_click_element(
            arguments.get("selector", ""),
            arguments.get("target")
        )
    elif name == "type_text":
        return await tool_type_text(
            arguments.get("selector", ""),
            arguments.get("text", ""),
            arguments.get("target")
        )
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

async def tool_list_browsers():
    """List all connected browsers."""
    data = get_connected_clients()
    
    if data is None:
        return [TextContent(
            type="text",
            text="⚠️ Cannot connect to Bridge Server. Start it first."
        )]
    
    if data["count"] == 0:
        return [TextContent(
            type="text",
            text="📭 No browsers connected. Open extension popup and click Connect."
        )]
    
    lines = ["📋 CONNECTED BROWSERS", "=" * 30, ""]
    for i, client in enumerate(data["clients"], 1):
        active = "→ " if client["id"] == data["active"] else "  "
        lines.append(f"{active}{i}. [{client['id']}] {client['browser']}")
        lines.append(f"     URL: {client['url'][:60]}..." if len(client['url']) > 60 else f"     URL: {client['url']}")
        lines.append("")
    
    lines.append(f"Active: {data['active']}")
    lines.append("Use select_browser to switch between browsers.")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def tool_select_browser(client_id: str):
    """Select which browser to control."""
    if not client_id:
        return [TextContent(type="text", text="❌ Error: No client_id provided.")]
    
    result = select_client(client_id)
    
    if result.get("success"):
        return [TextContent(type="text", text=f"✅ Now controlling browser: {client_id}")]
    else:
        return [TextContent(type="text", text=f"❌ Failed: {result.get('error', 'Unknown error')}")]


async def tool_get_browser_state(client_id: Optional[str] = None):
    """Get browser state."""
    state = get_browser_state_from_bridge(client_id)
    
    if state is None:
        return [TextContent(type="text", text="⚠️ Cannot connect to Bridge Server.")]
    
    if "error" in state:
        return [TextContent(type="text", text=f"⚠️ {state['error']}")]
    
    errors_text = "None" if not state.get("console_logs") else "\n".join(
        f"  - {err}" for err in state["console_logs"][-5:]
    )
    network_text = "None" if not state.get("network_logs") else "\n".join(
        f"  - {log}" for log in state["network_logs"][-5:]
    )
    dom = state.get("dom_summary", "")
    dom_snippet = dom[:2000] + "..." if len(dom) > 2000 else dom
    
    result = f"""
📊 BROWSER STATE [{state.get('browser', 'Unknown')}]
================

🔗 URL: {state.get("url", "N/A")}

🚨 Console Errors:
{errors_text}

🌐 Network Failures:
{network_text}

📄 DOM (truncated):
{dom_snippet if dom_snippet else "No DOM data"}
"""
    return [TextContent(type="text", text=result.strip())]


async def tool_click_element(selector: str, target: Optional[str] = None):
    """Click element."""
    if not selector:
        return [TextContent(type="text", text="❌ Error: No selector provided.")]
    
    result = send_command_to_bridge({"type": "click", "selector": selector}, target)
    
    if result.get("success"):
        client = result.get("client", "active browser")
        return [TextContent(type="text", text=f"✅ Clicked '{selector}' in {client}")]
    else:
        return [TextContent(type="text", text=f"❌ Failed: {result.get('error', 'Unknown error')}")]


async def tool_type_text(selector: str, text: str, target: Optional[str] = None):
    """Type text."""
    if not selector:
        return [TextContent(type="text", text="❌ Error: No selector provided.")]
    
    result = send_command_to_bridge({"type": "type", "selector": selector, "text": text}, target)
    
    if result.get("success"):
        client = result.get("client", "active browser")
        return [TextContent(type="text", text=f"✅ Typed '{text}' into '{selector}' in {client}")]
    else:
        return [TextContent(type="text", text=f"❌ Failed: {result.get('error', 'Unknown error')}")]


async def tool_verify_fix(selector: str, expected_text: Optional[str], should_exist: bool):
    """Verify DOM state."""
    state = get_browser_state_from_bridge()
    
    if state is None or "error" in state:
        return [TextContent(type="text", text="⚠️ Cannot get browser state.")]
    
    dom = state.get("dom_summary", "")
    if not dom:
        return [TextContent(type="text", text="⚠️ No DOM data available.")]
    
    # Simple CSS selector check without BeautifulSoup
    # Check if selector appears in DOM
    if should_exist:
        # Very basic check for element existence
        selector_parts = selector.replace(".", " ").replace("#", " ").replace("[", " ").replace("]", " ").split()
        found = any(part.lower() in dom.lower() for part in selector_parts if len(part) > 2)
        
        if found:
            if expected_text and expected_text in dom:
                return [TextContent(type="text", text=f"✅ Element '{selector}' likely contains '{expected_text}'.")]
            elif expected_text:
                return [TextContent(type="text", text=f"❌ Text '{expected_text}' not found in DOM.")]
            return [TextContent(type="text", text=f"✅ Element '{selector}' likely exists.")]
        return [TextContent(type="text", text=f"❌ Element '{selector}' likely NOT found.")]
    else:
        selector_parts = selector.replace(".", " ").replace("#", " ").replace("[", " ").replace("]", " ").split()
        found = any(part.lower() in dom.lower() for part in selector_parts if len(part) > 2)
        if found:
            return [TextContent(type="text", text=f"❌ Element '{selector}' likely still exists.")]
        return [TextContent(type="text", text=f"✅ Element '{selector}' likely removed.")]


async def tool_verify_api_cors(url: str, method: str, payload: Optional[str]):
    """Test API for CORS issues."""
    state = get_browser_state_from_bridge()
    network_logs = state.get("network_logs", []) if state else []
    browser_blocked = any(url in str(log) for log in network_logs)
    
    try:
        headers = {"Content-Type": "application/json"}
        
        with httpx.Client(timeout=10) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                data = json.loads(payload) if payload else {}
                response = client.post(url, json=data, headers=headers)
            elif method == "PUT":
                data = json.loads(payload) if payload else {}
                response = client.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                return [TextContent(type="text", text=f"❌ Unsupported method: {method}")]
        
        success = response.status_code < 400
        
        if success and browser_blocked:
            return [TextContent(type="text", text=f"""
🔍 CORS ISSUE DETECTED

📡 Python: Status {response.status_code}
🌐 Browser: Blocked

💡 Solution: Add 'Access-Control-Allow-Origin' header on backend.
""")]
        elif success:
            return [TextContent(type="text", text=f"✅ API reachable - Status: {response.status_code}")]
        else:
            return [TextContent(type="text", text=f"❌ API Error - Status: {response.status_code}")]
    except httpx.ConnectError:
        return [TextContent(type="text", text=f"❌ Connection Error: Cannot reach {url}")]
    except httpx.TimeoutException:
        return [TextContent(type="text", text=f"❌ Timeout")]
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
