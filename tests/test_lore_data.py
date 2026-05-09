"""Task 3.1+3.2 — Lore 锚点表 schema 测试。"""
from __future__ import annotations

import json
from pathlib import Path


def test_lore_voice_matrix_schema():
    p = Path("data/lore_voice_matrix.json")
    assert p.exists(), "data/lore_voice_matrix.json 不存在"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "matrix" in data and "redlines" in data
    for npc_id, m in data["matrix"].items():
        assert "before" in m and "after" in m, f"{npc_id} 缺 before/after"
        for state in ("before", "after"):
            for k in ("address", "tone", "era_words"):
                assert k in m[state], f"{npc_id}.{state} 缺 {k}"
            assert isinstance(m[state]["era_words"], list)


def test_lore_voice_matrix_covers_review_npcs():
    """Lore Keeper 钦定 4 NPC 必须在表里。"""
    data = json.loads(Path("data/lore_voice_matrix.json").read_text(encoding="utf-8"))
    required = {"linmou_1985", "old_grandma", "red_dress_girl", "worker_1986"}
    assert required.issubset(set(data["matrix"].keys())), \
        f"缺 NPC: {required - set(data['matrix'].keys())}"


def test_motif_anchors_schema():
    p = Path("data/motif_anchors.json")
    assert p.exists(), "data/motif_anchors.json 不存在"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "anchors" in data
    for motif_id, a in data["anchors"].items():
        for sense in ("visual", "audio", "scent"):
            assert sense in a, f"{motif_id} 缺 {sense}"
            assert isinstance(a[sense], str) and a[sense], f"{motif_id}.{sense} 空"


def test_motif_anchors_covers_six_themes():
    """6 母题必须全部覆盖。"""
    data = json.loads(Path("data/motif_anchors.json").read_text(encoding="utf-8"))
    required = {
        "hangzhou_constant", "scapegoat", "time_loop",
        "datafication", "thirteen_curse", "folklore",
    }
    assert required.issubset(set(data["anchors"].keys())), \
        f"缺母题: {required - set(data['anchors'].keys())}"


# --- Task 3.1: linmou_act1_lore ---

def test_linmou_act1_lore_schema():
    p = Path("data/linmou_act1_lore.json")
    assert p.exists(), "data/linmou_act1_lore.json 不存在"
    data = json.loads(p.read_text(encoding="utf-8"))
    for k in ("setting", "objects", "audio", "scent", "text_anchors",
              "redlines_vocab", "redlines_values", "redlines_objects",
              "endings_intent"):
        assert k in data, f"缺 {k}"


def test_linmou_act1_lore_setting_canonical():
    """1985 setting 必须固化:日期 / 地点 / 时间。"""
    data = json.loads(Path("data/linmou_act1_lore.json").read_text(encoding="utf-8"))
    s = data["setting"]
    assert s["date"] == "1985-10-18"
    assert "二轻物资" in s["location_unit"]
    assert "西湖" in s["location_lake"] and "锦带桥" in s["location_lake"]


def test_linmou_act1_lore_four_endings():
    """4 ending intent 必须齐全。"""
    data = json.loads(Path("data/linmou_act1_lore.json").read_text(encoding="utf-8"))
    required = {
        "E_LINMOU_GRIEVANCE", "E_LINMOU_REGRET",
        "E_LINMOU_RELEASE", "E_LINMOU_EXPOSED",
    }
    assert required == set(data["endings_intent"].keys())
    for eid, meta in data["endings_intent"].items():
        assert "core_emotion" in meta and "anchor" in meta, f"{eid} 缺 emotion/anchor"
