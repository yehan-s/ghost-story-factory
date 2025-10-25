#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

source venv/bin/activate 2>/dev/null || true

if command -v ruff >/dev/null 2>&1; then
  echo "Running ruff format…"
  ruff format .
elif command -v black >/dev/null 2>&1; then
  echo "Running black…"
  black .
else
  echo "No formatter (ruff/black) found. Skipping."
fi


