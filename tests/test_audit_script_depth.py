"""Pass 9 剧本深度 / 广度审计测试。"""

import json
from pathlib import Path

from tools.audit_script_depth import analyze_script_depth
from ghost_story_factory.v5.player import State, resolve_narrative


def test_official_hangzhou_tree_meets_pass9_depth_contract():
    """正式杭州树必须满足 Pass 9/17 厚度与终局门槛红线。"""
    tree = json.loads(Path("stories/hangzhou_yebanbaoan/tree.json").read_text(encoding="utf-8"))
    report = analyze_script_depth(tree)

    assert report.ok
    assert report.node_count >= 160
    assert report.intent_nodes >= 30
    assert report.linmou_shortest_ending_path >= 5
    assert len(report.linmou_landmark_variant_nodes) == 4
    assert len(report.g273_linmou_echo_nodes) >= 3
    assert report.ending_gate_violations == []
    assert report.one_way_violations == []
    assert report.protagonist_biography_violations == []


def test_official_g273_first_visit_text_keeps_protagonist_biography_consistent():
    """G-273 首访文本不能混入旧版中年老保安履历。"""
    tree = json.loads(Path("stories/hangzhou_yebanbaoan/tree.json").read_text(encoding="utf-8"))
    state = State({"character": "G-273"})
    forbidden = [
        "你媳妇",
        "你儿子",
        "你今年 51",
        "做夜班保安第 14 年",
        "你按了 14 年",
        "你 1985 年从二轻物资",
        "你父亲",
        "你妈临死",
        "2014 年自己扫",
        "2010 年接",
        "一个月工资是 38 块",
        "1987 年坐 K6",
    ]
    node_ids = [
        "n_npc_predecessor_voice",
        "n_scene_lost_archive",
        "n_lore_leifeng_worm",
        "n_lore_songmuchang_inn",
        "n_lore_zheda_clock_girl",
        "n_lore_wulinmen_execution",
        "n_lore_kongque_collapse",
    ]

    for node_id in node_ids:
        text = resolve_narrative(tree["nodes"][node_id], state)
        leaks = [term for term in forbidden if term in text]
        assert leaks == [], f"{node_id} 混入旧主角履历: {leaks}"


def test_g273_biography_leak_fails_depth_audit():
    """旧版主角履历泄漏必须让正式剧本审计失败。"""
    tree = {
        "start_node": "n_npc_predecessor_voice",
        "characters": {
            "linmou_1985": {"start_node": "n_l1985_entry"},
        },
        "nodes": {
            "n_npc_predecessor_voice": {
                "narrative_variants": [
                    {
                        "if": {"character": "G-273"},
                        "text": "你今年 51 岁,你媳妇还在等你。",
                    }
                ],
                "choices": [],
            },
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

    report = analyze_script_depth(tree, min_nodes=1, min_intent_nodes=0, min_linmou_path=1)

    assert not report.ok
    assert report.protagonist_biography_violations == [
        "n_npc_predecessor_voice 混入旧主角履历: 你媳妇, 你今年 51"
    ]


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


def test_morning_lakeside_ending_menu_without_gates_fails():
    """晨湖高阶结局不能退回菜单式自选。"""
    tree = {
        "start_node": "n_scene_morning_lakeside",
        "characters": {
            "linmou_1985": {"start_node": "n_l1985_entry"},
        },
        "nodes": {
            "n_scene_morning_lakeside": {
                "narrative": "晨湖。",
                "choices": [
                    {"text": "直接 True", "next": "n_end_true"},
                    {"text": "直接 Data", "next": "n_end_data", "require": {"flags": {"oneshot.chose_data": True}}},
                ],
            },
            "n_end_true": {"is_ending": True, "ending_type": "E_TRUE", "narrative": "true"},
            "n_end_data": {"is_ending": True, "ending_type": "E_DATA", "narrative": "data"},
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

    report = analyze_script_depth(tree, min_nodes=1, min_intent_nodes=0, min_linmou_path=1)

    assert not report.ok
    assert any("缺少 require" in item for item in report.ending_gate_violations)
    assert any("n_end_data" in item and "know.saw_8_zhao" in item for item in report.ending_gate_violations)


def test_one_way_node_returning_to_map_fails():
    """_one_way 节点不能偷偷退回地图。"""
    tree = {
        "start_node": "n_s7_arrive",
        "characters": {
            "linmou_1985": {"start_node": "n_l1985_entry"},
        },
        "nodes": {
            "n_s7_arrive": {
                "_one_way": True,
                "narrative": "B3。",
                "choices": [{"text": "退回地图", "next": "n_landmark_picker"}],
            },
            "n_landmark_picker": {"narrative": "地图。", "choices": []},
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

    report = analyze_script_depth(tree, min_nodes=1, min_intent_nodes=0, min_linmou_path=1)

    assert not report.ok
    assert report.one_way_violations == [
        "n_s7_arrive choices[1] 在 _one_way 节点返回 n_landmark_picker"
    ]
