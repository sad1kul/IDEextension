#!/bin/bash
# ============================================================================
# AntiGravity Browser Bridge - One-Click Installer
# ============================================================================
# This script installs everything needed for the Browser Bridge:
# - Python dependencies
# - Chrome Extension (instructions)
# - Native Messaging Host
# - MCP Server configuration
# - VS Code Extension
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     🚀 AntiGravity Browser Bridge - Installer                ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# Step 1: Check Python
# ============================================================================
echo -e "${BLUE}[1/5]${NC} Checking Python installation..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "${GREEN}  ✓${NC} Found: $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version 2>&1)
    if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
        echo -e "${GREEN}  ✓${NC} Found: $PYTHON_VERSION"
    else
        echo -e "${RED}  ✗${NC} Python 3 is required. Please install it first."
        exit 1
    fi
else
    echo -e "${RED}  ✗${NC} Python not found. Please install Python 3 first."
    exit 1
fi

# ============================================================================
# Step 2: Install Python Dependencies
# ============================================================================
echo -e "${BLUE}[2/5]${NC} Installing Python dependencies..."

$PYTHON_CMD -m pip install -q -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || \
$PYTHON_CMD -m pip install --user -q -r "$SCRIPT_DIR/requirements.txt"

echo -e "${GREEN}  ✓${NC} Dependencies installed"

# ============================================================================
# Step 3: Chrome Extension ID
# ============================================================================
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Chrome Extension Setup Required${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  1. Open Chrome and go to: chrome://extensions"
echo "  2. Enable 'Developer mode' (top right)"
echo "  3. Click 'Load unpacked'"
echo "  4. Select: $SCRIPT_DIR/../AntiGravityIDEconnector"
echo "  5. Copy the Extension ID shown under the extension name"
echo ""
echo -e "${BLUE}[3/5]${NC} Enter your Chrome Extension ID:"
read -p "  Extension ID: " EXTENSION_ID

if [ -z "$EXTENSION_ID" ] || [ ${#EXTENSION_ID} -lt 10 ]; then
    echo -e "${RED}  ✗${NC} Invalid Extension ID. Please run this script again."
    exit 1
fi

echo -e "${GREEN}  ✓${NC} Extension ID: $EXTENSION_ID"

# ============================================================================
# Step 4: Register Native Messaging Host
# ============================================================================
echo -e "${BLUE}[4/5]${NC} Registering native messaging host..."

HOST_NAME="com.antigravity.bridge"
NATIVE_HOST_PATH="$SCRIPT_DIR/native_host.py"

# Make executable
chmod +x "$NATIVE_HOST_PATH"

# Determine Chrome directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    CHROME_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CHROME_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
else
    echo -e "${RED}  ✗${NC} Unsupported OS. Manual setup required."
    exit 1
fi

mkdir -p "$CHROME_DIR"

# Create manifest
cat > "$CHROME_DIR/${HOST_NAME}.json" << EOF
{
  "name": "${HOST_NAME}",
  "description": "AntiGravity IDE Bridge - Native Messaging Host",
  "path": "${NATIVE_HOST_PATH}",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://${EXTENSION_ID}/"
  ]
}
EOF

echo -e "${GREEN}  ✓${NC} Native messaging host registered"

# ============================================================================
# Step 5: Configure MCP
# ============================================================================
echo -e "${BLUE}[5/5]${NC} Configuring MCP server..."

MCP_SERVER_PATH="$SCRIPT_DIR/mcp_server.py"
GEMINI_CONFIG_DIR="$HOME/.gemini/antigravity"
MCP_CONFIG_PATH="$GEMINI_CONFIG_DIR/mcp_config.json"

mkdir -p "$GEMINI_CONFIG_DIR"

cat > "$MCP_CONFIG_PATH" << EOF
{
  "mcpServers": {
    "browser-bridge": {
      "command": "$PYTHON_CMD",
      "args": ["$MCP_SERVER_PATH"],
      "env": {}
    }
  }
}
EOF

echo -e "${GREEN}  ✓${NC} MCP server configured"

# ============================================================================
# Done!
# ============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Installation Complete!                                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}IMPORTANT:${NC} Please restart Chrome (close all windows)"
echo ""
echo -e "  ${CYAN}To use:${NC}"
echo "  1. Click the AntiGravity extension icon in Chrome"
echo "  2. Click 'Start Server'"
echo "  3. Navigate to any webpage"
echo "  4. Click 'Connect'"
echo "  5. Use MCP tools in your IDE!"
echo ""
echo -e "  ${CYAN}Available MCP Tools:${NC}"
echo "  • get_browser_state - Get page URL, DOM, errors"
echo "  • click_element     - Click by CSS selector"
echo "  • type_text         - Type into inputs"
echo "  • verify_fix        - Check DOM elements"
echo "  • verify_api_cors   - Diagnose CORS issues"
echo ""
