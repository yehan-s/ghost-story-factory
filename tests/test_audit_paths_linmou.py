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
    """正常 Act 1:entry → 4 ending,must_die + 4 canon intent 齐全 → 0 INV 问题。

    Pass 2 INV-5 后 minimal tree 必须含 4 intent 全集。
    """
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {
                "choices": [
                    {"text": "A", "next": "E_LINMOU_GRIEVANCE"},
                    {"text": "B", "next": "E_LINMOU_REGRET"},
                    {"text": "C", "next": "E_LINMOU_RELEASE"},
                    {"text": "D", "next": "E_LINMOU_EXPOSED"},
                ],
            },
            "E_LINMOU_GRIEVANCE": {"choices": [], "_lore_canon": {"must_die": True, "intent": "冤"}},
            "E_LINMOU_REGRET": {"choices": [], "_lore_canon": {"must_die": True, "intent": "悔"}},
            "E_LINMOU_RELEASE": {"choices": [], "_lore_canon": {"must_die": True, "intent": "释"}},
            "E_LINMOU_EXPOSED": {"choices": [], "_lore_canon": {"must_die": True, "intent": "曝光"}},
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


# ---------- Pass 2 Task 4.1: INV-5 (4 canon intent 全覆盖) ----------

def _minimal_linmou_tree(intents):
    """构造最小 linmou 树,4 ending 各带 must_die + 指定 intent。

    intents: dict[ending_id, intent_or_None]
    """
    return {
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
        "nodes": {
            "n_l1985_entry": {
                "scene": "SCENE",
                "narrative": "...",
                "choices": [
                    {"text": "A", "next": "E_LINMOU_GRIEVANCE"},
                    {"text": "B", "next": "E_LINMOU_REGRET"},
                    {"text": "C", "next": "E_LINMOU_RELEASE"},
                    {"text": "D", "next": "E_LINMOU_EXPOSED"},
                ],
            },
            "E_LINMOU_GRIEVANCE": {
                "scene": "ENDING", "narrative": "...", "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_GRIEVANCE")},
            },
            "E_LINMOU_REGRET": {
                "scene": "ENDING", "narrative": "...", "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_REGRET")},
            },
            "E_LINMOU_RELEASE": {
                "scene": "ENDING", "narrative": "...", "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_RELEASE")},
            },
            "E_LINMOU_EXPOSED": {
                "scene": "ENDING", "narrative": "...", "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_EXPOSED")},
            },
        },
    }


def test_inv5_green_when_all_4_intents_covered():
    """INV-5 绿: 4 ending 各带 4 个不同 intent。"""
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": "曝光",
    })
    report = audit(_write(tree))
    inv5 = [p for p in report["problems"] if p["code"].startswith("INV5")]
    assert inv5 == []


def test_inv5_red_when_intent_missing():
    """INV-5 红: 1 ending 缺 intent。"""
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": None,  # 缺 intent
    })
    report = audit(_write(tree))
    inv5 = [p for p in report["problems"] if p["code"].startswith("INV5")]
    assert len(inv5) >= 1
    # 至少有一个 problem 提到 EXPOSED
    assert any("E_LINMOU_EXPOSED" in p.get("msg", "") for p in inv5)


def test_inv5_red_when_intent_not_in_canon_set():
    """INV-5 红: intent 不在 4 canon 集合内(野字段)。"""
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": "逃出生天",  # 野 intent
    })
    report = audit(_write(tree))
    inv5 = [p for p in report["problems"] if p["code"].startswith("INV5")]
    assert len(inv5) >= 1


def test_inv5_red_when_one_intent_unreachable():
    """INV-5 红: 4 intent 必须全部覆盖,某 intent 路径不可达 = FAIL。"""
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": "曝光",
    })
    # 移除 RELEASE 的可达边
    tree["nodes"]["n_l1985_entry"]["choices"] = [
        c for c in tree["nodes"]["n_l1985_entry"]["choices"]
        if c["next"] != "E_LINMOU_RELEASE"
    ]
    report = audit(_write(tree))
    inv5 = [p for p in report["problems"] if p["code"].startswith("INV5")]
    # RELEASE 不可达 = "释" intent 缺失
    assert len(inv5) >= 1
    assert any("释" in p.get("msg", "") for p in inv5)
