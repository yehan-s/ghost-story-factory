#!/usr/bin/env python3
"""Pass 22 — 跨周目联动连续性审计。

ADR-010 沙盒第一公理:跨周目联动靠 endings_seen[story_id]:list,0 新字段。
本工具验证"声明的 ending 都有跨周目消费侧":

- ENDING_NO_CROSS_REFERENCE:某 ending_type 至少应被 1 个 variant 在
  ending_seen.ending_id 引用,否则跨周目"看过这个结局"无任何反馈,
  违反 ADR-010 跨周目联动政策。
- WARN:Bad ending(E_BAD_*) 可豁免——它们往往作为"必死"分支,
  本周目内体验,跨周目无须额外回响。可通过 `_no_cross_ref_ok: true`
  在 ending 节点上显式声明豁免。

用法:
    python tools/audit_cross_run_continuity.py path/to/tree.json
退出码:0=全绿, 2=有阻断。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


def _walk_requires(node: Dict[str, Any]):
    for v in node.get("narrative_variants") or []:
        if "if" in v:
            yield v["if"]
    for ch in node.get("choices") or []:
        if "require" in ch:
            yield ch["require"]


def _walk_ending_seen(req: Dict[str, Any]):
    if not isinstance(req, dict):
        return
    if "ending_seen" in req:
        yield req["ending_seen"] or {}
    for sub in req.get("any_of") or []:
        yield from _walk_ending_seen(sub)
    for sub in req.get("all_of") or []:
        yield from _walk_ending_seen(sub)
    if "not" in req:
        yield from _walk_ending_seen(req["not"])


def audit(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    tree_story_id = tree.get("story_id") or ""
    problems: List[Dict[str, Any]] = []

    # 1. 收集所有 ending 节点的 ending_type + 豁免标记
    ending_types: Dict[str, Dict[str, Any]] = {}
    for nid, node in nodes.items():
        if not node.get("is_ending"):
            continue
        etype = node.get("ending_type") or ""
        if not etype:
            continue
        ending_types.setdefault(etype, {
            "nodes": [],
            "exempt": False,
        })
        ending_types[etype]["nodes"].append(nid)
        if node.get("_no_cross_ref_ok"):
            ending_types[etype]["exempt"] = True

    # 2. 收集所有 variant 里 ending_seen.ending_id 引用的 ending_type
    referenced: Set[str] = set()
    for nid, node in nodes.items():
        for req in _walk_requires(node):
            for spec in _walk_ending_seen(req):
                spec = spec or {}
                eid = spec.get("ending_id")
                spec_sid = spec.get("story_id")
                if not eid or eid == "*":
                    continue
                # 跨 story_id skip(双向 alias,同 audit_reactions Pass 20+24 修复)
                STORY_ALIASES = {
                    ("杭州_v7", "hangzhou_yebanbaoan"),
                    ("hangzhou_yebanbaoan", "杭州_v7"),
                }
                if (spec_sid and tree_story_id and spec_sid != tree_story_id
                        and (spec_sid, tree_story_id) not in STORY_ALIASES):
                    continue
                referenced.add(eid)

    # 3. 比对:每个非豁免 ending_type 必须被至少 1 个 variant 引用
    # BAD ending(E_BAD_*) 默认豁免——它们是死路径,本周目内体验,跨周目"上次死过"
    # 反咬是 nice-to-have 不是 must-have。如需强制,加 --strict-bad 选项。
    for etype, info in ending_types.items():
        if info["exempt"]:
            continue
        if etype.startswith("E_BAD"):
            # 默认豁免,记 info 不报 problem
            continue
        if etype not in referenced:
            problems.append({
                "code": "ENDING_NO_CROSS_REFERENCE",
                "ending_type": etype,
                "nodes": info["nodes"],
                "msg": (
                    f"ending_type {etype!r}(节点 {info['nodes']}) 在本树没有任何 "
                    f"variant/choice 通过 ending_seen 引用——跨周目无回响。"
                    f" 修复方向:在合适节点加 narrative_variants[].if.ending_seen,"
                    f"或在该 ending 节点声明 _no_cross_ref_ok: true 豁免。"
                ),
            })

    return {
        "tree": str(tree_path),
        "ending_type_count": len(ending_types),
        "referenced_count": len(referenced),
        "problems": problems,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="把 ENDING_NO_CROSS_REFERENCE 视为阻断级。默认只报告(debt 性质,靠剧本扩写偿还)。",
    )
    args = ap.parse_args()
    report = audit(args.tree)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and report["problems"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
