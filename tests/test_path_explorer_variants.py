"""path_explorer 三大盲区补丁测试(Task 13)。

覆盖:
- variants_coverage: narrative_variants / next_variants 是否被任何路径触发
- orphan_keys: require 引用但无人 set 的 flag / inv item
- picker_paths: landmark_picker 节点静态展开 picker_choices
"""
from __future__ import annotations

import json

import pytest

from tools.path_explorer import (
    analyze_static,
    analyze_variants_coverage,
    analyze_orphan_keys,
    analyze_picker_nodes,
    explore,
)


# ─────────────────────────────────────────────────────────────────────
# Fixture 1: narrative_variants 命中 / 永不命中
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def tree_with_variant_hit_and_miss():
    """三个 variants:
       - 0 命中(start 即 PR=0,符合 PR_max:50)
       - 1 命中(到达 n_mid 时 flags.x=true)
       - 2 永不命中(PR_min 100 但 PR 永远 ≤0)
    """
    return {
        "initial_state": {"PR": 0, "GR": 0, "flags": {}},
        "start_node": "n_start",
        "endings": {"E_TEST": {"name": "测试", "tone": "?"}},
        "nodes": {
            "n_start": {
                "narrative_variants": [
                    {"if": {"PR_max": 50}, "text": "PR 低,命中。"},   # idx 0: hit
                    {"if": {"PR_min": 100}, "text": "PR 必爆,永不命中。"},  # idx 1: miss
                ],
                "narrative": "default start",
                "choices": [
                    {
                        "text": "继续",
                        "next": "n_mid",
                        "effects": {"flags": {"x": True}},
                    },
                ],
            },
            "n_mid": {
                "narrative_variants": [
                    {"if": {"flags": {"x": True}}, "text": "x 已设,命中。"},  # idx 0: hit
                ],
                "narrative": "default mid",
                "choices": [
                    {"text": "结束", "next": "n_end"},
                ],
            },
            "n_end": {"narrative": "结束。", "is_ending": True, "ending_type": "E_TEST"},
        },
    }


def test_variants_coverage_detects_hit_and_miss(tree_with_variant_hit_and_miss):
    tree = tree_with_variant_hit_and_miss
    static = analyze_static(tree)
    dyn = explore(tree, max_depth=20, max_states=10_000)
    coverage = analyze_variants_coverage(tree, dyn)

    # 总共 3 个 narrative_variants(2 + 1)
    assert coverage.total_variants == 3
    # n_start#0 hit, n_start#1 miss, n_mid#0 hit
    assert coverage.hit_count == 2
    assert coverage.miss_count == 1
    # miss 应记录 n_start variant idx=1
    miss_keys = {(m["node_id"], m["variant_index"]) for m in coverage.misses}
    assert ("n_start", 1) in miss_keys


# ─────────────────────────────────────────────────────────────────────
# Fixture 2: require 引用 flag 但无人 set
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def tree_with_orphan_flag_and_inv():
    """require 引用 ghost_flag(无人 set)和 inv_has 'ghost_item'(无人 add)。"""
    return {
        "initial_state": {"PR": 0, "GR": 0, "flags": {}},
        "start_node": "n_start",
        "endings": {"E_TEST": {"name": "测试", "tone": "?"}},
        "nodes": {
            "n_start": {
                "choices": [
                    {
                        "text": "需要鬼标志",
                        "next": "n_end",
                        "require": {"flags": {"ghost_flag": True}},  # orphan
                    },
                    {
                        "text": "需要鬼物品",
                        "next": "n_end",
                        "require": {"inv_has": ["ghost_item"]},  # orphan
                    },
                    {
                        "text": "需要存在的标志",
                        "next": "n_end",
                        "require": {"flags": {"good_flag": True}},  # 不 orphan
                        "effects": {"flags": {"good_flag": True}},  # ← 自己 set,不算 orphan
                    },
                ],
            },
            "n_end": {"narrative": "结束。", "is_ending": True, "ending_type": "E_TEST"},
        },
    }


def test_orphan_flag_detection(tree_with_orphan_flag_and_inv):
    tree = tree_with_orphan_flag_and_inv
    orphans = analyze_orphan_keys(tree)
    flag_orphans = {o["key"] for o in orphans.flag_orphans}
    inv_orphans = {o["key"] for o in orphans.inv_orphans}

    assert "ghost_flag" in flag_orphans
    assert "good_flag" not in flag_orphans
    assert "ghost_item" in inv_orphans

    # 也要列出 required_by(谁引用了 orphan)
    ghost_flag_entry = next(o for o in orphans.flag_orphans if o["key"] == "ghost_flag")
    assert "n_start" in ghost_flag_entry["required_by"]


# ─────────────────────────────────────────────────────────────────────
# Fixture 3: landmark picker 节点静态展开
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def tree_with_landmark_picker():
    """n_picker 标了 _is_map_picker,但 choices 列表中已经包含 7 个 landmark(产线常态)。"""
    return {
        "initial_state": {"PR": 0, "GR": 0, "flags": {}},
        "start_node": "n_start",
        "endings": {"E_TEST": {"name": "测试", "tone": "?"}},
        "landmark_map": [
            {"id": "S1", "node_id": "n_s1", "place": "湖边"},
            {"id": "S2", "node_id": "n_s2", "place": "山上"},
        ],
        "nodes": {
            "n_start": {
                "choices": [{"text": "看地图", "next": "n_picker"}],
            },
            "n_picker": {
                "_is_map_picker": True,
                "scene": "MAP",
                "narrative": "你又站在地图前。",
                "choices": [
                    {"text": "去 S1", "next": "n_s1"},
                    {"text": "去 S2", "next": "n_s2"},
                ],
            },
            "n_s1": {
                "choices": [{"text": "回到地图", "next": "n_picker"}],
            },
            "n_s2": {
                "choices": [{"text": "回到地图", "next": "n_picker"}],
            },
            "n_end": {"narrative": "结束。", "is_ending": True, "ending_type": "E_TEST"},
        },
    }


def test_picker_node_recognized(tree_with_landmark_picker):
    tree = tree_with_landmark_picker
    pickers = analyze_picker_nodes(tree)

    # 应识别 n_picker 是 picker 节点
    picker_ids = {p["node_id"] for p in pickers}
    assert "n_picker" in picker_ids

    # 应静态展开 landmark_map 中的 node_id 作为 picker_paths
    n_picker_entry = next(p for p in pickers if p["node_id"] == "n_picker")
    assert "n_s1" in n_picker_entry["picker_paths"]
    assert "n_s2" in n_picker_entry["picker_paths"]


def test_picker_paths_keep_endings_reachable(tree_with_landmark_picker):
    """补丁不应破坏现有 ending 可达性。"""
    tree = tree_with_landmark_picker
    static = analyze_static(tree)
    dyn = explore(tree, max_depth=20, max_states=10_000)
    # n_s1 / n_s2 / n_picker 应该都被访问到
    assert "n_picker" in dyn.visited_nodes
    assert "n_s1" in dyn.visited_nodes
    assert "n_s2" in dyn.visited_nodes
