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
from ..engine.choice_evaluator import ChoiceQualityEvaluator
from ..engine.state import GameState


def _build_game_state_from_raw(raw: Dict[str, Any] | None) -> GameState:
    """从节点中的 game_state 字段构造 GameState（尽量兼容旧结构）"""
    data: Dict[str, Any] = dict(raw or {})

    # 旧树结构中使用 time 字段，这里归一化为 timestamp
    if "time" in data and "timestamp" not in data:
        data["timestamp"] = data.pop("time")

    # 只保留 GameState 支持的字段，避免多余键报错
    allowed_keys = set(GameState.__dataclass_fields__.keys())
    cleaned = {k: v for k, v in data.items() if k in allowed_keys}

    return GameState(**cleaned)


def _compute_choice_quality_by_act(
    dialogue_tree: Dict[str, Any],
    skeleton: Optional[PlotSkeleton],
) -> Dict[str, Any]:
    """
    基于 ChoiceQualityEvaluator，对每一幕进行离线 BMAD 式选择点质量评估。

    设计原则：
    - 只在有骨架时启用（需要 act_index 信息）；
    - 只做离线诊断，不影响主流程 verdict；
    - 评估对象为“有 choices 的节点”，按 act_index 聚合。
    """
    if skeleton is None:
        return {}

    try:
        evaluator = ChoiceQualityEvaluator()
    except Exception:
        # 评估器不可用时，不阻断主流程
        return {}

    # 展开骨架节拍，用于在缺少 metadata.act_index 时按 depth 近似映射
    beats = list(skeleton.beats)

    def _beat_for_depth(depth: Optional[int]):
        """根据节点深度获取对应节拍（与 DialogueTreeBuilder 保持一致）"""
        if depth is None or not beats:
            return None
        idx = max(0, depth - 1)
        if idx >= len(beats):
            idx = len(beats) - 1
        return beats[idx]

    # 每幕聚合统计：overall_score 与各维度平均分
    per_act: Dict[int, Dict[str, Any]] = {}

    for node in dialogue_tree.values():
        choices = node.get("choices") or []
        if not isinstance(choices, list) or not choices:
            continue

        meta = node.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = {}

        act_index = meta.get("act_index")
        beat_type = meta.get("beat_type")
        leads_to_ending = meta.get("leads_to_ending")

        # 若节点上没有显式 act_index，则退化为 depth -> beat 映射
        if act_index is None:
            depth = node.get("depth")
            beat = _beat_for_depth(depth)
            if beat is not None:
                act_index = getattr(beat, "act_index", None)
                if beat_type is None:
                    beat_type = getattr(beat, "beat_type", None)
                if leads_to_ending is None:
                    leads_to_ending = getattr(beat, "leads_to_ending", None)

        if act_index is None:
            # 无法确定幕信息时跳过该节点
            continue

        # 构造 GameState，尽量兼容旧树结构
        try:
            state = _build_game_state_from_raw(node.get("game_state") or {})
        except Exception:
            # 状态解析失败时，退回默认 GameState
            state = GameState()

        beat_info: Dict[str, Any] = {}
        if beat_type is not None:
            beat_info["beat_type"] = beat_type
        if leads_to_ending is not None:
            beat_info["leads_to_ending"] = leads_to_ending

        scene = str(node.get("scene", "")) or "未知场景"

        try:
            result = evaluator.evaluate(
                scene_id=scene,
                choices=choices,
                game_state=state,
                beat_info=beat_info or None,
            )
        except Exception:
            # 单节点评估失败不影响整体统计
            continue

        try:
            act_idx_int = int(act_index)
        except Exception:
            continue

        slot = per_act.setdefault(
            act_idx_int,
            {
                "count": 0,
                "overall_sum": 0.0,
                "dimensions": {},  # name -> {"sum": float, "count": int}
            },
        )

        slot["count"] += 1
        overall = float(result.get("overall_score", 0.0) or 0.0)
        slot["overall_sum"] += overall

        for dim in result.get("dimensions") or []:
            name = str(dim.get("name", "unknown"))
            score = float(dim.get("score", 0.0) or 0.0)
            d_slot = slot["dimensions"].setdefault(
                name,
                {"sum": 0.0, "count": 0},
            )
            d_slot["sum"] += score
            d_slot["count"] += 1

    if not per_act:
        return {}

    # 为每一幕补上 label 信息
    labels_by_index = {act.index: act.label for act in skeleton.acts}

    acts_summary = []
    for act_idx in sorted(per_act.keys()):
        data = per_act[act_idx]
        count = data["count"] or 0
        if count <= 0:
            continue
        avg_overall = data["overall_sum"] / float(count)

        dims_summary = []
        for name, d in data["dimensions"].items():
            dim_count = d["count"] or 0
            if dim_count <= 0:
                continue
            avg_score = d["sum"] / float(dim_count)
            dims_summary.append(
                {
                    "name": name,
                    "avg_score": avg_score,
                }
            )

        acts_summary.append(
            {
                "act_index": act_idx,
                "label": labels_by_index.get(act_idx, f"Act {act_idx}"),
                "num_nodes_evaluated": count,
                "avg_overall_score": avg_overall,
                "dimensions": dims_summary,
            }
        )

    return {"acts": acts_summary}


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

    # 按幕聚合的 BMAD 风格选择点质量指标（仅在有骨架时启用，且不影响主 verdict）
    try:
        choice_quality_by_act = _compute_choice_quality_by_act(dialogue_tree, skeleton)
    except Exception:
        choice_quality_by_act = {}

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
        "choice_quality_by_act": choice_quality_by_act,
        "verdict": verdict,
    }
