# Browser Bridge

Connect your AI IDE to any Chromium browser for real-time debugging and remote control.

## Quick Start

1. **Install VS Code Extension** - See `/vscode-extension/README.md`
2. **Install Browser Extension** - [github.com/sad1kul/IDEconnector](https://github.com/sad1kul/IDEconnector)
3. **Open IDE** - Server starts automatically
4. **Click extension in browser** → Connect
5. **Use MCP tools** to interact with the page

## Project Structure

```
├── bridge_server.py      # WebSocket server (runs in IDE)
├── mcp_server.py         # MCP tools for AI assistants
├── vscode-extension/     # VS Code/Cursor extension
│   ├── extension.js
│   └── package.json
└── requirements.txt      # Python dependencies
```

## Requirements

```bash
pip install fastapi uvicorn websockets
```

## Links

- **VS Code Extension:** `/vscode-extension/`
- **Browser Extension:** [github.com/sad1kul/IDEconnector](https://github.com/sad1kul/IDEconnector)
- **IDE Extension (this repo):** [github.com/sad1kul/IDEextension](https://github.com/sad1kul/IDEextension)

## License

MIT
