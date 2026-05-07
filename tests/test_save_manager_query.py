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
