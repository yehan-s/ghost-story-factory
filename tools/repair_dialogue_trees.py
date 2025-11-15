#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话树增量修复脚本

用途：
- 扫描数据库中的对话树
- 回填缺失的 next_node_id（可唯一推断时）
- 对无法推断的选项标记 hidden=true（运行时将自动隐藏）
- 保留原有压缩方式

使用：
    python3 tools/repair_dialogue_trees.py --db database/ghost_stories.db --story-id 2 --dry-run
    python3 tools/repair_dialogue_trees.py --db database/ghost_stories.db --story-id 2 --apply

默认 dry-run，仅打印修复报告，不写回。
"""

import argparse
import json
import sqlite3
import gzip
from typing import Dict, Any, Tuple


def _load_tree(row: sqlite3.Row) -> Tuple[Dict[str, Any], bool]:
    data = row["tree_data"]
    compressed = bool(row["compressed"]) if "compressed" in row.keys() else False
    if compressed:
        text = gzip.decompress(data).decode("utf-8")
    else:
        text = data
    return json.loads(text), compressed


def _dump_tree(tree: Dict[str, Any], compressed: bool):
    text = json.dumps(tree, ensure_ascii=False, indent=2)
    if compressed:
        return gzip.compress(text.encode("utf-8")), 1
    return text, 0


def _build_child_index(tree: Dict[str, Any]) -> Dict[Tuple[str, str], str]:
    """构建 (parent_id, parent_choice_id) -> child_id 的索引（仅唯一映射）。"""
    mapping = {}
    counts = {}
    for nid, node in tree.items():
        if not isinstance(node, dict):
            continue
        pid = node.get("parent_id")
        pcid = node.get("parent_choice_id")
        if pid and pcid:
            key = (pid, pcid)
            counts[key] = counts.get(key, 0) + 1
            # 先记录，待会只保留唯一计数项
            mapping[key] = nid
    # 过滤非唯一
    unique = {k: v for k, v in mapping.items() if counts.get(k) == 1}
    return unique


def repair_tree(tree: Dict[str, Any]) -> Dict[str, int]:
    """修复一棵对话树：
    - 缺 next_node_id 时，若 (parent_id, parent_choice_id) 唯一可推断，则回填
    - 否则将该选项标记 hidden=true
    返回统计信息
    """
    child_index = _build_child_index(tree)
    fixed = 0
    hidden = 0
    visited_nodes = 0

    for nid, node in tree.items():
        if not isinstance(node, dict):
            continue
        visited_nodes += 1
        choices = node.get("choices", []) or []
        new_choices = []
        for ch in choices:
            cid = ch.get("choice_id")
            next_id = ch.get("next_node_id")
            if next_id and next_id in tree:
                new_choices.append(ch)
                continue
            # 尝试唯一回填
            key = (nid, cid)
            maybe = child_index.get(key)
            if maybe:
                ch["next_node_id"] = maybe
                fixed += 1
                new_choices.append(ch)
            else:
                # 无法推断，标记隐藏（保留以便追溯）
                ch["hidden"] = True
                hidden += 1
                new_choices.append(ch)
        node["choices"] = new_choices

    return {"fixed": fixed, "hidden": hidden, "nodes": visited_nodes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="database/ghost_stories.db", help="SQLite 数据库路径")
    ap.add_argument("--story-id", type=int, default=None, help="仅修复指定故事ID（默认全部）")
    ap.add_argument("--apply", action="store_true", help="写回修复结果（默认仅dry-run）")
    ap.add_argument("--dry-run", action="store_true", help="仅打印报告，不写回（默认）")
    args = ap.parse_args()

    dry_run = not args.apply or args.dry_run

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 选出目标 rows
    if args.story_id:
        cur.execute(
            """
            SELECT story_id, character_id, tree_data, compressed
            FROM dialogue_trees
            WHERE story_id = ?
            ORDER BY character_id
            """,
            (args.story_id,),
        )
    else:
        cur.execute(
            """
            SELECT story_id, character_id, tree_data, compressed
            FROM dialogue_trees
            ORDER BY story_id, character_id
            """
        )

    rows = cur.fetchall()
    total_fixed = total_hidden = total_nodes = 0
    by_story: Dict[int, Dict[str, int]] = {}

    for row in rows:
        story_id = row["story_id"]
        character_id = row["character_id"]
        tree, compressed = _load_tree(row)
        stats = repair_tree(tree)
        total_fixed += stats["fixed"]
        total_hidden += stats["hidden"]
        total_nodes += stats["nodes"]
        s = by_story.setdefault(story_id, {"fixed": 0, "hidden": 0, "trees": 0})
        s["fixed"] += stats["fixed"]
        s["hidden"] += stats["hidden"]
        s["trees"] += 1

        if not dry_run and (stats["fixed"] > 0 or stats["hidden"] > 0):
            blob, comp_flag = _dump_tree(tree, compressed)
            cur.execute(
                """
                UPDATE dialogue_trees
                SET tree_data = ?, compressed = ?
                WHERE story_id = ? AND character_id = ?
                """,
                (blob, comp_flag, story_id, character_id),
            )

    if not dry_run:
        conn.commit()

    print("\n=== 修复报告 ===")
    print(f"总节点: {total_nodes} | 回填: {total_fixed} | 隐藏: {total_hidden}")
    for sid, st in sorted(by_story.items()):
        print(f"- 故事 {sid}: 树={st['trees']} 回填={st['fixed']} 隐藏={st['hidden']}")
    print("模式:", "dry-run" if dry_run else "APPLIED")

    conn.close()


if __name__ == "__main__":
    main()

