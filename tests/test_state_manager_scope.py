"""StateManager 近似合并 scope 分桶测试

目标：
- 近似合并必须支持 scope（例如 depth/beat），避免跨深度合并导致结构塌陷。
- legacy 的 scene_index 结构（scene -> list）仍能工作。
"""

from __future__ import annotations

from ghost_story_factory.pregenerator.state_manager import StateManager


def test_find_approximate_respects_scope_bucket():
    sm = StateManager()

    state = {
        "current_scene": "S1",
        "PR": 10,
        "GR": 0,
        "time": "00:00",
        "flags": {},
        "inventory": [],
    }

    state_hash = sm.get_state_hash(state)
    sm.register_state(state_hash, "node_1")
    sm.register_scene_index(state, state_hash, scope="depth=1|beat=B1")

    # 同一量化 key，但不同 scope 不应合并
    assert sm.find_approximate(state, scope="depth=2|beat=B2") is None
    assert sm.find_approximate(state, scope="depth=1|beat=B1") == "node_1"


def test_find_approximate_legacy_list_compatible():
    sm = StateManager()

    state = {
        "current_scene": "S1",
        "PR": 10,
        "GR": 0,
        "time": "00:00",
        "flags": {},
        "inventory": [],
    }

    state_hash = sm.get_state_hash(state)
    sm.register_state(state_hash, "node_1")

    # legacy checkpoint 结构：scene -> list
    sm.scene_index["S1"] = [(state_hash, sm._quantize_key_state(state))]

    assert sm.find_approximate(state) == "node_1"
