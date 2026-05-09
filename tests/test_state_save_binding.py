"""Task 1.2 — State 接受 save_manager + story_id 引用(单一真相源)。"""
from __future__ import annotations

from ghost_story_factory.v5.player import State


def test_state_default_save_manager_is_none():
    """向后兼容:不传 save_manager 仍能构造,字段默认 None。"""
    s = State({})
    assert s.save_manager is None
    assert s.story_id is None


def test_state_accepts_save_manager_injection():
    """新引擎入口可传入 save_manager + story_id。"""
    sentinel = object()
    s = State({}, save_manager=sentinel, story_id="杭州_v7")
    assert s.save_manager is sentinel
    assert s.story_id == "杭州_v7"


def test_state_tree_field_default_none():
    """tree 引用默认 None,引擎入口处显式注入。"""
    s = State({})
    assert s.tree is None
