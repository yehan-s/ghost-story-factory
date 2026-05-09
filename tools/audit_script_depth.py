#!/usr/bin/env python3
"""Pass 9 剧本深度 / 广度审计。

ADR-010 只证明“这是一棵沙盒树”。本工具检查它是否开始像一部
有厚度的视觉小说:角色线入口、最短结局路径、关键演出意图、跨线回声。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
for path in (ROOT_DIR, ROOT_DIR / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tools.audit_playability import choices_of, choice_targets, load_payload, node_map
from ghost_story_factory.v5.player import State, resolve_narrative


LINMOU_LANDMARKS = {
    "n_l1985_abacus_01",
    "n_l1985_boiler_01",
    "n_l1985_archive_01",
    "n_l1985_pavilion_01",
}

G273_BIOGRAPHY_AUDIT_NODES = [
    "n_npc_predecessor_voice",
    "n_scene_lost_archive",
    "n_lore_leifeng_worm",
    "n_lore_songmuchang_inn",
    "n_lore_zheda_clock_girl",
    "n_lore_wulinmen_execution",
    "n_lore_kongque_collapse",
]

G273_OLD_BIOGRAPHY_TERMS = [
    "你媳妇",
    "你儿子",
    "你今年 51",
    "做夜班保安第 14 年",
    "你按了 14 年",
    "你 1985 年从二轻物资",
    "你父亲",
    "你妈临死",
    "2014 年自己扫",
    "2010 年接",
    "一个月工资是 38 块",
    "1987 年坐 K6",
]


@dataclass
class ScriptDepthReport:
    """剧本厚度审计报告。"""

    tree_path: str = ""
    node_count: int = 0
    ending_count: int = 0
    intent_nodes: int = 0
    thin_nodes: List[str] = field(default_factory=list)
    linmou_start: str = ""
    linmou_reachable_nodes: int = 0
    linmou_shortest_ending_path: int = 0
    linmou_landmark_variant_nodes: List[str] = field(default_factory=list)
    linmou_endings: List[str] = field(default_factory=list)
    g273_linmou_echo_nodes: List[str] = field(default_factory=list)
    ending_gate_violations: List[str] = field(default_factory=list)
    one_way_violations: List[str] = field(default_factory=list)
    protagonist_biography_violations: List[str] = field(default_factory=list)
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
            "ending_count": self.ending_count,
            "intent_nodes": self.intent_nodes,
            "thin_nodes": self.thin_nodes,
            "linmou_start": self.linmou_start,
            "linmou_reachable_nodes": self.linmou_reachable_nodes,
            "linmou_shortest_ending_path": self.linmou_shortest_ending_path,
            "linmou_landmark_variant_nodes": self.linmou_landmark_variant_nodes,
            "linmou_endings": self.linmou_endings,
            "g273_linmou_echo_nodes": self.g273_linmou_echo_nodes,
            "ending_gate_violations": self.ending_gate_violations,
            "one_way_violations": self.one_way_violations,
            "protagonist_biography_violations": self.protagonist_biography_violations,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def analyze_script_depth(
    payload: Dict[str, Any],
    tree_path: str = "",
    *,
    min_nodes: int = 160,
    min_intent_nodes: int = 30,
    min_linmou_path: int = 5,
    min_g273_echo_nodes: int = 3,
) -> ScriptDepthReport:
    """审计正式剧本是否达到 Pass 9 的最低厚度。"""
    nodes = node_map(payload)
    report = ScriptDepthReport(tree_path=tree_path, node_count=len(nodes))
    report.ending_count = sum(1 for node in nodes.values() if node.get("is_ending"))
    report.intent_nodes = _count_intent_nodes(nodes)
    report.thin_nodes = _find_thin_nodes(nodes)

    if report.node_count < min_nodes:
        report.errors.append(f"正式树节点数不足: {report.node_count}/{min_nodes}")
    if report.intent_nodes < min_intent_nodes:
        report.errors.append(
            f"关键演出意图节点不足: {report.intent_nodes}/{min_intent_nodes}"
        )

    _check_linmou(payload, nodes, report, min_linmou_path)
    _check_g273_echo(nodes, report, min_g273_echo_nodes)
    _check_morning_lakeside_ending_gates(nodes, report)
    _check_one_way_contract(nodes, report)
    _check_g273_protagonist_biography(nodes, report)

    if len(report.thin_nodes) > 80:
        report.warnings.append(
            f"薄节点仍偏多: {len(report.thin_nodes)} 个。Pass 9 先报告,后续可继续压缩。"
        )
    return report


def _count_intent_nodes(nodes: Dict[str, Dict[str, Any]]) -> int:
    """统计具备镜头/CG/转场意图的节点数。"""
    count = 0
    for node in nodes.values():
        presentation = node.get("presentation") or {}
        if not isinstance(presentation, dict):
            continue
        if all(str(presentation.get(key) or "").strip() for key in (
            "camera",
            "cg_intent",
            "transition_intent",
        )):
            count += 1
    return count


def _find_thin_nodes(nodes: Dict[str, Dict[str, Any]]) -> List[str]:
    """找出可能像剧情跳板的节点。"""
    thin: List[str] = []
    for node_id, node in nodes.items():
        if node.get("is_ending") or node.get("_is_map_picker"):
            continue
        narrative = str(node.get("narrative") or "")
        choice_count = len(choices_of(node))
        variant_count = len(node.get("narrative_variants") or [])
        if choice_count <= 1 and len(narrative) < 220:
            thin.append(node_id)
        elif not variant_count and len(narrative) < 180:
            thin.append(node_id)
    return sorted(thin)


def _check_linmou(
    payload: Dict[str, Any],
    nodes: Dict[str, Dict[str, Any]],
    report: ScriptDepthReport,
    min_linmou_path: int,
) -> None:
    """检查林某线是否从注册角色变成可玩的前传线。"""
    characters = payload.get("characters") or {}
    linmou = characters.get("linmou_1985") if isinstance(characters, dict) else None
    if not isinstance(linmou, dict):
        report.errors.append("characters 缺少 linmou_1985")
        return

    start = linmou.get("start_node")
    report.linmou_start = start if isinstance(start, str) else ""
    if not report.linmou_start or report.linmou_start not in nodes:
        report.errors.append(f"linmou_1985.start_node 不存在: {report.linmou_start}")
        return

    reachable, shortest = _bfs_from_start(nodes, report.linmou_start)
    report.linmou_reachable_nodes = len(reachable)
    report.linmou_shortest_ending_path = shortest or 0
    report.linmou_endings = sorted(
        node_id for node_id in reachable if str(node_id).startswith("E_LINMOU_")
    )

    if len(report.linmou_endings) < 4:
        report.errors.append(f"林某结局不足: {len(report.linmou_endings)}/4")
    if not shortest or shortest < min_linmou_path:
        report.errors.append(
            f"林某线最短结局路径过短: {shortest or 0}/{min_linmou_path}"
        )

    report.linmou_landmark_variant_nodes = sorted(
        node_id
        for node_id in LINMOU_LANDMARKS
        if _has_variants(nodes.get(node_id) or {})
    )
    missing = sorted(LINMOU_LANDMARKS - set(report.linmou_landmark_variant_nodes))
    if missing:
        report.errors.append("林某地标缺少复访/回收 variant: " + ", ".join(missing))


def _check_g273_echo(
    nodes: Dict[str, Dict[str, Any]],
    report: ScriptDepthReport,
    min_g273_echo_nodes: int,
) -> None:
    """检查 G-273 主线是否能读到林某线造成的回声。"""
    echo_nodes: Set[str] = set()
    for node_id, node in nodes.items():
        if node_id.startswith("n_l1985_") or node_id.startswith("E_LINMOU_"):
            continue
        for variant in _iter_variants(node):
            cond = variant.get("if") or {}
            text = json.dumps(cond, ensure_ascii=False)
            if "E_LINMOU_" in text or '"l_' in text:
                echo_nodes.add(node_id)
    report.g273_linmou_echo_nodes = sorted(echo_nodes)
    if len(report.g273_linmou_echo_nodes) < min_g273_echo_nodes:
        report.errors.append(
            f"G-273 读取林某线回声的节点不足: "
            f"{len(report.g273_linmou_echo_nodes)}/{min_g273_echo_nodes}"
        )


def _check_morning_lakeside_ending_gates(
    nodes: Dict[str, Dict[str, Any]],
    report: ScriptDepthReport,
) -> None:
    """检查晨湖终局入口不能退回菜单式自选。

    这里锁的是剧本品味红线:高阶结局必须读取本轮行为账本。True / Truth /
    Broadcast / Data / Hidden 不能只靠一行文案伪装成结算。
    """
    node = nodes.get("n_scene_morning_lakeside") or {}
    if not node:
        report.errors.append("缺少晨湖终局节点: n_scene_morning_lakeside")
        return

    requirements = {
        "n_end_true": [
            ("inv_has", "⺶ 符文"),
            ("inv_has", "林副科长账本残页"),
            ("flag", "arc.seven_returned"),
            ("flag", "arc.named_the_dead"),
            ("flag", "know.claimed_linmou"),
            ("shifts_completed_min", None),
        ],
        "n_end_truth": [
            ("puzzle_pieces_min", None),
            ("flag", "arc.all_archives_photoed"),
            ("flag", "arc.named_the_dead"),
        ],
        "n_end_broadcast": [
            ("flag", "oneshot.posted_photo"),
            ("flag", "oneshot.live_streaming"),
            ("PR_min", None),
        ],
        "n_end_data": [
            ("flag", "oneshot.chose_data"),
            ("flag", "know.saw_8_zhao"),
            ("inv_has", "工牌 G-273"),
        ],
        "n_end_hidden": [
            ("flag", "arc.became_judge"),
            ("flag", "arc.got_judge_seal"),
        ],
    }
    low_route_targets = {
        "n_end_bad_1987",
        "n_end_bad_drown",
    }

    for idx, choice in enumerate(choices_of(node), start=1):
        target = choice.get("next")
        if target not in requirements and target not in low_route_targets:
            continue
        require = choice.get("require")
        if not isinstance(require, dict) or not require:
            report.ending_gate_violations.append(
                f"n_scene_morning_lakeside choices[{idx}] -> {target} 缺少 require"
            )
            continue
        if _require_contains(require, "ending_seen", None):
            # 跨周目入口已经由通关历史锁住,不强套本轮基础结局门槛。
            continue
        for kind, value in requirements.get(target, []):
            if not _require_contains(require, kind, value):
                report.ending_gate_violations.append(
                    f"n_scene_morning_lakeside choices[{idx}] -> {target} "
                    f"缺少门槛 {kind}:{value or '*'}"
                )

    if report.ending_gate_violations:
        report.errors.extend(report.ending_gate_violations)


def _check_one_way_contract(
    nodes: Dict[str, Dict[str, Any]],
    report: ScriptDepthReport,
) -> None:
    """检查 `_one_way` 节点不要偷偷返回地图。"""
    for node_id, node in nodes.items():
        if not node.get("_one_way"):
            continue
        for idx, choice in enumerate(choices_of(node), start=1):
            if choice.get("breaks_one_way"):
                continue
            targets = set(choice_targets(choice))
            if "n_landmark_picker" in targets:
                report.one_way_violations.append(
                    f"{node_id} choices[{idx}] 在 _one_way 节点返回 n_landmark_picker"
                )
    if report.one_way_violations:
        report.errors.extend(report.one_way_violations)


def _check_g273_protagonist_biography(
    nodes: Dict[str, Dict[str, Any]],
    report: ScriptDepthReport,
) -> None:
    """检查 G-273 首访文本不能泄漏旧版中年老保安设定。"""
    state = State({"character": "G-273"})
    for node_id in G273_BIOGRAPHY_AUDIT_NODES:
        node = nodes.get(node_id)
        if not node:
            continue
        text = resolve_narrative(node, state)
        leaks = [term for term in G273_OLD_BIOGRAPHY_TERMS if term in text]
        if leaks:
            report.protagonist_biography_violations.append(
                f"{node_id} 混入旧主角履历: {', '.join(leaks)}"
            )
    if report.protagonist_biography_violations:
        report.errors.extend(report.protagonist_biography_violations)


def _require_contains(require: Dict[str, Any], kind: str, value: Optional[str]) -> bool:
    """递归查找 require 是否包含指定门槛。"""
    if not isinstance(require, dict):
        return False
    if kind == "flag" and value:
        flags = require.get("flags") or {}
        if isinstance(flags, dict) and bool(flags.get(value)):
            return True
    elif kind == "inv_has" and value:
        if value in (require.get("inv_has") or []):
            return True
    elif kind in {"puzzle_pieces_min", "PR_min", "shifts_completed_min"}:
        if kind in require:
            return True
    elif kind == "ending_seen":
        if "ending_seen" in require:
            return True

    for key in ("all_of", "any_of"):
        for sub in require.get(key) or []:
            if _require_contains(sub, kind, value):
                return True
    if isinstance(require.get("not"), dict):
        return _require_contains(require["not"], kind, value)
    return False


def _bfs_from_start(
    nodes: Dict[str, Dict[str, Any]],
    start: str,
) -> Tuple[Set[str], Optional[int]]:
    """静态 BFS,返回可达节点和最短结局边数。"""
    visited: Set[str] = {start}
    queue: deque[Tuple[str, int]] = deque([(start, 0)])
    shortest: Optional[int] = None

    while queue:
        node_id, depth = queue.popleft()
        node = nodes[node_id]
        if node.get("is_ending"):
            shortest = depth if shortest is None else min(shortest, depth)
            continue
        for target in _targets_for_node(node):
            if target not in nodes or target in visited:
                continue
            visited.add(target)
            queue.append((target, depth + 1))
    return visited, shortest


def _targets_for_node(node: Dict[str, Any]) -> Iterable[str]:
    """抽取静态目标。"""
    for choice in choices_of(node):
        for target in choice_targets(choice):
            yield target
    extra = node.get("_picker_endshift_choice")
    if isinstance(extra, dict):
        for target in choice_targets(extra):
            yield target


def _has_variants(node: Dict[str, Any]) -> bool:
    """节点是否有叙事或选择变体。"""
    return bool(list(_iter_variants(node)))


def _iter_variants(node: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """遍历叙事变体和 choice next 变体。"""
    for variant in node.get("narrative_variants") or []:
        if isinstance(variant, dict):
            yield variant
    for choice in choices_of(node):
        for variant in choice.get("next_variants") or []:
            if isinstance(variant, dict):
                yield variant


def render_report(report: ScriptDepthReport) -> str:
    """渲染人类可读报告。"""
    lines = [
        "════════ Pass 9 剧本深度 / 广度审计 ════════",
        f"节点: {report.node_count}",
        f"结局: {report.ending_count}",
        f"演出意图节点: {report.intent_nodes}",
        f"薄节点: {len(report.thin_nodes)}",
        f"林某入口: {report.linmou_start or '(缺失)'}",
        f"林某可达节点: {report.linmou_reachable_nodes}",
        f"林某最短结局路径: {report.linmou_shortest_ending_path}",
        f"林某地标 variant: {len(report.linmou_landmark_variant_nodes)}/4",
        f"林某结局: {len(report.linmou_endings)}",
        f"G-273 林某回声节点: {len(report.g273_linmou_echo_nodes)}",
        f"终局门槛违规: {len(report.ending_gate_violations)}",
        f"单行路违规: {len(report.one_way_violations)}",
        f"主角履历违规: {len(report.protagonist_biography_violations)}",
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
    parser = argparse.ArgumentParser(description="审计正式剧本深度和广度")
    parser.add_argument("tree_json", help="故事树 JSON 路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args(argv)

    path = Path(args.tree_json)
    report = analyze_script_depth(load_payload(path), tree_path=str(path))
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
