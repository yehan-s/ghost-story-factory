"""
NodeTextFiller 测试

目标：
- 验证 NodeTextFiller 会为节点追加节拍元数据；
- 对缺失叙事的节点填充占位文本。
"""

from typing import Dict, Any

from ghost_story_factory.pregenerator.text_filler import NodeTextFiller
from ghost_story_factory.pregenerator.skeleton_model import (
    PlotSkeleton,
    ActConfig,
    BeatConfig,
    BranchSpec,
    SkeletonConfig,
)


def _build_sample_skeleton() -> PlotSkeleton:
    """构建一个简单骨架：两节拍，tension 不同。"""
    branches = [BranchSpec(branch_type="NORMAL", max_children=2, notes="测试")]
    beats = [
        BeatConfig(
            id="B1",
            act_index=1,
            beat_type="setup",
            tension_level=2,
            is_critical_branch_point=False,
            leads_to_ending=False,
            branches=branches,
        ),
        BeatConfig(
            id="B2",
            act_index=1,
            beat_type="climax",
            tension_level=9,
            is_critical_branch_point=True,
            leads_to_ending=True,
            branches=branches,
        ),
    ]
    return PlotSkeleton(
        title="骨架测试故事",
        acts=[ActConfig(index=1, label="Act I", beats=beats)],
        config=SkeletonConfig(
            min_main_depth=2,
            target_main_depth=3,
            target_endings=1,
            max_branches_per_node=2,
        ),
        metadata={"city": "测试城"},
    )


def test_text_filler_adds_metadata_and_narrative():
    """对话树节点应获得 beat 元数据，并填补空叙事。"""
    skeleton = _build_sample_skeleton()
    filler = NodeTextFiller(skeleton=skeleton)

    # 构造一个最小对话树：root + 两层子节点
    tree: Dict[str, Any] = {
        "root": {
            "node_id": "root",
            "scene": "S1",
            "depth": 0,
            "game_state": {"current_scene": "S1"},
            "children": ["node_0001"],
            "narrative": "",  # 故意留空
        },
        "node_0001": {
            "node_id": "node_0001",
            "scene": "S1",
            "depth": 1,
            "game_state": {"current_scene": "S1"},
            "children": ["node_0002"],
            "narrative": None,  # 故意留空
        },
        "node_0002": {
            "node_id": "node_0002",
            "scene": "S1",
            "depth": 2,
            "game_state": {"current_scene": "S1"},
            "children": [],
            "narrative": "已有叙事，不应被覆盖",
        },
    }

    filled = filler.fill(tree)

    # root 和 node_0001 narrative 应被填充
    assert filled["root"]["narrative"].strip()
    assert filled["node_0001"]["narrative"].strip()
    # node_0002 narrative 保持原值
    assert filled["node_0002"]["narrative"] == "已有叙事，不应被覆盖"

    # 检查元数据 beat_type / tension_level
    root_meta = filled["root"].get("metadata", {})
    n1_meta = filled["node_0001"].get("metadata", {})
    n2_meta = filled["node_0002"].get("metadata", {})

    # depth=1 对应第一个 beat（setup, tension=2）
    assert n1_meta.get("beat_type") == "setup"
    assert n1_meta.get("tension_level") == 2
    # depth=2 对应第二个 beat（climax, tension=9）
    assert n2_meta.get("beat_type") == "climax"
    assert n2_meta.get("tension_level") == 9

