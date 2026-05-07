"""Pass 2 — 林副科长 NPC 4 variant 矩阵 + 4 个 know.linmou_* set 点。

ADR/Spec: docs/team-reviews/2026-05-07-pass2-effects-learn-and-npc-drowned-pilot.md
Plan:    docs/superpowers/plans/2026-05-08-pass2-effects-learn-and-npc-drowned-pilot.md

测试矩阵:
- 4 个 know.linmou_* flag 都有 set 端 (Task 3.0 前置)
- V1 fallback / V2 警觉 / V3 防御 / V4 真相 — 各自命中 picker
- V4 priority > V3 (相同 know flag 都满足时 V4 抢先)
- V4 不能由 know 单独触发 (必须 deduction.predecessor_loop=resolved)
- V2 命中时通过追问 choice 把 asked_predecessor_name 设为 True (清孤儿 require)
"""

from __future__ import annotations

import json
from pathlib import Path

from ghost_story_factory.v5.player import State


TREE_PATH = Path("stories/hangzhou_yebanbaoan/tree.json")
NODE_ID = "n_npc_drowned_official"
FRAG_DIR = Path("stories/hangzhou_yebanbaoan")


def _all_set_flags_in_fragments() -> set:
    """扫所有 fragments,返回所有被 set 过的 flag key 集合。"""
    flags = set()
    for f in FRAG_DIR.glob("_fragment_v7_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        for node in (data.get("nodes") or {}).values():
            # 顶层 effects(罕见)/ choices effects / _scene_details effects
            for choice in node.get("choices") or []:
                eff = choice.get("effects") or {}
                for k in (eff.get("flags") or {}).keys():
                    flags.add(k)
                for nv in choice.get("next_variants") or []:
                    eff2 = nv.get("effects") or {}
                    for k in (eff2.get("flags") or {}).keys():
                        flags.add(k)
            for det in node.get("_scene_details") or []:
                eff = det.get("effects") or {}
                for k in (eff.get("flags") or {}).keys():
                    flags.add(k)
    return flags


def test_know_linmou_flags_have_set_points():
    """V2/V3 的前置 know.linmou_* 必须有 set 端,否则 variant 不可达。"""
    flags = _all_set_flags_in_fragments()
    required = {
        "know.linmou_badge",
        "know.linmou_archive_1985",
        "know.linmou_corruption",
        "know.read_newspaper_1985_10_19",
    }
    missing = required - flags
    assert not missing, f"缺 set 点: {missing}"


# ---------- variant picker tests(Task 3.1 后启用)----------

class _FakeSaveManager:
    """最小 SaveManager 替身,只支撑 is_deduction_resolved。"""

    def __init__(self, deductions=None):
        self._d = set(deductions or [])
        self.data = {}

    def is_deduction_resolved(self, story_id, did):
        return did in self._d


def _load_tree():
    return json.loads(TREE_PATH.read_text(encoding="utf-8"))


def _state_with_flags(flags=None, save_manager=None, story_id="hangzhou_yebanbaoan"):
    s = State(initial={"flags": dict(flags or {}), "character": "G-273"})
    if save_manager:
        s.save_manager = save_manager
        s.story_id = story_id
        s.tree = _load_tree()
    return s


def _node():
    return _load_tree()["nodes"][NODE_ID]


def _hit_variant_index(state):
    """返回当前 state 下命中的 narrative_variants 索引(无命中返回 None,fallback 走 narrative)。"""
    node = _node()
    for idx, v in enumerate(node.get("narrative_variants") or []):
        if state.meets(v.get("if")):
            return idx
    return None


def test_v1_fallback_empty_flags_hits_no_variant():
    """V1 = fallback,V4/V3/V2 都不满足时 narrative_variants 全 miss → 走 default narrative。"""
    s = _state_with_flags()
    idx = _hit_variant_index(s)
    node = _node()
    variants = node.get("narrative_variants") or []
    assert variants, "n_npc_drowned_official 必须有 narrative_variants"
    # narrative 字段必须仍然存在(V1 文案要么在 narrative_variants 末尾无 if,要么在 narrative)
    has_narrative = bool(node.get("narrative")) or any(not v.get("if") for v in variants)
    assert has_narrative, "V1 fallback 必须可达(narrative 或末尾无 if variant)"
    # 空 flags + 无 deduction 不应命中 V2/V3/V4
    if idx is not None:
        # 若有命中,只能是无 if 的 fallback variant
        assert not variants[idx].get("if"), "空 state 不该命中带 if 的 variant"


def test_v2_alert_on_know_linmou_badge():
    """V2: know.linmou_badge → 命中 V2(『小鬼,你翻那箱子做什么』)。"""
    s = _state_with_flags({"know.linmou_badge": True})
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "翻那箱子" in text or "小鬼" in text


def test_v2_alert_on_know_linmou_archive_1985():
    """V2: know.linmou_archive_1985(OR 关系)→ 同样命中 V2。"""
    s = _state_with_flags({"know.linmou_archive_1985": True})
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "翻那箱子" in text or "小鬼" in text


def test_v3_self_defense():
    """V3: know.linmou_corruption AND know.read_newspaper_1985_10_19 → 命中 V3。"""
    s = _state_with_flags({
        "know.linmou_corruption": True,
        "know.read_newspaper_1985_10_19": True,
    })
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "报纸都登了" in text or "你说我冤不冤" in text


def test_v4_truth_requires_deduction():
    """V4: deduction.predecessor_loop=resolved → 命中 V4(『小赵。这次轮到你了』)。"""
    sm = _FakeSaveManager(deductions={"predecessor_loop"})
    s = _state_with_flags(save_manager=sm)
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "小赵" in text and "这次轮到你了" in text


def test_v4_priority_over_v3():
    """风险 1: V4 priority 必须 > V3。同时满足 V3 + V4 时 picker 命中 V4。"""
    sm = _FakeSaveManager(deductions={"predecessor_loop"})
    s = _state_with_flags({
        "know.linmou_corruption": True,
        "know.read_newspaper_1985_10_19": True,
    }, save_manager=sm)
    idx = _hit_variant_index(s)
    text = _node()["narrative_variants"][idx]["text"]
    assert "小赵" in text  # V4 优先


def test_v4_NOT_triggered_by_know_alone():
    """风险 1 红线: know.* 单独不能触发 V4。"""
    s = _state_with_flags({
        "know.linmou_corruption": True,
        "know.read_newspaper_1985_10_19": True,
        "know.linmou_badge": True,
        "know.linmou_archive_1985": True,
    })  # 全 know set,但无 deduction
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "小赵。这次轮到你了" not in text  # V4 不该命中


def test_v2_sets_asked_predecessor_name():
    """风险 6: V2 命中时,玩家可通过追问 choice 把 asked_predecessor_name set 为 True。
    检查方式: grep n_npc_drowned_official 子树,确保 asked_predecessor_name set 至少一次。
    """
    frag = (FRAG_DIR / "_fragment_v7_shared.json").read_text(encoding="utf-8")
    start = frag.find('"n_npc_drowned_official"')
    assert start >= 0, "n_npc_drowned_official 节点必须存在"
    # 找下一个顶层节点 key 作为 block 边界
    end = frag.find('\n    "n_npc_predecessor_voice"', start + 30)
    if end < 0:
        end = len(frag)
    block = frag[start:end]
    assert "asked_predecessor_name" in block, (
        "V2 必须在 n_npc_drowned_official 子树内 set asked_predecessor_name"
    )
