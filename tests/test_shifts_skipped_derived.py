"""Task 9 验证:landmark_skipped 自动同步 shifts_skipped。

设计说明(参考 ADR-007 修订版):
- shifts_skipped 仍是 int 字段(不是 @property),保留 effects.shifts_skipped 直接处理(撕表场景需要)
- effects.landmark_skipped 处理:append 到 skipped_landmarks 时,同步 shifts_skipped += 1
- 这取代了 tree.json 中冗余的 `"shifts_skipped": 1` 配对(已在 tree.json 删除 9 处)
- 撕表场景的独立 `effects.shifts_skipped: 3`(无 landmark_skipped 配对)仍然合法

Pass 1 完成后此测试可删除(或合并到 test_player.py)。
"""
from __future__ import annotations


def test_landmark_skipped_syncs_counter():
    """apply effects.landmark_skipped → skipped_landmarks +1 且 shifts_skipped 自动 +1。"""
    from ghost_story_factory.v5.player import State

    s = State({})
    assert s.shifts_skipped == 0
    assert s.skipped_landmarks == []

    s.apply({"landmark_skipped": "S2"})
    assert s.skipped_landmarks == ["S2"]
    assert s.shifts_skipped == 1

    s.apply({"landmark_skipped": "S5"})
    assert s.skipped_landmarks == ["S2", "S5"]
    assert s.shifts_skipped == 2


def test_landmark_skipped_dedup_does_not_double_count():
    """重复 skip 同一个地标(如玩家通过环重复访问):list 不重复 append,counter 也不重复 +1。"""
    from ghost_story_factory.v5.player import State

    s = State({})
    s.apply({"landmark_skipped": "S2"})
    s.apply({"landmark_skipped": "S2"})  # 重复触发

    assert s.skipped_landmarks == ["S2"]
    assert s.shifts_skipped == 1, "重复 skip 同一地标不应该让 counter +2"


def test_effects_shifts_skipped_direct_still_works():
    """撕表场景:effects.shifts_skipped: 3(无 landmark_skipped)直接 +3。"""
    from ghost_story_factory.v5.player import State

    s = State({})
    s.apply({"shifts_skipped": 3})
    assert s.shifts_skipped == 3
    assert s.skipped_landmarks == [], "撕表场景不应该影响 skipped_landmarks"


def test_combined_landmark_skipped_then_penalty():
    """玩家先正常 skip 一个地标,再触发撕表惩罚:counter 累加。"""
    from ghost_story_factory.v5.player import State

    s = State({})
    s.apply({"landmark_skipped": "S1"})
    assert s.shifts_skipped == 1

    s.apply({"shifts_skipped": 3})  # 撕表
    assert s.shifts_skipped == 4
    assert s.skipped_landmarks == ["S1"], "撕表惩罚不污染 skipped_landmarks"


def test_initial_state_without_shifts_skipped():
    """initial_state 不传 shifts_skipped(tree.json 已删该字段)— 默认 0。"""
    from ghost_story_factory.v5.player import State

    s = State({})  # 无 shifts_skipped
    assert s.shifts_skipped == 0


def test_path_explorer_with_effects_syncs():
    """tools/path_explorer.py:with_effects 也要同样地 landmark_skipped → +1 shifts_skipped。"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
    from _state_sim import SimState
    from path_explorer import with_effects

    s0 = SimState()
    s1, _ = with_effects(s0, {"landmark_skipped": "S2"})
    assert s1.skipped_landmarks == ("S2",)
    assert s1.shifts_skipped == 1, "BFS 模拟器也要保持 list 与 counter 同步"

    # 撕表场景
    s2, _ = with_effects(s1, {"shifts_skipped": 3})
    assert s2.shifts_skipped == 4
    assert s2.skipped_landmarks == ("S2",)
