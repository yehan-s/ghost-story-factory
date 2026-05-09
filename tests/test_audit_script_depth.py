"""Pass 9 剧本深度 / 广度审计测试。"""

import json
from pathlib import Path

from tools.audit_script_depth import analyze_script_depth


def test_official_hangzhou_tree_meets_pass9_depth_contract():
    """正式杭州树必须满足 Pass 9 厚度红线。"""
    tree = json.loads(Path("stories/hangzhou_yebanbaoan/tree.json").read_text(encoding="utf-8"))
    report = analyze_script_depth(tree)

    assert report.ok
    assert report.node_count >= 160
    assert report.intent_nodes >= 30
    assert report.linmou_shortest_ending_path >= 5
    assert len(report.linmou_landmark_variant_nodes) == 4
    assert len(report.g273_linmou_echo_nodes) >= 3


def test_linear_thin_tree_fails_depth_contract():
    """线性薄树不能伪装成合格剧本。"""
    tree = {
        "start_node": "n_intro",
        "characters": {
            "linmou_1985": {"start_node": "n_l1985_entry"},
        },
        "nodes": {
            "n_intro": {
                "narrative": "开始。",
                "choices": [{"text": "结束", "next": "n_end"}],
                "presentation": {
                    "camera": "wide",
                    "cg_intent": "intro",
                    "transition_intent": "cut",
                },
            },
            "n_end": {"is_ending": True, "ending_type": "E_BAD", "narrative": "结束。"},
            "n_l1985_entry": {
                "narrative": "林某开始。",
                "choices": [{"text": "跳湖", "next": "E_LINMOU_RELEASE"}],
            },
            "E_LINMOU_RELEASE": {
                "is_ending": True,
                "ending_type": "E_LINMOU_RELEASE",
                "narrative": "结束。",
            },
        },
    }

    report = analyze_script_depth(tree)

    assert not report.ok
    assert any("节点数不足" in error for error in report.errors)
    assert any("最短结局路径过短" in error for error in report.errors)
    assert any("地标缺少" in error for error in report.errors)
