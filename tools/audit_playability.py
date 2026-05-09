#!/usr/bin/env python3
"""GameTree 可玩性审计。

这个工具只做一件事:判断一棵故事树有没有基本可玩闭环。
它同时兼容旧预生成树和 v7 沙盒树:

- 旧树:顶层就是 node_id -> node
- v7 树:顶层包含 nodes / start_node / landmark_map

注意:本工具不替代 `audit_tree.py` / `path_explorer.py`。它负责更靠前的红线:
坏跳转、非结局死路、动态 picker 目标缺失、结局识别缺口。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


@dataclass
class PlayabilityReport:
    """可玩性审计结果。"""

    total_nodes: int = 0
    start_node: str = ""
    extra_start_nodes: List[str] = field(default_factory=list)
    reachable_nodes: int = 0
    ending_nodes: int = 0
    dynamic_picker_nodes: int = 0
    presentation_nodes: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "total_nodes": self.total_nodes,
            "start_node": self.start_node,
            "extra_start_nodes": self.extra_start_nodes,
            "reachable_nodes": self.reachable_nodes,
            "ending_nodes": self.ending_nodes,
            "dynamic_picker_nodes": self.dynamic_picker_nodes,
            "presentation_nodes": self.presentation_nodes,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def load_payload(path: Path) -> Dict[str, Any]:
    """读取 JSON 文件。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"树文件顶层必须是对象: {path}")
    return data


