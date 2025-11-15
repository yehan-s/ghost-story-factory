#!/usr/bin/env python3
"""
结构指标检查脚本

用途：
- 对 PlotSkeleton（故事骨架）做基础结构指标统计与阈值检查；
- 后续可以扩展支持对话树 JSON。

用法示例：
    python tools/check_structure_metrics.py --skeleton path/to/skeleton.json
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from ghost_story_factory.pregenerator.skeleton_model import PlotSkeleton


def load_json(path: Path) -> Dict[str, Any]:
    """读取 JSON 文件"""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def analyze_skeleton(path: Path) -> int:
    """分析骨架结构并打印指标，返回建议退出码（0=通过，1=存在明显不足）"""
    data = load_json(path)
    skeleton = PlotSkeleton.from_dict(data)

    print("📁 骨架文件:", path)
    print("📖 标题:", skeleton.title)
    print()

    print("=== 基础结构 ===")
    print(f"- 幕数量: {skeleton.num_acts}")
    print(f"- 总节拍数: {skeleton.num_beats}")
    print(f"- 关键节拍数 (is_critical_branch_point=True): {skeleton.num_critical_beats}")
    print(f"- 标记为结局的节拍数 (leads_to_ending=True): {skeleton.num_ending_beats}")
    print()

    cfg = skeleton.config
    print("=== 配置约束 (SkeletonConfig) ===")
    print(f"- min_main_depth        : {cfg.min_main_depth}")
    print(f"- target_main_depth     : {cfg.target_main_depth}")
    print(f"- target_endings        : {cfg.target_endings}")
    print(f"- max_branches_per_node : {cfg.max_branches_per_node}")
    print()

    # 粗略估算：主线深度 ~ 非结局节拍数，结局数量 ~ leads_to_ending 标记数
    estimated_main_depth = max(0, skeleton.num_beats - skeleton.num_ending_beats)
    estimated_endings = skeleton.num_ending_beats or 0

    print("=== 粗略估算 ===")
    print(f"- 估算主线深度（非结局节拍数）: {estimated_main_depth}")
    print(f"- 估算结局数量（leads_to_ending=True）: {estimated_endings}")
    print()

    problems = []

    if estimated_main_depth < cfg.min_main_depth:
        problems.append(
            f"主线深度偏低：估算 {estimated_main_depth} < min_main_depth={cfg.min_main_depth}"
        )
    if estimated_endings < cfg.target_endings:
        problems.append(
            f"结局数量偏少：估算 {estimated_endings} < target_endings={cfg.target_endings}"
        )

    if problems:
        print("⚠️  结构告警：")
        for msg in problems:
            print(f"  - {msg}")
        return 1

    print("✅ 结构大致满足配置约束（仅为粗略静态检查）")
    return 0


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="骨架 / 结构指标检查工具")
    parser.add_argument(
        "--skeleton",
        type=str,
        help="PlotSkeleton JSON 文件路径",
    )
    args = parser.parse_args(argv)

    if not args.skeleton:
        parser.error("必须提供 --skeleton 路径（后续可扩展对话树检查）")

    path = Path(args.skeleton)
    if not path.exists():
        raise SystemExit(f"未找到文件: {path}")

    code = analyze_skeleton(path)
    raise SystemExit(code)


if __name__ == "__main__":
    main()

