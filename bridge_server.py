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
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


# =============================================================================
# MEMORY MANAGEMENT CONSTANTS
# =============================================================================

MAX_LOG_ENTRIES = 50          # Maximum console/network log entries
MAX_DOM_SIZE = 50000          # Maximum DOM summary size in characters
STALE_DATA_TIMEOUT = 300      # Clear data after 5 minutes of inactivity


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
        self._last_update = time.time()
        self.command_queue: asyncio.Queue = None
    
    def update(self, **kwargs):
        with self._lock:
            self._last_update = time.time()
            for key, value in kwargs.items():
                if key in self._state:
                    if key in ("console_logs", "network_logs"):
                        # Append and trim to max entries
                        if isinstance(value, list):
                            self._state[key].extend(value)
                        else:
                            self._state[key].append(value)
                        self._state[key] = self._state[key][-MAX_LOG_ENTRIES:]
                    elif key == "dom_summary":
                        # Truncate large DOM to prevent memory issues
                        self._state[key] = value[:MAX_DOM_SIZE] if len(value) > MAX_DOM_SIZE else value
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
            if not status:
                # Clear stale data on disconnect
                self._clear_volatile_data()
    
    def _clear_volatile_data(self):
        """Clear logs but keep URL and connection status."""
        self._state["console_logs"] = []
        self._state["network_logs"] = []
        self._state["dom_summary"] = ""
    
    def check_stale_and_cleanup(self):
        """Check if data is stale and cleanup if needed."""
        with self._lock:
            if time.time() - self._last_update > STALE_DATA_TIMEOUT:
                self._clear_volatile_data()
                return True
        return False
    
    def get_memory_stats(self) -> dict:
        """Get memory usage statistics."""
        with self._lock:
            return {
                "console_log_count": len(self._state["console_logs"]),
                "network_log_count": len(self._state["network_logs"]),
                "dom_size_chars": len(self._state["dom_summary"]),
                "last_update_seconds_ago": int(time.time() - self._last_update)
            }


# Global state
browser_state = BrowserState()


# =============================================================================
# PERIODIC CLEANUP TASK
# =============================================================================

async def periodic_cleanup():
    """Background task to periodically check and cleanup stale data."""
    while True:
        await asyncio.sleep(60)  # Check every minute
        if browser_state.check_stale_and_cleanup():
            print("[Bridge] Cleaned up stale data (inactive > 5 min)")


# =============================================================================
# FASTAPI + WEBSOCKET SERVER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    browser_state.command_queue = asyncio.Queue()
    # Start periodic cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    cleanup_task.cancel()


app = FastAPI(
    title="Browser Bridge Server",
    description="WebSocket bridge between Chrome and AI IDE",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "browser_connected": browser_state.get("connected"),
        "memory_stats": browser_state.get_memory_stats()
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
            
            url = browser_state.get('url')
            print(f"[Bridge] Updated - URL: {url[:60] if url else 'N/A'}...")
    
    except WebSocketDisconnect:
        print("[Bridge] Browser extension disconnected")
    except Exception as e:
        print(f"[Bridge] Error: {e}")
    finally:
        sender_task.cancel()
        browser_state.set_connected(False)


def main():
    print("=" * 50)
    print("🌉 Browser Bridge Server")
    print("=" * 50)
    print("📡 WebSocket: ws://127.0.0.1:8000/ws")
    print("📊 Health:    http://127.0.0.1:8000/health")
    print("🧠 Memory:    Auto-cleanup after 5 min inactivity")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
