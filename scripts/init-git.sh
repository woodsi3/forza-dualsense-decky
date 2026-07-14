#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .git ]]; then
  git init -b main
fi

git config user.name >/dev/null 2>&1 || git config user.name "Oli Woods"
git config user.email >/dev/null 2>&1 || git config user.email "woods.ollie@gmail.com"

git add .
if git diff --cached --quiet; then
  echo "Nothing new to commit."
else
  git commit -m "Initial safe Decky plugin baseline"
fi

echo
echo "Local Git repository ready at: $ROOT"
git status --short --branch
