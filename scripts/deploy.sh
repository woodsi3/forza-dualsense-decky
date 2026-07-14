#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="/home/deck/homebrew/plugins/forza-dualsense-haptics"
BACKUP_ROOT="/home/deck/homebrew/plugin-backups/forza-dualsense-haptics"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

if pgrep -x gamescope >/dev/null 2>&1; then
  echo "REFUSING DEPLOYMENT: Gamescope/Game Mode is active."
  echo "Switch to Desktop Mode, then run this script again."
  exit 20
fi

"$ROOT/scripts/verify.sh"
test -s "$ROOT/dist/index.js" || {
  echo "dist/index.js is missing. Run scripts/build.sh first."
  exit 21
}

sudo mkdir -p "$BACKUP_ROOT"
if sudo test -d "$PLUGIN_DIR"; then
  sudo mkdir -p "$BACKUP_DIR"
  sudo cp -a "$PLUGIN_DIR/." "$BACKUP_DIR/"
  echo "Backup created: $BACKUP_DIR"
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/forza-dualsense-haptics"
cp -a \
  "$ROOT/dist" \
  "$ROOT/forza_haptics" \
  "$ROOT/main.py" \
  "$ROOT/run_backend.py" \
  "$ROOT/settings.example.json" \
  "$ROOT/plugin.json" \
  "$ROOT/package.json" \
  "$ROOT/LICENSE" \
  "$ROOT/NOTICE" \
  "$ROOT/README.md" \
  "$ROOT/VERSION" \
  "$STAGE/forza-dualsense-haptics/"

sudo rm -rf "$PLUGIN_DIR.new"
sudo cp -a "$STAGE/forza-dualsense-haptics" "$PLUGIN_DIR.new"
sudo chown -R root:root "$PLUGIN_DIR.new"
sudo chmod -R a+rX "$PLUGIN_DIR.new"

if sudo test -d "$PLUGIN_DIR"; then
  sudo rm -rf "$PLUGIN_DIR.old"
  sudo mv "$PLUGIN_DIR" "$PLUGIN_DIR.old"
fi
sudo mv "$PLUGIN_DIR.new" "$PLUGIN_DIR"
sudo rm -rf "$PLUGIN_DIR.old"

echo "Deployment complete."
echo "Do NOT restart plugin_loader. Reboot the Steam Machine before testing in Game Mode."
