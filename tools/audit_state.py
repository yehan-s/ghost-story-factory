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
# years: 杭州夜班保安世界观允许的年份锚点。2024 = 主周目当代;1985 = linmou Act 1;
# 1924 雷峰塔倒 / 1947 武林门刑场 / 1957 拆庙 / 1959 留下小学 / 1987 松木场 /
# 1991 留下小学叶某 / 1996 红衣女孩 / 2007 孔雀塌楼 / 2019 媳妇阳台 等。
DEFAULT_LORE_CANON = {
    "years": [
        1924, 1933, 1947, 1957, 1958, 1959, 1965, 1970, 1972, 1976,
        1979, 1980, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990,
        1991, 1992, 1993, 1995, 1996, 1997, 1998, 2002, 2007, 2009,
        2013, 2019, 2020, 2023, 2024, 2029,
    ],
    "forbidden_terms": ["管理委员会", "员工编号", "林先生", "林总", "委员会"],
}

NAMESPACE_PREFIXES = ("know.", "oneshot.", "arc.", "route.", "state.", "meta.")
YEAR_RE = re.compile(r"\b(19[0-9]{2}|20[0-2][0-9])\b")

# Pass 6 评审报告 § 3 量化红线
# FLAG_COUNT_CEILING: 当前 baseline 92 + 8 席预算 = 100,Pass 7 单独立项把 92 降到 75。
# Pass 6 期间不允许增长(超过 100 即 blocking)。
FLAG_COUNT_CEILING = 100
VARIANT_COUNT_PER_NODE_WARN = 8


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
    namespace_violations: List[Tuple[str, str]] = []  # effects.flags key 缺命名空间
    require_namespace_violations: List[Tuple[str, str]] = []  # require/if.flags key 缺命名空间
    year_violations: List[Tuple[str, int]] = []
    term_violations: List[Tuple[str, str]] = []
    variant_overflow: List[Tuple[str, int]] = []  # 单节点 variants > VARIANT_COUNT_PER_NODE_WARN
    variant_if_dupes: List[Tuple[str, int, int]] = []  # (node_id, idx_a, idx_b) if 完全相同

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
            if not k.startswith(NAMESPACE_PREFIXES):
                require_namespace_violations.append((node_id, k))
        for item in inv_req:
            inv_require_by[item].append(node_id)
        # variant 数量 + variant if 重复检查
        variants = node.get("narrative_variants") or []
        if len(variants) > VARIANT_COUNT_PER_NODE_WARN:
            variant_overflow.append((node_id, len(variants)))
        if len(variants) >= 2:
            seen_keys: Dict[str, int] = {}
            for idx, v in enumerate(variants):
                key = json.dumps(v.get("if") or {}, sort_keys=True, ensure_ascii=False)
                if key in seen_keys:
                    variant_if_dupes.append((node_id, seen_keys[key], idx))
                else:
                    seen_keys[key] = idx
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
        "flag_count_ceiling": FLAG_COUNT_CEILING,
        "flag_count_over_ceiling": len(all_flags) > FLAG_COUNT_CEILING,
        "dead_set_flags": dead_set_flags,
        "dead_require_flags": dead_require_flags,
        "namespace_violations": namespace_violations,
        "require_namespace_violations": require_namespace_violations,
        "variant_count_overflow": variant_overflow,
        "variant_if_dupes": variant_if_dupes,
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
    # Blocking: 严守的红线 — 禁用术语 + flag 上限(Pass 6 不许增长)
    blocking = (
        report["term_violations"]
        or report["flag_count_over_ceiling"]
    )
    # Warnings: 创作弹性区(年份 / 命名空间 / 死字段) — strict 下报警
    warnings = (
        report["year_violations"]
        or report["dead_set_flags"]
        or report["dead_require_flags"]
        or report["namespace_violations"]
        or report["require_namespace_violations"]
        or report["dead_set_inv"]
        or report["variant_count_overflow"]
        or report["variant_if_dupes"]
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
