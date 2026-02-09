"""
Bridge Server - Multi-Client WebSocket Registry
================================================
Handles multiple browser connections with auto-discovery.
No native messaging required - browsers simply connect via WebSocket.
"""

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


# =============================================================================
# CONSTANTS
# =============================================================================

MAX_LOG_ENTRIES = 50
MAX_DOM_SIZE = 50000
STALE_DATA_TIMEOUT = 300


# =============================================================================
# CLIENT REGISTRY
# =============================================================================

class BrowserClient:
    """Represents a connected browser client."""
    
    def __init__(self, client_id: str, websocket: WebSocket):
        self.id = client_id
        self.websocket = websocket
        self.browser = "Unknown"
        self.url = ""
        self.dom_summary = ""
        self.console_logs = []
        self.network_logs = []
        self.connected_at = time.time()
        self.last_update = time.time()
        self.command_queue: asyncio.Queue = asyncio.Queue()
    
    def update(self, **kwargs):
        self.last_update = time.time()
        for key, value in kwargs.items():
            if key == "browser":
                self.browser = value
            elif key == "url":
                self.url = value
            elif key == "dom":
                self.dom_summary = value[:MAX_DOM_SIZE] if len(value) > MAX_DOM_SIZE else value
            elif key == "errors":
                if isinstance(value, list):
                    self.console_logs.extend(value)
                else:
                    self.console_logs.append(value)
                self.console_logs = self.console_logs[-MAX_LOG_ENTRIES:]
            elif key == "network":
                if isinstance(value, list):
                    self.network_logs.extend(value)
                else:
                    self.network_logs.append(value)
                self.network_logs = self.network_logs[-MAX_LOG_ENTRIES:]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "browser": self.browser,
            "url": self.url,
            "connected_seconds": int(time.time() - self.connected_at),
            "last_update_seconds_ago": int(time.time() - self.last_update)
        }
    
    def get_state(self) -> dict:
        return {
            "id": self.id,
            "browser": self.browser,
            "url": self.url,
            "dom_summary": self.dom_summary,
            "console_logs": self.console_logs,
            "network_logs": self.network_logs
        }


class ClientRegistry:
    """Manages all connected browser clients."""
    
    def __init__(self):
        self.clients: Dict[str, BrowserClient] = {}
        self.active_client_id: Optional[str] = None
    
    def add(self, websocket: WebSocket) -> BrowserClient:
        client_id = str(uuid.uuid4())[:8]
        client = BrowserClient(client_id, websocket)
        self.clients[client_id] = client
        
        # Auto-select if first client
        if self.active_client_id is None:
            self.active_client_id = client_id
        
        return client
    
    def remove(self, client_id: str):
        if client_id in self.clients:
            del self.clients[client_id]
        
        # Select next client if active was removed
        if self.active_client_id == client_id:
            self.active_client_id = next(iter(self.clients), None)
    
    def get(self, client_id: str) -> Optional[BrowserClient]:
        return self.clients.get(client_id)
    
    def get_active(self) -> Optional[BrowserClient]:
        if self.active_client_id:
            return self.clients.get(self.active_client_id)
        return None
    
    def select(self, client_id: str) -> bool:
        if client_id in self.clients:
            self.active_client_id = client_id
            return True
        return False
    
    def list_all(self) -> list:
        return [client.to_dict() for client in self.clients.values()]


# Global registry
registry = ClientRegistry()


# =============================================================================
# FASTAPI APP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Browser Bridge Server",
    description="Multi-client WebSocket bridge with auto-discovery",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "clients_connected": len(registry.clients),
        "active_client": registry.active_client_id
    }


@app.get("/clients")
async def list_clients():
    """List all connected browser clients."""
    return {
        "clients": registry.list_all(),
        "active": registry.active_client_id,
        "count": len(registry.clients)
    }


@app.post("/select/{client_id}")
async def select_client(client_id: str):
    """Select which browser to send commands to."""
    if registry.select(client_id):
        return {"success": True, "active": client_id}
    return {"success": False, "error": "Client not found"}


@app.get("/state")
async def get_state():
    """Get state of active browser client."""
    client = registry.get_active()
    if client:
        return client.get_state()
    return {"error": "No browser connected"}


@app.get("/state/{client_id}")
async def get_client_state(client_id: str):
    """Get state of specific browser client."""
    client = registry.get(client_id)
    if client:
        return client.get_state()
    return {"error": "Client not found"}


class CommandRequest(BaseModel):
    type: str
    selector: Optional[str] = None
    text: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    code: Optional[str] = None
    target: Optional[str] = None  # Optional: target specific client


@app.post("/command")
async def send_command(command: CommandRequest):
    """Send command to browser (active or specified client)."""
    # Determine target client
    target_id = command.target or registry.active_client_id
    client = registry.get(target_id) if target_id else None
    
    if not client:
        return {"success": False, "error": "No browser connected"}
    
    cmd = command.model_dump(exclude_none=True, exclude={'target'})
    await client.command_queue.put(cmd)
    return {"success": True, "message": f"Command queued for {client.browser}", "client": client.id}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Register new client
    client = registry.add(websocket)
    print(f"[Bridge] Client {client.id} connected ({len(registry.clients)} total)")
    
    async def send_commands():
        try:
            while True:
                command = await client.command_queue.get()
                await websocket.send_json(command)
                print(f"[Bridge] Sent to {client.id}: {command}")
        except asyncio.CancelledError:
            pass
    
    sender_task = asyncio.create_task(send_commands())
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle registration message
            if data.get("type") == "register":
                client.update(browser=data.get("browser", "Unknown"))
                print(f"[Bridge] Client {client.id} identified as {client.browser}")
            
            # Update client state
            if "url" in data:
                client.update(url=data["url"])
            if "dom" in data:
                client.update(dom=data["dom"])
            if "errors" in data:
                client.update(errors=data["errors"])
            if "network" in data:
                client.update(network=data["network"])
    
    except WebSocketDisconnect:
        print(f"[Bridge] Client {client.id} ({client.browser}) disconnected")
    except Exception as e:
        print(f"[Bridge] Error with {client.id}: {e}")
    finally:
        sender_task.cancel()
        registry.remove(client.id)
        print(f"[Bridge] {len(registry.clients)} client(s) remaining")


def main():
    print("=" * 50)
    print("🌉 Browser Bridge Server")
    print("=" * 50)
    print("📡 WebSocket:  ws://127.0.0.1:8000/ws")
    print("📋 Clients:    http://127.0.0.1:8000/clients")
    print("🎯 Select:     POST /select/{client_id}")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
