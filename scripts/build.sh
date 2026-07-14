#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

"$ROOT/scripts/verify.sh"
if [[ -f pnpm-lock.yaml ]]; then
  pnpm install --frozen-lockfile
else
  pnpm install --no-frozen-lockfile
fi
pnpm run build

test -s dist/index.js
echo "Build complete: $ROOT/dist/index.js"
