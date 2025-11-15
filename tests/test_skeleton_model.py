"""
骨架模型单元测试

验证 PlotSkeleton / ActConfig / BeatConfig / BranchSpec / SkeletonConfig
的基本行为和统计属性。
"""

from ghost_story_factory.pregenerator.skeleton_model import (
    PlotSkeleton,
    ActConfig,
    BeatConfig,
    BranchSpec,
    SkeletonConfig,
)


def test_plot_skeleton_basic_stats():
    """基础统计属性：幕数 / 节拍数 / 关键节拍 / 结局节拍"""
    branches = [
        BranchSpec(branch_type="CRITICAL", max_children=2, notes="关键分支"),
        BranchSpec(branch_type="NORMAL", max_children=1, notes="普通分支"),
    ]

    beats_act1 = [
        BeatConfig(
            id="A1_B1",
            act_index=1,
            beat_type="setup",
            tension_level=3,
            is_critical_branch_point=False,
            leads_to_ending=False,
            branches=branches,
        ),
        BeatConfig(
            id="A1_B2",
            act_index=1,
            beat_type="escalation",
            tension_level=5,
            is_critical_branch_point=True,
            leads_to_ending=False,
            branches=branches,
        ),
    ]

    beats_act2 = [
        BeatConfig(
            id="A2_B1",
            act_index=2,
            beat_type="climax",
            tension_level=9,
            is_critical_branch_point=True,
            leads_to_ending=True,
            branches=branches,
        ),
    ]

    skeleton = PlotSkeleton(
        title="测试故事",
        acts=[
            ActConfig(index=1, label="Act I", beats=beats_act1),
            ActConfig(index=2, label="Act II", beats=beats_act2),
        ],
        config=SkeletonConfig(
            min_main_depth=10,
            target_main_depth=20,
            target_endings=3,
            max_branches_per_node=3,
        ),
        metadata={"city": "杭州"},
    )

    assert skeleton.num_acts == 2
    assert skeleton.num_beats == 3
    # 关键节拍：A1_B2 + A2_B1
    assert skeleton.num_critical_beats == 2
    # 结局节拍：A2_B1
    assert skeleton.num_ending_beats == 1


def test_plot_skeleton_roundtrip_dict():
    """to_dict / from_dict 往返不丢失关键结构信息"""
    branches = [BranchSpec(branch_type="NORMAL", max_children=1)]
    beats = [
        BeatConfig(
            id="B1",
            act_index=1,
            beat_type="setup",
            tension_level=4,
            is_critical_branch_point=False,
            leads_to_ending=False,
            branches=branches,
        )
    ]

    original = PlotSkeleton(
        title="Roundtrip Story",
        acts=[ActConfig(index=1, label="Act I", beats=beats)],
        config=SkeletonConfig(
            min_main_depth=5,
            target_main_depth=8,
            target_endings=2,
            max_branches_per_node=2,
        ),
        metadata={"city": "测试城"},
    )

    data = original.to_dict()
    restored = PlotSkeleton.from_dict(data)

    assert restored.title == original.title
    assert restored.num_acts == original.num_acts
    assert restored.num_beats == original.num_beats
    assert restored.config.min_main_depth == original.config.min_main_depth
    assert restored.metadata.get("city") == "测试城"

