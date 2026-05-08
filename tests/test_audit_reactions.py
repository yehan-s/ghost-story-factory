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


def test_consumer_unreachable_from_resolver_per_run():
    """per_run trigger:resolver 走不到 consumer 宿主 → 阻断。"""
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
            "deductions": {"D-001": {
                "resolver_node": "n_resolver",
                "consumer_nodes": ["n_consumer"],
                "trigger_type": "per_run",
            }},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "UNREACHABLE_REACTION" and "n_consumer" in p["msg"]
               for p in report["problems"])


def test_cross_run_resolver_at_ending_consumer_reachable_from_root():
    """cross_run trigger:resolver 是 ending(死胡同),
    consumer 从 root 可达 → 通过。
    """
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {"choices": [
                {"text": "to_ending", "next": "n_ending"},
                {"text": "to_picker", "next": "n_picker"},
            ]},
            "n_ending": {"choices": []},  # ending 死胡同
            "n_picker": {
                "narrative_variants": [
                    {"if": {"deduction_resolved": "D-001"}, "text": "下周目反应"},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {
            "deductions": {"D-001": {
                "resolver_node": "n_ending",
                "consumer_nodes": ["n_picker"],
                "trigger_type": "cross_run",
            }},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "UNREACHABLE_REACTION")]
    assert blockers == []


def test_cross_character_dead_ending_seen():
    """variant require ending_seen 但该 ending_id 不在节点表 → DEAD_ENDING_SEEN。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "narrative_variants": [
                    {"if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_GHOST"}}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "DEAD_ENDING_SEEN" and "E_GHOST" in p["msg"]
               for p in report["problems"])


def test_cross_character_existing_ending_seen_passes():
    """ending_seen 引用了真实存在的 ending 节点 → 通过。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "narrative_variants": [
                    {"if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [{"text": "x", "next": "E_LINMOU_RELEASE"}],
            },
            "E_LINMOU_RELEASE": {"choices": [], "_lore_canon": {"must_die": True}},
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "DEAD_ENDING_SEEN")]
    assert blockers == []


def test_cross_character_wildcard_ending_seen_no_check():
    """ending_id='*' 通配 → 不检查存在性(语义是『任意 ending』)。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "narrative_variants": [
                    {"if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "*"}}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    assert not any(p["code"] == "DEAD_ENDING_SEEN" for p in report["problems"])


def test_ending_seen_in_any_of_nested():
    """ending_seen 嵌在 any_of 数组里 → DEAD_ENDING_SEEN 应触发(递归 any_of 分支)。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "narrative_variants": [
                    {"if": {"any_of": [
                        {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_FAKE"}},
                    ]}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "DEAD_ENDING_SEEN" and "E_FAKE" in p["msg"]
               for p in report["problems"])


def test_ending_seen_in_all_of_and_not():
    """ending_seen 嵌在 all_of + not 中 → 两条 DEAD_ENDING_SEEN 都应触发(递归 all_of/not)。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "narrative_variants": [
                    {"if": {"all_of": [
                        {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_NESTED_A"}},
                        {"not": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_NESTED_B"}}},
                    ]}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    dead_eids = {
        p["msg"].split("ending_id=")[1].split(" ")[0].strip("'\"")
        for p in report["problems"] if p["code"] == "DEAD_ENDING_SEEN"
    }
    assert "E_NESTED_A" in dead_eids
    assert "E_NESTED_B" in dead_eids


def test_ending_seen_missing_ending_id_field():
    """ending_seen spec 缺 ending_id 字段 → 静默跳过(不触发 DEAD_ENDING_SEEN)。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {
                "narrative_variants": [
                    {"if": {"ending_seen": {"story_id": "杭州_v7"}}, "text": "..."},
                    {"if": {"ending_seen": None}, "text": "..."},
                    {"if": {"ending_seen": {}}, "text": "..."},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    assert not any(p["code"] == "DEAD_ENDING_SEEN" for p in report["problems"])


def test_main_tree_no_dead_resolver():
    """主 tree.json 当前应该 0 DEAD_REACTION/UNREACHABLE_REACTION(reaction_contracts 是空 = trivial pass)。

    注意:此测试**不卡 DEAD_ENDING_SEEN**(故意),否则在 sandbox debt 期会破回归。
    主 tree 的 DEAD_ENDING_SEEN 状态由 ADR-009 § Sandbox Debt 跟踪。
    """
    report = audit(Path("stories/hangzhou_yebanbaoan/tree.json"))
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "UNREACHABLE_REACTION")]
    assert blockers == [], f"主 tree 反应式 variant 死代码:\n{blockers}"
