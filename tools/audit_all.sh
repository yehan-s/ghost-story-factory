#!/usr/bin/env bash
# 一键跑全套审计 — 守门工具。
# 任一报错即停;全绿才允许 commit / merge。
set -e

TREE="stories/hangzhou_yebanbaoan/tree.json"

# 用 mktemp 避免并发(local jobs / CI shards)写同一 /tmp 文件竞态
CROSS_RUN_JSON="$(mktemp -t cross_run.XXXXXX.json)"
VARIANT_TRIGGER_JSON="$(mktemp -t variant_trigger.XXXXXX.json)"
trap 'rm -f "$CROSS_RUN_JSON" "$VARIANT_TRIGGER_JSON"' EXIT

echo "=== 1/12 audit_playability(GameTree 可玩闭环)==="
python tools/audit_playability.py "$TREE"
echo
echo "=== 2/12 audit_sandbox(ADR-010 沙盒骨架)==="
python tools/audit_sandbox.py "$TREE"
echo
echo "=== 3/12 audit_script_depth(Pass 9 剧本厚度)==="
python tools/audit_script_depth.py "$TREE"
echo
echo "=== 4/12 audit_tree(节点引用完整性 + lore 红线)==="
python tools/audit_tree.py "$TREE"
echo
echo "=== 5/12 audit_state(flags / inv 引用矩阵)==="
python tools/audit_state.py "$TREE"
echo
echo "=== 6/12 audit_variants(variant 覆盖矩阵 + 重访无分化)==="
python tools/audit_variants.py "$TREE"
echo
echo "=== 7/12 audit_reactions(反应式 variant 三红线 ADR-008)==="
python tools/audit_reactions.py "$TREE" > /dev/null
echo "  反应契约审计通过"
echo
echo "=== 8/12 audit_paths_linmou(linmou 必死不变量 ADR-009)==="
python tools/audit_paths_linmou.py "$TREE" > /dev/null
echo "  必死不变量审计通过"
echo
echo "=== 9/12 audit_foreshadow_chain(Pass 22 — 伏笔链条完整性)==="
python tools/audit_foreshadow_chain.py "$TREE" > /dev/null
echo "  伏笔链条审计通过"
echo
echo "=== 10/12 audit_cross_run_continuity(Pass 22 — 跨周目消费侧覆盖)==="
python tools/audit_cross_run_continuity.py "$TREE" > "$CROSS_RUN_JSON"
PROBLEMS=$(python3 -c "import json,sys; print(len(json.load(open(sys.argv[1]))['problems']))" "$CROSS_RUN_JSON")
if [ "$PROBLEMS" -gt 0 ]; then
  echo "  ⚠️  跨周目消费侧 debt: $PROBLEMS 处主结局无反咬(留剧本扩写偿还,非阻断)"
else
  echo "  跨周目消费侧审计通过"
fi
echo
echo "=== 11/12 audit_variant_trigger(Pass 22 — variant 触发难度)==="
python tools/audit_variant_trigger.py "$TREE" > "$VARIANT_TRIGGER_JSON"
ERRORS=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['errors_count'])" "$VARIANT_TRIGGER_JSON")
if [ "$ERRORS" -gt 0 ]; then
  echo "  ❌ 触发难度 ERROR: $ERRORS"
  python tools/audit_variant_trigger.py "$TREE"
  exit 2
fi
echo "  触发难度审计通过(0 ERROR)"
echo
echo "=== 12/12 audit_protagonist_behavior(Pass 22 — G-273 行为画像不变量)==="
python tools/audit_protagonist_behavior.py "$TREE" > /dev/null
echo "  G-273 行为画像审计通过"
echo
echo "=== 全套审计通过 ✅ ==="
