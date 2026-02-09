
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

HOST_NAME="com.browserbridge.host"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_PATH="${SCRIPT_DIR}/native_host.py"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Browser Bridge Installer${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check for extension ID
if [ -z "$1" ]; then
    echo -e "${RED}Error: Extension ID required${NC}"
    echo ""
    echo "Usage: ./install_host.sh <EXTENSION_ID>"
    echo ""
    echo "To find your Extension ID:"
    echo "  1. Open chrome://extensions (or browser equivalent)"
    echo "  2. Enable 'Developer mode'"
    echo "  3. Load the extension folder"
    echo "  4. Copy the ID shown"
    echo ""
    exit 1
fi

EXTENSION_ID="$1"

echo -e "${YELLOW}Extension ID:${NC} $EXTENSION_ID"
echo -e "${YELLOW}Host Script:${NC} $HOST_PATH"
echo ""

# Make host script executable
chmod +x "$HOST_PATH"
echo -e "${GREEN}✓${NC} Made native_host.py executable"

# Create manifest function
create_manifest() {
    local dest_dir="$1"
    local browser_name="$2"
    local manifest_path="$dest_dir/${HOST_NAME}.json"
    
    mkdir -p "$dest_dir" 2>/dev/null || return 1
    
    cat > "$manifest_path" << EOF
{
  "name": "${HOST_NAME}",
  "description": "Browser Bridge - Native Messaging Host",
  "path": "${HOST_PATH}",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://${EXTENSION_ID}/"
  ]
}
EOF
    echo -e "${GREEN}✓${NC} Installed for ${browser_name}: $manifest_path"
    return 0
}

# Detect OS and set browser paths
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    declare -A BROWSERS=(
        ["Chrome"]="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
        ["Brave"]="$HOME/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"
        ["Edge"]="$HOME/Library/Application Support/Microsoft Edge/NativeMessagingHosts"
        ["Opera"]="$HOME/Library/Application Support/com.operasoftware.Opera/NativeMessagingHosts"
        ["Vivaldi"]="$HOME/Library/Application Support/Vivaldi/NativeMessagingHosts"
        ["Arc"]="$HOME/Library/Application Support/Arc/User Data/NativeMessagingHosts"
        ["Chromium"]="$HOME/Library/Application Support/Chromium/NativeMessagingHosts"
    )
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    declare -A BROWSERS=(
        ["Chrome"]="$HOME/.config/google-chrome/NativeMessagingHosts"
        ["Brave"]="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
        ["Edge"]="$HOME/.config/microsoft-edge/NativeMessagingHosts"
        ["Opera"]="$HOME/.config/opera/NativeMessagingHosts"
        ["Vivaldi"]="$HOME/.config/vivaldi/NativeMessagingHosts"
        ["Chromium"]="$HOME/.config/chromium/NativeMessagingHosts"
    )
else
    echo -e "${RED}Error: Unsupported OS: $OSTYPE${NC}"
    echo "For Windows, please install manually."
    exit 1
fi

# Install for all browsers
echo ""
echo -e "${YELLOW}Installing for detected browsers...${NC}"
installed_count=0

for browser in "${!BROWSERS[@]}"; do
    dir="${BROWSERS[$browser]}"
    # Check if browser's parent directory exists (browser is installed)
    parent_dir=$(dirname "$dir")
    if [ -d "$parent_dir" ]; then
        if create_manifest "$dir" "$browser"; then
            ((installed_count++))
        fi
    fi
done

if [ $installed_count -eq 0 ]; then
    echo -e "${YELLOW}No browsers detected. Creating for Chrome anyway...${NC}"
    create_manifest "${BROWSERS["Chrome"]}" "Chrome"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Installed for ${GREEN}$installed_count${NC} browser(s)"
echo ""
echo -e "Next steps:"
echo -e "  1. ${YELLOW}Restart your browser${NC} (close all windows)"
echo -e "  2. Open the Browser Bridge extension popup"
echo -e "  3. Click '${BLUE}Connect${NC}' to begin"
echo ""
