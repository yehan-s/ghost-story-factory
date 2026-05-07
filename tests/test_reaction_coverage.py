"""Task 2.3 — 反应式 variant 全可达性测试。CI 必跑。

保证:
1. 反应式 variant 引用的 deduction/foreshadow/theme 都在 reaction_contracts 中声明
2. 声明的 resolver_node 都在节点表里且从 root 可达
3. 没有声明了 resolver 但无 variant 消费的孤儿(剧本浪费)
"""
from __future__ import annotations

from pathlib import Path

from tools.audit_reactions import audit

TREE = Path("stories/hangzhou_yebanbaoan/tree.json")


def test_main_tree_no_dead_reactions():
    """DEAD_REACTION:variant 引用了不存在的 contract — 必须 0。"""
    report = audit(TREE)
    blockers = [p for p in report["problems"]
                if p["code"] == "DEAD_REACTION"]
    assert blockers == [], f"反应式 variant 死代码:\n{blockers}"


def test_main_tree_no_unreachable_reactions():
    """UNREACHABLE_REACTION:resolver 不可达 / consumer 走不到 — 必须 0。"""
    report = audit(TREE)
    blockers = [p for p in report["problems"]
                if p["code"] == "UNREACHABLE_REACTION"]
    assert blockers == [], f"反应式 variant 不可达:\n{blockers}"


def test_main_tree_no_orphan_resolves():
    """ORPHAN_RESOLVE:声明了 resolver 但无 variant 消费 — 必须 0(剧本浪费)。"""
    report = audit(TREE)
    orphans = [p for p in report["problems"]
               if p["code"] == "ORPHAN_RESOLVE"]
    assert orphans == [], f"声明了 resolver 但无消费:\n{orphans}"
