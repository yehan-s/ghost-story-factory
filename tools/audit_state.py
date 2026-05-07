"""tools/audit_state.py — flags / inv / state 字段引用矩阵审计。

用法:
    python tools/audit_state.py path/to/tree.json [--strict]

输出 JSON 报告(stdout)+ exit code:
    0 = 全绿
    1 = 有警告(死字段、命名空间违规)— 仅 --strict 时返回
    2 = 有阻断(Lore 红线)

设计:数据说话,不掺合品味判断。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


# Lore 红线默认值(可被 tree.lore_canon 覆盖)
DEFAULT_LORE_CANON = {
    "years": [1924, 1933, 1959, 1985, 1986, 1987, 1991, 1996, 2009],
    "forbidden_terms": ["管理委员会", "员工编号", "林先生", "林总", "委员会"],
}

NAMESPACE_PREFIXES = ("know.", "oneshot.", "arc.", "route.", "state.", "meta.")
YEAR_RE = re.compile(r"\b(19[0-9]{2}|20[0-2][0-9])\b")


def _walk_requires(node: Dict[str, Any]):
    """遍历节点中所有 require 字典(选项 + variants)。"""
    for ch in node.get("choices") or []:
        if "require" in ch:
            yield ch["require"]
    for v in node.get("narrative_variants") or []:
        if "if" in v:
            yield v["if"]
    for v in node.get("next_variants") or []:
        if "if" in v:
            yield v["if"]


def _walk_effects(node: Dict[str, Any]):
    """遍历节点中所有 effects 字典。

    effects 在数据中的位置:
    - 顶层 `node.effects`(罕见,但允许)
    - `node.choices[].effects`(主要位置)
    - `node.narrative_variants[].effects`(可选)
    """
    if isinstance(node.get("effects"), dict):
        yield node["effects"]
    for ch in node.get("choices") or []:
        if isinstance(ch.get("effects"), dict):
            yield ch["effects"]
    for v in node.get("narrative_variants") or []:
        if isinstance(v.get("effects"), dict):
            yield v["effects"]


def _flatten_flags_in_require(req: Any, out: Set[str]) -> None:
    """递归收集 require 中提到的 flag key。"""
    if not isinstance(req, dict):
        return
    for k in (req.get("flags") or {}).keys():
        out.add(k)
    for sub in req.get("any_of", []) or []:
        _flatten_flags_in_require(sub, out)
    for sub in req.get("all_of", []) or []:
        _flatten_flags_in_require(sub, out)
    if "not" in req:
        _flatten_flags_in_require(req["not"], out)


def _flatten_inv_in_require(req: Any, out: Set[str]) -> None:
    """递归收集 require 中提到的 inv item。"""
    if not isinstance(req, dict):
        return
    for item in req.get("inv_has", []) or []:
        out.add(item)
    for sub in req.get("any_of", []) or []:
        _flatten_inv_in_require(sub, out)
    for sub in req.get("all_of", []) or []:
        _flatten_inv_in_require(sub, out)
    if "not" in req:
        _flatten_inv_in_require(req["not"], out)


def _scan_text_for_lore_violations(
    text: str,
    canon: Dict[str, Any],
) -> Tuple[List[int], List[str]]:
    """返回 (越界年份列表, 出现的禁用术语列表)。"""
    bad_years: List[int] = []
    for m in YEAR_RE.finditer(text):
        y = int(m.group(0))
        if y not in canon["years"] and 1900 <= y <= 2030:
            bad_years.append(y)
    bad_terms = [t for t in canon["forbidden_terms"] if t in text]
    return bad_years, bad_terms


def audit_tree(tree_path: Path) -> Dict[str, Any]:
    """主审计入口,返回结构化报告。"""
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    nodes = tree.get("nodes", {})
    canon = tree.get("lore_canon", DEFAULT_LORE_CANON)

    flag_set_by: Dict[str, List[str]] = defaultdict(list)
    flag_require_by: Dict[str, List[str]] = defaultdict(list)
    inv_add_by: Dict[str, List[str]] = defaultdict(list)
    inv_require_by: Dict[str, List[str]] = defaultdict(list)
    namespace_violations: List[Tuple[str, str]] = []  # (node_id, flag_key)
    year_violations: List[Tuple[str, int]] = []
    term_violations: List[Tuple[str, str]] = []

    for node_id, node in nodes.items():
        # effects.flags / effects.inv_add(从所有 effects 出现处遍历)
        for eff in _walk_effects(node):
            for k in (eff.get("flags") or {}).keys():
                flag_set_by[k].append(node_id)
                if not k.startswith(NAMESPACE_PREFIXES):
                    namespace_violations.append((node_id, k))
            for item in eff.get("inv_add", []) or []:
                inv_add_by[item].append(node_id)
        # require.flags / inv_has(递归收集)
        flags_req: Set[str] = set()
        inv_req: Set[str] = set()
        for req in _walk_requires(node):
            _flatten_flags_in_require(req, flags_req)
            _flatten_inv_in_require(req, inv_req)
        for k in flags_req:
            flag_require_by[k].append(node_id)
        for item in inv_req:
            inv_require_by[item].append(node_id)
        # Lore 红线:narrative + 所有 variant 文本扫描
        text_parts: List[str] = [node.get("narrative") or ""]
        for v in node.get("narrative_variants") or []:
            text_parts.append(v.get("text", ""))
        for ch in node.get("choices") or []:
            text_parts.append(ch.get("text", ""))
        text = " ".join(text_parts)
        bad_years, bad_terms = _scan_text_for_lore_violations(text, canon)
        for y in bad_years:
            year_violations.append((node_id, y))
        for t in bad_terms:
            term_violations.append((node_id, t))

    all_flags = set(flag_set_by) | set(flag_require_by)
    dead_set_flags = sorted(set(flag_set_by) - set(flag_require_by))
    dead_require_flags = sorted(set(flag_require_by) - set(flag_set_by))
    all_inv = set(inv_add_by) | set(inv_require_by)
    dead_set_inv = sorted(set(inv_add_by) - set(inv_require_by))

    return {
        "tree_path": str(tree_path),
        "node_count": len(nodes),
        "flags": {
            k: {
                "set_by": flag_set_by.get(k, []),
                "require_by": flag_require_by.get(k, []),
            }
            for k in sorted(all_flags)
        },
        "flag_total": len(all_flags),
        "dead_set_flags": dead_set_flags,
        "dead_require_flags": dead_require_flags,
        "namespace_violations": namespace_violations,
        "inv": {
            k: {
                "add_by": inv_add_by.get(k, []),
                "require_by": inv_require_by.get(k, []),
            }
            for k in sorted(all_inv)
        },
        "dead_set_inv": dead_set_inv,
        "year_violations": year_violations,
        "term_violations": term_violations,
    }


def _exit_code(report: Dict[str, Any], strict: bool) -> int:
    blocking = report["year_violations"] or report["term_violations"]
    warnings = (
        report["dead_set_flags"]
        or report["dead_require_flags"]
        or report["namespace_violations"]
        or report["dead_set_inv"]
    )
    if blocking:
        return 2
    if warnings and strict:
        return 1
    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit tree.json state space.")
    parser.add_argument("tree_path", type=Path)
    parser.add_argument("--strict", action="store_true", help="warnings exit 1")
    args = parser.parse_args(argv)
    report = audit_tree(args.tree_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return _exit_code(report, args.strict)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
