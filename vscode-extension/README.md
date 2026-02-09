# 🌉 Browser Bridge

> **Connect your AI assistant to any browser tab in seconds.**

Turn your AI into a web developer's superpower. Browser Bridge streams live DOM, console errors, and network failures directly to your IDE — and lets your AI click, type, and interact with pages in real-time.

---

## ⚡ 30-Second Install

```bash
# Clone and install
git clone https://github.com/YOUR_REPO/browser-bridge.git
cd browser-bridge
./install.sh
```

**That's it.** The script automatically:
- ✅ Installs Python dependencies
- ✅ Configures MCP for Gemini, Windsurf, Claude, Cursor
- ✅ Clones the browser extension

**One manual step:** Load the browser extension in Chrome/Brave:
1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → Select `~/AntiGravityIDEconnector`

---

## 🎯 How It Works

```
┌─────────────┐     WebSocket      ┌──────────────┐      MCP       ┌────────────┐
│   Browser   │ ◄──────────────► │ Bridge Server │ ◄───────────► │   AI IDE   │
│  Extension  │     DOM/Events     │  (Python)    │    Tools       │  (Gemini)  │
└─────────────┘                    └──────────────┘                └────────────┘
```

1. **Browser extension** captures page state (DOM, errors, network)
2. **Bridge server** relays to your IDE via WebSocket
3. **MCP tools** let your AI read and control the page

---

## 💻 Supported IDEs

| IDE | Extension | MCP Tools | Auto-Configured |
|-----|-----------|-----------|-----------------|
| **VS Code** | ✅ | ✅ | ✅ |
| **Cursor** | ✅ | ✅ | ✅ |
| **Gemini CLI** | — | ✅ | ✅ |
| **Windsurf** | — | ✅ | ✅ |
| **Claude Desktop** | — | ✅ | ✅ |

---

## 🛠️ MCP Tools

Ask your AI to use these:

| Tool | What it does |
|------|--------------|
| `get_browser_state` | 📊 Get URL, DOM, console errors, network failures |
| `list_browsers` | 📋 List all connected browser tabs |
| `select_browser` | 🔀 Switch between multiple tabs |
| `click_element` | 👆 Click any element by CSS selector |
| `type_text` | ⌨️ Type into input fields |
| `verify_fix` | ✅ Check if an element exists |
| `verify_api_cors` | 🔍 Debug CORS issues |

### Example Prompts

```
"What errors are showing in the console?"
"Click the submit button"
"Type 'hello@test.com' into the email input"
"Check if the login button exists"
"Get the current browser state"
```

---

## 🚀 Quick Start

1. **Start your IDE** — Server starts automatically
2. **Open any webpage**
3. **Click Browser Bridge extension** → **Connect**
4. **Ask your AI:** `"Get the browser state"`

### Status Bar (VS Code/Cursor)

| Icon | Meaning |
|------|---------|
| `⊘ Offline` | Server not running |
| `🌐 No Browser` | Ready, no browsers connected |
| `🛡️ Brave (2)` | Connected to Brave, 2 tabs |

---

## ⚙️ Configuration

### MCP Config Locations

| IDE | Config Path |
|-----|-------------|
| Gemini CLI | `~/.gemini/antigravity/mcp_config.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |

### Manual MCP Setup

If needed, add to your IDE's MCP config:

```json
{
  "mcpServers": {
    "browser-bridge": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

### VS Code Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `browserbridge.autoStart` | `true` | Start server on IDE boot |
| `browserbridge.pythonPath` | `python3` | Python interpreter |
| `browserbridge.serverPath` | auto | Path to bridge_server.py |

---

## 🔧 Troubleshooting

### MCP Server Timeout (Windsurf)
```bash
# Test if MCP server starts
python3 /path/to/mcp_server.py
```

### Server Not Starting
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill and restart
lsof -ti :8000 | xargs kill
python3 bridge_server.py
```

### Browser Not Connecting
1. Make sure server is running (check status bar)
2. Refresh the webpage
3. Click extension popup → **Connect**

---

## 📦 Project Structure

```
browser-bridge/
├── bridge_server.py      # WebSocket server
├── mcp_server.py         # MCP tools for AI
├── install.sh            # Automated installer
├── requirements.txt      # Python deps
└── vscode-extension/     # VS Code/Cursor extension
    ├── extension.js
    └── package.json
```

---

## 🔗 Links

- **Browser Extension:** [github.com/sad1kul/AntiGravityIDEconnector](https://github.com/sad1kul/AntiGravityIDEconnector)

---

## 📋 Requirements

- Python 3.8+
- Chromium browser (Chrome, Brave, Edge, Arc)

---

## 🧑‍💻 Author

**Sadikul Islam**

## 📄 License

MIT
