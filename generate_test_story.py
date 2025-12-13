#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简化的故事生成脚本 - 跳过CrewAI素材收集，直接使用已有资源"""

import os
import sys
from pathlib import Path
import json

# 设置环境变量
os.environ["USE_PLOT_SKELETON"] = "1"

from ghost_story_factory.pregenerator.skeleton_generator import SkeletonGenerator
from ghost_story_factory.pregenerator.tree_builder import DialogueTreeBuilder
from ghost_story_factory.pregenerator.time_validator import TimeValidator
from ghost_story_factory.database import DatabaseManager
from ghost_story_factory.utils.llm_client import LLMClient, create_llm_client
from ghost_story_factory.utils.logging_utils import get_run_logger

def load_resource(file_path: str) -> str:
    """加载资源文件内容"""
    path = Path(file_path)
    if not path.exists():
        return ""
    return path.read_text(encoding='utf-8')

def main():
    city = "杭州"
    title = "断桥残血"
    protagonist = "夜班网约车司机"

    # 初始化日志
    logger, log_path = get_run_logger("test_story_generation")
    print(f"\n📝 日志文件: {log_path}\n")

    print(f"🎬 开始为【{city}】生成测试故事...")
    print(f"📖 标题: {title}")
    print(f"🎭 主角: {protagonist}\n")

    # 加载已有资源
    base_dir = Path(f"deliverables/程序-{city}/断桥残血")
    gdd_file = base_dir / f"{city}_{title}_gdd.md"
    lore_file = base_dir / f"{city}_{title}_lore_v2.md"
    story_file = base_dir / f"{city}_{title}_story.md"

    print(f"📁 资源目录: {base_dir}")
    print(f"   GDD: {'✅' if gdd_file.exists() else '❌'} {gdd_file.name}")
    print(f"   Lore: {'✅' if lore_file.exists() else '❌'} {lore_file.name}")
    print(f"   Story: {'✅' if story_file.exists() else '❌'} {story_file.name}\n")

    gdd_content = load_resource(str(gdd_file))
    lore_content = load_resource(str(lore_file))
    main_story = load_resource(str(story_file))

    # ============================================================
    # 阶段 1: 生成情节骨架 (使用 LLMClient)
    # ============================================================
    print("="*60)
    print("阶段 1: 生成情节骨架 (LLMClient 模式)")
    print("="*60)

    llm_client = create_llm_client()  # 自动检测 LLM_PROVIDER 环境变量
    skeleton_gen = SkeletonGenerator(city=city, llm=llm_client)

    print(f"[SkeletonGenerator] 使用 LLMClient 模式")
    skeleton = skeleton_gen.generate(
        title=title,
        synopsis=main_story[:500] if main_story else f"{city} {title} 测试故事",
        lore_v2_text=lore_content,
        main_story_text=main_story
    )

    if not skeleton:
        print("❌ 骨架生成失败")
        return

    print(f"\n✅ 骨架生成成功:")
    print(f"   标题: {skeleton.title}")
    print(f"   幕数: {len(skeleton.acts)}")
    print(f"   节拍数: {skeleton.num_beats}")
    print(f"   结局节拍数: {skeleton.num_ending_beats}")
    print(f"   配置: min_main_depth={skeleton.config.min_main_depth}, "
          f"target_main_depth={skeleton.config.target_main_depth}, "
          f"max_branches={skeleton.config.max_branches_per_node}\n")

    # 保存骨架到文件
    skeleton_file = base_dir / f"{city}_{title}_skeleton.json"
    skeleton_file.write_text(json.dumps(skeleton.to_dict(), ensure_ascii=False, indent=2))
    print(f"💾 骨架已保存: {skeleton_file}\n")

    # ============================================================
    # 阶段 2: 生成对话树 (Guided 模式)
    # ============================================================
    print("="*60)
    print("阶段 2: 生成对话树 (Guided 模式)")
    print("="*60)

    tree_builder = DialogueTreeBuilder(
        city=city,
        synopsis=main_story[:500] if main_story else f"{city} {title} 测试故事",
        gdd_content=gdd_content,
        lore_content=lore_content,
        main_story=main_story,
        plot_skeleton=skeleton
    )

    print(f"[TreeBuilder] 使用 Guided 模式 + LLMClient")
    print(f"[TreeBuilder] 目标深度: {skeleton.config.min_main_depth}-{skeleton.config.target_main_depth}")
    print(f"[TreeBuilder] 最大分支数: {skeleton.config.max_branches_per_node}\n")

    dialogue_tree = tree_builder.generate_tree(
        max_depth=skeleton.config.target_main_depth + 10,
        min_main_path_depth=skeleton.config.min_main_depth
    )

    if not dialogue_tree:
        print("❌ 对话树生成失败")
        return

    print(f"\n✅ 对话树生成成功:")
    print(f"   根节点: root")
    print(f"   总节点数: {len(dialogue_tree)}")

    # 计算深度和结局数
    max_depth = 0
    ending_count = 0
    visited = set()  # 添加访问集合，防止重复访问导致无限递归

    def traverse(node_id, depth=0):
        nonlocal max_depth, ending_count

        # 检查是否已访问（防止环路导致的无限递归）
        if node_id in visited:
            return

        visited.add(node_id)  # 标记为已访问
        max_depth = max(max_depth, depth)

        node = dialogue_tree.get(node_id)
        if not node:
            return

        if node.get('is_ending', False):
            ending_count += 1

        for choice in node.get('choices', []):
            next_id = choice.get('next_node_id')
            if next_id:  # visited 集合已经处理了循环检查
                traverse(next_id, depth + 1)

    traverse('root')

    print(f"   最大深度: {max_depth}")
    print(f"   结局数量: {ending_count}\n")

    # 保存到文件
    tree_file = base_dir / f"{city}_{title}_tree.json"
    tree_file.write_text(json.dumps(dialogue_tree, ensure_ascii=False, indent=2))
    print(f"💾 对话树已保存: {tree_file}\n")

    # ============================================================
    # 阶段 3: 保存到数据库
    # ============================================================
    print("="*60)
    print("阶段 3: 保存到数据库")
    print("="*60)

    db = DatabaseManager(db_path="database/ghost_stories.db")

    # 准备数据
    characters = [
        {
            "name": protagonist,
            "is_protagonist": True,
            "description": f"{city}的{protagonist}"
        }
    ]

    dialogue_trees_dict = {
        protagonist: dialogue_tree
    }

    # 使用时间验证器估算时长/深度，避免缺失字段导致崩溃
    time_validator = TimeValidator()
    validation_report = time_validator.get_validation_report(dialogue_tree)

    metadata = {
        "estimated_duration": validation_report.get("estimated_duration_minutes"),
        "total_nodes": len(dialogue_tree),
        "max_depth": max_depth
    }

    # 保存完整故事
    story_id = db.save_story(
        city_name=city,
        title=title,
        synopsis=main_story[:500] if main_story else "测试故事",
        characters=characters,
        dialogue_trees=dialogue_trees_dict,
        metadata=metadata
    )

    print(f"✅ 故事已保存到数据库: ID={story_id}\n")

    print("="*60)
    print("🎉 故事生成完成！")
    print("="*60)
    print(f"Story ID: {story_id}")
    print(f"城市: {city}")
    print(f"标题: {title}")
    print(f"节点数: {len(dialogue_tree)}")
    print(f"最大深度: {max_depth}")
    print(f"结局数: {ending_count}")
    print(f"\n可以使用以下命令查看质量报告:")
    print(f"  python3 tools/repair_choices_quality.py --db database/ghost_stories.db --story-id {story_id} --dry-run")
    print()

if __name__ == "__main__":
    main()
