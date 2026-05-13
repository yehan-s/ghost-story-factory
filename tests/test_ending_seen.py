"""Task 1.1 — _meets_clause 加 ending_seen 跨周目条件。

形式: {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}
通配: ending_id="*" → 该 story 的任意 ending 都满足
"""
from __future__ import annotations

from ghost_story_factory.v5.player import State


class FakeSave:
    """模拟 SaveManager.data 字典 (含 endings_seen)。"""

    def __init__(self, endings_seen=None):
        # endings_seen: dict[story_id, list[ending_id]] 或 list[ending_id](旧版)
        self.data = {"endings_seen": endings_seen if endings_seen is not None else {}}

    def is_deduction_resolved(self, sid, did):
        return False

    def is_foreshadow_resolved(self, sid, fid):
        return False

    def get_resolved_foreshadows(self, sid):
        return set()


def _state_with(endings):
    sm = FakeSave(endings_seen=endings)
    return State({}, save_manager=sm, story_id="杭州_v7")


# --- 字段精确匹配 ---

def test_ending_seen_exact_match_dict():
    s = _state_with({"杭州_v7": ["E_LINMOU_RELEASE"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}) is True


def test_ending_seen_story_mismatch():
    s = _state_with({"杭州_v7": ["E_TRUTH"]})
    assert s.meets({"ending_seen": {"story_id": "其他故事", "ending_id": "E_TRUTH"}}) is False


def test_ending_seen_ending_mismatch():
    s = _state_with({"杭州_v7": ["E_TRUTH"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}) is False


# --- 通配 ---

def test_ending_seen_wildcard_ending_any_match():
    """ending_id='*' → 任意该 story 的 ending 都满足。"""
    s = _state_with({"杭州_v7": ["E_TRUTH"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "*"}}) is True


def test_ending_seen_wildcard_ending_empty_fails():
    """ending_id='*' + 该 story 0 ending → False。"""
    s = _state_with({"杭州_v7": []})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "*"}}) is False


# --- 兼容性 / 安全降级 ---

def test_ending_seen_no_save_manager_returns_false():
    s = State({})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_TRUTH"}}) is False


def test_ending_seen_legacy_list_format():
    """旧版 SaveManager: endings_seen 是 list,不是 dict。仍能查询(全 story 视为 杭州_v7)。"""
    s = _state_with(["E_TRUTH"])  # 旧版 list
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_TRUTH"}}) is True


def test_ending_seen_missing_spec_returns_false():
    """spec 缺 story_id 或 ending_id → False(防御性)。"""
    s = _state_with({"杭州_v7": ["E_TRUTH"]})
    assert s.meets({"ending_seen": {}}) is False
    assert s.meets({"ending_seen": {"story_id": "杭州_v7"}}) is False
    assert s.meets({"ending_seen": {"ending_id": "E_TRUTH"}}) is False


# --- Pass 25:人格惯性 .last 协议 ---

def test_ending_seen_last_matches_tail():
    """ending_seen.last 匹配 list[-1]。"""
    s = _state_with({"杭州_v7": ["E_TRUTH", "E_DATA", "E_TRUE"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "last": "E_TRUE"}}) is True


def test_ending_seen_last_mismatch_non_tail():
    """ending_seen.last 不是末尾 → False(就算 list 里出现过)。"""
    s = _state_with({"杭州_v7": ["E_TRUTH", "E_DATA", "E_TRUE"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "last": "E_TRUTH"}}) is False


def test_ending_seen_last_empty_list_false():
    s = _state_with({"杭州_v7": []})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "last": "E_TRUE"}}) is False


def test_ending_seen_malformed_spec_returns_false():
    """spec 非 dict(true / list / str)→ False 不 raise。"""
    s = _state_with({"杭州_v7": ["E_TRUE"]})
    assert s.meets({"ending_seen": True}) is False
    assert s.meets({"ending_seen": ["E_TRUE"]}) is False
    assert s.meets({"ending_seen": "E_TRUE"}) is False


def test_ending_seen_non_str_fields_return_false():
    """story_id / ending_id / last 非 str → False。"""
    s = _state_with({"杭州_v7": ["E_TRUE"]})
    # story_id 非 str
    assert s.meets({"ending_seen": {"story_id": 123, "last": "E_TRUE"}}) is False
    # ending_id 非 str
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": ["E_TRUE"]}}) is False
    # last 非 str
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "last": 42}}) is False


def test_ending_seen_last_and_ending_id_both_required():
    """last + ending_id 同时给 → AND 关系。"""
    s = _state_with({"杭州_v7": ["E_TRUTH", "E_TRUE"]})
    require = {
        "ending_seen": {
            "story_id": "杭州_v7",
            "last": "E_TRUE",
            "ending_id": "E_TRUTH",
        }
    }
    assert s.meets(require) is True
    # E_DATA 不在 list 里 → False
    require["ending_seen"]["ending_id"] = "E_DATA"
    assert s.meets(require) is False
