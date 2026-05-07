"""验证 _state_sim.SimState.meets() 与 player.py:State.meets() 行为一致。

覆盖:
- 全部 _meets_clause 字段(min/max 对偶、列表/字符串分支、空集合)
- 嵌套组合(any_of / all_of / not),含空列表与深度嵌套
- 每类至少 1 pass + 1 fail
"""
import pytest
from tools._state_sim import SimState, meets
from ghost_story_factory.v5.player import State


@pytest.mark.parametrize("require,initial,expected", [
    # ── PR_min / PR_max(下界 + 上界对偶)
    ({"PR_min": 5}, {"PR": 10}, True),
    ({"PR_min": 5}, {"PR": 3}, False),
    ({"PR_max": 50}, {"PR": 30}, True),
    ({"PR_max": 50}, {"PR": 80}, False),

    # ── GR_min / GR_max
    ({"GR_min": 20}, {"GR": 25}, True),
    ({"GR_min": 20}, {"GR": 10}, False),
    ({"GR_max": 60}, {"GR": 40}, True),
    ({"GR_max": 60}, {"GR": 90}, False),

    # ── inv_has / inv_lacks
    ({"inv_has": ["羊符"]}, {"inv": ["羊符"]}, True),
    ({"inv_has": ["羊符", "钥匙"]}, {"inv": ["羊符"]}, False),  # 缺一个
    ({"inv_lacks": ["羊符"]}, {"inv": ["羊符"]}, False),
    ({"inv_lacks": ["羊符"]}, {"inv": ["钥匙"]}, True),

    # ── flags(布尔字典)
    ({"flags": {"radio_listened": True}}, {"flags": {"radio_listened": True}}, True),
    ({"flags": {"radio_listened": True}}, {"flags": {"radio_listened": False}}, False),
    ({"flags": {"missing_key": True}}, {}, False),  # 缺失视为 False

    # ── shifts_skipped_min / shifts_completed_min
    ({"shifts_skipped_min": 2}, {"shifts_skipped": 3}, True),
    ({"shifts_skipped_min": 2}, {"shifts_skipped": 1}, False),
    ({"shifts_completed_min": 4}, {"shifts_completed": 5}, True),
    ({"shifts_completed_min": 4}, {"shifts_completed": 2}, False),

    # ── landmark_visited(列表形式 — 必须全部 visited 才通过)
    ({"landmark_visited": ["S1"]}, {"visited_landmarks": ["S1", "S2"]}, True),
    ({"landmark_visited": ["S1", "S3"]}, {"visited_landmarks": ["S1", "S2"]}, False),

    # ── puzzle_pieces_min
    ({"puzzle_pieces_min": 3}, {"puzzle_pieces": ["a", "b", "c"]}, True),
    ({"puzzle_pieces_min": 3}, {"puzzle_pieces": ["a", "b"]}, False),

    # ── visit_count_min
    ({"visit_count_min": {"n_x": 2}}, {"visit_counts": {"n_x": 3}}, True),
    ({"visit_count_min": {"n_x": 2}}, {"visit_counts": {"n_x": 1}}, False),

    # ── last_landmark(字符串分支)
    ({"last_landmark": "S2"}, {"last_landmark_id": "S2"}, True),
    ({"last_landmark": "S2"}, {"last_landmark_id": "S3"}, False),
    # ── last_landmark(列表分支 — 类型分支最容易翻车)
    ({"last_landmark": ["S2", "S3"]}, {"last_landmark_id": "S2"}, True),
    ({"last_landmark": ["S2", "S3"]}, {"last_landmark_id": "S5"}, False),

    # ── character(字符串分支)
    ({"character": "G-273"}, {"character": "G-273"}, True),
    ({"character": "G-273"}, {"character": "L-101"}, False),
    # ── character(列表分支)
    ({"character": ["G-273", "L-101"]}, {"character": "L-101"}, True),
    ({"character": ["G-273", "L-101"]}, {"character": "X-999"}, False),

    # ── 嵌套:any_of(OR)
    ({"any_of": [{"PR_min": 5}, {"GR_min": 5}]}, {"PR": 10, "GR": 0}, True),
    ({"any_of": [{"PR_min": 50}, {"GR_min": 50}]}, {"PR": 10, "GR": 10}, False),

    # ── 嵌套:all_of(显式 AND)
    ({"all_of": [{"PR_min": 5}, {"GR_min": 5}]}, {"PR": 10, "GR": 0}, False),
    ({"all_of": [{"PR_min": 5}, {"GR_min": 5}]}, {"PR": 10, "GR": 10}, True),

    # ── 嵌套:not
    ({"not": {"PR_min": 5}}, {"PR": 3}, True),
    ({"not": {"PR_min": 5}}, {"PR": 10}, False),

    # ── 嵌套边界:空 any_of(player.py 实现:空列表 → 跳过此分支,不触发 OR 失败)
    ({"any_of": []}, {"PR": 0}, True),
    # ── 嵌套边界:空 all_of(player.py 实现:all([]) == True,通过)
    ({"all_of": []}, {"PR": 0}, True),

    # ── 深度嵌套:not(any_of([all_of([...])]))
    # NOT (PR_min:5 AND GR_min:5) — 当前 PR=10 GR=10,内层 True → not False
    (
        {"not": {"any_of": [{"all_of": [{"PR_min": 5}, {"GR_min": 5}]}]}},
        {"PR": 10, "GR": 10},
        False,
    ),
    # NOT (PR_min:50 AND GR_min:50) — 当前 PR=10 GR=10,内层 False → not True
    (
        {"not": {"any_of": [{"all_of": [{"PR_min": 50}, {"GR_min": 50}]}]}},
        {"PR": 10, "GR": 10},
        True,
    ),
])
def test_meets_matches_player_state(require, initial, expected):
    sim = SimState.from_dict(initial)
    player = State(initial)
    sim_result = meets(sim, require)
    player_result = player.meets(require)
    # 行为必须 1:1 对齐
    assert sim_result == player_result, (
        f"SimState.meets={sim_result} but State.meets={player_result} "
        f"for require={require}, initial={initial}"
    )
    # 且符合预期
    assert sim_result == expected, (
        f"meets returned {sim_result}, expected {expected} "
        f"for require={require}, initial={initial}"
    )
