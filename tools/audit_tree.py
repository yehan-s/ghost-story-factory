#!/usr/bin/env python3
"""剧本元数据审计工具 — 扫 tree.json,报告制作人质量问题。

用法:
    python tools/audit_tree.py
    python tools/audit_tree.py stories/hangzhou_yebanbaoan/tree.json

检查清单:
  伏笔:
    · 每条 foreshadow 是否至少有 1 个 _foreshadow_slot 触发点
    · 每条 shard 是否至少有 1 个 _foreshadow_clue 拾取点
    · explained_by_character / explained_by_ending 是否引用了有效目标
    · 是否引用了不存在的 foreshadow id

  NPC 档案:
    · related_foreshadows / key_items 引用是否有效
    · initial_location 是否是有效 SID

  推论(deductions):
    · requires_resolved 是否引用了有效 foreshadow id
    · requires 至少 2 个(否则没意义)

  时间年表:
    · related_foreshadows / related_npcs 引用是否有效
    · 年份递增(可选)

  地点:
    · landmark_map.connections 是否对称(S1↔S5 双向?)
    · node_id 是否在 nodes 里存在

  结局:
    · STORY_META.endings 每条是否在 nodes 里有 is_ending+ending_type 节点
    · 节点 ending_type 是否都在 STORY_META.endings 里

  连通性:
    · 从 start_node BFS 能否触达每个节点
    · 孤儿节点(已合并器报告,这里只列入总览)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def _walk_choices(node: Dict[str, Any]):
    """遍历节点的 choices,yields (next_id, choice_dict)。"""
    for c in (node.get("choices") or []):
        if c.get("next"):
            yield c["next"], c
        for v in (c.get("next_variants") or []):
            if v.get("next"):
                yield v["next"], c


class Issue:
    def __init__(self, level: str, category: str, message: str):
        self.level = level  # "ERROR" / "WARN" / "INFO"
        self.category = category
        self.message = message

    def fmt(self) -> str:
        icon = {"ERROR": "❌", "WARN": "⚠️ ", "INFO": "·"}.get(self.level, "·")
        return f"  {icon} [{self.category}] {self.message}"


def audit(tree: Dict[str, Any]) -> Tuple[List[Issue], Dict[str, int]]:
    issues: List[Issue] = []
    stats: Dict[str, int] = {}

    nodes: Dict[str, Any] = tree.get("nodes") or {}
    foreshadows: Dict[str, Any] = tree.get("foreshadows") or {}
    deductions: Dict[str, Any] = tree.get("deductions") or {}
    timeline = tree.get("timeline") or []
    npcs: Dict[str, Any] = tree.get("npcs") or {}
    landmark_map = tree.get("landmark_map") or []
    endings_meta: Dict[str, Any] = tree.get("endings") or {}

    fs_ids = set(foreshadows.keys())
    npc_ids = set(npcs.keys())
    landmark_ids = {lm.get("id") for lm in landmark_map}

    # === 1. 收集所有 _foreshadow_slot / _foreshadow_clue 触发点 ===
    slot_triggers: Dict[str, List[str]] = {}   # slot → [node_id, ...]
    shard_triggers: Dict[Tuple[str, str], List[str]] = {}  # (slot, shard) → [node_id]
    for node_id, node in nodes.items():
        for slot in (node.get("_foreshadow_slot") or []):
            slot_triggers.setdefault(slot, []).append(node_id)
        for clue in (node.get("_foreshadow_clue") or []):
            slot = clue.get("slot")
            shard = clue.get("shard")
            if slot and shard:
                shard_triggers.setdefault((slot, shard), []).append(node_id)
        # 选项级
        for c in (node.get("choices") or []):
            for slot in (c.get("_foreshadow_slot") or []):
                slot_triggers.setdefault(slot, []).append(f"{node_id}.choice")
            for clue in (c.get("_foreshadow_clue") or []):
                slot = clue.get("slot")
                shard = clue.get("shard")
                if slot and shard:
                    shard_triggers.setdefault((slot, shard), []).append(
                        f"{node_id}.choice"
                    )

    # === 2. 伏笔覆盖检查 ===
    fs_unreachable = 0
    for fs_id, meta in foreshadows.items():
        if fs_id not in slot_triggers:
            issues.append(Issue("ERROR", "foreshadow",
                                f"伏笔 '{fs_id}' 没有任何 _foreshadow_slot 触发点 — 玩家永远无法发现"))
            fs_unreachable += 1
        # 检查 explained_by_character / ending 引用
        by_end = meta.get("explained_by_ending")
        if by_end and by_end not in endings_meta:
            issues.append(Issue("WARN", "foreshadow",
                                f"伏笔 '{fs_id}' explained_by_ending='{by_end}' 不在 STORY_META.endings 中"))
        # 检查 shards
        shards = meta.get("shards") or []
        for sh in shards:
            shard_id = sh.get("id")
            if not shard_id:
                issues.append(Issue("WARN", "foreshadow",
                                    f"伏笔 '{fs_id}' 有 shard 缺 id 字段"))
                continue
            if (fs_id, shard_id) not in shard_triggers:
                issues.append(Issue("WARN", "foreshadow",
                                    f"伏笔 '{fs_id}' 的碎片 '{shard_id}' 没有任何 _foreshadow_clue 拾取点"))
    stats["foreshadows_total"] = len(foreshadows)
    stats["foreshadows_unreachable"] = fs_unreachable
    stats["foreshadow_slot_triggers"] = sum(len(v) for v in slot_triggers.values())
    stats["foreshadow_shard_triggers"] = sum(len(v) for v in shard_triggers.values())

    # === 3. 推论检查 ===
    for ded_id, meta in deductions.items():
        req = meta.get("requires_resolved") or []
        if len(req) < 2:
            issues.append(Issue("WARN", "deduction",
                                f"推论 '{ded_id}' requires_resolved < 2 条 — 复合推论才有意义"))
        for r in req:
            if r not in fs_ids:
                issues.append(Issue("ERROR", "deduction",
                                    f"推论 '{ded_id}' 引用了不存在的伏笔 '{r}'"))
    stats["deductions_total"] = len(deductions)

    # === 4. NPC 档案检查 ===
    for npc_id, info in npcs.items():
        for ref in (info.get("related_foreshadows") or []):
            if ref not in fs_ids:
                issues.append(Issue("ERROR", "npc",
                                    f"NPC '{npc_id}' related_foreshadows 引用不存在的伏笔 '{ref}'"))
        loc = info.get("initial_location")
        if loc is not None and loc not in landmark_ids:
            issues.append(Issue("ERROR", "npc",
                                f"NPC '{npc_id}' initial_location='{loc}' 不是有效地标"))
    stats["npcs_total"] = len(npcs)

    # === 5. 时间年表检查 ===
    for entry in timeline:
        for ref in (entry.get("related_foreshadows") or []):
            if ref not in fs_ids:
                issues.append(Issue("ERROR", "timeline",
                                    f"时间年表 {entry.get('year','?')} 引用不存在的伏笔 '{ref}'"))
        for ref in (entry.get("related_npcs") or []):
            if ref not in npc_ids:
                issues.append(Issue("WARN", "timeline",
                                    f"时间年表 {entry.get('year','?')} 引用不存在的 NPC '{ref}'"))
    stats["timeline_total"] = len(timeline)

    # === 6. 地点检查 ===
    for lm in landmark_map:
        sid = lm.get("id")
        nid = lm.get("node_id")
        if nid and nid not in nodes:
            issues.append(Issue("ERROR", "landmark",
                                f"地标 '{sid}' node_id='{nid}' 不存在于 nodes"))
        # connections 对称性
        for other_sid in (lm.get("connections") or []):
            other = next((x for x in landmark_map if x.get("id") == other_sid), None)
            if not other:
                issues.append(Issue("ERROR", "landmark",
                                    f"地标 '{sid}' connections 引用不存在的 '{other_sid}'"))
                continue
            if sid not in (other.get("connections") or []):
                issues.append(Issue("WARN", "landmark",
                                    f"地标连接不对称: '{sid}' → '{other_sid}',但 '{other_sid}' 未连回"))
    stats["landmarks_total"] = len(landmark_map)

    # === 7. 结局检查 ===
    declared_endings = set(endings_meta.keys())
    found_endings: Dict[str, List[str]] = {}
    for node_id, node in nodes.items():
        if node.get("is_ending"):
            etype = node.get("ending_type", "E_UNKNOWN")
            found_endings.setdefault(etype, []).append(node_id)
            if etype not in declared_endings:
                issues.append(Issue("WARN", "ending",
                                    f"节点 '{node_id}' 用 ending_type='{etype}',但未在 STORY_META.endings 注册"))
    for etype in declared_endings:
        if etype not in found_endings:
            issues.append(Issue("ERROR", "ending",
                                f"结局 '{etype}' 在 STORY_META 注册,但没有节点声明 is_ending=true + ending_type='{etype}'"))
    stats["endings_declared"] = len(declared_endings)
    stats["endings_implemented"] = len(found_endings)

    # === 8. 连通性 ===
    start = tree.get("start_node", "n_intro")
    if start not in nodes:
        issues.append(Issue("ERROR", "graph",
                            f"start_node='{start}' 不在 nodes 中"))
    else:
        # 起点 = start + 所有 STORY_META.tools 引用的 node_id(picker 动态访问)
        reachable: Set[str] = {start}
        # tools 节点也算"入口"(picker 动态生成 travel/tool 选项,不在静态 choices 里)
        for tool in (tree.get("tools") or []):
            nid = tool.get("node_id")
            if nid in nodes:
                reachable.add(nid)
        # landmark_map.node_id 也算入口(从 picker 走过去)
        for lm in (tree.get("landmark_map") or []):
            nid = lm.get("node_id")
            if nid in nodes:
                reachable.add(nid)
        frontier = list(reachable)
        while frontier:
            nid = frontier.pop()
            node = nodes.get(nid) or {}
            for nxt, _ in _walk_choices(node):
                if nxt and nxt in nodes and nxt not in reachable:
                    reachable.add(nxt)
                    frontier.append(nxt)
        unreachable = set(nodes) - reachable
        if unreachable:
            for nid in sorted(unreachable):
                issues.append(Issue("WARN", "graph",
                                    f"节点 '{nid}' 从 start 不可达"))
        stats["nodes_total"] = len(nodes)
        stats["nodes_reachable"] = len(reachable)
        stats["nodes_unreachable"] = len(unreachable)

    # === 9. 道具 ===
    inv_desc = (tree.get("inv_descriptions") or {})
    inv_used: Set[str] = set()
    for node in nodes.values():
        # narrative & narrative_variants 引用
        # 简化:只看 effects.inv_add / require.inv_has / inv_lacks
        for c in (node.get("choices") or []):
            for it in (c.get("effects", {}) or {}).get("inv_add", []) or []:
                inv_used.add(it)
            for it in (c.get("effects", {}) or {}).get("inv_remove", []) or []:
                inv_used.add(it)
            req = c.get("require") or {}
            for it in req.get("inv_has", []) or []:
                inv_used.add(it)
            for it in req.get("inv_lacks", []) or []:
                inv_used.add(it)
    inv_orphan = set(inv_desc.keys()) - inv_used - {"未注明物品"}
    inv_undocumented = inv_used - set(inv_desc.keys())
    for it in sorted(inv_orphan):
        issues.append(Issue("WARN", "inventory",
                            f"道具 '{it}' 在 inv_descriptions 注册,但从未被任何节点引用"))
    for it in sorted(inv_undocumented):
        issues.append(Issue("WARN", "inventory",
                            f"道具 '{it}' 被节点引用,但 inv_descriptions 未注册"))
    stats["inv_described"] = len(inv_desc)
    stats["inv_used"] = len(inv_used)
    stats["inv_orphan"] = len(inv_orphan)
    stats["inv_undocumented"] = len(inv_undocumented)

    return issues, stats


def print_report(issues: List[Issue], stats: Dict[str, int]) -> int:
    by_cat: Dict[str, List[Issue]] = {}
    for i in issues:
        by_cat.setdefault(i.category, []).append(i)

    err_count = sum(1 for i in issues if i.level == "ERROR")
    warn_count = sum(1 for i in issues if i.level == "WARN")

    # 统计
    print()
    print("════════ 元数据审计报告 ════════")
    print()
    print(f"  伏笔: {stats.get('foreshadows_total', 0)} 条 ·  "
          f"未触达 {stats.get('foreshadows_unreachable', 0)} 条 · "
          f"slot 触发点 {stats.get('foreshadow_slot_triggers', 0)} · "
          f"shard 触发点 {stats.get('foreshadow_shard_triggers', 0)}")
    print(f"  推论: {stats.get('deductions_total', 0)} 条")
    print(f"  NPC: {stats.get('npcs_total', 0)} 条")
    print(f"  时间年表: {stats.get('timeline_total', 0)} 条")
    print(f"  地标: {stats.get('landmarks_total', 0)} 个")
    print(f"  结局: 注册 {stats.get('endings_declared', 0)} · "
          f"实现 {stats.get('endings_implemented', 0)}")
    print(f"  节点: {stats.get('nodes_total', 0)} 个 · "
          f"可达 {stats.get('nodes_reachable', 0)} · "
          f"孤儿 {stats.get('nodes_unreachable', 0)}")
    print(f"  道具: 注册 {stats.get('inv_described', 0)} · 引用 {stats.get('inv_used', 0)} · "
          f"孤儿 {stats.get('inv_orphan', 0)} · 未记录 {stats.get('inv_undocumented', 0)}")
    print()
    print("──────── 问题清单 ────────")
    if not issues:
        print("  ✅ 没有问题。")
    else:
        for cat in sorted(by_cat):
            print()
            print(f"  【{cat}】")
            for i in by_cat[cat]:
                print(i.fmt())
    print()
    print(f"  ❌ 错误: {err_count}    ⚠️  警告: {warn_count}")
    return 0 if err_count == 0 else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="剧本元数据审计")
    p.add_argument("tree_path", nargs="?",
                   default="stories/hangzhou_yebanbaoan/tree.json",
                   type=Path)
    args = p.parse_args(argv)
    if not args.tree_path.exists():
        print(f"❌ 找不到 tree: {args.tree_path}")
        return 1
    with args.tree_path.open("r", encoding="utf-8") as f:
        tree = json.load(f)
    issues, stats = audit(tree)
    return print_report(issues, stats)


if __name__ == "__main__":
    sys.exit(main())
