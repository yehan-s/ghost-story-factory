"""Task 2.1 — audit_paths_linmou 必死不变量 INV-1~4 测试。

ADR-009 守门:linmou 周目必死铁律。

INV-1: 所有 linmou 周目终态(choices=[])∈ 4 ending 白名单
INV-2: 无边从 linmou 子图通向 Act 2/3 节点(本期 trivial)
INV-3: 投湖节点 n_l1985_lake_jump 后置必为 ending
INV-4: 4 ending 节点必须有 _lore_canon.must_die: true
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tools.audit_paths_linmou import audit


def _write(tree):
    p = Path(tempfile.mkdtemp()) / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False), encoding="utf-8")
    return p


def test_inv1_terminal_must_be_in_4_endings():
    """INV-1: 终态不在 4 ending 集合 → FAIL。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "go", "next": "n_dead_end"}]},
            "n_dead_end": {"choices": []},
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    assert any(p["code"] == "INV1_TERMINAL_NOT_IN_ENDINGS" and "n_dead_end" in p["msg"]
               for p in report["problems"])


def test_inv1_terminal_in_endings_passes():
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "go", "next": "E_LINMOU_RELEASE"}]},
            "E_LINMOU_RELEASE": {"choices": [], "_lore_canon": {"must_die": True}},
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    inv1 = [p for p in report["problems"] if p["code"] == "INV1_TERMINAL_NOT_IN_ENDINGS"]
    assert inv1 == []


def test_inv3_lake_jump_must_lead_to_ending():
    """INV-3: 投湖节点出口指向非 ending → FAIL。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "x", "next": "n_l1985_lake_jump"}]},
            "n_l1985_lake_jump": {"choices": [{"text": "wat", "next": "n_l1985_after"}]},
            "n_l1985_after": {"choices": []},
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    assert any(p["code"] == "INV3_LAKE_JUMP_NOT_TO_ENDING" for p in report["problems"])


def test_inv4_ending_missing_must_die_canon():
    """INV-4: ending 缺 _lore_canon.must_die → FAIL。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "x", "next": "E_LINMOU_RELEASE"}]},
            "E_LINMOU_RELEASE": {"choices": []},  # 无 _lore_canon
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    assert any(p["code"] == "INV4_MISSING_MUST_DIE_CANON" for p in report["problems"])


def test_clean_act1_passes():
    """正常 Act 1:entry → ending,must_die 标记齐全 → 0 INV 问题。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "x", "next": "E_LINMOU_RELEASE"}]},
            "E_LINMOU_RELEASE": {"choices": [], "_lore_canon": {"must_die": True}},
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    inv = [p for p in report["problems"] if p["code"].startswith("INV")]
    assert inv == []


def test_no_linmou_character_trivial_pass():
    """无 linmou_1985 character → trivial pass(本期之前的 G-273 only)。"""
    tree = {"start_node": "n_intro", "nodes": {"n_intro": {"choices": []}},
            "characters": {"G-273": {"start_node": "n_intro"}}}
    report = audit(_write(tree))
    assert report["problems"] == []


def test_main_tree_currently_clean():
    """主 tree.json:linmou_1985 character 还没注册 → trivial pass。"""
    report = audit(Path("stories/hangzhou_yebanbaoan/tree.json"))
    assert report["problems"] == []
