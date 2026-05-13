"""Pass 22 — audit 语义化三件套 + 保安线行为画像不变量。

测试:
- audit_foreshadow_chain:contract 链条完整性
- audit_cross_run_continuity:跨周目消费侧覆盖
- audit_variant_trigger:触发难度
- audit_protagonist_behavior:G-273 ending 识别玩家
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from tools.audit_foreshadow_chain import audit as audit_fc
from tools.audit_cross_run_continuity import audit as audit_cr
from tools.audit_variant_trigger import audit as audit_vt
from tools.audit_protagonist_behavior import audit as audit_pb
from tools.audit_profile_inheritance import audit as audit_pi


OFFICIAL_TREE = Path("stories/hangzhou_yebanbaoan/tree.json")


def _write_tree(tree: dict) -> Path:
    """把 dict 写入临时文件,返回 Path。"""
    fd, name = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    Path(name).write_text(json.dumps(tree, ensure_ascii=False), encoding="utf-8")
    return Path(name)


# ============== audit_foreshadow_chain ==============


def test_official_tree_foreshadow_chain_complete():
    """正式树的 reaction_contracts 必须链条完整。"""
    report = audit_fc(OFFICIAL_TREE)
    assert report["problems"] == [], f"foreshadow_chain 异常: {report['problems']}"


def test_foreshadow_chain_detects_missing_label():
    """contract 缺 _label 应当报 MISSING_LABEL。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_a": {
                "narrative_variants": [
                    {"if": {"foreshadow_resolved": "f1"}, "text": "x"},
                ],
                "choices": [],
            }
        },
        "reaction_contracts": {
            "foreshadows": {
                "f1": {
                    "resolver_node": "n_a",
                    "consumer_nodes": ["n_a"],
                    "trigger_type": "per_run",
                    # 缺 _label
                }
            }
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_fc(path)
        codes = {p["code"] for p in report["problems"]}
        assert "MISSING_LABEL" in codes
    finally:
        path.unlink()


def test_foreshadow_chain_detects_consumer_not_consuming():
    """声明 consumer 但实际节点没引用对应 _resolved 应当报。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_a": {"narrative_variants": [], "choices": []},
        },
        "reaction_contracts": {
            "deductions": {
                "d1": {
                    "_label": "测试",
                    "resolver_node": "n_a",
                    "consumer_nodes": ["n_a"],
                    "trigger_type": "per_run",
                }
            }
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_fc(path)
        codes = {p["code"] for p in report["problems"]}
        assert "CONSUMER_NOT_CONSUMING" in codes
    finally:
        path.unlink()


# ============== audit_cross_run_continuity ==============


def test_official_tree_cross_run_runs_clean_default():
    """正式树:默认非 strict 模式跑通(debt 性质允许问题存在)。"""
    report = audit_cr(OFFICIAL_TREE)
    # 至少要识别出 ending_type 数
    assert report["ending_type_count"] >= 8
    # 默认模式只报告,不强制要求 0 problems(主结局 debt 留挂账)


def test_cross_run_bad_endings_are_exempt():
    """E_BAD_* 结局默认豁免,不报跨周目缺失。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_bad": {
                "is_ending": True,
                "ending_type": "E_BAD_TEST",
                "narrative_variants": [],
            },
            "n_main": {
                "is_ending": True,
                "ending_type": "E_MAIN",
                "narrative_variants": [],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_cr(path)
        # E_BAD_TEST 应被豁免,只 E_MAIN 报缺失
        bad_problems = [p for p in report["problems"] if p["ending_type"] == "E_BAD_TEST"]
        main_problems = [p for p in report["problems"] if p["ending_type"] == "E_MAIN"]
        assert bad_problems == []
        assert len(main_problems) == 1
    finally:
        path.unlink()


def test_cross_run_explicit_exempt_via_flag():
    """节点显式声明 _no_cross_ref_ok: true 也豁免。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_main": {
                "is_ending": True,
                "ending_type": "E_MAIN",
                "_no_cross_ref_ok": True,
                "narrative_variants": [],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_cr(path)
        assert report["problems"] == []
    finally:
        path.unlink()


# ============== audit_variant_trigger ==============


def test_official_tree_variant_trigger_no_errors():
    """正式树:variant 触发难度无 ERROR 级。"""
    report = audit_vt(OFFICIAL_TREE)
    assert report["errors_count"] == 0, f"有触发难度 ERROR: {report['problems']}"


def test_variant_trigger_atoms_counted_correctly():
    """前置条件计数:flags 字典逐 key 算,inv_has 逐项算,组合递归。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_a": {
                "narrative_variants": [
                    {
                        # 7 atoms:3 flags + 2 inv_has + 1 puzzle_pieces_min + 1 ending_seen
                        "if": {
                            "flags": {"f1": True, "f2": True, "f3": True},
                            "inv_has": ["a", "b"],
                            "puzzle_pieces_min": 5,
                            "ending_seen": {"story_id": "test", "ending_id": "E"},
                        },
                        "text": "x",
                    }
                ],
                "choices": [],
            }
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_vt(path, warn_th=5, error_th=8)
        # 应当报 WARN(7 ≥ 5)但不 ERROR(7 < 8)
        codes = {p["code"] for p in report["problems"]}
        assert "TRIGGER_HIGH_DIFFICULTY" in codes
        assert "TRIGGER_TOO_HARD" not in codes
        assert any(p["atoms"] == 7 for p in report["problems"])
    finally:
        path.unlink()


