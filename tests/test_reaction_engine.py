"""Task 1.3 + 1.4 + 1.5 — _meets_clause 三新条件:
deduction_resolved / foreshadow_resolved / theme_resolved。

设计:State 通过 save_manager + tree 引用查询单一真相源。
list 是 ANY 语义(任一满足即 True);ALL 用 all_of 显式。
save_manager / tree None 时安全降级返回 False。
"""
from __future__ import annotations

from ghost_story_factory.v5.player import State


class FakeSave:
    """测试 fixture — 模拟 SaveManager 三个查询方法。"""

    def __init__(self, resolved_d=None, resolved_f=None):
        self._resolved_d = set(resolved_d or [])
        self._resolved_f = set(resolved_f or [])

    def is_deduction_resolved(self, sid, did):
        return did in self._resolved_d

    def is_foreshadow_resolved(self, sid, fid):
        return fid in self._resolved_f

    def get_resolved_foreshadows(self, sid):
        return set(self._resolved_f)


# --- deduction_resolved ---

def test_deduction_resolved_str_match():
    s = State({}, save_manager=FakeSave(resolved_d=["D-001"]), story_id="杭州_v7")
    assert s.meets({"deduction_resolved": "D-001"}) is True
    assert s.meets({"deduction_resolved": "D-999"}) is False


def test_deduction_resolved_list_any_semantic():
    """list 是 ANY 语义:任一解开即满足。"""
    s = State({}, save_manager=FakeSave(resolved_d=["D-001"]), story_id="杭州_v7")
    assert s.meets({"deduction_resolved": ["D-001", "D-999"]}) is True
    assert s.meets({"deduction_resolved": ["D-998", "D-999"]}) is False


def test_deduction_resolved_no_save_manager_returns_false():
    """save_manager None → 新条件安全降级。"""
    s = State({})
    assert s.meets({"deduction_resolved": "D-001"}) is False


# --- foreshadow_resolved ---

def test_foreshadow_resolved_str_match():
    s = State({}, save_manager=FakeSave(resolved_f=["F-001"]), story_id="杭州_v7")
    assert s.meets({"foreshadow_resolved": "F-001"}) is True
    assert s.meets({"foreshadow_resolved": "F-999"}) is False


def test_foreshadow_resolved_list_any():
    s = State({}, save_manager=FakeSave(resolved_f=["F-002"]), story_id="杭州_v7")
    assert s.meets({"foreshadow_resolved": ["F-001", "F-002"]}) is True
    assert s.meets({"foreshadow_resolved": []}) is False


def test_foreshadow_resolved_no_save_returns_false():
    s = State({})
    assert s.meets({"foreshadow_resolved": "F-001"}) is False


# --- theme_resolved ---

def _tree_with_themes(themes):
    return {"themes": themes}


def test_theme_resolved_all_manifestations_resolved():
    """6 母题"通透":所有 manifestations 全部解开。"""
    sm = FakeSave(resolved_f=["F-001", "F-002"])
    s = State({}, save_manager=sm, story_id="杭州_v7")
    s.tree = _tree_with_themes({"hangzhou_constant": {"manifestations": ["F-001", "F-002"]}})
    assert s.meets({"theme_resolved": "hangzhou_constant"}) is True


def test_theme_resolved_partial_returns_false():
    sm = FakeSave(resolved_f=["F-1"])  # 只解开 1/3
    s = State({}, save_manager=sm, story_id="杭州_v7")
    s.tree = _tree_with_themes({"t1": {"manifestations": ["F-1", "F-2", "F-3"]}})
    assert s.meets({"theme_resolved": "t1"}) is False


def test_theme_resolved_list_any():
    """list ANY:任一母题通透即可。"""
    sm = FakeSave(resolved_f=["F-2"])  # t2 通透,t1 没
    s = State({}, save_manager=sm, story_id="杭州_v7")
    s.tree = _tree_with_themes({
        "t1": {"manifestations": ["F-1"]},
        "t2": {"manifestations": ["F-2"]},
    })
    assert s.meets({"theme_resolved": ["t1", "t2"]}) is True


def test_theme_resolved_no_tree_returns_false():
    s = State({})
    assert s.meets({"theme_resolved": "t1"}) is False


def test_theme_resolved_empty_manifestations_returns_false():
    """manifestations 为空 list 不应判 True(空集 issubset 任意集 = True 是陷阱)。"""
    sm = FakeSave(resolved_f=[])
    s = State({}, save_manager=sm, story_id="杭州_v7")
    s.tree = _tree_with_themes({"empty_motif": {"manifestations": []}})
    assert s.meets({"theme_resolved": "empty_motif"}) is False


# --- 多条件组合 ---

def test_multiple_reaction_conditions_all_must_match():
    """deduction_resolved + foreshadow_resolved 同时出现 = AND(顶层 require 是 AND)。"""
    sm = FakeSave(resolved_d=["D-1"], resolved_f=["F-1"])
    s = State({}, save_manager=sm, story_id="杭州_v7")
    assert s.meets({"deduction_resolved": "D-1", "foreshadow_resolved": "F-1"}) is True
    assert s.meets({"deduction_resolved": "D-1", "foreshadow_resolved": "F-MISSING"}) is False


def test_reaction_with_existing_flag_condition():
    """新条件与现有 flags 字段共存,AND 关系。"""
    sm = FakeSave(resolved_d=["D-1"])
    s = State({"flags": {"radio_listened": True}}, save_manager=sm, story_id="杭州_v7")
    assert s.meets({"deduction_resolved": "D-1", "flags": {"radio_listened": True}}) is True
    assert s.meets({"deduction_resolved": "D-1", "flags": {"radio_listened": False}}) is False
