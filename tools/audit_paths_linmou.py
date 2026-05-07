"""tools/audit_paths_linmou.py — linmou_1985 周目必死不变量(INV-1~5)。

ADR-009 守门工具。Linmou Act 1 是悲剧 lore canon 红线,任何路径都必须收束到
4 个执念 ending(冤/悔/释/曝光),不允许"逃出生天"。

INV-1: 所有 linmou 周目终态(choices=[])∈ 4 ending 白名单
INV-2: 无边从 linmou 子图通向 Act 2/3 节点(本期 Act 2/3 不存在,trivial)
INV-3: 投湖节点 n_l1985_lake_jump 后置必为 ending,无中间 narrative
INV-4: 4 ending 节点必须有 _lore_canon.must_die: true(canon 标记)
INV-5(Pass 2): reachable 范围内 must_die 节点的 intent 必须 ⊆ {释/悔/冤/曝光},
        且 4 个 intent 必须全部由 reachable ending 承载(防止某 intent 路径塌陷)

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
from typing import Any, Dict, List, Optional, Set


LINMOU_ENDINGS: Set[str] = {
    "E_LINMOU_GRIEVANCE",
    "E_LINMOU_REGRET",
    "E_LINMOU_RELEASE",
    "E_LINMOU_EXPOSED",
}

LAKE_JUMP_NODE = "n_l1985_lake_jump"

# INV-5 (Pass 2 评审 R-Q1):林必死的 4 canon intent。
# 任何 must_die 节点的 _lore_canon.intent 必须 ⊆ 此集合;
# reachable 范围内 4 个 intent 必须各自至少有一个 ending 承载。
CANON_INTENTS: Set[str] = {"释", "悔", "冤", "曝光"}


def _bfs_reachable(
    nodes: Dict[str, Any],
    start: str,
    extra_entries: Optional[List[str]] = None,
) -> Set[str]:
    """BFS 可达性。

    ADR-010 沙盒契约:`_is_map_picker` 节点的 choices 由引擎动态生成
    (从 STORY_META.landmark_map),静态扫不到。所以接受 extra_entries 列表
    (通常是 landmark_map[*].node_id 和 _picker_endshift_choice.next),
    把它们也算入 BFS 起点。
    """
    if not start or start not in nodes:
        return set()
    entries: Set[str] = {start}
    for nid in (extra_entries or []):
        if nid in nodes:
            entries.add(nid)
    seen = set(entries)
    q = deque(entries)
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
        # picker 节点的 _picker_endshift_choice.next
        ec = node.get("_picker_endshift_choice")
        if ec:
            nxt = ec.get("next")
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

    # ADR-010 沙盒契约:linmou picker 是 _is_map_picker,choices 由引擎从
    # landmark_map 动态生成 — 把 linmou 的 4 地标 node_id 也作为 BFS 入口。
    extra_entries: List[str] = []
    for lm in (tree.get("landmark_map") or []):
        if lm.get("character") == "linmou_1985":
            nid = lm.get("node_id")
            if nid:
                extra_entries.append(nid)

    reachable = _bfs_reachable(nodes, start, extra_entries=extra_entries)

    # INV-1: 所有终态 ∈ 4 ending
    # ADR-010 沙盒契约:_is_map_picker 节点的 choices 由引擎动态生成,
    # 静态扫到 choices=[] 不代表 terminal,跳过 INV-1。
    for nid in reachable:
        node = nodes[nid] or {}
        if node.get("_is_map_picker"):
            continue
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

    # INV-5 (Pass 2 评审 R-Q1): 林必死零退让 — 4 canon intent 必须全部覆盖。
    # 语义: reachable 范围内,所有 must_die 节点的 intent 必须 ⊆ 4 canon 集合;
    # 且这 4 个 intent 必须各自至少有一个 reachable ending 承载
    # (防止某 intent 路径塌陷,导致 林必死 弱化为 "只有 3 种死法")。
    covered_intents: Set[str] = set()
    for nid in reachable:
        node = nodes[nid] or {}
        canon = node.get("_lore_canon") or {}
        if not canon.get("must_die"):
            continue
        intent = canon.get("intent")
        if not intent:
            problems.append({
                "code": "INV5_MISSING_INTENT",
                "node": nid,
                "msg": (
                    f"{nid} must_die=True 但缺 _lore_canon.intent "
                    f"(必须 ∈ {sorted(CANON_INTENTS)})"
                ),
            })
            continue
        if intent not in CANON_INTENTS:
            problems.append({
                "code": "INV5_INTENT_NOT_IN_CANON",
                "node": nid,
                "msg": (
                    f"{nid} intent={intent!r} 不在 canon 集 "
                    f"{sorted(CANON_INTENTS)}"
                ),
            })
            continue
        covered_intents.add(intent)

    missing_intents = CANON_INTENTS - covered_intents
    if missing_intents:
        problems.append({
            "code": "INV5_INTENT_NOT_REACHABLE",
            "node": "<global>",
            "msg": (
                f"以下 canon intent 无 reachable ending 承载: "
                f"{sorted(missing_intents)}"
                f"(林必死零退让,4 intent 必须全部覆盖)"
            ),
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
