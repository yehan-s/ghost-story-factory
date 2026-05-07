#!/usr/bin/env bash
# 一键跑全套审计 — 4 项守门工具。
# 任一报错即停;全绿才允许 commit / merge。
set -e

TREE="stories/hangzhou_yebanbaoan/tree.json"

echo "=== 1/4 audit_tree(节点引用完整性 + lore 红线)==="
python tools/audit_tree.py "$TREE"
echo
echo "=== 2/4 audit_state(flags / inv 引用矩阵)==="
python tools/audit_state.py "$TREE"
echo
echo "=== 3/4 audit_variants(variant 覆盖矩阵 + 重访无分化)==="
python tools/audit_variants.py "$TREE"
echo
echo "=== 4/4 audit_reactions(反应式 variant 三红线 ADR-008)==="
python tools/audit_reactions.py "$TREE" > /dev/null
echo "  反应契约审计通过"
echo
echo "=== 全套审计通过 ✅ ==="
