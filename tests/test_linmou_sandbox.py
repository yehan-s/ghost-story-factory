"""ADR-010 沙盒契约:linmou_1985 picker 走 picker_choices 框架的回归测试。

- linmou picker = `_is_map_picker: true`
- picker_choices 按 state.character 过滤,linmou 看到 L1-L4,看不到 G-273 的 S1-S7
- _picker_endshift_choice 的 require any_of(3 个 intent flag)正确生效
- G-273 周目向后兼容:仍能看到 7 地标 + endshift threshold
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ghost_story_factory.v5.player import State
from ghost_story_factory.v7.map_view import picker_choices, _landmarks_for


TREE = json.loads(
    Path("stories/hangzhou_yebanbaoan/tree.json").read_text(encoding="utf-8")
)
LINMOU_PICKER = TREE["nodes"]["n_l1985_landmark_picker"]
G273_PICKER = TREE["nodes"]["n_landmark_picker"]


def _state(character: str, **overrides):
    initial = {"character": character, "known_landmarks": list(overrides.pop("known", []))}
    initial.update(overrides)
    s = State(initial)
    s.tree = TREE
    return s


# === 沙盒结构契约 ===

def test_linmou_picker_is_map_picker():
    """linmou picker 必须 `_is_map_picker: true`。"""
    assert LINMOU_PICKER.get("_is_map_picker") is True


def test_linmou_picker_no_handwritten_landmark_choices():
    """linmou picker 不应有手写 [01]-[04] 地标 choices(引擎动态生成)。"""
    for c in LINMOU_PICKER.get("choices") or []:
        text = c.get("text", "")
        assert not any(tag in text for tag in ("[01]", "[02]", "[03]", "[04]")), (
            f"linmou picker 仍有手写地标 choice: {text}"
        )


def test_linmou_picker_endshift_anyof():
    """_picker_endshift_choice.require 必须是 any_of 3 个 intent flag。"""
    ec = LINMOU_PICKER.get("_picker_endshift_choice") or {}
    require = ec.get("require") or {}
    any_of = require.get("any_of") or []
    flags_seen = {
        list(c.get("flags", {}).keys())[0]
        for c in any_of if c.get("flags")
    }
    assert flags_seen == {"l_intent_release", "l_intent_regret", "l_intent_grievance"}


# === landmark_map character 过滤 ===

def test_landmarks_for_g273_sees_only_g273():
    """G-273 state 只看到 7 个 G-273 地标,不看到 linmou L1-L4。"""
    s = _state(character="G-273")
    lms = _landmarks_for(TREE, s)
    sids = {lm["id"] for lm in lms}
    assert sids == {"S1", "S2", "S3", "S4", "S5", "S6", "S7"}


def test_landmarks_for_linmou_sees_only_linmou():
    """linmou state 只看到 4 个 linmou 地标,不看到 G-273 的 S1-S7。"""
    s = _state(character="linmou_1985")
    lms = _landmarks_for(TREE, s)
    sids = {lm["id"] for lm in lms}
    assert sids == {"L1", "L2", "L3", "L4"}


def test_landmarks_for_no_character_sees_all():
    """没有 character(state=None 或缺失)→ 向后兼容,看到全部。"""
    s = _state(character="")
    lms = _landmarks_for(TREE, s)
    sids = {lm["id"] for lm in lms}
    assert "S1" in sids and "L1" in sids


# === picker_choices 动态生成 ===

def test_picker_choices_linmou_4_landmarks_known_all():
    """linmou state(known=L1-L4)在 picker 节点 → picker_choices 生成 4 个 travel + endshift(锁定时不显示)。"""
    s = _state(character="linmou_1985", known=["L1", "L2", "L3", "L4"])
    choices = picker_choices(TREE, s, node=LINMOU_PICKER)
    travel = [c for c in choices if c.get("_picker_kind") == "travel"]
    travel_sids = {c.get("_landmark_id") for c in travel}
    assert travel_sids == {"L1", "L2", "L3", "L4"}, travel_sids
    # 没有 endshift(intent flag 都是 false → require any_of 不满足)
    assert not any(c.get("_picker_kind") == "endshift" for c in choices)


def test_picker_choices_linmou_endshift_visible_when_intent_set():
    """任一 l_intent_* flag = True → endshift "[05] 直接去湖边" 出现。"""
    s = _state(
        character="linmou_1985",
        known=["L1", "L2", "L3", "L4"],
        flags={"l_intent_release": True},
    )
    choices = picker_choices(TREE, s, node=LINMOU_PICKER)
    end = [c for c in choices if c.get("_picker_kind") == "endshift"]
    assert len(end) == 1
    assert end[0].get("next") == "n_l1985_lake_jump"


def test_picker_choices_g273_endshift_threshold():
    """G-273 没有 _picker_endshift_choice,落入默认 G-273 endshift 逻辑(shifts ≥ 4)。"""
    s = _state(character="G-273", known=["S1"], visited_landmarks=["S1", "S2", "S3", "S4"])
    choices = picker_choices(TREE, s, node=G273_PICKER)
    end = [c for c in choices if c.get("_picker_kind") == "endshift"]
    assert len(end) == 1
    assert end[0].get("next") == "n_scene_morning_lakeside"


def test_picker_choices_g273_no_endshift_below_threshold():
    """G-273 shifts < 4 → 默认 endshift 不显示。"""
    s = _state(character="G-273", known=["S1"], visited_landmarks=["S1"])
    choices = picker_choices(TREE, s, node=G273_PICKER)
    end = [c for c in choices if c.get("_picker_kind") == "endshift"]
    assert len(end) == 0


# === 沙盒最小骨架 5 项(ADR-010) ===

def test_linmou_landmarks_have_connections():
    """linmou 4 地标必须有 connections(网,非辐射)。"""
    by_id = {lm["id"]: lm for lm in TREE.get("landmark_map", [])}
    for sid in ("L1", "L2", "L3", "L4"):
        lm = by_id.get(sid)
        assert lm, f"缺少 {sid}"
        assert lm.get("character") == "linmou_1985"
        conns = lm.get("connections") or []
        assert len(conns) >= 1, f"{sid} 必须 ≥ 1 条 connections,当前 {conns}"
