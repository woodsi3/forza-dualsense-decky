#!/usr/bin/env bash
set -euo pipefail

systemctl --user disable --now forza-dualsense-backend.service 2>/dev/null || true
rm -f "${HOME}/.config/systemd/user/forza-dualsense-backend.service"
rm -rf "${HOME}/.local/share/forza-dualsense/backend"
systemctl --user daemon-reload
echo "Backend removed. Settings and status were retained in ~/.local/share/forza-dualsense/"
