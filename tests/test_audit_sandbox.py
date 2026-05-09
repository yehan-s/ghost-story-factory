"""ADR-010 沙盒骨架审计测试。"""

import json
from pathlib import Path

from ghost_story_factory.pregenerator.gametree_plan import GameTreePlan
from tests.test_gametree_plan import _sandbox_skeleton
from tools.audit_sandbox import analyze_sandbox


def test_gametree_plan_minimal_tree_passes_sandbox_audit():
    """GameTreePlan 的内存导出必须满足最小沙盒骨架。"""
    plan = GameTreePlan.from_skeleton(_sandbox_skeleton())
    report = analyze_sandbox(plan.to_minimal_tree())

    assert report.ok
    assert len(report.picker_nodes) == 1
    assert report.landmark_count == 4
    assert len(report.tool_nodes) == 2
    assert report.stay_loop_nodes
    assert report.reaction_variant_nodes


def test_official_hangzhou_tree_passes_sandbox_audit():
    """正式杭州树必须继续满足 ADR-010 沙盒骨架。"""
    tree = json.loads(Path("stories/hangzhou_yebanbaoan/tree.json").read_text(encoding="utf-8"))
    report = analyze_sandbox(tree)

    assert report.ok
    assert report.landmark_count >= 4
    assert len(report.tool_nodes) >= 2


def test_missing_sandbox_primitives_fail():
    """缺少沙盒原语的线性树必须失败。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_intro": {
                "narrative": "开始。",
                "choices": [{"text": "下一步", "next": "n_end"}],
                "presentation": {"background": "text"},
            },
            "n_end": {
                "narrative": "结束。",
                "is_ending": True,
                "ending_type": "E_BAD",
                "presentation": {"background": "text"},
            },
        },
    }

    report = analyze_sandbox(tree)

    assert not report.ok
    assert any("picker" in error for error in report.errors)
    assert any("地标数量不足" in error for error in report.errors)
    assert any("工具节点数量不足" in error for error in report.errors)
