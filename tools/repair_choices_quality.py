#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择点质量驱动的对话树修复工具

用途：
- 扫描对话树中质量不佳的节点（基于 BMAD 评分、默认选择占比）
- 对质量不佳的节点重新调用 ChoicePointsGenerator 生成新选择
- 回写修复后的树到数据库

使用：
    # Dry-run 模式（仅扫描和报告）
    python3 tools/repair_choices_quality.py --db database/ghost_stories.db --story-id 2 --dry-run

    # 应用修复（写回数据库）
    python3 tools/repair_choices_quality.py --db database/ghost_stories.db --story-id 2 --apply

    # 只修复低于特定评分的节点
    python3 tools/repair_choices_quality.py --db database/ghost_stories.db --story-id 2 --min-score 6.0 --apply

    # 只修复默认选择占比高的节点
    python3 tools/repair_choices_quality.py --db database/ghost_stories.db --story-id 2 --max-default-ratio 0.3 --apply

设计理念（遵循 ADR-004 & TASK_CHOICE_POINTS_QUALITY）：
- 不在 TreeBuilder 主循环中"现场死磕"单个节点
- 通过离线工具有计划地修复质量问题
- 使用 LLMClient 模式（而非 CrewAI）进行重新生成
"""

import argparse
import json
import sqlite3
import gzip
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# 添加项目路径到 sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

try:
    from src.ghost_story_factory.engine.choice_evaluator import ChoiceQualityEvaluator
    from src.ghost_story_factory.engine.choices import ChoicePointsGenerator, Choice
    from src.ghost_story_factory.engine.state import GameState
    from src.ghost_story_factory.utils.logging_utils import get_logger
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保从项目根目录运行此脚本，或已安装项目包：pip install -e .")
    sys.exit(1)

logger, _ = get_logger()


def _load_tree(row: sqlite3.Row) -> Tuple[Dict[str, Any], bool]:
    """加载对话树（支持压缩）"""
    data = row["tree_data"]
    compressed = bool(row["compressed"]) if "compressed" in row.keys() else False
    if compressed:
        text = gzip.decompress(data).decode("utf-8")
    else:
        text = data
    return json.loads(text), compressed


def _dump_tree(tree: Dict[str, Any], compressed: bool) -> Tuple[bytes | str, int]:
    """序列化对话树（保持原压缩方式）"""
    text = json.dumps(tree, ensure_ascii=False, indent=2)
    if compressed:
        return gzip.compress(text.encode("utf-8")), 1
    return text, 0


def _is_default_choice(choice: Dict[str, Any]) -> bool:
    """判断是否为默认选择（兜底选项）"""
    text = choice.get("choice_text", "")
    choice_id = choice.get("choice_id", "")

    # 检查常见的默认选择模式
    default_patterns = [
        "继续调查", "原地观察", "直面关键线索",
        "_E1", "_E2", "_E3",  # 默认选择 ID 后缀
        "保持警惕", "寻找线索"
    ]

    return any(pattern in text or pattern in choice_id for pattern in default_patterns)


def scan_tree_quality(
    tree: Dict[str, Any],
    evaluator: ChoiceQualityEvaluator,
    min_score: float = 6.0,
    max_default_ratio: float = 0.5
) -> List[Dict[str, Any]]:
    """
    扫描对话树，识别质量不佳的节点

    Args:
        tree: 对话树 JSON
        evaluator: BMAD 评估器
        min_score: 最低可接受的整体评分（低于此值需要修复）
        max_default_ratio: 最大允许的默认选择占比（高于此值需要修复）

    Returns:
        需要修复的节点列表，每项包含：node_id, score, default_ratio, reasons
    """
    problematic_nodes = []

    for node_id, node_data in tree.items():
        if not isinstance(node_data, dict):
            continue

        choices = node_data.get("choices", [])
        if not choices:
            continue

        # 构造简单的 GameState（用于评估）
        game_state = GameState()
        game_state.current_scene = node_data.get("scene_id", "S1")

        # 提取节拍信息（如果有）
        beat_info = {
            "beat_type": node_data.get("beat_type"),
            "leads_to_ending": node_data.get("leads_to_ending", False),
            "tension_level": node_data.get("tension_level")
        }

        # BMAD 评估
        eval_result = evaluator.evaluate(
            scene_id=game_state.current_scene,
            choices=choices,
            game_state=game_state,
            beat_info=beat_info
        )

        overall_score = eval_result.get("overall_score", 10.0)

        # 计算默认选择占比
        default_count = sum(1 for c in choices if _is_default_choice(c))
        default_ratio = default_count / len(choices) if choices else 0.0

        # 判断是否需要修复
        reasons = []
        needs_repair = False

        if overall_score < min_score:
            needs_repair = True
            reasons.append(f"BMAD 评分过低: {overall_score:.2f} < {min_score}")

        if default_ratio > max_default_ratio:
            needs_repair = True
            reasons.append(f"默认选择占比过高: {default_ratio:.2%} > {max_default_ratio:.0%}")

        if needs_repair:
            problematic_nodes.append({
                "node_id": node_id,
                "scene_id": game_state.current_scene,
                "score": overall_score,
                "default_ratio": default_ratio,
                "num_choices": len(choices),
                "reasons": reasons,
                "dimensions": eval_result.get("dimensions", []),
                "suggestions": eval_result.get("suggestions", []),
                "beat_info": beat_info
            })

    return problematic_nodes


def repair_node_choices(
    node_id: str,
    node_data: Dict[str, Any],
    generator: ChoicePointsGenerator,
    original_score: float
) -> Tuple[List[Dict[str, Any]], float]:
    """
    为单个节点重新生成高质量选择

    Args:
        node_id: 节点 ID
        node_data: 节点数据
        generator: ChoicePointsGenerator 实例
        original_score: 原始 BMAD 评分

    Returns:
        (新选择列表, 新 BMAD 评分)
    """
    # 构造 GameState
    game_state = GameState()
    game_state.current_scene = node_data.get("scene_id", "S1")
    game_state.timestamp = node_data.get("timestamp", "00:00")
    game_state.PR = node_data.get("PR", 0)
    game_state.GR = node_data.get("GR", 0)
    game_state.WF = node_data.get("WF", 0)

    # 提取节拍信息
    beat_type = node_data.get("beat_type")
    tension_level = node_data.get("tension_level")
    is_critical_beat = node_data.get("is_critical_beat", False)
    beat_leads_to_ending = node_data.get("leads_to_ending", False)

    # 提取叙事上下文（如果有）
    narrative_context = node_data.get("narrative")

    # 获取最近的选择（用于去重）
    recent_choices = []
    if "choices" in node_data:
        recent_choices = [c.get("choice_text", "") for c in node_data["choices"][:3]]

    try:
        # 调用生成器（使用 LLMClient 模式）
        new_choices_objs = generator.generate_choices(
            current_scene=game_state.current_scene,
            game_state=game_state,
            narrative_context=narrative_context,
            beat_type=beat_type,
            tension_level=tension_level,
            is_critical_beat=is_critical_beat,
            beat_leads_to_ending=beat_leads_to_ending,
            recent_choices=recent_choices
        )

        # 转换为 dict（兼容 Pydantic 和普通对象）
        new_choices = []
        for c in new_choices_objs:
            if hasattr(c, "dict"):
                new_choices.append(c.dict())
            elif isinstance(c, dict):
                new_choices.append(c)
            else:
                # 手动构造
                new_choices.append({
                    "choice_id": getattr(c, "choice_id", ""),
                    "choice_text": getattr(c, "choice_text", ""),
                    "choice_type": str(getattr(c, "choice_type", "normal")),
                    "consequences": getattr(c, "consequences", {}),
                    "preconditions": getattr(c, "preconditions", {}),
                    "tags": getattr(c, "tags", [])
                })

        # 评估新选择
        evaluator = ChoiceQualityEvaluator()
        beat_info = {
            "beat_type": beat_type,
            "leads_to_ending": beat_leads_to_ending,
            "tension_level": tension_level
        }
        eval_result = evaluator.evaluate(
            scene_id=game_state.current_scene,
            choices=new_choices,
            game_state=game_state,
            beat_info=beat_info
        )

        new_score = eval_result.get("overall_score", 0.0)

        logger.info(
            f"[Repair] Node {node_id} | 原评分: {original_score:.2f} → 新评分: {new_score:.2f} | "
            f"选项数: {len(new_choices)}"
        )

        return new_choices, new_score

    except Exception as e:
        logger.error(f"[Repair] Node {node_id} 修复失败: {e}")
        # 修复失败时返回空列表和原评分
        return [], original_score


def repair_tree(
    tree: Dict[str, Any],
    story_info: Dict[str, Any],
    problematic_nodes: List[Dict[str, Any]],
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    修复对话树中的质量问题节点

    Args:
        tree: 对话树 JSON
        story_info: 故事信息（包含 GDD, Lore 等）
        problematic_nodes: 需要修复的节点列表
        dry_run: 是否仅模拟（不实际修改树）

    Returns:
        修复统计信息
    """
    stats = {
        "total_scanned": len(tree),
        "total_problematic": len(problematic_nodes),
        "attempted_repair": 0,
        "successful_repair": 0,
        "failed_repair": 0,
        "score_improvements": []
    }

    if dry_run:
        print(f"\n🔍 Dry-run 模式：发现 {len(problematic_nodes)} 个质量问题节点")
        for node in problematic_nodes[:5]:  # 只显示前 5 个
            print(f"  - {node['node_id']}: 评分={node['score']:.2f}, "
                  f"默认占比={node['default_ratio']:.0%}, 原因={'; '.join(node['reasons'])}")
        if len(problematic_nodes) > 5:
            print(f"  ... 及其他 {len(problematic_nodes) - 5} 个节点")
        return stats

    # 初始化 ChoicePointsGenerator
    gdd_content = story_info.get("gdd", "")
    lore_content = story_info.get("lore", "")
    main_story = story_info.get("main_story", "")

    generator = ChoicePointsGenerator(
        gdd_content=gdd_content,
        lore_content=lore_content,
        main_story=main_story
    )

    print(f"\n🔧 开始修复 {len(problematic_nodes)} 个节点...")

    for node_info in problematic_nodes:
        node_id = node_info["node_id"]
        node_data = tree.get(node_id)

        if not node_data:
            logger.warning(f"[Repair] 节点 {node_id} 在树中不存在，跳过")
            continue

        stats["attempted_repair"] += 1

        # 修复节点
        new_choices, new_score = repair_node_choices(
            node_id=node_id,
            node_data=node_data,
            generator=generator,
            original_score=node_info["score"]
        )

        if new_choices and new_score > node_info["score"]:
            # 回写树
            node_data["choices"] = new_choices
            stats["successful_repair"] += 1
            stats["score_improvements"].append({
                "node_id": node_id,
                "before": node_info["score"],
                "after": new_score,
                "delta": new_score - node_info["score"]
            })
            print(f"  ✅ {node_id}: {node_info['score']:.2f} → {new_score:.2f} "
                  f"(+{new_score - node_info['score']:.2f})")
        else:
            stats["failed_repair"] += 1
            print(f"  ❌ {node_id}: 修复未改善质量或失败")

    return stats


