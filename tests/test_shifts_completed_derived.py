"""Task 8 验证:shifts_completed 改为 @property 派生。

Pass 1 完成后可删除本文件。
"""
import pytest


def test_shifts_completed_derived_from_visited():
    from ghost_story_factory.v5.player import State
    s = State({"visited_landmarks": ["S1", "S2", "S3"]})
    assert s.shifts_completed == 3


def test_shifts_completed_ignores_non_S_landmarks():
    from ghost_story_factory.v5.player import State
    s = State({"visited_landmarks": ["S1", "S2", "extra_node"]})
    assert s.shifts_completed == 2


def test_shifts_completed_is_property_not_field():
    from ghost_story_factory.v5.player import State
    s = State({})
    # @property 不可赋值
    try:
        s.shifts_completed = 99
        raised = False
    except AttributeError:
        raised = True
    assert raised, "shifts_completed should be read-only @property"


def test_shifts_completed_sim_state_derived():
    """SimState 的 shifts_completed 也应从 visited_landmarks 派生。"""
    from tools._state_sim import SimState
    s = SimState(visited_landmarks=("S1", "S2", "S4", "some_other"))
    assert s.shifts_completed == 3


def test_shifts_completed_sim_state_from_dict():
    """from_dict 不再接受 shifts_completed 字段,而是由 visited_landmarks 派生。"""
    from tools._state_sim import SimState
    s = SimState.from_dict({"visited_landmarks": ["S1", "S3", "S5", "S6"]})
    assert s.shifts_completed == 4
