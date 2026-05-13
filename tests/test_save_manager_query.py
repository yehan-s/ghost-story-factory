"""Task 1.1 — SaveManager.get_resolved_foreshadows 查询方法。

设计目标:给 _meets_clause 的 theme_resolved 检查用 — 取某 story 已解开的所有
foreshadow id 集合,O(1) 转 set,只读不改。
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ghost_story_factory.v7.save_manager import DEFAULT_SAVE, SaveManager


def _save_with(data):
    p = Path(tempfile.mkdtemp()) / "save.json"
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return SaveManager(p)


def test_get_resolved_foreshadows_returns_set():
    sm = _save_with({
        "version": 4,
        "foreshadows_resolved": {"杭州_v7": ["F-001", "F-002"]},
    })
    result = sm.get_resolved_foreshadows("杭州_v7")
    assert result == {"F-001", "F-002"}
    assert isinstance(result, set)


def test_get_resolved_foreshadows_empty_story_returns_empty_set():
    sm = _save_with({"version": 4, "foreshadows_resolved": {}})
    assert sm.get_resolved_foreshadows("不存在") == set()


def test_get_resolved_foreshadows_missing_field_returns_empty_set():
    sm = _save_with({"version": 4})  # 字段完全缺失
    assert sm.get_resolved_foreshadows("杭州_v7") == set()


# --- Task 1.2: endings_seen schema 升级到 dict[story_id, list] ---

def test_endings_seen_legacy_list_migrates_to_dict():
    """旧版 list 自动迁移到 dict[story_id]。归入 杭州_v7。"""
    sm = _save_with({
        "version": 4,
        "endings_seen": ["E_TRUTH", "E_NEUTRAL"],
    })
    es = sm.data.get("endings_seen")
    assert isinstance(es, dict), "迁移后应为 dict"
    assert "杭州_v7" in es
    assert "E_TRUTH" in es["杭州_v7"]
    assert "E_NEUTRAL" in es["杭州_v7"]


def test_endings_seen_already_dict_preserved():
    """已是 dict 的存档保持不变。"""
    sm = _save_with({
        "version": 5,
        "endings_seen": {"杭州_v7": ["E_TRUTH"]},
    })
    es = sm.data["endings_seen"]
    assert es == {"杭州_v7": ["E_TRUTH"]}


def test_endings_seen_empty_legacy_list_migrates_to_empty_dict():
    sm = _save_with({"version": 4, "endings_seen": []})
    assert sm.data.get("endings_seen") == {}


def test_endings_seen_property_flatten_for_backward_compat():
    """property endings_seen 扁平化所有 story 的 ending(向后兼容旧调用方)。"""
    sm = _save_with({
        "version": 5,
        "endings_seen": {"杭州_v7": ["E_TRUTH", "E_LINMOU_RELEASE"]},
    })
    flat = sm.endings_seen
    assert isinstance(flat, list)
    assert "E_TRUTH" in flat
    assert "E_LINMOU_RELEASE" in flat


def test_record_ending_writes_to_dict():
    """record_ending 写入 endings_seen[story_id]。"""
    import tempfile
    p = Path(tempfile.mkdtemp()) / "save.json"
    sm = SaveManager(p)
    sm.record_ending("E_LINMOU_RELEASE", story_id="杭州_v7")
    es = sm.data["endings_seen"]
    assert isinstance(es, dict)
    assert "E_LINMOU_RELEASE" in es.get("杭州_v7", [])


def test_record_ending_repeat_moves_to_tail():
    """Pass 25:重复通关把 ending 移到末尾,list[-1] 永远是最近一次通关。"""
    import tempfile
    p = Path(tempfile.mkdtemp()) / "save.json"
    sm = SaveManager(p)
    sm.record_ending("E_TRUTH", story_id="杭州_v7")
    sm.record_ending("E_DATA", story_id="杭州_v7")
    sm.record_ending("E_TRUTH", story_id="杭州_v7")  # 重复通关
    seq = sm.data["endings_seen"]["杭州_v7"]
    # 去重不变(2 项),但顺序变成 [E_DATA, E_TRUTH]
    assert seq == ["E_DATA", "E_TRUTH"]
    assert seq[-1] == "E_TRUTH"


def test_record_ending_purges_legacy_duplicates_in_tail_reorder():
    """CodeRabbit:旧版数据若含重复项,record_ending 也得全清后 append。"""
    import tempfile
    p = Path(tempfile.mkdtemp()) / "save.json"
    sm = SaveManager(p)
    # 构造一个含重复项的"旧版"历史(模拟 v4 → v5 迁移残留)
    sm.data["endings_seen"] = {"杭州_v7": ["E_TRUE", "E_DATA", "E_TRUE", "E_TRUE"]}
    sm.record_ending("E_TRUE", story_id="杭州_v7")
    seq = sm.data["endings_seen"]["杭州_v7"]
    # 所有 E_TRUE 应被全部清除,只保留一个在末尾
    assert seq == ["E_DATA", "E_TRUE"]


def test_check_achievements_counts_flattened_endings_seen():
    """endings_seen_min 应统计 ending 数,不是 story 数。"""
    sm = _save_with({
        "version": 5,
        "endings_seen": {"杭州_v7": ["E_TRUTH", "E_DATA"]},
        "achievements_unlocked": [],
    })
    tree = {
        "achievements": {
            "A_TWO_ENDINGS": {
                "trigger": {"endings_seen_min": 2}
            }
        }
    }

    newly = sm.check_achievements(tree, state=None, story_id="杭州_v7")

    assert newly == ["A_TWO_ENDINGS"]


def test_default_save_nested_data_is_not_shared_between_instances():
    """默认存档里的嵌套列表/字典不能跨实例串味。"""
    p1 = Path(tempfile.mkdtemp()) / "save1.json"
    p2 = Path(tempfile.mkdtemp()) / "save2.json"
    sm1 = SaveManager(p1)
    sm2 = SaveManager(p2)

    sm1.data["unlocked_characters"].append("linmou_1985")
    sm1.data["foreshadows_seen"].setdefault("杭州_v7", []).append("F-001")

    assert sm2.data["unlocked_characters"] == DEFAULT_SAVE["unlocked_characters"]
    assert sm2.data["foreshadows_seen"] == {}


def test_reset_restores_all_default_nested_fields():
    """reset 应完整回到默认结构,不能只清一半字段。"""
    p = Path(tempfile.mkdtemp()) / "save.json"
    sm = SaveManager(p)
    sm.data["endings_seen"] = {"杭州_v7": ["E_TRUTH"]}
    sm.data["foreshadow_shards"] = {"杭州_v7": {"F-001": ["s1"]}}
    sm.data["deductions_resolved"] = {"杭州_v7": ["D-001"]}
    sm.data["achievements_unlocked"] = ["A-001"]

    sm.reset()

    assert sm.data == DEFAULT_SAVE
