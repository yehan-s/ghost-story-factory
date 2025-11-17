"""
ChoiceQualityEvaluator BMAD 启发式评估测试

目标：
- 验证在无 LLM 环境下，启发式路径能够对一组选项给出结构化评分；
- 覆盖典型的“良好结构”与“糟糕结构”场景；
- 确认评估器能同时兼容 Choice 对象与原始 dict。
"""

from ghost_story_factory.engine.choice_evaluator import ChoiceQualityEvaluator
from ghost_story_factory.engine.state import GameState
from ghost_story_factory.engine.choices import Choice, ChoiceType


def _make_state() -> GameState:
    """构造一个最小可用的 GameState。"""
    return GameState(PR=50, GR=10, WF=0, current_scene="S1", timestamp="00:30")


def test_evaluate_with_good_structure_and_ending_flag():
    """当结构合理且在结局节拍给出结局 flag 时，应得到较高评分。"""
    evaluator = ChoiceQualityEvaluator()
    state = _make_state()

    choices = [
        Choice(
            choice_id="A",
            choice_text="沿主线继续深入调查断桥下的锁链来源。",
            choice_type=ChoiceType.NORMAL,
            consequences={"timestamp": "+5min", "flags": {"investigate_chain": True}},
        ),
        Choice(
            choice_id="B",
            choice_text="接受白娘子的交易,用自己的班次替换她的轮回,结束这轮夜班。",
            choice_type=ChoiceType.CRITICAL,
            consequences={
                "timestamp": "+10min",
                "flags": {"结局_班次替换": True},
            },
        ),
    ]

    beat_info = {"beat_type": "climax", "leads_to_ending": True}

    result = evaluator.evaluate(
        scene_id="S1",
        choices=choices,
        game_state=state,
        beat_info=beat_info,
    )

    assert isinstance(result, dict)
    assert result["overall_score"] > 7.0
    dims = {d["name"]: d for d in result["dimensions"]}
    assert dims["structure"]["score"] >= 8.0
    assert dims["diversity"]["score"] >= 7.0


def test_evaluate_with_poor_structure_and_repetition_dict_input():
    """
    当只有一个重复且缺少 critical/结局 flag 的选项时，
    结构/多样性维度应当被明显拉低，且允许使用 dict 作为输入。
    """
    evaluator = ChoiceQualityEvaluator()
    state = _make_state()

    choices = [
        {
            "choice_id": "A",
            "choice_text": "原地等一等,再仔细观察周围环境。",
            "choice_type": "normal",
            "consequences": {"timestamp": "+1min"},
        }
    ]

    beat_info = {"beat_type": "escalation", "leads_to_ending": True}

    result = evaluator.evaluate(
        scene_id="S1",
        choices=choices,  # 直接传 dict
        game_state=state,
        beat_info=beat_info,
    )

    assert isinstance(result, dict)
    dims = {d["name"]: d for d in result["dimensions"]}

    # 结构维度：数量过少 + 缺少结局 flag，应低于 6
    assert dims["structure"]["score"] < 6.0

    # 多样性维度：只有一个选项，但至少给出 0 或中性评分
    assert 0.0 <= dims["diversity"]["score"] <= 8.0

