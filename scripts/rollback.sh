#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="/home/deck/homebrew/plugins/forza-dualsense-haptics"
BACKUP_ROOT="/home/deck/homebrew/plugin-backups/forza-dualsense-haptics"

if pgrep -x gamescope >/dev/null 2>&1; then
  echo "REFUSING ROLLBACK: Gamescope/Game Mode is active."
  echo "Switch to Desktop Mode first."
  exit 20
fi

BACKUP="${1:-}"
if [[ -z "$BACKUP" ]]; then
  BACKUP="$(sudo find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d | sort | tail -n1)"
fi

if [[ -z "$BACKUP" ]] || ! sudo test -d "$BACKUP"; then
  echo "No backup found."
  exit 1
fi

sudo rm -rf "$PLUGIN_DIR"
sudo mkdir -p "$PLUGIN_DIR"
sudo cp -a "$BACKUP/." "$PLUGIN_DIR/"
sudo chown -R root:root "$PLUGIN_DIR"
sudo chmod -R a+rX "$PLUGIN_DIR"

echo "Rolled back from: $BACKUP"
echo "Reboot before entering Game Mode."
