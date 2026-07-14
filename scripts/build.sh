#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

"$ROOT/scripts/verify.sh"
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
pnpm run build

test -s dist/index.js
echo "Build complete: $ROOT/dist/index.js"
