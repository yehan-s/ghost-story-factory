"""tools/audit_variants.py — narrative_variants 覆盖矩阵 + 重复访问无分化检测。

用法:
    python tools/audit_variants.py path/to/tree.json [--strict]

输出 JSON 报告 + exit code:
    0 = 全绿
    1 = 有警告(无分化重访节点 / 静态不可达 variant) — 仅 --strict 时返回
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _is_node_revisitable(node_id: str, nodes: Dict[str, Any]) -> bool:
    """节点是否可能被多次访问 — 简单判断:
    - ending 节点不可重访
    - 入度 ≥ 2(被多个其他节点指过来)→ 重访
    - 自身指自身(任意 choice → 自己)→ 重访
    """
    if nodes[node_id].get("ending_type"):
        return False
    inbound = 0
    for other_id, other in nodes.items():
        # 自身指自身 → 直接判定为重访
        if other_id == node_id:
            for ch in other.get("choices") or []:
                if ch.get("next") == node_id:
                    return True
            continue
        if other.get("next") == node_id:
            inbound += 1
        for ch in other.get("choices") or []:
            if ch.get("next") == node_id:
                inbound += 1
        for v in other.get("next_variants") or []:
            if v.get("next") == node_id:
                inbound += 1
    return inbound >= 2


def _is_clause_obviously_unreachable(req: Dict[str, Any]) -> bool:
    """启发式:if 条件明显不可能满足(纯静态,不需 BFS)。"""
    if not isinstance(req, dict):
        return False
    if "PR_min" in req and "PR_max" in req:
        if int(req["PR_min"]) > int(req["PR_max"]):
            return True
    if "GR_min" in req and "GR_max" in req:
        if int(req["GR_min"]) > int(req["GR_max"]):
            return True
    return False


def audit_variants(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    nodes = tree.get("nodes", {})

    variants_total = 0
    unreachable_variants: List[Dict[str, Any]] = []
    undifferentiated_revisit_nodes: List[str] = []
    coverage_matrix: Dict[str, Dict[str, Any]] = {}

    for node_id, node in nodes.items():
        nv = node.get("narrative_variants") or []
        next_v = node.get("next_variants") or []
        revisitable = _is_node_revisitable(node_id, nodes)
        coverage_matrix[node_id] = {
            "narrative_variants": len(nv),
            "next_variants": len(next_v),
            "is_revisitable": revisitable,
        }
        # 重访无分化(可重访但既无 narrative_variants 也无 next_variants)
        if revisitable and not nv and not next_v:
            undifferentiated_revisit_nodes.append(node_id)
        # 静态不可达 variant
        for v in nv + next_v:
            variants_total += 1
            cond = v.get("if") or {}
            if _is_clause_obviously_unreachable(cond):
                unreachable_variants.append(
                    {"node_id": node_id, "if": cond, "reason": "static_dead"}
                )

    return {
        "tree_path": str(tree_path),
        "node_count": len(nodes),
        "variants_total": variants_total,
        "coverage_matrix": coverage_matrix,
        "undifferentiated_revisit_nodes": sorted(undifferentiated_revisit_nodes),
        "unreachable_variants": unreachable_variants,
    }


def _exit_code(report: Dict[str, Any], strict: bool) -> int:
    if strict and (
        report["undifferentiated_revisit_nodes"] or report["unreachable_variants"]
    ):
        return 1
    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit tree.json variants coverage.")
    parser.add_argument("tree_path", type=Path)
    parser.add_argument("--strict", action="store_true", help="warnings exit 1")
    args = parser.parse_args(argv)
    report = audit_variants(args.tree_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return _exit_code(report, args.strict)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
