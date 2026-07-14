#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="${HOME}/homebrew/plugins/forza-dualsense-haptics"

if [[ ! -f "${SOURCE_DIR}/dist/index.js" ]]; then
  echo "dist/index.js is missing."
  echo "Build first with:"
  echo "  corepack enable"
  echo "  pnpm install"
  echo "  pnpm build"
  exit 1
fi

rm -rf "${PLUGIN_DIR}"
mkdir -p "${PLUGIN_DIR}"
cp -R \
  "${SOURCE_DIR}/dist" \
  "${SOURCE_DIR}/forza_haptics" \
  "${SOURCE_DIR}/main.py" \
  "${SOURCE_DIR}/run_backend.py" \
  "${SOURCE_DIR}/settings.example.json" \
  "${SOURCE_DIR}/plugin.json" \
  "${SOURCE_DIR}/LICENSE" \
  "${SOURCE_DIR}/NOTICE" \
  "${PLUGIN_DIR}/"

echo "Installed to ${PLUGIN_DIR}"
echo "Restart Decky Loader or reboot Steam."