def main():
    ap = argparse.ArgumentParser(description="选择点质量驱动的对话树修复工具")
    ap.add_argument("--db", default="database/ghost_stories.db", help="SQLite 数据库路径")
    ap.add_argument("--story-id", type=int, required=True, help="故事 ID")
    ap.add_argument("--min-score", type=float, default=6.0,
                   help="最低可接受的 BMAD 评分（默认 6.0）")
    ap.add_argument("--max-default-ratio", type=float, default=0.5,
                   help="最大允许的默认选择占比（默认 0.5）")
    ap.add_argument("--dry-run", action="store_true",
                   help="仅扫描和报告，不实际修复（默认）")
    ap.add_argument("--apply", action="store_true",
                   help="应用修复并写回数据库")
    args = ap.parse_args()

    dry_run = not args.apply or args.dry_run

    # 连接数据库
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 加载故事信息
    cur.execute(
        """
        SELECT c.name as city, s.title, s.synopsis
        FROM stories s
        JOIN cities c ON s.city_id = c.id
        WHERE s.id = ?
        """,
        (args.story_id,)
    )
    story_row = cur.fetchone()

    if not story_row:
        print(f"❌ 故事 ID {args.story_id} 不存在")
        conn.close()
        sys.exit(1)

    story_info = {
        "city": story_row["city"],
        "title": story_row["title"],
        "synopsis": story_row["synopsis"],
        "gdd": "",  # GDD 存储在文件系统中，修复时可选
        "lore": "",  # Lore 存储在文件系统中，修复时可选
        "main_story": ""  # 可选：从其他表加载
    }

    print(f"📖 故事: {story_info['city']} - {story_info['title']}")

    # 加载对话树
    cur.execute(
        """
        SELECT character_id, tree_data, compressed
        FROM dialogue_trees
        WHERE story_id = ?
        ORDER BY character_id
        """,
        (args.story_id,)
    )

    tree_rows = cur.fetchall()

    if not tree_rows:
        print(f"❌ 故事 ID {args.story_id} 没有对话树")
        conn.close()
        sys.exit(1)

    print(f"📊 找到 {len(tree_rows)} 个对话树")

    # 初始化评估器
    evaluator = ChoiceQualityEvaluator(
        gdd_content=story_info["gdd"],
        lore_content=story_info["lore"],
        main_story=story_info.get("main_story", "")
    )

    # 处理每个角色的对话树
    total_stats = {
        "total_scanned": 0,
        "total_problematic": 0,
        "attempted_repair": 0,
        "successful_repair": 0,
        "failed_repair": 0,
        "score_improvements": []
    }

    for row in tree_rows:
        character_id = row["character_id"]
        tree, compressed = _load_tree(row)

        print(f"\n🎭 角色: {character_id}")

        # 扫描质量问题
        problematic_nodes = scan_tree_quality(
            tree=tree,
            evaluator=evaluator,
            min_score=args.min_score,
            max_default_ratio=args.max_default_ratio
        )

        # 修复（或报告）
        stats = repair_tree(
            tree=tree,
            story_info=story_info,
            problematic_nodes=problematic_nodes,
            dry_run=dry_run
        )

        # 累计统计
        for key in ["total_scanned", "total_problematic", "attempted_repair",
                   "successful_repair", "failed_repair"]:
            total_stats[key] += stats[key]
        total_stats["score_improvements"].extend(stats.get("score_improvements", []))

        # 写回数据库（如果不是 dry-run）
        if not dry_run and stats["successful_repair"] > 0:
            blob, comp_flag = _dump_tree(tree, compressed)
            cur.execute(
                """
                UPDATE dialogue_trees
                SET tree_data = ?, compressed = ?
                WHERE story_id = ? AND character_id = ?
                """,
                (blob, comp_flag, args.story_id, character_id)
            )
            print(f"  💾 已写回数据库")

    # 提交事务
    if not dry_run:
        conn.commit()
        print(f"\n✅ 修复已提交到数据库")

    # 打印总结
    print(f"\n{'='*60}")
    print(f"📊 修复总结")
    print(f"{'='*60}")
    print(f"扫描节点总数: {total_stats['total_scanned']}")
    print(f"发现问题节点: {total_stats['total_problematic']}")
    print(f"尝试修复节点: {total_stats['attempted_repair']}")
    print(f"成功修复节点: {total_stats['successful_repair']}")
    print(f"修复失败节点: {total_stats['failed_repair']}")

    if total_stats["score_improvements"]:
        print(f"\n🎯 评分改善详情（前 10 个）:")
        for item in total_stats["score_improvements"][:10]:
            print(f"  - {item['node_id']}: "
                  f"{item['before']:.2f} → {item['after']:.2f} "
                  f"(+{item['delta']:.2f})")

    print(f"\n模式: {'Dry-run（未写回）' if dry_run else 'Applied（已写回）'}")

    conn.close()


if __name__ == "__main__":
    main()
