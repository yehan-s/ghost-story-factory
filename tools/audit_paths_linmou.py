"""tools/audit_paths_linmou.py — linmou_1985 周目必死不变量(INV-1~4)。

ADR-009 守门工具。Linmou Act 1 是悲剧 lore canon 红线,任何路径都必须收束到
4 个执念 ending(冤/悔/释/曝光),不允许"逃出生天"。

INV-1: 所有 linmou 周目终态(choices=[])∈ 4 ending 白名单
INV-2: 无边从 linmou 子图通向 Act 2/3 节点(本期 Act 2/3 不存在,trivial)
INV-3: 投湖节点 n_l1985_lake_jump 后置必为 ending,无中间 narrative
INV-4: 4 ending 节点必须有 _lore_canon.must_die: true(canon 标记)

用法:
    python tools/audit_paths_linmou.py path/to/tree.json
退出码:0=全绿, 2=有 INV 违规
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Set


LINMOU_ENDINGS: Set[str] = {
    "E_LINMOU_GRIEVANCE",
    "E_LINMOU_REGRET",
    "E_LINMOU_RELEASE",
    "E_LINMOU_EXPOSED",
}

LAKE_JUMP_NODE = "n_l1985_lake_jump"


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
            if nxt and nxt in nodes and nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
        for nv in node.get("next_variants") or []:
            nxt = nv.get("next")
            if nxt and nxt in nodes and nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def audit(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    chars = tree.get("characters") or {}
    linmou = chars.get("linmou_1985") or {}
    start = linmou.get("start_node")

    problems: List[Dict[str, Any]] = []

    # 无 linmou character 注册 → trivial pass(P0 之前)
    if not start or start not in nodes:
        return {
            "tree": str(tree_path),
            "linmou_active": False,
            "problems": [],
        }

    reachable = _bfs_reachable(nodes, start)

    # INV-1: 所有终态 ∈ 4 ending
    for nid in reachable:
        node = nodes[nid] or {}
        if not (node.get("choices") or []):
            if nid not in LINMOU_ENDINGS:
                problems.append({
                    "code": "INV1_TERMINAL_NOT_IN_ENDINGS",
                    "node": nid,
                    "msg": (
                        f"{nid} choices=[] 但不在 4 ending 集合 "
                        f"{sorted(LINMOU_ENDINGS)}"
                    ),
                })

    # INV-3: 投湖节点出口必为 ending
    if LAKE_JUMP_NODE in nodes:
        node = nodes[LAKE_JUMP_NODE]
        for ch in node.get("choices") or []:
            nxt = ch.get("next")
            if nxt and nxt not in LINMOU_ENDINGS:
                problems.append({
                    "code": "INV3_LAKE_JUMP_NOT_TO_ENDING",
                    "node": LAKE_JUMP_NODE,
                    "msg": f"投湖节点出口 {nxt!r} 不在 4 ending 集合",
                })

    # INV-4: 4 ending 必须有 _lore_canon.must_die
    for eid in LINMOU_ENDINGS:
        if eid in reachable:
            node = nodes[eid]
            canon = node.get("_lore_canon") or {}
            if not canon.get("must_die"):
                problems.append({
                    "code": "INV4_MISSING_MUST_DIE_CANON",
                    "node": eid,
                    "msg": f"{eid} 缺 _lore_canon.must_die: true(ADR-009 必填)",
                })

    return {
        "tree": str(tree_path),
        "linmou_active": True,
        "linmou_reachable_count": len(reachable),
        "problems": problems,
    }


def main():
    ap = argparse.ArgumentParser(description="linmou_1985 必死不变量审计(ADR-009)")
    ap.add_argument("tree", type=Path)
    args = ap.parse_args()
    report = audit(args.tree)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(2 if report["problems"] else 0)


if __name__ == "__main__":
    main()
