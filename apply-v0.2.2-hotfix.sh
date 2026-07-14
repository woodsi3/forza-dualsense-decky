#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="/home/deck/homebrew/plugins/forza-dualsense-haptics"

sudo cp "${SOURCE_DIR}/main.py" "${PLUGIN_DIR}/main.py"
sudo chmod 0644 "${PLUGIN_DIR}/main.py"
sudo systemctl restart plugin_loader
echo "Decky path compatibility fix installed."
