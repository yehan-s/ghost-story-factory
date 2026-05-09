#!/usr/bin/env python3
"""ADR-010 沙盒骨架审计。

本工具只检查 GameTree v1 是否具备最小沙盒拓扑:
- picker hub;
- landmark_map 网状地标;
- tool 节点;
- stay 自循环;
- 反应式 narrative variant;
- presentation 文本演出兜底。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.audit_playability import choices_of, choice_targets, load_payload, node_map


REACTION_KEYS = {
    "deduction_resolved",
    "foreshadow_resolved",
    "theme_resolved",
    "ending_seen",
}


@dataclass
class SandboxReport:
    """沙盒骨架审计结果。"""

    tree_path: str = ""
    node_count: int = 0
    picker_nodes: List[str] = field(default_factory=list)
    landmark_count: int = 0
    tool_nodes: List[str] = field(default_factory=list)
    stay_loop_nodes: List[str] = field(default_factory=list)
    reaction_variant_nodes: List[str] = field(default_factory=list)
    presentation_nodes: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        """转成 JSON 友好的报告。"""
        return {
            "ok": self.ok,
            "tree_path": self.tree_path,
            "node_count": self.node_count,
            "picker_nodes": self.picker_nodes,
            "landmark_count": self.landmark_count,
            "tool_nodes": self.tool_nodes,
            "stay_loop_nodes": self.stay_loop_nodes,
            "reaction_variant_nodes": self.reaction_variant_nodes,
            "presentation_nodes": self.presentation_nodes,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def analyze_sandbox(payload: Dict[str, Any], tree_path: str = "") -> SandboxReport:
    """审计一棵 GameTree v1 是否具备 ADR-010 最小沙盒骨架。"""
    nodes = node_map(payload)
    report = SandboxReport(tree_path=tree_path, node_count=len(nodes))
    if not nodes:
        report.errors.append("树中没有节点")
        return report

    _check_picker(nodes, report)
    _check_landmarks(payload, nodes, report)
    _check_tools(payload, nodes, report)
    _check_reaction_variants(nodes, report)
    _check_presentation(nodes, report)
    return report


def _check_picker(nodes: Dict[str, Dict[str, Any]], report: SandboxReport) -> None:
    """检查 picker hub。"""
    report.picker_nodes = sorted(
        node_id for node_id, node in nodes.items() if node.get("_is_map_picker")
    )
    if not report.picker_nodes:
        report.errors.append("缺少 _is_map_picker=true 的 picker hub")


def _check_landmarks(
    payload: Dict[str, Any],
    nodes: Dict[str, Dict[str, Any]],
    report: SandboxReport,
) -> None:
    """检查 landmark_map 网状地标。"""
    landmark_map = payload.get("landmark_map") or []
    if not isinstance(landmark_map, list):
        report.errors.append("landmark_map 必须是数组")
        return

    report.landmark_count = len(landmark_map)
    if report.landmark_count < 4:
        report.errors.append(f"地标数量不足: {report.landmark_count}/4")

    by_id: Dict[str, Dict[str, Any]] = {}
    for item in landmark_map:
        if not isinstance(item, dict):
            report.errors.append("landmark_map 含非对象条目")
            continue
        landmark_id = item.get("id")
        node_id = item.get("node_id")
        if not isinstance(landmark_id, str) or not landmark_id:
            report.errors.append("landmark_map 条目缺少 id")
            continue
        by_id[landmark_id] = item
        if not isinstance(node_id, str) or node_id not in nodes:
            report.errors.append(f"地标 {landmark_id} 指向不存在节点: {node_id}")

    for landmark_id, item in by_id.items():
        connections = item.get("connections") or []
        if not connections:
            report.errors.append(f"地标 {landmark_id} 缺少 connections 邻边")
            continue
        for target in connections:
            if target not in by_id:
                report.errors.append(f"地标 {landmark_id} 连接不存在地标: {target}")


def _check_tools(
    payload: Dict[str, Any],
    nodes: Dict[str, Dict[str, Any]],
    report: SandboxReport,
) -> None:
    """检查工具节点和 stay 自循环。"""
    tool_nodes = {node_id for node_id, node in nodes.items() if node.get("_is_tool")}
    tools_meta = payload.get("tools") or {}
    if isinstance(tools_meta, dict):
        for tool_id, meta in tools_meta.items():
            if not isinstance(meta, dict):
                report.errors.append(f"tools.{tool_id} 必须是对象")
                continue
            node_id = meta.get("node_id")
            if isinstance(node_id, str) and node_id in nodes:
                tool_nodes.add(node_id)
            else:
                report.errors.append(f"tools.{tool_id}.node_id 指向不存在节点: {node_id}")

    report.tool_nodes = sorted(tool_nodes)
    if len(report.tool_nodes) < 2:
        report.errors.append(f"工具节点数量不足: {len(report.tool_nodes)}/2")

    stay_loop_nodes: Set[str] = set()
    for node_id in tool_nodes:
        node = nodes.get(node_id) or {}
        for choice in choices_of(node):
            effects = choice.get("effects") or {}
            if not isinstance(effects, dict) or not effects.get("stay"):
                continue
            if node_id in choice_targets(choice):
                stay_loop_nodes.add(node_id)
    report.stay_loop_nodes = sorted(stay_loop_nodes)
    if not report.stay_loop_nodes:
        report.errors.append("缺少 effects.stay=true 且 next 指回自身的工具自循环")


def _check_reaction_variants(
    nodes: Dict[str, Dict[str, Any]],
    report: SandboxReport,
) -> None:
    """检查至少一个 variant 使用反应 clause。"""
    reaction_nodes: Set[str] = set()
    for node_id, node in nodes.items():
        for variant in _iter_variants(node):
            cond = variant.get("if") or {}
            if _contains_reaction_clause(cond):
                reaction_nodes.add(node_id)
    report.reaction_variant_nodes = sorted(reaction_nodes)
    if not report.reaction_variant_nodes:
        report.errors.append("缺少使用 deduction/foreshadow/theme/ending_seen 的反应式 variant")


def _iter_variants(node: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """遍历 narrative_variants 和 choice.next_variants。"""
    for variant in node.get("narrative_variants") or []:
        if isinstance(variant, dict):
            yield variant
    for choice in choices_of(node):
        for variant in choice.get("next_variants") or []:
            if isinstance(variant, dict):
                yield variant


def _contains_reaction_clause(clause: Any) -> bool:
    """递归判断条件里是否含 ADR-010 反应 clause。"""
    if not isinstance(clause, dict):
        return False
    if any(key in clause for key in REACTION_KEYS):
        return True
    for key in ("all_of", "any_of"):
        items = clause.get(key) or []
        if isinstance(items, list) and any(_contains_reaction_clause(item) for item in items):
            return True
    return _contains_reaction_clause(clause.get("not"))


def _check_presentation(nodes: Dict[str, Dict[str, Any]], report: SandboxReport) -> None:
    """统计 presentation 覆盖率。

    presentation 红线由 audit_playability 负责,这里仅保留计数,避免工具职责打架。
    """
    report.presentation_nodes = sum(
        1 for node in nodes.values() if isinstance(node.get("presentation"), dict)
    )


def render_report(report: SandboxReport) -> str:
    """渲染人类可读报告。"""
    lines = [
        "════════ ADR-010 沙盒骨架审计 ════════",
        f"节点: {report.node_count}",
        f"picker hub: {len(report.picker_nodes)}",
        f"地标: {report.landmark_count}",
        f"工具节点: {len(report.tool_nodes)}",
        f"stay 自循环工具: {len(report.stay_loop_nodes)}",
        f"反应 variant 节点: {len(report.reaction_variant_nodes)}",
        f"演出节点: {report.presentation_nodes}/{report.node_count}",
        "",
    ]
    if report.errors:
        lines.append("错误:")
        lines.extend(f"  ❌ {item}" for item in report.errors)
    if report.warnings:
        if report.errors:
            lines.append("")
        lines.append("警告:")
        lines.extend(f"  ⚠️  {item}" for item in report.warnings)
    if not report.errors and not report.warnings:
        lines.append("无错误 / 无警告")
    lines.append("")
    lines.append("结果: " + ("通过" if report.ok else "失败"))
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="审计 GameTree v1 是否符合 ADR-010 沙盒骨架")
    parser.add_argument("tree_json", help="故事树 JSON 路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args(argv)

    path = Path(args.tree_json)
    report = analyze_sandbox(load_payload(path), tree_path=str(path))
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
