# AntiGravity Browser Bridge

Connect your AI IDE to Chrome for real-time debugging, DOM inspection, and remote browser control.

## Features

- 📊 **Live DOM Streaming** - See page content in your IDE
- 🚨 **Error Capture** - Console errors streamed to IDE
- 🌐 **Network Monitoring** - Failed API calls detected
- 🖱️ **Remote Control** - Click & type via MCP tools
- 🔍 **CORS Diagnostics** - Detect and diagnose CORS issues


## Installation

### 1. Install this VS Code Extension

Open VS Code and install this extension. On first run, it will:
- ✅ Check Python installation
- ✅ Install required Python packages
- ✅ Ask for Chrome Extension ID (one-time)
- ✅ Register native messaging host
- ✅ Configure MCP server

### 2. Install Chrome Extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → Select `AntiGravityIDEconnector` folder
4. Copy the **Extension ID** shown

### 3. Run Setup

When prompted by VS Code, enter your Chrome Extension ID.

## Usage

1. **Start Server**: Use command `AntiGravity: Start Bridge Server`
2. **Connect Browser**: Click the Chrome extension icon → Connect
3. **Use MCP Tools**: The following tools are now available:
   - `get_browser_state` - Get current page info
   - `click_element` - Click by CSS selector
   - `type_text` - Type into inputs
   - `verify_fix` - Verify DOM changes
   - `verify_api_cors` - Diagnose CORS issues

### One-Click Install (Recommended)

```bash
git clone <this-repo>
cd IDEextension
./install.sh
```

### Install VSIX

```bash
cd {{Repo-Directory}}/vscode-extension
npm install -g @vscode/vsce
npx vsce package
```

The script will:
1. ✅ Install Python dependencies
2. ✅ Prompt for Chrome Extension ID
3. ✅ Register native messaging host
4. ✅ Configure MCP server

### Manual Install

See [Manual Installation Guide](vscode-extension/README.md)

## Usage

1. **Chrome Extension** → Click "Start Server"
2. **Navigate** to any webpage
3. **Click "Connect"** in extension
4. **Use MCP Tools** in your IDE:
   - `get_browser_state`
   - `click_element`
   - `type_text`
   - `verify_fix`
   - `verify_api_cors`

## Requirements

- Python 3.8+
- Chromium Browser
- AI IDE with MCP support

## Author

Sadikul Islam

## License

MIT License

