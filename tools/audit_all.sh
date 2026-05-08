#!/usr/bin/env bash
# 一键跑全套审计 — 守门工具。
# 任一报错即停;全绿才允许 commit / merge。
set -e

TREE="stories/hangzhou_yebanbaoan/tree.json"

echo "=== 1/6 audit_playability(GameTree 可玩闭环)==="
python tools/audit_playability.py "$TREE"
echo
echo "=== 2/6 audit_tree(节点引用完整性 + lore 红线)==="
python tools/audit_tree.py "$TREE"
echo
echo "=== 3/6 audit_state(flags / inv 引用矩阵)==="
python tools/audit_state.py "$TREE"
echo
echo "=== 4/6 audit_variants(variant 覆盖矩阵 + 重访无分化)==="
python tools/audit_variants.py "$TREE"
echo
echo "=== 5/6 audit_reactions(反应式 variant 三红线 ADR-008)==="
python tools/audit_reactions.py "$TREE" > /dev/null
echo "  反应契约审计通过"
echo
echo "=== 6/6 audit_paths_linmou(linmou 必死不变量 ADR-009)==="
python tools/audit_paths_linmou.py "$TREE" > /dev/null
echo "  必死不变量审计通过"
echo
echo "=== 全套审计通过 ✅ ==="
