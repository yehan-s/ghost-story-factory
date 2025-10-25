#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Load env if exists
[ -f ./load_env.sh ] && source ./load_env.sh

echo "Cleaning checkpoints/ and incremental logs…"
rm -f checkpoints/*.json checkpoints/*.jsonl 2>/dev/null || true

echo "Cleaning __pycache__/…"
find . -type d -name "__pycache__" -prune -print -exec rm -rf {} +

echo "Cleaning saves temp artifacts…"
find saves -type f -name "*.tmp" -delete 2>/dev/null || true

echo "Cleaning SQLite journaling files…"
rm -f database/*.db-shm database/*.db-wal 2>/dev/null || true

echo "Done."


