#!/usr/bin/env python3
"""Pass 22 — 主角行为画像不变量审计(G-273 线)。

对称于 audit_paths_linmou 的"必死不变量",本工具守 G-273 线的
"人格反馈不变量":每个 G-273 ending 至少有 1 个 variant 引用
某种"画像识别条件"(behavior_profile / reaction / flag),
确保 ending 不是"随机抵达就拿到",而是对玩家行为的回应。

linmou ending 通过 ending_type 前缀识别(E_LINMOU_*),不在本审计范围。

用法:
    python tools/audit_protagonist_behavior.py path/to/tree.json
退出码:0=全绿, 2=有阻断。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


RECOGNITION_KEYS = {
    "behavior_profile",
    "deduction_resolved", "foreshadow_resolved", "theme_resolved",
    "ending_seen",
    "flags",  # flag 表达"做过某事"也算识别
    "inv_has",  # 道具表达"取证 / 拼图"也算识别
    "puzzle_pieces_min",
    "shifts_completed_min", "shifts_skipped_min",
    "all_of", "any_of",  # 组合也算
}


def _has_recognition(req: Dict[str, Any]) -> bool:
    """递归判断 require 是否含任一识别键。"""
    if not isinstance(req, dict) or not req:
        return False
    if any(k in req for k in RECOGNITION_KEYS):
        # 嵌套 all_of / any_of 仍要递归看子句是否真有内容
        if "all_of" in req:
            return any(_has_recognition(c) for c in (req.get("all_of") or []))
        if "any_of" in req:
            return any(_has_recognition(c) for c in (req.get("any_of") or []))
        return True
    if "not" in req:
        return _has_recognition(req["not"])
    return False


def audit(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    problems: List[Dict[str, Any]] = []
    g273_endings: List[str] = []

    for nid, node in nodes.items():
        if not node.get("is_ending"):
            continue
        etype = node.get("ending_type") or ""
        # linmou ending 不审本规则
        if etype.startswith("E_LINMOU"):
            continue
        # 微结局豁免:节点既无 narrative_variants 又无明确 _is_main_ending 标记,
        # 视作"做错某个具体选择 = 这里结束"的段子级 ending,不要求识别玩家。
        # 主结局(n_end_*)即使 variants 为空也必须识别。
        variants = node.get("narrative_variants") or []
        is_main_ending = nid.startswith("n_end_") or node.get("_is_main_ending")
        if not variants and not is_main_ending:
            continue
        g273_endings.append(nid)

        # 是否至少有 1 个 variant.if 含识别条件
        recognized = False
        for v in variants:
            if _has_recognition(v.get("if") or {}):
                recognized = True
                break
        if not recognized:
            problems.append({
                "code": "ENDING_BLIND_TO_PLAYER",
                "node": nid,
                "ending_type": etype,
                "msg": (
                    f"G-273 ending {nid}(type={etype})无任何 variant 识别玩家"
                    f"行为/状态。每个 ending 应至少有 1 个 variant 通过 "
                    f"behavior_profile / *_resolved / flags / inv_has 等识别玩家。"
                    f" 修复方向:补 narrative_variants[].if 反映"
                    f"该 ending 的人格逻辑。"
                ),
            })

    return {
        "tree": str(tree_path),
        "g273_ending_count": len(g273_endings),
        "problems": problems,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    args = ap.parse_args()
    report = audit(args.tree)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(2 if report["problems"] else 0)


if __name__ == "__main__":
    main()
