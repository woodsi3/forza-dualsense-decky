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

echo "Verification passed: safe child control and controller-focus frontend are present."
