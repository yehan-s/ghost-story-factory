"""
story_report 模块测试

目标：
- 验证 build_story_report 能在有/无骨架的情况下生成合理的报告结构；
- 验证 verdict 字段与 TimeValidator 的输出一致。
"""

from typing import Dict, Any

from ghost_story_factory.pregenerator.story_report import build_story_report
from ghost_story_factory.pregenerator.skeleton_model import (
    PlotSkeleton,
    ActConfig,
    BeatConfig,
    BranchSpec,
    SkeletonConfig,
)


def _build_minimal_tree() -> Dict[str, Any]:
    """构造一个极小的对话树，仅用于测试统计逻辑。"""
    return {
        "root": {
            "node_id": "root",
            "scene": "S1",
            "depth": 0,
            "game_state": {"current_scene": "S1"},
            "children": ["node_0001"],
            "is_ending": False,
        },
        "node_0001": {
            "node_id": "node_0001",
            "scene": "S1",
            "depth": 1,
            "game_state": {
                "current_scene": "S1",
                "flags": {"结局_测试": True},
            },
            "children": [],
            "is_ending": True,
        },
    }


def _build_minimal_skeleton() -> PlotSkeleton:
    branches = [BranchSpec(branch_type="NORMAL", max_children=1, notes="测试")]
    beats = [
        BeatConfig(
            id="B1",
            act_index=1,
            beat_type="setup",
            tension_level=3,
            is_critical_branch_point=False,
            leads_to_ending=True,
            branches=branches,
        )
    ]
    return PlotSkeleton(
        title="测试故事",
        acts=[ActConfig(index=1, label="Act I", beats=beats)],
        config=SkeletonConfig(
            min_main_depth=0,
            target_main_depth=1,
            target_endings=1,
            max_branches_per_node=1,
        ),
        metadata={"city": "测试城"},
    )


def test_story_report_without_skeleton():
    """无骨架时，仍应生成 tree_metrics 与 verdict。"""
    tree = _build_minimal_tree()
    report = build_story_report(tree, skeleton=None)

    assert "tree_metrics" in report
    assert "verdict" in report
    assert "skeleton_metrics" in report  # 仍然返回一个字典


def test_story_report_with_skeleton():
    """有骨架时，skeleton_metrics 应包含基本结构指标。"""
    tree = _build_minimal_tree()
    skeleton = _build_minimal_skeleton()

    report = build_story_report(tree, skeleton=skeleton)
    sk = report["skeleton_metrics"]

    assert sk.get("title") == "测试故事"
    assert sk.get("num_acts") == 1
    assert sk.get("num_beats") == 1
    assert sk.get("num_ending_beats") == 1
    cfg = sk.get("config", {})
    assert cfg.get("min_main_depth") == 0
    assert cfg.get("target_endings") == 1

