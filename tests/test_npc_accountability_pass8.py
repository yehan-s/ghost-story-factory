"""Pass 8 NPC 关系账本回归测试。"""

import json
from pathlib import Path


TREE_PATH = Path("stories/hangzhou_yebanbaoan/tree.json")


def _tree():
    return json.loads(TREE_PATH.read_text(encoding="utf-8"))


def _variant_matches(variant, expected_flags):
    """检查 narrative variant 是否读取指定 flag 集合。"""
    cond = variant.get("if") or {}
    clauses = cond.get("all_of") or [cond]
    seen = {}
    for clause in clauses:
        seen.update(clause.get("flags") or {})
    return all(seen.get(key) == value for key, value in expected_flags.items())


def test_forum_correction_writes_named_dead_flag():
    tree = _tree()
    forum = tree["nodes"]["n_npc_forum_lurkers"]
    correction = next(
        choice for choice in forum["choices"] if choice["text"].startswith("只发一条更正")
    )
    assert correction["effects"]["flags"]["oneshot.forum_posted"] is True
    assert correction["effects"]["flags"]["arc.named_the_dead"] is True


def test_cleaner_reads_forum_naming_accountability():
    tree = _tree()
    cleaner = tree["nodes"]["n_npc_cleaner_null"]

    assert any(
        _variant_matches(
            variant,
            {"oneshot.live_streaming": True, "arc.named_the_dead": True},
        )
        for variant in cleaner["narrative_variants"]
    )


def test_b3_reads_forum_cleaner_and_evaluator_ledger():
    tree = _tree()
    b3 = tree["nodes"]["n_scene_b3_corridor"]

    assert any(
        _variant_matches(
            variant,
            {
                "oneshot.live_streaming": True,
                "oneshot.s6_no_fingerprint": True,
                "arc.got_judge_seal": True,
            },
        )
        for variant in b3["narrative_variants"]
    )


def test_morning_lakeside_reads_self_audit_and_naming():
    tree = _tree()
    lakeside = tree["nodes"]["n_scene_morning_lakeside"]

    assert any(
        _variant_matches(
            variant,
            {
                "oneshot.forum_posted": True,
                "arc.named_the_dead": True,
                "route.behavior_self_audit": True,
            },
        )
        for variant in lakeside["narrative_variants"]
    )
