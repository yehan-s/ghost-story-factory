"""
TreeBuilder guided 模式测试

目标：
- 验证在提供 PlotSkeleton 时，DialogueTreeBuilder 会：
  - 遵守骨架中的 max_branches_per_node / branches.max_children 约束；
  - 遵守 leads_to_ending 布局：不在早期深度提前终止，允许在后期深度出现结局。
"""

from pathlib import Path
from typing import Dict, Any, List

from ghost_story_factory.pregenerator.tree_builder import DialogueTreeBuilder
from ghost_story_factory.pregenerator.skeleton_model import (
    PlotSkeleton,
    ActConfig,
    BeatConfig,
    BranchSpec,
    SkeletonConfig,
)


class DummyDialogueTreeBuilder(DialogueTreeBuilder):
    """测试用的简化版本：不调用真实 LLM，仅使用固定选择/响应。"""

    def _init_generators(self):
        # 覆盖以避免初始化真实 ChoicePointsGenerator / RuntimeResponseGenerator
        return None

    def _generate_opening(self) -> str:
        return "测试开场"

    def _generate_choices(self, node) -> List[Dict[str, Any]]:
        # 每个节点都给出多个候选选择，用于测试 max_children 限制。
        # 使用 GR/flags 改变关键状态，避免被 StateManager 去重合并。
        return [
            {
                "choice_id": "A",
                "choice_text": "分支 A",
                "choice_type": "normal",
                "consequences": {
                    "GR": 5,
                    "flags": {"ENDING_MARK": True},
                },
                "preconditions": {},
            },
            {
                "choice_id": "B",
                "choice_text": "分支 B",
                "choice_type": "normal",
                "consequences": {
                    "GR": 5,
                    "flags": {"ENDING_MARK": True},
                },
                "preconditions": {},
            },
        ]

    def _generate_response(self, choice: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        return f"选择了: {choice.get('choice_id', '')}"

    def _check_ending(self, state: Dict[str, Any]) -> bool:
        """简化结局判断：只看自定义标志位，避免依赖 PR/GR/内置 flags 前缀。"""
        flags = state.get("flags", {})
        return bool(flags.get("ENDING_MARK"))


def _build_simple_skeleton() -> PlotSkeleton:
    """构建一个简单的骨架：

    - 统一 max_branches_per_node = 1
    - 第 1 层（depth=1）不允许结局
    - 第 2 层（depth=2）允许结局
    """
    branches = [BranchSpec(branch_type="NORMAL", max_children=1, notes="单分支测试")]
    beats = [
        BeatConfig(
            id="B1",
            act_index=1,
            beat_type="setup",
            tension_level=3,
            is_critical_branch_point=False,
            leads_to_ending=False,
            branches=branches,
        ),
        BeatConfig(
            id="B2",
            act_index=1,
            beat_type="climax",
            tension_level=8,
            is_critical_branch_point=True,
            leads_to_ending=True,
            branches=branches,
        ),
    ]

    return PlotSkeleton(
        title="骨架测试故事",
        acts=[ActConfig(index=1, label="Act I", beats=beats)],
        config=SkeletonConfig(
            min_main_depth=1,
            target_main_depth=3,
            target_endings=1,
            max_branches_per_node=1,
        ),
        metadata={"city": "测试城"},
    )


def test_guided_respects_max_branches_and_ending_depth(tmp_path, monkeypatch):
    """guided 模式应遵守：
    - 根节点只展开骨架允许的分支数量；
    - 不在 depth=1 提前结局，而在 depth>=2 时允许出现结局。
    """
    skeleton = _build_simple_skeleton()

    # 将增量日志写到临时目录，避免污染项目根目录
    inc_log = tmp_path / "tree_incremental.jsonl"
    monkeypatch.setenv("INCREMENTAL_LOG_PATH", str(inc_log))

    builder = DummyDialogueTreeBuilder(
        city="测试城",
        synopsis="测试 synopsis",
        gdd_content="GDD",
        lore_content="LORE",
        main_story="STORY",
        test_mode=True,
        plot_skeleton=skeleton,
    )

    checkpoint_path = tmp_path / "checkpoint.json"
    tree = builder.generate_tree(
        max_depth=3,
        min_main_path_depth=1,
        checkpoint_path=str(checkpoint_path),
    )

    # 1) 根节点的子节点数量应该被骨架的 max_children 限制为 1
    root = tree["root"]
    root_children = root.get("children", [])
    assert len(root_children) == 1

    # 2) 验证结局深度：不在 depth=1 提前结束，至少有一个结局出现在更深层
    depths = {nid: node.get("depth", 0) for nid, node in tree.items()}
    endings = [(nid, depths[nid]) for nid, node in tree.items() if node.get("is_ending")]

    # 至少应该存在一个结局节点
    assert endings, "guided 模式下应该至少存在一个结局节点"

    # 所有结局都不应出现在 depth=1
    assert all(depth >= 2 for _, depth in endings)


def test_guided_uses_skeleton_thresholds_for_validator(tmp_path, monkeypatch):
    """guided 模式下，TimeValidator 应与调用参数和骨架配置对齐：
    - min_main_path_depth 由 generate_tree 传入的参数决定；
    - min_endings 默认对齐骨架 config.target_endings。
    """
    skeleton = _build_simple_skeleton()

    inc_log = tmp_path / "tree_incremental.jsonl"
    monkeypatch.setenv("INCREMENTAL_LOG_PATH", str(inc_log))

    builder = DummyDialogueTreeBuilder(
        city="测试城",
        synopsis="测试 synopsis",
        gdd_content="GDD",
        lore_content="LORE",
        main_story="STORY",
        test_mode=True,
        plot_skeleton=skeleton,
    )

    checkpoint_path = tmp_path / "checkpoint_thresholds.json"

    # 显式传入一个与骨架 config 略有不同的主线最小深度，确保覆盖覆写逻辑
    tree = builder.generate_tree(
        max_depth=4,
        min_main_path_depth=2,
        checkpoint_path=str(checkpoint_path),
    )

    assert "root" in tree
    # generate_tree 调用后，TreeBuilder 与 TimeValidator 的深度阈值应保持一致
    assert builder.min_main_path_depth == 2
    assert builder.time_validator.min_main_path_depth == 2
    # 结局数量门槛应默认对齐骨架配置
    assert builder.time_validator.min_endings == skeleton.config.target_endings
