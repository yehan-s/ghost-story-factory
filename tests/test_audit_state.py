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
    """禁用术语触发 blocking (exit 2)。年份越界降为 warning(strict 下 1)。"""
    # term_violation = blocking
    tree_term = {
        "lore_canon": {"years": [1985], "forbidden_terms": ["管理委员会"]},
        "initial_state": {},
        "nodes": {"n": {"narrative": "管理委员会发文。"}},
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree_term, ensure_ascii=False))
    report = audit_tree(p)
    assert _exit_code(report, strict=False) == 2
    assert _exit_code(report, strict=True) == 2

    # year_violation only = warning
    tree_year = {
        "lore_canon": {"years": [1985], "forbidden_terms": []},
        "initial_state": {},
        "nodes": {"n": {"narrative": "1900 年的事。"}},
    }
    p2 = tmp_path / "tree2.json"
    p2.write_text(json.dumps(tree_year, ensure_ascii=False))
    report2 = audit_tree(p2)
    assert _exit_code(report2, strict=False) == 0
    assert _exit_code(report2, strict=True) == 1


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


# Pass 6 新增 audit 项 ---

def test_flag_count_ceiling_blocks(tmp_path):
    """flag 总数超上限 (默认 100) 应触发 blocking。"""
    nodes = {}
    for i in range(101):
        nodes[f"n_set_{i}"] = {
            "narrative": "x",
            "effects": {"flags": {f"oneshot.flag_{i}": True}},
        }
        nodes[f"n_req_{i}"] = {
            "narrative": "x",
            "choices": [{
                "text": "x",
                "next": "n_set_0",
                "require": {"flags": {f"oneshot.flag_{i}": True}},
            }],
        }
    tree = {"lore_canon": {"years": [], "forbidden_terms": []}, "nodes": nodes}
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    assert report["flag_total"] >= 101
    assert report["flag_count_over_ceiling"] is True
    assert _exit_code(report, strict=False) == 2


def test_flag_count_under_ceiling_no_block(tmp_path):
    """flag 总数 ≤ 100 不阻断。"""
    tree = {
        "lore_canon": {"years": [], "forbidden_terms": []},
        "nodes": {
            "n_a": {"narrative": "x", "effects": {"flags": {"oneshot.foo": True}}},
            "n_b": {
                "narrative": "x",
                "choices": [{"text": "x", "next": "n_a", "require": {"flags": {"oneshot.foo": True}}}],
            },
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    assert report["flag_count_over_ceiling"] is False


def test_variant_count_overflow_warns(tmp_path):
    """单节点 narrative_variants > 8 进入 warning 列表。"""
    variants = [{"if": {"visit_count_min": {"n_a": i}}, "text": f"v{i}"} for i in range(10)]
    tree = {
        "lore_canon": {"years": [], "forbidden_terms": []},
        "nodes": {"n_a": {"narrative": "x", "narrative_variants": variants}},
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    over = [n for n, _ in report["variant_count_overflow"] if n == "n_a"]
    assert len(over) == 1
    # warning,non-strict 不阻断
    assert _exit_code(report, strict=False) == 0
    assert _exit_code(report, strict=True) == 1


def test_variant_if_dupes_detected(tmp_path):
    """同节点 ≥2 条 variants 的 if 完全相同时应报。"""
    tree = {
        "lore_canon": {"years": [], "forbidden_terms": []},
        "nodes": {
            "n_a": {
                "narrative": "x",
                "narrative_variants": [
                    {"if": {"visit_count_min": {"n_a": 1}}, "text": "v0"},
                    {"if": {"visit_count_min": {"n_a": 1}}, "text": "v1"},
                    {"if": {}, "text": "default"},
                ],
            },
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    dupes = [d for d in report["variant_if_dupes"] if d[0] == "n_a"]
    assert len(dupes) == 1
    assert dupes[0] == ("n_a", 0, 1)


def test_require_namespace_violation_detected(tmp_path):
    """require/if 子句中 flag 缺命名空间前缀应被报。"""
    tree = {
        "lore_canon": {"years": [], "forbidden_terms": []},
        "nodes": {
            "n_a": {
                "narrative": "x",
                "choices": [{
                    "text": "x",
                    "next": "n_a",
                    "require": {"flags": {"raw_flag_no_ns": True}},
                }],
            },
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_tree(p)
    assert ("n_a", "raw_flag_no_ns") in report["require_namespace_violations"]


def test_real_tree_passes_with_new_audits(tmp_path):
    """主 tree.json 在新 audit 加固下 non-strict 必过(Pass 6 baseline 防线)。"""
    from pathlib import Path
    real_tree = Path(__file__).parent.parent / "stories" / "hangzhou_yebanbaoan" / "tree.json"
    if not real_tree.exists():
        pytest.skip("real tree not available")
    report = audit_tree(real_tree)
    # baseline debt 不阻断
    assert _exit_code(report, strict=False) == 0
    # flag 上限留余量
    assert report["flag_total"] <= 100, (
        f"flag_total={report['flag_total']} 超过 100,Pass 6 baseline 失守"
    )
