#!/usr/bin/env python3
"""Pass 25 — 人格惯性(profile inheritance)审计。

State Architect A方案落地后的可观测度:
contracts.py 已支持 `ending_seen.last` 协议,record_ending 已保证 list[-1]
是最近一次通关。本工具检查"5 个 main ending 是否被剧本作为 .last
的人格惯性触发条件消费"。

main ending(在本 audit 范围内):
- E_TRUE / E_TRUTH / E_BROADCAST / E_DATA / E_HIDDEN
- BAD ending / NEUTRAL / LINMOU 不在 .last 反咬范围(见 ADR-011)

报告级别(Pass 26 起):
- **默认 strict**:5 个 main ending 都必须有 ≥1 个非结局 variant 用 .last 反咬,
  否则退出码 2。这是引擎已支持、剧本已落地的协议,不允许新 ending 再留账。
- --lenient:仅用于本地新铺剧本期间临时绕开,CI 不接受。

用法:
    python tools/audit_profile_inheritance.py path/to/tree.json
    python tools/audit_profile_inheritance.py path/to/tree.json --lenient
退出码:0=全绿;2=有缺失(默认)。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


MAIN_ENDINGS = {"E_TRUE", "E_TRUTH", "E_BROADCAST", "E_DATA", "E_HIDDEN"}

# 与 audit_reactions / audit_cross_run_continuity 保持一致:
# 剧本写 story_id="杭州_v7" 但 tree.json 的 story_id="hangzhou_yebanbaoan",
# 这是 ADR-009 时期的历史包袱,双向 alias 兜底而不阻塞。
STORY_ALIASES = {
    ("杭州_v7", "hangzhou_yebanbaoan"),
    ("hangzhou_yebanbaoan", "杭州_v7"),
}


def _walk_requires(node: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for v in node.get("narrative_variants") or []:
        if "if" in v:
            yield v["if"]
    for ch in node.get("choices") or []:
        if "require" in ch:
            yield ch["require"]


def _walk_ending_seen(req: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    if not isinstance(req, dict):
        return
    if "ending_seen" in req:
        yield req["ending_seen"] or {}
    for sub in req.get("any_of") or []:
        yield from _walk_ending_seen(sub)
    for sub in req.get("all_of") or []:
        yield from _walk_ending_seen(sub)
    if "not" in req:
        yield from _walk_ending_seen(req["not"])


def audit(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    tree_story_id = tree.get("story_id") or ""

    # 收集每个 ending 被 .last 引用的 consumer 节点(排除 ending 节点本身,
    # 因为 ending 内的 variant 是结算文案,不是"开场人格惯性")
    last_consumers: Dict[str, Set[str]] = {e: set() for e in MAIN_ENDINGS}
    for nid, node in nodes.items():
        if node.get("is_ending"):
            continue
        for req in _walk_requires(node):
            for spec in _walk_ending_seen(req):
                # CodeRabbit: spec 可能是 true / list / str(剧本错误形式),
                # 跳过而不是 raise。审计永远不应该因为剧本数据形态崩溃。
                if not isinstance(spec, dict):
                    continue
                last_id = spec.get("last")
                if not last_id:
                    continue
                spec_sid = spec.get("story_id")
                if (spec_sid and tree_story_id and spec_sid != tree_story_id
                        and (spec_sid, tree_story_id) not in STORY_ALIASES):
                    continue
                if last_id in MAIN_ENDINGS:
                    last_consumers[last_id].add(nid)

    problems: List[Dict[str, Any]] = []
    for etype in sorted(MAIN_ENDINGS):
        if not last_consumers[etype]:
            problems.append({
                "code": "MAIN_ENDING_NO_LAST_INHERITANCE",
                "ending_type": etype,
                "msg": (
                    f"main ending {etype!r} 没有任何非结局 variant 用 "
                    f"ending_seen.last 反咬——上次通关此结局的玩家,本周目"
                    f"开场看不到「人格惯性」残影。修复方向:在合适早期节点"
                    f"(n_intro / picker / 首次访问场景)加 "
                    f"narrative_variants[].if.ending_seen.last = {etype!r}。"
                ),
            })

    return {
        "tree": str(tree_path),
        "main_endings_count": len(MAIN_ENDINGS),
        "consumers_by_ending": {k: sorted(v) for k, v in last_consumers.items()},
        "problems": problems,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    # Pass 26 起:strict 升级为默认。5 个 main ending 都必须有 ≥1 个 .last consumer。
    # `--lenient` 用于本地新铺剧本时临时绕开,CI 不接受。
    ap.add_argument(
        "--lenient",
        action="store_true",
        help=(
            "缺失 main ending .last 反咬时**不**阻断,仅报告。"
            "仅用于本地新铺剧本期间;CI / merge gate 不应使用。"
        ),
    )
    args = ap.parse_args()
    report = audit(args.tree)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["problems"] and not args.lenient:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
