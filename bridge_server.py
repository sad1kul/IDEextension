"""
Bridge Server - WebSocket Only
==============================
This is the WebSocket server that handles browser communication.
Started by the Chrome extension via Native Messaging.
MCP server runs separately (spawned by the IDE).
"""

import asyncio
import json
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


# =============================================================================
# STATE MANAGEMENT (The "Brain")
# =============================================================================

class BrowserState:
    """Thread-safe global state manager for browser information."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            "connected": False,
            "url": "",
            "dom_summary": "",
            "console_logs": [],
            "network_logs": [],
        }
        self.command_queue: asyncio.Queue = None
    
    def update(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                if key in self._state:
                    if key in ("console_logs", "network_logs"):
                        if isinstance(value, list):
                            self._state[key].extend(value)
                        else:
                            self._state[key].append(value)
                        self._state[key] = self._state[key][-50:]
                    else:
                        self._state[key] = value
    
    def get(self, key: str):
        with self._lock:
            return self._state.get(key)
    
    def get_all(self) -> dict:
        with self._lock:
            return self._state.copy()
    
    def set_connected(self, status: bool):
        with self._lock:
            self._state["connected"] = status


# Global state
browser_state = BrowserState()


# =============================================================================
# FASTAPI + WEBSOCKET SERVER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    browser_state.command_queue = asyncio.Queue()
    yield


app = FastAPI(
    title="AntiGravity Bridge Server",
    description="WebSocket bridge between Chrome and AI IDE",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "browser_connected": browser_state.get("connected")
    }


@app.get("/state")
async def get_state():
    return browser_state.get_all()


@app.post("/command")
async def send_command(command: dict):
    """HTTP endpoint to send commands to browser (for MCP server to use)."""
    if not browser_state.get("connected"):
        return {"success": False, "error": "Browser not connected"}
    
    await browser_state.command_queue.put(command)
    return {"success": True, "message": "Command queued"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    browser_state.set_connected(True)
    print("[Bridge] Browser extension connected")
    
    async def send_commands():
        try:
            while True:
                command = await browser_state.command_queue.get()
                await websocket.send_json(command)
                print(f"[Bridge] Sent command: {command}")
        except asyncio.CancelledError:
            pass
    
    sender_task = asyncio.create_task(send_commands())
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if "url" in data:
                browser_state.update(url=data["url"])
            if "dom" in data:
                browser_state.update(dom_summary=data["dom"])
            if "errors" in data:
                browser_state.update(console_logs=data["errors"])
            if "network" in data:
                browser_state.update(network_logs=data["network"])
            
            print(f"[Bridge] Updated - URL: {browser_state.get('url')[:60]}...")
    
    except WebSocketDisconnect:
        print("[Bridge] Browser extension disconnected")
    except Exception as e:
        print(f"[Bridge] Error: {e}")
    finally:
        sender_task.cancel()
        browser_state.set_connected(False)


def main():
    print("=" * 50)
    print("🌉 AntiGravity Bridge Server")
    print("=" * 50)
    print("📡 WebSocket: ws://127.0.0.1:8000/ws")
    print("📊 Health:    http://127.0.0.1:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
