#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/out"
PACKAGE_NAME="forza-dualsense-haptics"

cd "$ROOT"

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

command -v python3 >/dev/null 2>&1 ||
    fail "python3 is required"

command -v zip >/dev/null 2>&1 ||
    fail "zip is required"

command -v sha256sum >/dev/null 2>&1 ||
    fail "sha256sum is required"

[[ -f VERSION ]] ||
    fail "VERSION is missing"

VERSION="$(tr -d '[:space:]' < VERSION)"

[[ -n "$VERSION" ]] ||
    fail "VERSION is empty"

# Refuse to package uncommitted tracked changes. Ignored build output does
# not affect this check.
git diff --quiet ||
    fail "Tracked files contain uncommitted changes"

git diff --cached --quiet ||
    fail "The Git index contains uncommitted changes"

# Confirm all public version fields agree before producing an archive.
python3 - "$VERSION" <<'PY'
from pathlib import Path
import json
import sys

expected = sys.argv[1]

for filename in ("package.json", "plugin.json"):
    path = Path(filename)
    data = json.loads(path.read_text(encoding="utf-8"))
    actual = str(data.get("version", "")).strip()

    if actual != expected:
        raise SystemExit(
            f"{filename} version is {actual!r}, "
            f"but VERSION contains {expected!r}"
        )
PY

printf 'Packaging Forza DualSense Haptics v%s\n' "$VERSION"

# build.sh already runs verify.sh before building.
"$ROOT/scripts/build.sh"

[[ -s "$ROOT/dist/index.js" ]] ||
    fail "dist/index.js was not created"

STAGE_ROOT="$(mktemp -d)"
trap 'rm -rf "$STAGE_ROOT"' EXIT

PACKAGE_DIR="$STAGE_ROOT/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR/dist"

# Runtime files required by Decky and the Python backend.
cp "$ROOT/plugin.json" "$PACKAGE_DIR/"
cp "$ROOT/package.json" "$PACKAGE_DIR/"
cp "$ROOT/main.py" "$PACKAGE_DIR/"
cp "$ROOT/run_backend.py" "$PACKAGE_DIR/"
cp "$ROOT/settings.example.json" "$PACKAGE_DIR/"
cp "$ROOT/VERSION" "$PACKAGE_DIR/"
cp "$ROOT/dist/index.js" "$PACKAGE_DIR/dist/"

cp -a "$ROOT/forza_haptics" "$PACKAGE_DIR/"

# Useful information for manual-install users.
cp "$ROOT/README.md" "$PACKAGE_DIR/"
cp "$ROOT/CHANGELOG.md" "$PACKAGE_DIR/"
cp "$ROOT/LICENSE" "$PACKAGE_DIR/"
cp "$ROOT/NOTICE" "$PACKAGE_DIR/"

# Never ship generated Python cache files.
find "$PACKAGE_DIR" \
    -type d -name '__pycache__' \
    -prune -exec rm -rf -- {} +

find "$PACKAGE_DIR" \
    -type f \( -name '*.pyc' -o -name '*.pyo' \) \
    -delete

mkdir -p "$OUT_DIR"

ARCHIVE="$OUT_DIR/${PACKAGE_NAME}-v${VERSION}.zip"
CHECKSUM="$ARCHIVE.sha256"

rm -f "$ARCHIVE" "$CHECKSUM"

(
    cd "$STAGE_ROOT"
    zip -qr "$ARCHIVE" "$PACKAGE_NAME"
)

(
    cd "$OUT_DIR"
    sha256sum "$(basename "$ARCHIVE")" \
        > "$(basename "$CHECKSUM")"
)

printf '\nRelease package created:\n'
printf '  %s\n' "$ARCHIVE"
printf '  %s\n\n' "$CHECKSUM"

printf 'Archive contents:\n'
unzip -Z1 "$ARCHIVE"

printf '\nChecksum:\n'
cat "$CHECKSUM"
