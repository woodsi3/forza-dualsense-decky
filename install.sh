#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/share/forza-dualsense/backend"
DATA_DIR="${HOME}/.local/share/forza-dualsense"
SYSTEMD_DIR="${HOME}/.config/systemd/user"

mkdir -p "${INSTALL_DIR}" "${DATA_DIR}" "${SYSTEMD_DIR}"
cp -R "${SOURCE_DIR}/forza_haptics" "${INSTALL_DIR}/"
cp "${SOURCE_DIR}/run_backend.py" "${INSTALL_DIR}/"
cp "${SOURCE_DIR}/settings.example.json" "${INSTALL_DIR}/"
cp "${SOURCE_DIR}/packaging/forza-dualsense-backend.service" \
   "${SYSTEMD_DIR}/forza-dualsense-backend.service"

chmod +x "${INSTALL_DIR}/run_backend.py"

if [[ ! -f "${DATA_DIR}/settings.json" ]]; then
    cp "${SOURCE_DIR}/settings.example.json" "${DATA_DIR}/settings.json"
fi

systemctl --user daemon-reload

echo
echo "Installed backend to: ${INSTALL_DIR}"
echo "Settings:             ${DATA_DIR}/settings.json"
echo
echo "Run the controller test:"
echo "  python3 ${INSTALL_DIR}/run_backend.py controller-test"
echo
echo "Run manually:"
echo "  python3 ${INSTALL_DIR}/run_backend.py run"
echo
echo "Or enable the user service:"
echo "  systemctl --user enable --now forza-dualsense-backend.service"
