#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Usage: scripts/organize_root.sh [--apply]
# Without --apply, runs in dry-run mode and prints planned moves.

APPLY=0
if [ "${1:-}" = "--apply" ]; then
  APPLY=1
fi

mkdir -p docs/reports docs/audit docs/archive docs/notes tools

move() {
  src="$1"; dst="$2";
  [ -e "$src" ] || return 0
  if [ $APPLY -eq 1 ]; then
    if command -v git >/dev/null 2>&1 && git ls-files --error-unmatch "$src" >/dev/null 2>&1; then
      git mv -f "$src" "$dst"
    else
      mv -f "$src" "$dst"
    fi
    echo "moved: $src -> $dst"
  else
    echo "plan:  $src -> $dst"
  fi
}

# Reports & audits
move "FINAL_AUDIT_REPORT.md" docs/audit/
move "AUDIT_SUMMARY_简报.md" docs/audit/
move "FINAL_INTEGRATION_REPORT.md" docs/reports/
move "BUGFIX_SUMMARY.md" docs/reports/

# Project notes/one-offs
move "HYBRID_APPROACH.md" docs/notes/
move "IMPLEMENTATION_COMPLETE.md" docs/archive/
move "SESSION_CACHE_IMPLEMENTATION.md" docs/archive/

# Top-level quick guides (already duplicated in docs/) -> archive
move "QUICK_START.md" docs/archive/
move "USAGE.md" docs/archive/

# Legacy generators/tools to tools/
move "generate_mvp.py" tools/
move "run_all_tests.py" tools/

echo ""
if [ $APPLY -eq 1 ]; then
  echo "Done. Review git status and commit the reorg."
else
  echo "Dry-run complete. Re-run with --apply to execute moves."
fi


