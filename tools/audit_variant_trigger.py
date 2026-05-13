#!/usr/bin/env python3
"""Pass 22 — variant 触发难度审计。

针对"variant 写了但实际触发条件叠太多 → 玩家见不到"问题。
统计每个 variant.if 的"前置原子条件数"(展开 all_of),超阈值标 warning。

度量(每个 atomic 算 1):
- flags 字典每个 key
- inv_has / inv_lacks 每个 item
- puzzle_pieces_min / shifts_completed_min / shifts_skipped_min(各 1)
- visit_count_min 每个 key
- deduction_resolved / foreshadow_resolved / theme_resolved(各 1)
- ending_seen(1)
- behavior_profile(1)
- character / landmark_visited / last_landmark(各 1)

阈值:
- WARN(≥ 5):触发难度高,可能少有玩家见到
- ERROR(≥ 8):事实上死代码

用法:
    python tools/audit_variant_trigger.py path/to/tree.json [--warn 5 --error 8]
退出码:0=全绿, 2=有 ERROR 级。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ATOMIC_KEYS_COUNT_AS_ONE = {
    "puzzle_pieces_min", "shifts_completed_min", "shifts_skipped_min",
    "deduction_resolved", "foreshadow_resolved", "theme_resolved",
    "ending_seen", "behavior_profile",
    "character", "last_landmark",
    "PR_min", "PR_max", "GR_min", "GR_max",
}


def _count_clause(req: Dict[str, Any]) -> int:
    """统计原子条件数(展开 all_of/any_of/not)。"""
    if not isinstance(req, dict) or not req:
        return 0
    count = 0
    for k in ATOMIC_KEYS_COUNT_AS_ONE:
        if k in req:
            count += 1
    count += len(req.get("flags") or {})
    count += len(req.get("inv_has") or [])
    count += len(req.get("inv_lacks") or [])
    count += len(req.get("visit_count_min") or {})
    count += len(req.get("landmark_visited") or [])
    for sub in req.get("all_of") or []:
        count += _count_clause(sub)
    # any_of 取最小子句(玩家只需一条满足),减少难度
    any_of = req.get("any_of") or []
    if any_of:
        count += min((_count_clause(c) for c in any_of), default=0)
    if "not" in req:
        count += _count_clause(req["not"])
    return count


def audit(tree_path: Path, warn_th: int = 5, error_th: int = 8) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    problems: List[Dict[str, Any]] = []
    histogram: Dict[int, int] = {}

    for nid, node in nodes.items():
        for idx, v in enumerate(node.get("narrative_variants") or []):
            cond = v.get("if") or {}
            n = _count_clause(cond)
            histogram[n] = histogram.get(n, 0) + 1
            if n >= error_th:
                problems.append({
                    "code": "TRIGGER_TOO_HARD",
                    "node": nid,
                    "variant": idx,
                    "atoms": n,
                    "msg": (
                        f"{nid}.variant[{idx}] 前置条件数 {n} ≥ {error_th},"
                        f" 实际触发概率近 0,视为死代码。建议拆分或降级。"
                    ),
                })
            elif n >= warn_th:
                problems.append({
                    "code": "TRIGGER_HIGH_DIFFICULTY",
                    "node": nid,
                    "variant": idx,
                    "atoms": n,
                    "severity": "warning",
                    "msg": (
                        f"{nid}.variant[{idx}] 前置条件数 {n} ≥ {warn_th},"
                        f" 触发难度高,可能少有玩家见到。"
                    ),
                })

    errors = [p for p in problems if p["code"] == "TRIGGER_TOO_HARD"]
    return {
        "tree": str(tree_path),
        "warn_threshold": warn_th,
        "error_threshold": error_th,
        "atoms_histogram": dict(sorted(histogram.items())),
        "problems": problems,
        "errors_count": len(errors),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    ap.add_argument("--warn", type=int, default=5)
    ap.add_argument("--error", type=int, default=8)
    args = ap.parse_args()
    report = audit(args.tree, warn_th=args.warn, error_th=args.error)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(2 if report["errors_count"] else 0)


if __name__ == "__main__":
    main()