def test_variant_trigger_too_hard_blocks():
    """超 ERROR 阈值的 variant 算 TRIGGER_TOO_HARD。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_a": {
                "narrative_variants": [
                    {
                        # 10 atoms:10 个 flags
                        "if": {"flags": {f"f{i}": True for i in range(10)}},
                        "text": "x",
                    }
                ],
                "choices": [],
            }
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_vt(path, warn_th=5, error_th=8)
        assert report["errors_count"] == 1
        assert report["problems"][0]["code"] == "TRIGGER_TOO_HARD"
    finally:
        path.unlink()


# ============== audit_protagonist_behavior ==============


def test_official_tree_protagonist_behavior_clean():
    """正式树:主结局都有识别玩家的 variant。"""
    report = audit_pb(OFFICIAL_TREE)
    assert report["problems"] == [], f"protagonist_behavior 异常: {report['problems']}"


def test_protagonist_behavior_micro_ending_exempted():
    """无 variant 的微结局豁免。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_micro": {
                "is_ending": True,
                "ending_type": "E_BAD",
                "narrative_variants": [],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pb(path)
        assert report["problems"] == []
    finally:
        path.unlink()


def test_protagonist_behavior_blind_main_ending_fails():
    """n_end_* 主结局即使无 variant 也必须识别玩家。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_end_blind": {
                "is_ending": True,
                "ending_type": "E_BLIND",
                # narrative_variants 为空且是 n_end_* → 仍要识别
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pb(path)
        codes = {p["code"] for p in report["problems"]}
        assert "ENDING_BLIND_TO_PLAYER" in codes
    finally:
        path.unlink()


def test_protagonist_behavior_recognition_keys_accepted():
    """behavior_profile / deduction_resolved / flags 任一识别即通过。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "n_end_ok": {
                "is_ending": True,
                "ending_type": "E_OK",
                "narrative_variants": [
                    {"if": {"behavior_profile": {"has": "曝光"}}, "text": "a"},
                ],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pb(path)
        assert report["problems"] == []
    finally:
        path.unlink()


def test_protagonist_behavior_linmou_endings_skipped():
    """linmou ending(E_LINMOU_*)不在 G-273 审计范围。"""
    tree = {
        "story_id": "test",
        "nodes": {
            "E_LINMOU_X": {
                "is_ending": True,
                "ending_type": "E_LINMOU_X",
                # 无 variant 也 OK
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pb(path)
        assert report["g273_ending_count"] == 0
        assert report["problems"] == []
    finally:
        path.unlink()


# ============== audit_profile_inheritance(Pass 25) ==============


def test_profile_inheritance_empty_tree_reports_all_5_missing():
    """空树 → 5 个 main ending 都缺 .last consumer。"""
    tree = {"story_id": "杭州_v7", "nodes": {}}
    path = _write_tree(tree)
    try:
        report = audit_pi(path)
        assert report["main_endings_count"] == 5
        missing = sorted(p["ending_type"] for p in report["problems"])
        assert missing == ["E_BROADCAST", "E_DATA", "E_HIDDEN", "E_TRUE", "E_TRUTH"]
    finally:
        path.unlink()


def test_profile_inheritance_recognises_last_consumer():
    """.last consumer 命中后,对应 ending 不再报 problem。"""
    tree = {
        "story_id": "杭州_v7",
        "nodes": {
            "n_intro": {
                "narrative_variants": [
                    {
                        "if": {"ending_seen": {"story_id": "杭州_v7", "last": "E_TRUE"}},
                        "text": "残影",
                    },
                ],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pi(path)
        assert report["consumers_by_ending"]["E_TRUE"] == ["n_intro"]
        missing = sorted(p["ending_type"] for p in report["problems"])
        assert "E_TRUE" not in missing
        # 其余 4 个仍 missing
        assert len(missing) == 4
    finally:
        path.unlink()


def test_profile_inheritance_ignores_ending_id_form():
    """旧形式 ending_id 不算 .last 消费——这是 Pass 23 已覆盖的"曾经"。"""
    tree = {
        "story_id": "杭州_v7",
        "nodes": {
            "n_intro": {
                "narrative_variants": [
                    {
                        "if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_TRUE"}},
                        "text": "曾经",
                    },
                ],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pi(path)
        # ending_id 形式不计入 .last consumers
        assert report["consumers_by_ending"]["E_TRUE"] == []
    finally:
        path.unlink()


def test_profile_inheritance_skips_ending_nodes():
    """ending 节点内部 variant 的 .last 不算"开场反咬",不计入 consumer。"""
    tree = {
        "story_id": "杭州_v7",
        "nodes": {
            "n_end_neutral": {
                "is_ending": True,
                "ending_type": "E_NEUTRAL",
                "narrative_variants": [
                    {
                        "if": {"ending_seen": {"story_id": "杭州_v7", "last": "E_TRUE"}},
                        "text": "结算文案",
                    },
                ],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pi(path)
        # ending 节点的 .last 不被认作开场反咬,不计入 consumer
        assert report["consumers_by_ending"]["E_TRUE"] == []
    finally:
        path.unlink()


def test_profile_inheritance_story_alias_works():
    """story_id 别名:variant 写"杭州_v7",tree 写"hangzhou_yebanbaoan" → 仍认。"""
    tree = {
        "story_id": "hangzhou_yebanbaoan",
        "nodes": {
            "n_picker": {
                "narrative_variants": [
                    {
                        "if": {"ending_seen": {"story_id": "杭州_v7", "last": "E_DATA"}},
                        "text": "残影",
                    },
                ],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pi(path)
        assert report["consumers_by_ending"]["E_DATA"] == ["n_picker"]
    finally:
        path.unlink()


def test_profile_inheritance_malformed_spec_does_not_raise():
    """CodeRabbit:spec 非 dict(true / list / str)应被跳过,不 raise。"""
    tree = {
        "story_id": "杭州_v7",
        "nodes": {
            "n_a": {
                "narrative_variants": [
                    {"if": {"ending_seen": True}, "text": "x"},
                    {"if": {"ending_seen": ["E_TRUE"]}, "text": "y"},
                    {"if": {"ending_seen": "E_TRUE"}, "text": "z"},
                ],
            },
        },
    }
    path = _write_tree(tree)
    try:
        report = audit_pi(path)
        # 不 raise + 0 consumer + 5 个 main ending 都 missing
        assert all(not v for v in report["consumers_by_ending"].values())
        assert len(report["problems"]) == 5
    finally:
        path.unlink()


def test_profile_inheritance_official_tree_pass_24_25_state():
    """正式树状态:Pass 25 落地后 E_TRUE 有 1 个 consumer(n_intro),其余 4 个仍 debt。"""
    report = audit_pi(OFFICIAL_TREE)
    assert report["consumers_by_ending"]["E_TRUE"] == ["n_intro"]
    missing = sorted(p["ending_type"] for p in report["problems"])
    # 这条断言保护 ADR-011 debt 的可观测度:E_TRUE 已偿,4 个未偿
    assert "E_TRUE" not in missing
    assert len(missing) == 4
