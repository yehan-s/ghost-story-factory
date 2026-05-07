"""tools/audit_variants.py 单元测试。"""
import json

import pytest

from tools.audit_variants import audit_variants, _exit_code


@pytest.fixture
def tree_with_undifferentiated_revisit(tmp_path):
    tree = {
        "initial_state": {},
        "nodes": {
            "n_revisitable": {
                "narrative": "你又来了。",
                # 入边:n_a / n_b 都指向它,且 n_revisitable 自身的选项也回到自己
                "choices": [
                    {"text": "回到自己", "next": "n_revisitable"},
                    {"text": "离开", "next": "n_end"},
                ],
            },
            "n_a": {"narrative": "a", "next": "n_revisitable"},
            "n_b": {"narrative": "b", "next": "n_revisitable"},
            "n_end": {"narrative": "结束。", "ending_type": "test"},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    return p


@pytest.fixture
def tree_with_dead_variant(tmp_path):
    tree = {
        "initial_state": {},
        "nodes": {
            "n_dead": {
                "narrative": "默认。",
                "narrative_variants": [
                    # 永假条件 — PR_min > PR_max
                    {"if": {"PR_min": 9999, "PR_max": 0}, "text": "你不可能看到这条。"},
                ],
            },
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    return p


@pytest.fixture
def tree_no_revisit(tmp_path):
    """单入边节点不算 revisitable。"""
    tree = {
        "initial_state": {},
        "nodes": {
            "n_start": {"narrative": "start", "next": "n_only"},
            "n_only": {"narrative": "only", "next": "n_end"},
            "n_end": {"narrative": "结束。", "ending_type": "test"},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    return p


def test_finds_undifferentiated_revisit_node(tree_with_undifferentiated_revisit):
    report = audit_variants(tree_with_undifferentiated_revisit)
    assert "n_revisitable" in report["undifferentiated_revisit_nodes"]


def test_finds_unreachable_variant(tree_with_dead_variant):
    report = audit_variants(tree_with_dead_variant)
    flagged = [v for v in report["unreachable_variants"] if v["node_id"] == "n_dead"]
    assert len(flagged) == 1
    assert flagged[0]["reason"] == "static_dead"


def test_single_inbound_node_not_revisitable(tree_no_revisit):
    """只有 1 个入边的节点不算可重访(不应被列入 undifferentiated)。"""
    report = audit_variants(tree_no_revisit)
    assert "n_only" not in report["undifferentiated_revisit_nodes"]


def test_ending_never_revisitable(tree_with_undifferentiated_revisit):
    """ending 节点永远不算可重访。"""
    report = audit_variants(tree_with_undifferentiated_revisit)
    assert "n_end" not in report["undifferentiated_revisit_nodes"]


def test_coverage_matrix_records_variants_count(tree_with_dead_variant):
    """每个节点都进 coverage_matrix。"""
    report = audit_variants(tree_with_dead_variant)
    assert report["coverage_matrix"]["n_dead"]["narrative_variants"] == 1
    assert report["coverage_matrix"]["n_dead"]["is_revisitable"] is False


def test_exit_code_strict_warns_on_issues(tree_with_undifferentiated_revisit):
    report = audit_variants(tree_with_undifferentiated_revisit)
    assert _exit_code(report, strict=False) == 0
    assert _exit_code(report, strict=True) == 1


def test_self_loop_via_choice_is_revisitable(tmp_path):
    """单入边但有自指 choice 也算 revisitable。"""
    tree = {
        "initial_state": {},
        "nodes": {
            "n_start": {"narrative": "start", "next": "n_loop"},
            "n_loop": {
                "narrative": "loop",
                "choices": [
                    {"text": "stay", "next": "n_loop"},
                    {"text": "exit", "next": "n_end"},
                ],
            },
            "n_end": {"narrative": "end", "ending_type": "test"},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    report = audit_variants(p)
    # 自指节点没有 narrative_variants → 应被标记为 undifferentiated revisit
    assert "n_loop" in report["undifferentiated_revisit_nodes"]
