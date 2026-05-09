"""GameTree 可玩性审计测试。"""

from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from tools.audit_playability import analyze_playability


def test_legacy_tree_passes_basic_playability():
    """旧预生成树有完整 next_node_id 时应通过。"""
    tree = {
        "root": {
            "node_id": "root",
            "choices": [{"choice_id": "C1", "next_node_id": "end"}],
            "is_ending": False,
        },
        "end": {
            "node_id": "end",
            "choices": [],
            "is_ending": True,
            "ending_type": "E_OK",
        },
    }

    report = analyze_playability(tree)

    assert report.ok is True
    assert report.total_nodes == 2
    assert report.reachable_nodes == 2
    assert report.ending_nodes == 1


def test_missing_choice_target_is_error():
    """choice 指向不存在节点时必须报错。"""
    tree = {
        "root": {
            "node_id": "root",
            "choices": [{"choice_id": "C1", "next_node_id": "missing"}],
            "is_ending": False,
        },
    }

    report = analyze_playability(tree)

    assert report.ok is False
    assert any("不存在节点 missing" in item for item in report.errors)


def test_non_ending_dead_node_is_error():
    """非结局节点没有 choices 不是可玩节点。"""
    tree = {
        "root": {
            "node_id": "root",
            "choices": [],
            "is_ending": False,
        },
    }

    report = analyze_playability(tree)

    assert report.ok is False
    assert any("非结局节点没有 choices" in item for item in report.errors)


def test_v7_map_picker_uses_landmark_map_targets():
    """v7 `_is_map_picker` 没有静态 choices,但可通过 landmark_map 动态生成。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_intro": {
                "choices": [{"text": "去地图", "next": "n_picker"}],
            },
            "n_picker": {
                "_is_map_picker": True,
                "choices": [],
            },
            "n_s1": {
                "choices": [{"text": "结束", "next": "n_end"}],
            },
            "n_end": {
                "choices": [],
                "is_ending": True,
                "ending_type": "E_OK",
            },
        },
        "landmark_map": [
            {"id": "S1", "node_id": "n_s1", "connections": []},
        ],
        "endings": {"E_OK": "完成"},
    }

    report = analyze_playability(tree)

    assert report.ok is True
    assert report.dynamic_picker_nodes == 1
    assert report.reachable_nodes == 4


def test_ending_type_without_is_ending_is_compat_warning_not_dead_end():
    """历史数据里 ending_type + 空 choices 可识别为结局,但要给 warning。"""
    tree = {
        "root": {
            "node_id": "root",
            "choices": [{"choice_id": "C1", "next_node_id": "end"}],
            "is_ending": False,
        },
        "end": {
            "node_id": "end",
            "choices": [],
            "ending_type": "E_LEGACY",
        },
    }

    report = analyze_playability(tree)

    assert report.ok is True
    assert report.ending_nodes == 1
    assert any("缺少 is_ending=true" in item for item in report.warnings)


def test_character_start_nodes_count_as_reachable():
    """多角色周目的 start_node 也应纳入可达性。"""
    tree = {
        "start_node": "n_intro",
        "characters": {
            "main": {"start_node": "n_intro"},
            "side": {"start_node": "n_side_intro"},
        },
        "nodes": {
            "n_intro": {
                "choices": [],
                "is_ending": True,
                "ending_type": "E_MAIN",
            },
            "n_side_intro": {
                "choices": [{"text": "结束", "next": "n_side_end"}],
            },
            "n_side_end": {
                "choices": [],
                "is_ending": True,
                "ending_type": "E_SIDE",
            },
        },
    }

    report = analyze_playability(tree)

    assert report.ok is True
    assert report.reachable_nodes == 3
    assert report.extra_start_nodes == ["n_side_intro"]
    assert not any("不可达" in item for item in report.warnings)


def test_presentation_asset_reference_error():
    """presentation 不能引用不存在的 VN 资产。"""
    tree = {
        "start_node": "n_intro",
        "assets": {
            "backgrounds": {"bg_ok": {"kind": "text_fallback"}},
            "bgm": {},
            "sfx": {},
            "sprites": {},
        },
        "nodes": {
            "n_intro": {
                "choices": [],
                "is_ending": True,
                "ending_type": "E_OK",
                "presentation": {
                    "background": "bg_missing",
                    "bgm": None,
                    "sfx": [],
                    "sprite": None,
                },
            },
        },
    }

    report = analyze_playability(tree)

    assert report.ok is False
    assert any("background 引用不存在资产" in item for item in report.errors)


def test_key_presentation_intent_warning():
    """正式关键节点缺少镜头 / CG / 转场意图时要被审计提示。"""
    tree = {
        "start_node": "n_intro",
        "assets": {
            "backgrounds": {"bg_ok": {"kind": "text_fallback"}},
            "bgm": {},
            "sfx": {},
            "sprites": {},
        },
        "nodes": {
            "n_intro": {
                "choices": [],
                "is_ending": True,
                "ending_type": "E_OK",
                "presentation": {
                    "background": "bg_ok",
                    "bgm": None,
                    "sfx": [],
                    "sprite": None,
                },
            },
        },
    }

    report = analyze_playability(tree)

    assert report.ok is True
    assert any("关键演出意图缺少字段" in item for item in report.warnings)


def test_official_hangzhou_tree_has_vn_presentation_contract():
    """正式杭州树必须有 assets manifest,且关键节点具备演出意图。"""
    import json

    tree = json.loads(
        Path("stories/hangzhou_yebanbaoan/tree.json").read_text(encoding="utf-8")
    )

    report = analyze_playability(tree)

    assert report.ok is True
    assert report.presentation_nodes == report.total_nodes
    assert report.total_nodes >= 160
    assert not any("presentation" in item for item in report.warnings)
    assert not any("关键演出意图缺少字段" in item for item in report.warnings)
