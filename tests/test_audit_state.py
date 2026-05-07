"""tools/audit_state.py 单元测试 + 真 tree.json 集成。"""
import json

import pytest

from tools.audit_state import audit_tree, _exit_code


@pytest.fixture
def minimal_tree(tmp_path):
    tree = {
        "initial_state": {"flags": {}},
        "nodes": {
            "n_a": {
                "narrative": "...",
                "effects": {"flags": {"oneshot.foo": True}},
                "next": "n_b",
            },
            "n_b": {
                "narrative": "...",
                "choices": [
                    {
                        "text": "X",
                        "next": "n_a",
                        "require": {"flags": {"oneshot.foo": True}},
                    }
                ],
            },
            "n_dead_set": {
                "narrative": "...",
                "effects": {"flags": {"oneshot.never_read": True}},
                "next": "n_b",
            },
            "n_dead_require": {
                "narrative": "...",
                "choices": [
                    {
                        "text": "Y",
                        "next": "n_b",
                        "require": {"flags": {"oneshot.never_set": True}},
                    }
                ],
            },
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree), encoding="utf-8")
    return p


def test_audit_finds_dead_set_flag(minimal_tree):
    """只 set 不 require 的 flag 应该被标记。"""
    report = audit_tree(minimal_tree)
    assert "oneshot.never_read" in report["dead_set_flags"]


def test_audit_finds_dead_require_flag(minimal_tree):
    """只 require 不 set 的 flag 应该被标记。"""
    report = audit_tree(minimal_tree)
    assert "oneshot.never_set" in report["dead_require_flags"]


def test_audit_healthy_flag_not_flagged(minimal_tree):
    """正常被 set 又被 require 的 flag 不出现在死字段清单。"""
    report = audit_tree(minimal_tree)
    assert "oneshot.foo" not in report["dead_set_flags"]
    assert "oneshot.foo" not in report["dead_require_flags"]


def test_audit_returns_flag_usage_matrix(minimal_tree):
    """每个 flag 都有 set_by + require_by 节点列表。"""
    report = audit_tree(minimal_tree)
    assert report["flags"]["oneshot.foo"]["set_by"] == ["n_a"]
    assert report["flags"]["oneshot.foo"]["require_by"] == ["n_b"]


def test_namespace_violation_detected(tmp_path):
    """未 namespace 化的 flag(无前缀)应被标记。"""
    tree = {
        "initial_state": {"flags": {}},
        "nodes": {
            "n_a": {
                "narrative": "...",
                "effects": {"flags": {"raw_flag_no_ns": True}},
                "next": "n_b",
            },
            "n_b": {"narrative": "...", "ending_type": "test"},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree))
    report = audit_tree(p)
    assert ("n_a", "raw_flag_no_ns") in report["namespace_violations"]


def test_year_violation_detected(tmp_path):
    """narrative 文本中引用白名单外年份应被标记。"""
    tree = {
        "lore_canon": {
            "years": [1985, 1987],
            "forbidden_terms": [],
        },
        "initial_state": {},
        "nodes": {
            "n_bad": {"narrative": "据说 2003 年这里发生过事故。"},
            "n_ok": {"narrative": "1985 年的档案显示..."},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    bad = [v for v in report["year_violations"] if v[1] == 2003]
    assert len(bad) == 1
    assert bad[0][0] == "n_bad"
    # 1985 在白名单,不应报
    assert all(v[1] != 1985 for v in report["year_violations"])


def test_forbidden_term_detected(tmp_path):
    """narrative 文本中出现禁用术语应被标记。"""
    tree = {
        "lore_canon": {
            "years": [],
            "forbidden_terms": ["管理委员会", "员工编号"],
        },
        "initial_state": {},
        "nodes": {
            "n_bad": {"narrative": "管理委员会发布了新规定。"},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    bad = [v for v in report["term_violations"] if v[1] == "管理委员会"]
    assert len(bad) == 1


def test_exit_code_blocks_on_lore_violation(tmp_path):
    """有 year/term violation 时 exit code = 2。"""
    tree = {
        "lore_canon": {"years": [1985], "forbidden_terms": []},
        "initial_state": {},
        "nodes": {"n": {"narrative": "1900 年的事。"}},
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    assert _exit_code(report, strict=False) == 2
    assert _exit_code(report, strict=True) == 2


def test_exit_code_warning_only_when_strict(minimal_tree):
    """死字段是 warning,只在 --strict 时返回 1。"""
    report = audit_tree(minimal_tree)
    assert _exit_code(report, strict=False) == 0  # 0 — 死字段不阻断
    assert _exit_code(report, strict=True) == 1  # 1 — 严格模式下报警


def test_inv_dead_set_detected(tmp_path):
    """只 inv_add 不 inv_has 的道具应被标记。"""
    tree = {
        "initial_state": {},
        "nodes": {
            "n_a": {
                "narrative": "...",
                "effects": {"inv_add": ["unread_item"]},
                "next": "n_b",
            },
            "n_b": {"narrative": "...", "ending_type": "test"},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    assert "unread_item" in report["dead_set_inv"]