def node_map(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """抽取节点表,兼容 v7 `nodes` 子树和旧预生成树。"""
    raw_nodes = payload.get("nodes")
    if isinstance(raw_nodes, dict):
        return {str(k): v for k, v in raw_nodes.items() if isinstance(v, dict)}
    return {str(k): v for k, v in payload.items() if isinstance(v, dict)}


def start_node_id(payload: Dict[str, Any], nodes: Dict[str, Dict[str, Any]]) -> str:
    """确定起点。"""
    start = payload.get("start_node")
    if isinstance(start, str) and start:
        return start
    if "root" in nodes:
        return "root"
    if "n_intro" in nodes:
        return "n_intro"
    return next(iter(nodes.keys()), "")


def character_start_nodes(payload: Dict[str, Any]) -> List[str]:
    """抽取多角色周目的起点。"""
    starts: List[str] = []
    characters = payload.get("characters") or {}
    if not isinstance(characters, dict):
        return starts
    for meta in characters.values():
        if not isinstance(meta, dict):
            continue
        start = meta.get("start_node")
        if isinstance(start, str) and start:
            starts.append(start)
    return starts


def choices_of(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """取静态 choices。"""
    choices = node.get("choices") or []
    if not isinstance(choices, list):
        return []
    return [c for c in choices if isinstance(c, dict)]


def choice_targets(choice: Dict[str, Any]) -> List[str]:
    """抽取一个 choice 的所有可能目标。"""
    targets: List[str] = []
    for key in ("next_node_id", "next"):
        value = choice.get(key)
        if isinstance(value, str) and value:
            targets.append(value)

    variants = choice.get("next_variants") or []
    if isinstance(variants, list):
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            nxt = variant.get("next")
            if isinstance(nxt, str) and nxt:
                targets.append(nxt)
    return targets


def is_dynamic_picker(node: Dict[str, Any]) -> bool:
    """v7 沙盒地图 picker 由运行时根据 landmark_map 生成 choices。"""
    return bool(node.get("_is_map_picker"))


def is_ending_node(node: Dict[str, Any]) -> bool:
    """识别结局节点。

    新数据必须写 `is_ending: true`。`ending_type + 空 choices` 只是历史兼容,
    用 warning 提醒作者补显式字段。
    """
    if bool(node.get("is_ending")):
        return True
    if node.get("ending_type") and not choices_of(node):
        return True
    return False


KEY_PRESENTATION_INTENT_NODES: Set[str] = {
    "n_intro",
    "n_briefing",
    "n_landmark_picker",
    "n_npc_red_dress_girl",
    "n_npc_forum_lurkers",
    "n_npc_evaluator_chair",
    "n_npc_eight_self",
    "n_npc_cleaner_null",
    "n_scene_b3_corridor",
    "n_scene_evaluator_room",
    "n_scene_lost_archive",
    "n_scene_morning_lakeside",
    "n_scene_red_telephone",
    "n_end_true",
    "n_end_truth",
    "n_end_data",
    "n_end_broadcast",
    "n_end_bad_1987",
    "n_end_bad_drown",
    "n_end_neutral",
    "n_end_hidden",
}


def landmark_targets(payload: Dict[str, Any], report: PlayabilityReport) -> Set[str]:
    """抽取 `landmark_map` 中的动态目标,并检查地标连接。"""
    targets: Set[str] = set()
    landmark_map = payload.get("landmark_map") or []
    if not isinstance(landmark_map, list):
        return targets

    by_id: Dict[str, Dict[str, Any]] = {}
    for item in landmark_map:
        if not isinstance(item, dict):
            continue
        lid = item.get("id")
        node_id = item.get("node_id")
        if isinstance(lid, str) and lid:
            by_id[lid] = item
        if isinstance(node_id, str) and node_id:
            targets.add(node_id)

    for lid, item in by_id.items():
        for conn in item.get("connections") or []:
            if conn not in by_id:
                report.errors.append(f"landmark_map.{lid}.connections 指向不存在地标: {conn}")

    return targets


def dynamic_targets_for_node(
    payload: Dict[str, Any],
    node: Dict[str, Any],
    report: PlayabilityReport,
) -> Set[str]:
    """抽取动态节点的可能目标。"""
    targets: Set[str] = set()
    if is_dynamic_picker(node):
        targets.update(landmark_targets(payload, report))
        extra = node.get("_picker_endshift_choice")
        if isinstance(extra, dict):
            targets.update(choice_targets(extra))
    return targets


def build_edges(
    payload: Dict[str, Any],
    nodes: Dict[str, Dict[str, Any]],
    report: PlayabilityReport,
) -> Dict[str, Set[str]]:
    """构建静态 + 动态边集合。"""
    edges: Dict[str, Set[str]] = {nid: set() for nid in nodes}
    node_ids = set(nodes.keys())
    declared_endings = set((payload.get("endings") or {}).keys()) if isinstance(payload.get("endings"), dict) else set()
    implemented_endings: Set[str] = set()

    for nid, node in nodes.items():
        if is_dynamic_picker(node):
            report.dynamic_picker_nodes += 1

        if bool(node.get("ending_type")) and not bool(node.get("is_ending")):
            report.warnings.append(f"{nid}: 有 ending_type 但缺少 is_ending=true")

        if is_ending_node(node):
            report.ending_nodes += 1
            ending_type = str(node.get("ending_type") or "")
            if ending_type:
                implemented_endings.add(ending_type)
                if declared_endings and ending_type not in declared_endings:
                    report.warnings.append(f"{nid}: ending_type 未在顶层 endings 注册: {ending_type}")
            if choices_of(node):
                report.warnings.append(f"{nid}: 结局节点仍有 choices,请确认是否故意")
            continue

        static_choices = choices_of(node)
        dynamic_targets = dynamic_targets_for_node(payload, node, report)

        if not static_choices and not dynamic_targets:
            report.errors.append(f"{nid}: 非结局节点没有 choices,也不是动态 picker")

        for choice in static_choices:
            targets = choice_targets(choice)
            label = choice.get("choice_id") or choice.get("text") or choice.get("choice_text") or "(无文本)"
            if not targets:
                report.errors.append(f"{nid}: choice 缺少 next/next_node_id/next_variants 目标: {label}")
                continue
            for target in targets:
                if target not in node_ids:
                    report.errors.append(f"{nid}: choice 指向不存在节点 {target}: {label}")
                else:
                    edges[nid].add(target)

        for target in dynamic_targets:
            if target not in node_ids:
                report.errors.append(f"{nid}: 动态 picker 指向不存在节点 {target}")
            else:
                edges[nid].add(target)

    for ending_type in sorted(declared_endings - implemented_endings):
        report.warnings.append(f"顶层 endings 注册但未被任何节点实现: {ending_type}")

    return edges


def validate_presentation(
    payload: Dict[str, Any],
    nodes: Dict[str, Dict[str, Any]],
    report: PlayabilityReport,
) -> None:
    """检查 VN 演出字段是否引用有效资产。"""
    assets = payload.get("assets") or {}
    if not isinstance(assets, dict):
        assets = {}
    backgrounds = set((assets.get("backgrounds") or {}).keys())
    bgm = set((assets.get("bgm") or {}).keys())
    sfx = set((assets.get("sfx") or {}).keys())
    sprites = set((assets.get("sprites") or {}).keys())

    has_v7_shape = isinstance(payload.get("nodes"), dict)
    if has_v7_shape and not assets:
        report.warnings.append("缺少顶层 assets manifest; VN 演出只能退回纯文本")

    for nid, node in nodes.items():
        presentation = node.get("presentation")
        if not presentation:
            if has_v7_shape:
                report.warnings.append(f"{nid}: 缺少 presentation; VN 演出无法定位场景素材")
            continue
        if not isinstance(presentation, dict):
            report.errors.append(f"{nid}: presentation 必须是对象")
            continue

        report.presentation_nodes += 1

        background = presentation.get("background")
        if background and backgrounds and background not in backgrounds:
            report.errors.append(f"{nid}: presentation.background 引用不存在资产: {background}")

        music = presentation.get("bgm")
        if music and bgm and music not in bgm:
            report.errors.append(f"{nid}: presentation.bgm 引用不存在资产: {music}")

        sprite = presentation.get("sprite")
        if sprite and sprites and sprite not in sprites:
            report.errors.append(f"{nid}: presentation.sprite 引用不存在资产: {sprite}")

        for item in presentation.get("sfx") or []:
            if item and sfx and item not in sfx:
                report.errors.append(f"{nid}: presentation.sfx 引用不存在资产: {item}")

        if has_v7_shape and nid in KEY_PRESENTATION_INTENT_NODES:
            missing_intent = [
                field_name
                for field_name in ("camera", "cg_intent", "transition_intent")
                if not presentation.get(field_name)
            ]
            if missing_intent:
                report.warnings.append(
                    f"{nid}: 关键演出意图缺少字段: {', '.join(missing_intent)}"
                )


def reachable_from(start: str, edges: Dict[str, Set[str]]) -> Set[str]:
    """从起点按边遍历可达节点。"""
    if not start or start not in edges:
        return set()
    seen: Set[str] = set()
    stack = [start]
    while stack:
        nid = stack.pop()
        if nid in seen:
            continue
        seen.add(nid)
        stack.extend(sorted(edges.get(nid, set()) - seen))
    return seen


def reachable_from_many(starts: Iterable[str], edges: Dict[str, Set[str]]) -> Set[str]:
    """从多个角色起点合并遍历。"""
    seen: Set[str] = set()
    for start in starts:
        seen.update(reachable_from(start, edges))
    return seen


def analyze_playability(payload: Dict[str, Any]) -> PlayabilityReport:
    """生成可玩性报告。"""
    nodes = node_map(payload)
    report = PlayabilityReport(total_nodes=len(nodes))
    if not nodes:
        report.errors.append("树中没有节点")
        return report

    start = start_node_id(payload, nodes)
    report.start_node = start
    extra_starts = sorted(set(character_start_nodes(payload)) - {start})
    report.extra_start_nodes = extra_starts
    if not start:
        report.errors.append("无法确定 start_node")
    elif start not in nodes:
        report.errors.append(f"start_node 不存在: {start}")
    for extra_start in extra_starts:
        if extra_start not in nodes:
            report.errors.append(f"characters.start_node 不存在: {extra_start}")

    edges = build_edges(payload, nodes, report)
    validate_presentation(payload, nodes, report)
    reachable = reachable_from_many([start, *extra_starts], edges)
    report.reachable_nodes = len(reachable)

    unreachable = sorted(set(nodes.keys()) - reachable)
    for nid in unreachable:
        report.warnings.append(f"{nid}: 从 start_node 不可达")

    return report


def render_report(report: PlayabilityReport) -> str:
    """渲染人类可读报告。"""
    lines = [
        "════════ GameTree 可玩性审计 ════════",
        f"节点: {report.total_nodes}",
        f"起点: {report.start_node or '(缺失)'}",
        f"额外角色起点: {', '.join(report.extra_start_nodes) if report.extra_start_nodes else '(无)'}",
        f"可达: {report.reachable_nodes}/{report.total_nodes}",
        f"结局节点: {report.ending_nodes}",
        f"动态 picker: {report.dynamic_picker_nodes}",
        f"演出节点: {report.presentation_nodes}/{report.total_nodes}",
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="审计 GameTree 是否具备基本可玩闭环")
    parser.add_argument("tree_json", help="故事树 JSON 路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args(argv)

    payload = load_payload(Path(args.tree_json))
    report = analyze_playability(payload)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
