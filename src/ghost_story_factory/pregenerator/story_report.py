"""
故事结构与时长验收报告

用途：
- 对单个角色的对话树做结构 + 时长的综合分析；
- 可选结合 PlotSkeleton，给出骨架与实际树之间的对照信息。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .time_validator import TimeValidator
from .skeleton_model import PlotSkeleton


def build_story_report(
    dialogue_tree: Dict[str, Any],
    skeleton: Optional[PlotSkeleton] = None,
) -> Dict[str, Any]:
    """
    生成故事结构与时长综合报告。

    Args:
        dialogue_tree: 对话树（node_id -> node_dict）
        skeleton: 可选的 PlotSkeleton，用于附加骨架指标

    Returns:
        报告字典
    """
    # 若有骨架，则优先使用骨架配置中的 min_main_depth 作为主线深度阈值，
    # 避免 TimeValidator 只依赖环境变量。
    min_depth_override: Optional[int] = None
    if skeleton is not None:
        try:
            min_depth_override = int(skeleton.config.min_main_depth)
        except Exception:
            min_depth_override = None

    tv = TimeValidator(min_main_path_depth=min_depth_override)
    tree_report = tv.get_validation_report(dialogue_tree)

    # 选择点质量基础指标（与结构解耦，只做统计）
    choice_metrics: Dict[str, Any] = {}
    try:
        total_nodes_with_choices = 0
        total_choices = 0
        choice_counts = []
        texts = []

        # 默认兜底选项的典型文案（用于估算默认选项占比）
        default_texts = {
            "沿主线线索继续深入",
            "原地观察环境细节",
            "直面关键线索（可能触发结局）",
            "继续调查",
            "离开此地",
        }
        default_choice_count = 0

        for node in dialogue_tree.values():
            choices = node.get("choices") or []
            if not isinstance(choices, list):
                continue
            if choices:
                total_nodes_with_choices += 1
                choice_counts.append(len(choices))
            for ch in choices:
                text = str(ch.get("choice_text", "")).strip()
                if not text:
                    continue
                texts.append(text)
                if text in default_texts:
                    default_choice_count += 1

        total_choices = len(texts)
        unique_count = len(set(texts)) if texts else 0
        avg_choices = (sum(choice_counts) / len(choice_counts)) if choice_counts else 0.0
        repetition_rate = 0.0
        if total_choices > 0 and unique_count >= 0:
            repetition_rate = 1.0 - (unique_count / float(total_choices))

        default_ratio = (default_choice_count / float(total_choices)) if total_choices else 0.0

        choice_metrics = {
            "total_nodes_with_choices": total_nodes_with_choices,
            "total_choices": total_choices,
            "avg_choices_per_node": avg_choices,
            "unique_choice_texts": unique_count,
            "repetition_rate": repetition_rate,
            "default_choice_count": default_choice_count,
            "default_choice_ratio": default_ratio,
        }
    except Exception:
        # 指标失败不影响主流程
        choice_metrics = {}

    # 骨架指标（可选）
    skeleton_report: Dict[str, Any] = {}
    if skeleton is not None:
        try:
            skeleton_report = {
                "title": skeleton.title,
                "num_acts": skeleton.num_acts,
                "num_beats": skeleton.num_beats,
                "num_critical_beats": skeleton.num_critical_beats,
                "num_ending_beats": skeleton.num_ending_beats,
                "config": {
                    "min_main_depth": skeleton.config.min_main_depth,
                    "target_main_depth": skeleton.config.target_main_depth,
                    "target_endings": skeleton.config.target_endings,
                    "max_branches_per_node": skeleton.config.max_branches_per_node,
                },
            }
        except Exception:
            skeleton_report = {"error": "骨架指标生成失败"}

    # 综合结论
    verdict = {
        "passes": bool(
            tree_report.get("passes_depth_check")
            and tree_report.get("passes_duration_check")
            and tree_report.get("passes_endings_check")
        ),
        "depth_ok": bool(tree_report.get("passes_depth_check")),
        "duration_ok": bool(tree_report.get("passes_duration_check")),
        "endings_ok": bool(tree_report.get("passes_endings_check")),
    }

    return {
        "tree_metrics": tree_report,
        "skeleton_metrics": skeleton_report,
        "choice_metrics": choice_metrics,
        "verdict": verdict,
    }
