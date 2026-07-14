#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m py_compile "$ROOT/main.py" "$ROOT/run_backend.py"
python3 -m compileall -q "$ROOT/forza_haptics"

grep -q 'process\.terminate()' "$ROOT/main.py"
grep -q 'process\.kill()' "$ROOT/main.py"
! grep -qE 'killpg|start_new_session' "$ROOT/main.py"

grep -q 'ButtonItem' "$ROOT/src/index.tsx"
! grep -q '<button' "$ROOT/src/index.tsx"
! grep -q 'onChangeEnd' "$ROOT/src/index.tsx"

grep -q '_reload_settings' "$ROOT/forza_haptics/backend.py"
grep -q 'list_presets' "$ROOT/main.py"
grep -q 'test_effect' "$ROOT/main.py"
grep -q 'controller_battery_percent' "$ROOT/forza_haptics/status.py"
grep -q 'COMMAND_PATH' "$ROOT/main.py"

echo "Verification passed: v0.4 features and safe child control are present."

# v0.5 checks
grep -q 'traction_intensity' settings.example.json
grep -q 'surface_state' forza_haptics/telemetry.py
grep -q 'automatic_car_profiles' main.py
if grep -Rqi 'custom curve' src forza_haptics; then echo 'Custom curves must remain out of scope'; exit 1; fi
