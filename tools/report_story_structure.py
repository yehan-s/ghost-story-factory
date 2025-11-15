#!/usr/bin/env python3
"""
故事结构与时长验收脚本

用途：
- 从 JSON 文件加载对话树（以及可选的 PlotSkeleton）；
- 使用 TimeValidator + PlotSkeleton 指标生成一份综合报告；
- 以人类可读的方式输出到控制台。

用法示例：
    venv/bin/python tools/report_story_structure.py \
        --tree-json checkpoints/sample_tree.json \
        --skeleton-json checkpoints/sample_skeleton.json
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from ghost_story_factory.pregenerator.story_report import build_story_report
from ghost_story_factory.pregenerator.skeleton_model import PlotSkeleton


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="故事结构与时长验收工具")
    parser.add_argument(
        "--tree-json",
        required=True,
        help="对话树 JSON 文件路径（node_id -> node_dict 结构）",
    )
    parser.add_argument(
        "--skeleton-json",
        help="PlotSkeleton JSON 文件路径（可选）",
    )

    args = parser.parse_args(argv)

    tree_path = Path(args.tree_json)
    if not tree_path.exists():
        raise SystemExit(f"未找到对话树文件: {tree_path}")

    tree_data = _load_json(tree_path)

    skeleton: Optional[PlotSkeleton] = None
    if args.skeleton_json:
        sk_path = Path(args.skeleton_json)
        if not sk_path.exists():
            raise SystemExit(f"未找到骨架文件: {sk_path}")
        sk_data = _load_json(sk_path)
        skeleton = PlotSkeleton.from_dict(sk_data)

    report = build_story_report(tree_data, skeleton)

    # 控制台输出（简洁模式）
    tree_metrics = report.get("tree_metrics", {})
    sk_metrics = report.get("skeleton_metrics", {})
    verdict = report.get("verdict", {})

    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║              故事结构与时长验收报告                             ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")

    print("【对话树指标】")
    print(f"  总节点数           : {tree_metrics.get('total_nodes')}")
    print(f"  主线深度           : {tree_metrics.get('main_path_depth')}")
    print(f"  预计时长（分钟）   : {tree_metrics.get('estimated_duration_minutes')}")
    print(f"  结局数量           : {tree_metrics.get('ending_count')}")
    print(f"  深度达标           : {tree_metrics.get('passes_depth_check')}")
    print(f"  时长达标           : {tree_metrics.get('passes_duration_check')}")
    print(f"  结局数量达标       : {tree_metrics.get('passes_endings_check')}")
    print("")

    if sk_metrics:
        print("【骨架指标】")
        if "error" in sk_metrics:
            print(f"  骨架解析错误       : {sk_metrics['error']}")
        else:
            cfg = sk_metrics.get("config", {})
            print(f"  骨架标题           : {sk_metrics.get('title')}")
            print(f"  幕数量             : {sk_metrics.get('num_acts')}")
            print(f"  总节拍数           : {sk_metrics.get('num_beats')}")
            print(f"  关键节拍数         : {sk_metrics.get('num_critical_beats')}")
            print(f"  结局节拍数         : {sk_metrics.get('num_ending_beats')}")
            print(f"  配置 min_main_depth: {cfg.get('min_main_depth')}")
            print(f"  配置 target_depth  : {cfg.get('target_main_depth')}")
            print(f"  配置 target_endings: {cfg.get('target_endings')}")
            print(f"  配置 max_branches  : {cfg.get('max_branches_per_node')}")
        print("")

    print("【综合结论】")
    print(f"  全部达标           : {verdict.get('passes')}")
    print(f"  深度 OK            : {verdict.get('depth_ok')}")
    print(f"  时长 OK            : {verdict.get('duration_ok')}")
    print(f"  结局 OK            : {verdict.get('endings_ok')}")
    print("")


if __name__ == "__main__":
    main()

