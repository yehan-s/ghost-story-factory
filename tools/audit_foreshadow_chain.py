#!/usr/bin/env python3
"""Pass 22 — 伏笔/推论/母题链条完整性审计。

ADR-008 反应契约的延伸:audit_reactions 已经检查 DEAD_REACTION / UNREACHABLE_REACTION /
ORPHAN_RESOLVE,本工具补三件:

- MISSING_LABEL:契约缺 `_label`(写在 reaction_contracts 但没人类可读标签)
- CONSUMER_NOT_REGISTERED:声明的 consumer_node 不在 nodes 表
- CONSUMER_NOT_CONSUMING:声明的 consumer_node 实际没 variant 引用对应 _resolved key

用法:
    python tools/audit_foreshadow_chain.py path/to/tree.json
退出码:0=全绿, 2=有阻断。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


REACTION_TO_KEY = {
    "deductions": "deduction_resolved",
    "foreshadows": "foreshadow_resolved",
    "themes": "theme_resolved",
}


def _walk_requires(node: Dict[str, Any]):
    for v in node.get("narrative_variants") or []:
        if "if" in v:
            yield v["if"]
    for ch in node.get("choices") or []:
        if "require" in ch:
            yield ch["require"]


def _walk_reaction_refs(req: Dict[str, Any]):
    if not isinstance(req, dict):
        return
    for k in ("deduction_resolved", "foreshadow_resolved", "theme_resolved"):
        if k in req:
            yield (k, req[k])
    for sub in req.get("any_of") or []:
        yield from _walk_reaction_refs(sub)
    for sub in req.get("all_of") or []:
        yield from _walk_reaction_refs(sub)
    if "not" in req:
        yield from _walk_reaction_refs(req["not"])


def _ids(value: Any) -> List[str]:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value or [])


def audit(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    contracts = tree.get("reaction_contracts") or {}
    problems: List[Dict[str, Any]] = []

    for ctype, key in REACTION_TO_KEY.items():
        for ref_id, contract in (contracts.get(ctype) or {}).items():
            contract = contract or {}
            label = contract.get("_label")
            consumer_nodes = contract.get("consumer_nodes") or []

            if not label:
                problems.append({
                    "code": "MISSING_LABEL",
                    "contract": f"{ctype}.{ref_id}",
                    "msg": f"reaction_contracts.{ctype}.{ref_id} 缺 _label 人类可读标签",
                })

            for cn in consumer_nodes:
                if cn not in nodes:
                    problems.append({
                        "code": "CONSUMER_NOT_REGISTERED",
                        "contract": f"{ctype}.{ref_id}",
                        "node": cn,
                        "msg": (
                            f"{ctype}.{ref_id} 声明 consumer_node={cn!r} 不在 nodes 表"
                        ),
                    })
                    continue
                # 验证该 consumer_node 实际有 variant/choice require 引用该 _resolved
                node = nodes[cn]
                found = False
                for req in _walk_requires(node):
                    for k, val in _walk_reaction_refs(req):
                        if k == key and ref_id in _ids(val):
                            found = True
                            break
                    if found:
                        break
                if not found:
                    problems.append({
                        "code": "CONSUMER_NOT_CONSUMING",
                        "contract": f"{ctype}.{ref_id}",
                        "node": cn,
                        "msg": (
                            f"{ctype}.{ref_id} 声明 {cn} 为 consumer 但该节点无 "
                            f"variant/choice 引用 {key}={ref_id!r}"
                        ),
                    })

    return {
        "tree": str(tree_path),
        "contracts_count": {k: len(contracts.get(k) or {}) for k in REACTION_TO_KEY},
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
