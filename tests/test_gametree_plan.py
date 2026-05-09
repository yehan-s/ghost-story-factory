"""GameTreePlan 草案单元测试。"""

import json

from ghost_story_factory.pregenerator.gametree_plan import GameTreePlan
from ghost_story_factory.pregenerator.skeleton_model import (
    ActConfig,
    BeatConfig,
    BranchSpec,
    PlotSkeleton,
    SkeletonConfig,
)
from tools.audit_playability import analyze_playability
from tools.audit_reactions import audit as audit_reactions


def _sandbox_skeleton() -> PlotSkeleton:
    branches = [BranchSpec(branch_type="NORMAL", max_children=2)]
    beats = [
        BeatConfig(
            id="A1_B1",
            act_index=1,
            beat_type="setup",
            location_id="S1_security_room",
            npc_ids=["g273"],
            event_slots=["hub", "npc_meet"],
            asset_cues={"background": "security_room"},
            sandbox_role="hub",
            branches=branches,
        ),
        BeatConfig(
            id="A1_B2",
            act_index=1,
            beat_type="setup",
            location_id="S2_lobby",
            npc_ids=["red_girl"],
            event_slots=["landmark"],
            asset_cues={"background": "lobby"},
            sandbox_role="landmark",
            branches=branches,
        ),
        BeatConfig(
            id="A2_B1",
            act_index=2,
            beat_type="escalation",
            location_id="S3_archive",
            npc_ids=["archivist"],
            event_slots=["tool", "revisit"],
            asset_cues={"background": "archive", "sfx": ["paper_noise"]},
            sandbox_role="tool",
            revisit_hooks=["deduction_resolved:sandbox_probe"],
            branches=branches,
        ),
        BeatConfig(
            id="A2_B2",
            act_index=2,
            beat_type="twist",
            location_id="S4_roof",
            npc_ids=["g273"],
            event_slots=["tool", "ending_gate"],
            asset_cues={"background": "roof"},
            sandbox_role="tool",
            revisit_hooks=["ending_seen:E_TRUTH"],
            branches=branches,
        ),
    ]

    return PlotSkeleton(
        title="沙盒测试",
        acts=[
            ActConfig(index=1, label="Act I", beats=beats[:2]),
            ActConfig(index=2, label="Act II", beats=beats[2:]),
            ActConfig(index=3, label="Act III", beats=[]),
        ],
        config=SkeletonConfig(
            min_main_depth=4,
            target_main_depth=8,
            target_endings=1,
            max_branches_per_node=3,
        ),
    )


def test_gametree_plan_from_skeleton_builds_sandbox_outline():
    """从骨架生成的计划应有 hub、地标、工具和 NPC 路线。"""
    plan = GameTreePlan.from_skeleton(_sandbox_skeleton())

    assert plan.picker_location_id == "S1_security_room"
    assert len(plan.locations) == 4
    assert len(plan.tools) == 2
    assert len(plan.npc_routes) == 3
    assert all(location.connections for location in plan.locations)
    assert plan.tools[0].revisit_hooks == ["deduction_resolved:sandbox_probe"]
    assert plan.presentation_defaults["S3_archive"]["background"] == "archive"


def test_gametree_plan_minimal_tree_passes_playability_redlines():
    """M3 只验证内存导出能过基本可玩红线,不接正式审计链。"""
    plan = GameTreePlan.from_skeleton(_sandbox_skeleton())
    tree = plan.to_minimal_tree()
    report = analyze_playability(tree)

    assert report.ok
    assert report.dynamic_picker_nodes == 1
    assert report.ending_nodes == 1
    assert report.reachable_nodes == report.total_nodes
    assert len(tree["landmark_map"]) == 4
    assert len(tree["tools"]) == 2
    assert "E_SANDBOX_PROBE" in tree["endings"]
    assert any(
        choice.get("effects", {}).get("stay")
        for node in tree["nodes"].values()
        for choice in node.get("choices", [])
    )
    assert any(
        variant.get("if", {}).get("deduction_resolved") == "sandbox_probe"
        for node in tree["nodes"].values()
        for variant in node.get("narrative_variants", [])
    )


def test_gametree_plan_minimal_tree_has_real_navigation_edges():
    """地标连接应既存在于 landmark_map,也能转成实际可走 choice。"""
    plan = GameTreePlan.from_skeleton(_sandbox_skeleton())
    tree = plan.to_minimal_tree()
    location_nodes = {
        landmark["id"]: tree["nodes"][landmark["node_id"]]
        for landmark in tree["landmark_map"]
    }

    assert any(
        choice["next"] == "n_loc_s2_lobby"
        for choice in location_nodes["S1_security_room"]["choices"]
    )


def test_gametree_plan_minimal_tree_reactions_are_declared(tmp_path):
    """导出的反应 variant 必须有 resolver_node,不能只是孤立消费。"""
    plan = GameTreePlan.from_skeleton(_sandbox_skeleton())
    path = tmp_path / "tree.json"
    path.write_text(json.dumps(plan.to_minimal_tree(), ensure_ascii=False), encoding="utf-8")

    report = audit_reactions(path)
    blockers = [
        problem
        for problem in report["problems"]
        if problem["code"] in ("DEAD_REACTION", "UNREACHABLE_REACTION")
    ]

    assert blockers == []
