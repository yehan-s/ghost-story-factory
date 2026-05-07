"""Task 1.1 — SaveManager.get_resolved_foreshadows 查询方法。

设计目标:给 _meets_clause 的 theme_resolved 检查用 — 取某 story 已解开的所有
foreshadow id 集合,O(1) 转 set,只读不改。
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ghost_story_factory.v7.save_manager import SaveManager


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
