"""Task 2.1 — tree.json 顶层 reaction_contracts 字段 schema 测试。

reaction_contracts 是剧本契约:每个 deduction/foreshadow/theme 必须声明
resolver_node(在哪个节点解开)+ consumer_nodes(哪些节点消费它)。
"""
from __future__ import annotations

import json
from pathlib import Path

TREE = Path("stories/hangzhou_yebanbaoan/tree.json")


def _load():
    return json.loads(TREE.read_text(encoding="utf-8"))


def test_tree_has_reaction_contracts_field():
    tree = _load()
    assert "reaction_contracts" in tree, "tree.json 顶层缺 reaction_contracts"
    rc = tree["reaction_contracts"]
    assert isinstance(rc, dict)
    for key in ("deductions", "foreshadows", "themes"):
        assert key in rc, f"reaction_contracts.{key} 缺"
        assert isinstance(rc[key], dict)


def test_reaction_contracts_entries_have_required_fields():
    tree = _load()
    rc = tree["reaction_contracts"]
    for ctype in ("deductions", "foreshadows", "themes"):
        for ref_id, contract in (rc.get(ctype) or {}).items():
            assert "resolver_node" in contract, f"{ctype}.{ref_id} 缺 resolver_node"
            assert "consumer_nodes" in contract, f"{ctype}.{ref_id} 缺 consumer_nodes"
            assert isinstance(contract["consumer_nodes"], list)
