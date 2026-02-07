#!/bin/bash
# ============================================================================
# AntiGravity IDE Bridge - Native Messaging Host Installer
# ============================================================================
# This script registers the native messaging host with Chrome/Chromium.
# 
# Usage:
#   ./install_host.sh <EXTENSION_ID>
#
# The EXTENSION_ID is shown in chrome://extensions after loading the extension.
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

HOST_NAME="com.antigravity.bridge"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_PATH="${SCRIPT_DIR}/native_host.py"
MANIFEST_TEMPLATE="${SCRIPT_DIR}/com.antigravity.bridge.json"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AntiGravity IDE Bridge Installer${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check for extension ID argument
if [ -z "$1" ]; then
    echo -e "${RED}Error: Extension ID required${NC}"
    echo ""
    echo "Usage: ./install_host.sh <EXTENSION_ID>"
    echo ""
    echo "To find your Extension ID:"
    echo "  1. Open chrome://extensions"
    echo "  2. Enable 'Developer mode'"
    echo "  3. Load the AntiGravityIDEconnector folder"
    echo "  4. Copy the ID shown under the extension name"
    echo ""
    exit 1
fi

EXTENSION_ID="$1"

echo -e "${YELLOW}Extension ID:${NC} $EXTENSION_ID"
echo -e "${YELLOW}Host Script:${NC} $HOST_PATH"
echo ""

# Make the host script executable
chmod +x "$HOST_PATH"
echo -e "${GREEN}✓${NC} Made native_host.py executable"

# Determine Chrome native messaging hosts directory based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
    CHROMIUM_DIR="$HOME/Library/Application Support/Chromium/NativeMessagingHosts"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
    CHROMIUM_DIR="$HOME/.config/chromium/NativeMessagingHosts"
else
    echo -e "${RED}Error: Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

# Create directories if they don't exist
mkdir -p "$CHROME_DIR" 2>/dev/null || true
mkdir -p "$CHROMIUM_DIR" 2>/dev/null || true

# Create the manifest with the actual extension ID and absolute path
create_manifest() {
    local dest_dir="$1"
    local manifest_path="$dest_dir/${HOST_NAME}.json"
    
    cat > "$manifest_path" << EOF
{
  "name": "${HOST_NAME}",
  "description": "AntiGravity IDE Bridge - Native Messaging Host",
  "path": "${HOST_PATH}",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://${EXTENSION_ID}/"
  ]
}
EOF
    echo -e "${GREEN}✓${NC} Created manifest: $manifest_path"
}

# Install for Chrome
if [ -d "$CHROME_DIR" ] || mkdir -p "$CHROME_DIR" 2>/dev/null; then
    create_manifest "$CHROME_DIR"
fi

# Install for Chromium
if [ -d "$CHROMIUM_DIR" ] || mkdir -p "$CHROMIUM_DIR" 2>/dev/null; then
    create_manifest "$CHROMIUM_DIR"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. ${YELLOW}Restart Chrome${NC} (close all windows)"
echo -e "  2. Open the AntiGravity extension popup"
echo -e "  3. Click '${BLUE}Start Server${NC}' to begin"
echo ""
