"""Task 2.2 — audit_reactions.py 三红线检测测试。"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tools.audit_reactions import audit


def _write_tree(tree):
    p = Path(tempfile.mkdtemp()) / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False), encoding="utf-8")
    return p


def test_dead_reaction_detected():
    """variant require D-X 但 reaction_contracts 没声明 resolver。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "narrative_variants": [
                    {"if": {"deduction_resolved": "D-MISSING"}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [],
            }
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "DEAD_REACTION" and "D-MISSING" in p["msg"]
               for p in report["problems"])


def test_orphan_resolve_detected():
    """contracts 声明了 resolver,但无 variant 消费。"""
    tree = {
        "start_node": "n1",
        "nodes": {"n1": {"narrative_variants": [{"text": "x"}], "choices": []}},
        "reaction_contracts": {
            "deductions": {"D-001": {"resolver_node": "n1", "consumer_nodes": []}},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "ORPHAN_RESOLVE" for p in report["problems"])


def test_unreachable_resolver_node_detected():
    """resolver_node 引用的节点不存在。"""
    tree = {
        "start_node": "n1",
        "nodes": {"n1": {"narrative_variants": [{"text": "x"}], "choices": []}},
        "reaction_contracts": {
            "deductions": {"D-001": {"resolver_node": "n_ghost", "consumer_nodes": []}},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "UNREACHABLE_REACTION" for p in report["problems"])


def test_clean_tree_zero_problems():
    """有 reaction 的 variant + 已声明的 contract + 可达,无问题。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {"choices": [{"text": "go", "next": "n2"}]},
            "n2": {
                "narrative_variants": [
                    {"if": {"deduction_resolved": "D-001"}, "text": "reaction"},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {
            "deductions": {"D-001": {"resolver_node": "n1", "consumer_nodes": ["n2"]}},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    assert report["problems"] == []


def test_consumer_unreachable_from_resolver():
    """resolver 走不到 consumer 宿主。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {"choices": [
                {"text": "to_resolver", "next": "n_resolver"},
                {"text": "to_consumer", "next": "n_consumer"},
            ]},
            "n_resolver": {"choices": []},  # 死胡同,走不到 n_consumer
            "n_consumer": {
                "narrative_variants": [
                    {"if": {"deduction_resolved": "D-001"}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {
            "deductions": {"D-001": {"resolver_node": "n_resolver", "consumer_nodes": ["n_consumer"]}},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "UNREACHABLE_REACTION" and "n_consumer" in p["msg"]
               for p in report["problems"])


def test_main_tree_currently_clean():
    """主 tree.json 当前应该全绿(reaction_contracts 是空 = trivial pass)。"""
    report = audit(Path("stories/hangzhou_yebanbaoan/tree.json"))
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "UNREACHABLE_REACTION")]
    assert blockers == [], f"主 tree 反应式 variant 死代码:\n{blockers}"
