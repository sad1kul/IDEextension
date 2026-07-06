# Browser Bridge — IDE Extension

A VS Code / Cursor extension that runs a local WebSocket server so your browser can stay in sync with your IDE.  
Works on **macOS, Windows, and Linux**.

---

## How it works

```
Browser Extension  <──WebSocket──>  bridge_server.py  <──HTTP──>  VS Code Extension
```

The Python server is the middleman. The browser extension connects to it via WebSocket and sends live page data (URL, title, console errors). VS Code talks to the server over HTTP to read state or send commands back to the browser.

---

## Requirements

- Python 3.8 or later
- Node.js (only if you're building the extension yourself)

Install Python dependencies:

```bash
pip install fastapi uvicorn websockets
```

---

## Setup

### 1. Install the VS Code extension

Install from [Open VSX](https://open-vsx.org/extension/sad1kul/browser-bridge) or manually:

```
Extensions panel → ... → Install from VSIX
```

### 2. Point the extension to bridge_server.py

Open the command palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run:

```
Browser Bridge: Configure Server Path
```

Examples:
- **macOS / Linux:** `/home/yourname/browser-bridge/bridge_server.py`
- **Windows:** `C:\Users\yourname\browser-bridge\bridge_server.py`

### 3. Install the browser extension

Load the `IDEconnector` folder as an unpacked extension:

1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `IDEconnector` folder

### 4. Connect

1. The server starts automatically when VS Code opens (or run **Browser Bridge: Start Server**)
2. Click the Browser Bridge icon in your browser toolbar
3. Hit **Connect This Tab**
4. The status bar in VS Code will show the connected browser name

---

## Commands

| Command | What it does |
|---|---|
| `Browser Bridge: Show Menu` | Quick-pick menu for all actions |
| `Browser Bridge: Start Server` | Start the Python bridge server |
| `Browser Bridge: Stop Server` | Stop the server |
| `Browser Bridge: Restart Server` | Restart the server |
| `Browser Bridge: Select Browser` | Switch between connected tabs |
| `Browser Bridge: Configure Server Path` | Set path to `bridge_server.py` |

---

## Settings

| Setting | Default | Description |
|---|---|---|
| `browserbridge.serverPath` | _(empty)_ | Full path to `bridge_server.py`. Leave empty to auto-detect. |
| `browserbridge.pythonPath` | _(empty)_ | Python interpreter. Defaults to `python3` on mac/linux, `python` on Windows. |
| `browserbridge.autoStart` | `true` | Start the server automatically when VS Code opens. |

---

## Project structure

```
├── bridge_server.py          # FastAPI WebSocket server
├── mcp_server.py             # MCP tool definitions (for AI assistants)
├── requirements.txt          # Python dependencies
├── install.sh                # Setup script (macOS/Linux)
└── vscode-extension/
    ├── extension.js
    ├── package.json
    └── icon.png
```

---

## Troubleshooting

**Status bar shows Offline**  
The server is not running. Open the command palette and run `Browser Bridge: Start Server`.

**bridge_server.py not found**  
Run `Browser Bridge: Configure Server Path` and set the correct path.

**Port 8000 already in use**  
Another process is using port 8000. Stop it or change the port in `bridge_server.py` (and update `BRIDGE_URL` in `extension.js`).

**Windows: server doesn't stop cleanly**  
Run `Browser Bridge: Restart Server` — it will kill by stored PID.

---

## License

MIT
