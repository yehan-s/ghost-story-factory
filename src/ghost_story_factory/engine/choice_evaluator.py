"""
选择点质量评估器（BMAD 风格，多维离线打分）

用途：
- 针对单个节点的一组选项，从结构 / 世界观 / 节奏 / 多样性等维度打分；
- 默认使用启发式评估（无 LLM 依赖），可选在运行环境中启用 LLM 多评委策略；
- 仅作为离线诊断工具，不直接干预 TreeBuilder 的实时生成逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .state import GameState

try:
    from .choices import Choice
except Exception:
    # 兼容：当 pydantic 不可用时，退化为简单对象
    @dataclass
    class Choice:  # type: ignore
        choice_id: str
        choice_text: str
        choice_type: str = "normal"
        consequences: Optional[Dict[str, Any]] = None
        preconditions: Optional[Dict[str, Any]] = None
        tags: Optional[List[str]] = None


@dataclass
class DimensionScore:
    """单个维度的打分结果"""

    name: str
    score: float
    comment: str


class ChoiceQualityEvaluator:
    """
    选择点质量评估器（BMAD 风格）

    说明：
    - 评估入口为 evaluate(...)；
    - 若运行环境中可用 CrewAI/LLM，可拓展 _evaluate_with_llm；
    - 默认实现只使用启发式评估，保证在无外部依赖的环境中也能工作。
    """

    def __init__(self, gdd_content: str = "", lore_content: str = "", main_story: str = ""):
        self.gdd = gdd_content
        self.lore = lore_content
        self.main_story = main_story

    def evaluate(
        self,
        scene_id: str,
        choices: List[Choice],
        game_state: GameState,
        beat_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        评估一组选项的质量（多维度）

        Args:
            scene_id: 当前场景 ID
            choices: 选项列表（Choice 或等价对象）
            game_state: 当前游戏状态
            beat_info: 可选的节拍信息（包含 beat_type / leads_to_ending 等）

        Returns:
            dict: {overall_score: float, dimensions: [...], suggestions: [...]}
        """
        # 目前默认走启发式路径，避免在测试环境中引入 LLM 依赖。
        return self._evaluate_heuristic(scene_id, choices, game_state, beat_info)

    def _evaluate_heuristic(
        self,
        scene_id: str,
        choices: List[Choice],
        game_state: GameState,
        beat_info: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        启发式评估：基于简单统计给出结构化评分。
        """
        dim_scores: List[DimensionScore] = []
        suggestions: List[str] = []

        # 内部工具：同时兼容 Choice 对象与原始 dict
        def _get_text(c: Choice | Dict[str, Any]) -> str:
            if isinstance(c, dict):
                return str(c.get("choice_text") or c.get("text") or "").strip()
            return str(getattr(c, "choice_text", "") or "").strip()

        def _get_type(c: Choice | Dict[str, Any]) -> str:
            if isinstance(c, dict):
                return str(c.get("choice_type") or c.get("type") or "normal")
            return str(getattr(c, "choice_type", "normal"))

        def _get_consequences(c: Choice | Dict[str, Any]) -> Dict[str, Any]:
            if isinstance(c, dict):
                cons = c.get("consequences")
            else:
                cons = getattr(c, "consequences", None)
            return cons or {}

        # 预处理
        texts = [_get_text(c) for c in choices]
        texts_non_empty = [t for t in texts if t]
        num_choices = len(texts_non_empty)

        # ==================== 结构维度 ====================
        structure_score = 5.0
        if num_choices < 2:
            structure_score = 2.0
            suggestions.append("该节点选项数量少于 2 个，容易形成伪选择。")
        elif 2 <= num_choices <= 4:
            structure_score = 8.0
        else:
            structure_score = 6.0
            suggestions.append("该节点选项数量超过 4 个，可能导致选择瘫痪。")

        # 检查是否存在 critical 选项
        has_critical = any(_get_type(c).lower() == "critical" for c in choices)
        if has_critical:
            structure_score += 0.5
        else:
            suggestions.append("可以考虑在关键节拍上增加至少一个 critical 选项。")

        # 若 beat 允许结局，检查是否有结局 flag
        if beat_info and beat_info.get("leads_to_ending"):
            has_ending_flag = False
            for c in choices:
                cons = _get_consequences(c)
                flags = cons.get("flags") or {}
                if any(str(k).startswith("结局_") for k in flags.keys()):
                    has_ending_flag = True
                    break
            if has_ending_flag:
                structure_score += 1.0
            else:
                structure_score -= 1.0
                suggestions.append("该节拍允许结局出现，但选项中没有显式的结局 flag（结局_XXX）。")

        structure_score = max(0.0, min(10.0, structure_score))
        dim_scores.append(
            DimensionScore(
                name="structure",
                score=structure_score,
                comment=f"选项数={num_choices}，存在critical={has_critical}",
            )
        )

        # ==================== 多样性维度 ====================
        diversity_score = 5.0
        unique_texts = set(texts_non_empty)
        if not texts_non_empty:
            diversity_score = 0.0
            suggestions.append("该节点没有有效的选项文本。")
        else:
            uniq_ratio = len(unique_texts) / float(len(texts_non_empty))
            if uniq_ratio >= 0.9:
                diversity_score = 8.0
            elif uniq_ratio >= 0.7:
                diversity_score = 7.0
            else:
                diversity_score = 5.0
                suggestions.append("该节点选项文本重复度较高，可以进一步拉开差异。")

        dim_scores.append(
            DimensionScore(
                name="diversity",
                score=diversity_score,
                comment=f"唯一文本比例={len(unique_texts)}/{len(texts_non_empty)}",
            )
        )

        # ==================== 节奏维度（粗略） ====================
        beat_type = (beat_info or {}).get("beat_type")
        pacing_score = 7.0  # 默认中等偏上
        if beat_type in ("setup", "aftermath"):
            # 这些节拍不需要极端行动，普通选择即可
            pacing_score = 7.5
        elif beat_type in ("escalation", "twist", "climax"):
            # 希望看到更多“推进型”选项
            # 简单用包含“前往/推进/直接/关键”等词来估计
            advance_like = [
                t for t in texts_non_empty if any(kw in t for kw in ("前往", "推进", "直接", "关键"))
            ]
            if not advance_like:
                pacing_score = 5.5
                suggestions.append(
                    f"在 {beat_type} 节拍下应至少有一条明显推动剧情的选项（例如包含“前往/推进/直接/关键”等）。"
                )
        dim_scores.append(
            DimensionScore(
                name="pacing",
                score=pacing_score,
                comment=f"beat_type={beat_type or '未知'}",
            )
        )

        # ==================== 世界观维度（占位） ====================
        # 目前启发式无法真正理解世界观，仅给出中性评分。
        lore_score = 7.0
        dim_scores.append(
            DimensionScore(
                name="lore",
                score=lore_score,
                comment="启发式模式下无法核实世界观一致性，如需严格检查请使用 LLM 评估路径。",
            )
        )

        # ==================== 汇总 ====================
        overall = sum(d.score for d in dim_scores) / float(len(dim_scores)) if dim_scores else 0.0

        return {
            "overall_score": overall,
            "dimensions": [d.__dict__ for d in dim_scores],
            "suggestions": suggestions,
        }
