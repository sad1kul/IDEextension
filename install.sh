#!/bin/bash
# =============================================================================
# Browser Bridge - Automated Installation Script
# =============================================================================
# This script automatically:
# 1. Installs Python dependencies
# 2. Configures MCP for supported IDEs (Gemini CLI, Cursor, Windsurf, Claude)
# 3. Installs VS Code extension (if applicable)
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           🌉 Browser Bridge - Installation Script             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get script directory (where Bridge files are located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MCP_SERVER_PATH="$SCRIPT_DIR/mcp_server.py"
BRIDGE_SERVER_PATH="$SCRIPT_DIR/bridge_server.py"

echo -e "${YELLOW}📂 Installation directory: $SCRIPT_DIR${NC}"
echo ""

# =============================================================================
# Step 1: Install Python Dependencies
# =============================================================================
echo -e "${BLUE}[1/4] Installing Python dependencies...${NC}"

if command -v pip3 &> /dev/null; then
    pip3 install --user fastapi uvicorn websockets httpx mcp --quiet 2>/dev/null || \
    pip3 install fastapi uvicorn websockets httpx mcp --quiet 2>/dev/null || \
    echo -e "${YELLOW}   ⚠️  Some packages may need manual install: pip3 install fastapi uvicorn websockets httpx mcp${NC}"
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ pip3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# =============================================================================
# Step 2: Detect and Configure IDEs
# =============================================================================
echo ""
echo -e "${BLUE}[2/4] Configuring MCP for detected IDEs...${NC}"

configure_mcp() {
    local config_path="$1"
    local ide_name="$2"
    
    # Create directory if needed
    mkdir -p "$(dirname "$config_path")"
    
    # Check if config exists
    if [ -f "$config_path" ]; then
        # Check if browser-bridge already configured
        if grep -q "browser-bridge" "$config_path" 2>/dev/null; then
            echo -e "${YELLOW}   ⚠️  $ide_name: Already configured${NC}"
            return
        fi
        
        # Merge with existing config using Python
        python3 << EOF
import json

config_path = "$config_path"
mcp_server = "$MCP_SERVER_PATH"

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['browser-bridge'] = {
    "command": "python3",
    "args": [mcp_server],
    "env": {}
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
EOF
        echo -e "${GREEN}   ✅ $ide_name: Configured${NC}"
    else
        # Create new config
        cat > "$config_path" << EOF
{
  "mcpServers": {
    "browser-bridge": {
      "command": "python3",
      "args": ["$MCP_SERVER_PATH"],
      "env": {}
    }
  }
}
EOF
        echo -e "${GREEN}   ✅ $ide_name: Configured${NC}"
    fi
}

# Gemini CLI / Antigravity
GEMINI_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"
if [ -d "$HOME/.gemini" ]; then
    configure_mcp "$GEMINI_CONFIG" "Gemini CLI"
else
    mkdir -p "$HOME/.gemini/antigravity"
    configure_mcp "$GEMINI_CONFIG" "Gemini CLI"
fi

# Windsurf
WINDSURF_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
mkdir -p "$HOME/.codeium/windsurf"
configure_mcp "$WINDSURF_CONFIG" "Windsurf"

# Claude Desktop (macOS)
if [ "$(uname)" == "Darwin" ]; then
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    if [ -d "$HOME/Library/Application Support/Claude" ]; then
        configure_mcp "$CLAUDE_CONFIG" "Claude Desktop"
    else
        mkdir -p "$HOME/Library/Application Support/Claude"
        configure_mcp "$CLAUDE_CONFIG" "Claude Desktop"
    fi
fi

# Cursor (just inform about extension)
if [ -d "$HOME/Library/Application Support/Cursor" ] || [ -d "$HOME/.config/Cursor" ]; then
    echo -e "${GREEN}   ✅ Cursor: Install .vsix extension from vscode-extension/${NC}"
fi

# =============================================================================
# Step 3: Install VS Code Extension
# =============================================================================
echo ""
echo -e "${BLUE}[3/4] Installing VS Code extension...${NC}"

VSIX_PATH="$SCRIPT_DIR/vscode-extension/browser-bridge-1.2.0.vsix"

if [ -f "$VSIX_PATH" ]; then
    # Try VS Code
    if command -v code &> /dev/null; then
        code --install-extension "$VSIX_PATH" --force 2>/dev/null && \
            echo -e "${GREEN}   ✅ VS Code: Extension installed${NC}" || \
            echo -e "${YELLOW}   ⚠️  VS Code: Install manually from $VSIX_PATH${NC}"
    else
        echo -e "${YELLOW}   ⏭️  VS Code CLI not found${NC}"
    fi
    
    # Try Cursor
    if command -v cursor &> /dev/null; then
        cursor --install-extension "$VSIX_PATH" --force 2>/dev/null && \
            echo -e "${GREEN}   ✅ Cursor: Extension installed${NC}" || \
            echo -e "${YELLOW}   ⚠️  Cursor: Install manually from $VSIX_PATH${NC}"
    else
        echo -e "${YELLOW}   ⏭️  Cursor CLI not found${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠️  .vsix not found. Build with: cd vscode-extension && npx vsce package${NC}"
fi

# =============================================================================
# Step 4: Clone Browser Extension
# =============================================================================
echo ""
echo -e "${BLUE}[4/4] Browser Extension Setup...${NC}"

BROWSER_EXT_DIR="$HOME/IDEconnector"

if [ -d "$BROWSER_EXT_DIR" ]; then
    echo -e "${YELLOW}   ⚠️  Browser extension already exists at $BROWSER_EXT_DIR${NC}"
elif command -v git &> /dev/null; then
    git clone --quiet https://github.com/sad1kul/IDEconnector.git "$BROWSER_EXT_DIR" 2>/dev/null && \
        echo -e "${GREEN}   ✅ Browser extension cloned to $BROWSER_EXT_DIR${NC}" || \
        echo -e "${YELLOW}   ⚠️  Clone failed. Clone manually: git clone https://github.com/sad1kul/IDEconnector.git${NC}"
else
    echo -e "${YELLOW}   ⚠️  Git not found. Clone manually from: https://github.com/sad1kul/IDEconnector${NC}"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ Installation Complete!                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Final Steps:${NC}"
echo ""
echo "1. ${BLUE}Load Browser Extension:${NC}"
echo "   - Open chrome://extensions (or brave://extensions)"
echo "   - Enable Developer mode"
echo "   - Click 'Load unpacked' → Select: $BROWSER_EXT_DIR"
echo ""
echo "2. ${BLUE}Restart your IDE${NC} to load MCP configuration"
echo ""
echo "3. ${BLUE}Connect:${NC}"
echo "   - Open any webpage"
echo "   - Click Browser Bridge extension → Connect"
echo "   - Ask your AI: 'get browser state'"
echo ""
echo -e "${BLUE}Configured IDEs:${NC}"
echo "   - Gemini CLI: ~/.gemini/antigravity/mcp_config.json"
echo "   - Windsurf:   ~/.codeium/windsurf/mcp_config.json"
[ "$(uname)" == "Darwin" ] && echo "   - Claude:     ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
