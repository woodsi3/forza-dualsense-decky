#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="/home/deck/homebrew/plugins/forza-dualsense-haptics"

if [[ ! -d "${PLUGIN_DIR}" ]]; then
  echo "Plugin directory not found: ${PLUGIN_DIR}"
  exit 1
fi

sudo cp "${SOURCE_DIR}/main.py" "${PLUGIN_DIR}/main.py"
sudo chmod 0644 "${PLUGIN_DIR}/main.py"
sudo systemctl restart plugin_loader

echo "v0.2.3 safe child-process hotfix installed."
echo "The plugin no longer sends signals to a process group."
