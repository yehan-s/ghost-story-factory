"""tools/audit_reactions.py — 反应式 variant 死代码 / 不可达 / 孤儿 resolver 检测。

ADR-008 守门工具。三红线:
- DEAD_REACTION:variant 引用某 X_resolved=Y,但 reaction_contracts 无声明
- UNREACHABLE_REACTION:resolver 节点存在,但 BFS 走不到 consumer 宿主
- ORPHAN_RESOLVE:声明了 resolver 但无 variant 消费

用法:
    python tools/audit_reactions.py path/to/tree.json
退出码:0=全绿, 2=有阻断(DEAD/UNREACHABLE)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


REACTION_KEYS = ("deduction_resolved", "foreshadow_resolved", "theme_resolved")
KEY_TO_CONTRACT = {
    "deduction_resolved": "deductions",
    "foreshadow_resolved": "foreshadows",
    "theme_resolved": "themes",
}


def _walk_requires(node: Dict[str, Any]):
    """yield (ctx, require_dict) 给节点的所有 require 字典(variants 的 if + choices 的 require)。"""
    for v in node.get("narrative_variants") or []:
        if "if" in v:
            yield ("variant", v["if"])
    for ch in node.get("choices") or []:
        if "require" in ch:
            yield ("choice", ch["require"])


def _walk_reaction_keys(req: Dict[str, Any]):
    """递归遍历 require(含 any_of/all_of/not),yield (key, value)。"""
    if not isinstance(req, dict):
        return
    for key in REACTION_KEYS:
        if key in req:
            yield (key, req[key])
    for sub in req.get("any_of") or []:
        yield from _walk_reaction_keys(sub)
    for sub in req.get("all_of") or []:
        yield from _walk_reaction_keys(sub)
    if "not" in req:
        yield from _walk_reaction_keys(req["not"])


def _collect_ids(value: Any) -> List[str]:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value or [])


def _bfs_reachable(nodes: Dict[str, Any], start: str) -> Set[str]:
    if not start or start not in nodes:
        return set()
    seen = {start}
    q = deque([start])
    while q:
        cur = q.popleft()
        node = nodes.get(cur) or {}
        for ch in node.get("choices") or []:
            nxt = ch.get("next")
            if nxt and nxt not in seen and nxt in nodes:
                seen.add(nxt)
                q.append(nxt)
        # next_variants(v6+ 跳转分支)
        for nv in node.get("next_variants") or []:
            nxt = nv.get("next")
            if nxt and nxt not in seen and nxt in nodes:
                seen.add(nxt)
                q.append(nxt)
    return seen


def audit(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    contracts = tree.get("reaction_contracts") or {}
    start = tree.get("start_node") or tree.get("start_node_id") or next(iter(nodes), None)
    reachable = _bfs_reachable(nodes, start) if start else set()
    problems: List[Dict[str, Any]] = []

    # 收集所有 reaction 引用 + 宿主节点
    consumed: Dict[str, Set[str]] = {"deductions": set(), "foreshadows": set(), "themes": set()}
    consumer_map: Dict[Tuple[str, str], Set[str]] = {}
    for nid, node in nodes.items():
        for ctx, req in _walk_requires(node):
            for key, val in _walk_reaction_keys(req):
                ctype = KEY_TO_CONTRACT[key]
                for x in _collect_ids(val):
                    consumed[ctype].add(x)
                    consumer_map.setdefault((ctype, x), set()).add(nid)
                    if x not in (contracts.get(ctype) or {}):
                        problems.append({
                            "code": "DEAD_REACTION",
                            "node": nid,
                            "ctx": ctx,
                            "msg": f"{key}={x!r} 但 reaction_contracts.{ctype} 无声明",
                        })

    # UNREACHABLE_REACTION
    for ctype in ("deductions", "foreshadows", "themes"):
        for ref_id, contract in (contracts.get(ctype) or {}).items():
            resolver = (contract or {}).get("resolver_node")
            if not resolver or resolver not in nodes:
                problems.append({
                    "code": "UNREACHABLE_REACTION",
                    "node": resolver or "?",
                    "msg": f"{ctype}.{ref_id} resolver_node {resolver!r} 不存在于节点表",
                })
                continue
            if resolver not in reachable:
                problems.append({
                    "code": "UNREACHABLE_REACTION",
                    "node": resolver,
                    "msg": f"{ctype}.{ref_id} resolver_node 从 root 不可达",
                })
                continue
            from_resolver = _bfs_reachable(nodes, resolver)
            for host in consumer_map.get((ctype, ref_id), set()):
                if host not in from_resolver:
                    problems.append({
                        "code": "UNREACHABLE_REACTION",
                        "node": host,
                        "msg": f"{ctype}.{ref_id} 解开后回不到 consumer {host}",
                    })

    # ORPHAN_RESOLVE
    for ctype in ("deductions", "foreshadows", "themes"):
        for ref_id in (contracts.get(ctype) or {}).keys():
            if ref_id not in consumed[ctype]:
                resolver = ((contracts[ctype][ref_id] or {}).get("resolver_node")) or "?"
                problems.append({
                    "code": "ORPHAN_RESOLVE",
                    "node": resolver,
                    "msg": f"{ctype}.{ref_id} 声明了 resolver 但无 variant 消费",
                })

    return {
        "tree": str(tree_path),
        "consumed_count": {k: len(v) for k, v in consumed.items()},
        "contracts_count": {k: len(contracts.get(k) or {}) for k in ("deductions", "foreshadows", "themes")},
        "problems": problems,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    args = ap.parse_args()
    report = audit(args.tree)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "UNREACHABLE_REACTION")]
    sys.exit(2 if blockers else 0)


if __name__ == "__main__":
    main()
