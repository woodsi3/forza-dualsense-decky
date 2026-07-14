#!/usr/bin/env bash
set -u

echo "=== Plugin log ==="
sudo tail -n 120 /home/deck/homebrew/logs/forza-dualsense-haptics/forza-dualsense-haptics.log 2>&1 || true

echo
echo "=== Engine log ==="
sudo tail -n 120 /home/deck/homebrew/logs/forza-dualsense-haptics/forza-dualsense-engine.log 2>&1 || true

echo
echo "=== Port 5300 ==="
sudo ss -lunp | grep ':5300' || echo "No process is bound to UDP 5300"

echo
echo "=== Backend processes ==="
pgrep -af 'run_backend.py|forza-dualsense' || true
