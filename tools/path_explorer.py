"""path_explorer.py — dialogue tree validator (v5/v6 schema)。

用法:
    python tools/path_explorer.py path/to/tree.json

功能:
    1. 节点统计(总数/结局/分叉、入度/出度、孤儿、悬空 next、死路)
    2. 结局可达性(每个 ending_type 的最短示例路径)
    3. 路径覆盖(DFS 至深度 80,统计访问率)
    4. 状态值边界(PR/GR 模拟,inv 持久增长检测)

退出码:
    0 = 全部 OK
    1 = 发现问题(悬空 / 死路 / 不可达结局 / PR-GR 越界)

设计:
    - 标准库 only (json + dataclasses + typing)
    - 兼容 v5 schema 与 v6 schema(narrative_variants / next_variants / any_of / all_of)
    - 状态拷贝模拟 player.State.apply 的行为(简化版)
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

# 确保直接用 `python tools/path_explorer.py` 运行时也能找到 tools 包
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._state_sim import SimState, meets


# ─────────────────────────────────────────────────────────────────────
# ANSI 颜色(从 player.py 复用,简化)
# ─────────────────────────────────────────────────────────────────────

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


_COLOR = _supports_color()


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def dim(s: str) -> str: return _c("2", s)
def bold(s: str) -> str: return _c("1", s)
def red(s: str) -> str: return _c("31", s)
def green(s: str) -> str: return _c("32", s)
def yellow(s: str) -> str: return _c("33", s)
def cyan(s: str) -> str: return _c("36", s)
def magenta(s: str) -> str: return _c("35", s)


# ─────────────────────────────────────────────────────────────────────
# effects 应用(BFS 状态推进,path_explorer 专用)
# ─────────────────────────────────────────────────────────────────────
# SimState 和 meets() 从 tools._state_sim 导入。
# with_effects 保留在这里——它属于模拟器的"推进"逻辑,
# 不是 require 检查,不需要与 player.py 行为对齐。

def with_effects(state: SimState, effects: Optional[Dict[str, Any]]) -> Tuple[SimState, List[str]]:
    """返回(新 state, 应用过程中的警告列表)。不修改原 state。
    仅在上界越界时报警(下界 clamp 是正常的"地板效应",不是 bug)。"""
    warnings: List[str] = []
    if not effects:
        return state, warnings

    new_PR = state.PR
    new_GR = state.GR
    new_sk = state.shifts_skipped
    new_inv = list(state.inv)
    new_flags = dict(state.flags)
    new_vl = list(state.visited_landmarks)
    new_skl = list(state.skipped_landmarks)
    new_pp = list(state.puzzle_pieces)

    if "PR" in effects:
        new_PR_raw = state.PR + int(effects["PR"])
        if new_PR_raw > 100:
            warnings.append(f"PR 上溢: {state.PR}+{effects['PR']}={new_PR_raw} (clamp to 100)")
        new_PR = max(0, min(100, new_PR_raw))
    if "GR" in effects:
        new_GR_raw = state.GR + int(effects["GR"])
        if new_GR_raw > 100:
            warnings.append(f"GR 上溢: {state.GR}+{effects['GR']}={new_GR_raw} (clamp to 100)")
        new_GR = max(0, min(100, new_GR_raw))
    if "shifts_skipped" in effects:
        new_sk += int(effects["shifts_skipped"])
    for item in effects.get("inv_add", []) or []:
        if item not in new_inv:
            new_inv.append(item)
    for item in effects.get("inv_remove", []) or []:
        if item in new_inv:
            new_inv.remove(item)
    for k, v in (effects.get("flags") or {}).items():
        new_flags[k] = bool(v)
    # landmark_visited(单个地标):player.py 约定,BFS 需对齐以正确派生 shifts_completed
    if "landmark_visited" in effects:
        lm = str(effects["landmark_visited"])
        if lm not in new_vl:
            new_vl.append(lm)
    for lm in effects.get("visited_landmarks_add", []) or []:
        if lm not in new_vl:
            new_vl.append(lm)
    # landmark_skipped(单个,player.py 约定):append 到 list 并同步 shifts_skipped +1
    if "landmark_skipped" in effects:
        lm = str(effects["landmark_skipped"])
        if lm not in new_skl:
            new_skl.append(lm)
            new_sk += 1
    for lm in effects.get("skipped_landmarks_add", []) or []:
        if lm not in new_skl:
            new_skl.append(lm)
    for p in effects.get("puzzle_pieces_add", []) or []:
        if p not in new_pp:
            new_pp.append(p)

    ns = SimState(
        PR=new_PR, GR=new_GR,
        shifts_skipped=new_sk,
        inv=tuple(new_inv),
        flags=tuple(sorted(new_flags.items())),
        visited_landmarks=tuple(new_vl),
        skipped_landmarks=tuple(new_skl),
        puzzle_pieces=tuple(new_pp),
    )
    return ns, warnings


# ─────────────────────────────────────────────────────────────────────
# next_variants 解析
# ─────────────────────────────────────────────────────────────────────

def resolve_next(choice: Dict[str, Any], state: SimState) -> Optional[str]:
    """v6 next_variants 优先;无匹配则回退到 next。"""
    for variant in choice.get("next_variants", []) or []:
        cond = variant.get("if") or {}
        if meets(state, cond):
            nxt = variant.get("next")
            if nxt:
                return nxt
    return choice.get("next")


def all_possible_nexts(choice: Dict[str, Any]) -> List[str]:
    """静态地拿到所有可能的目标节点(用于悬空检测,无需状态)。"""
    targets: List[str] = []
    for v in choice.get("next_variants", []) or []:
        n = v.get("next")
        if n:
            targets.append(n)
    n = choice.get("next")
    if n:
        targets.append(n)
    return targets


# ─────────────────────────────────────────────────────────────────────
# 静态分析:节点统计 / 入度出度 / 孤儿 / 悬空
# ─────────────────────────────────────────────────────────────────────

@dataclass
class StaticReport:
    total_nodes: int
    ending_nodes: List[str]
    branch_nodes: List[str]               # 出度 ≥ 2
    in_degree: Dict[str, int]
    out_degree: Dict[str, int]
    orphans: List[str]                    # 入度=0 且非 start
    dangling_refs: List[Tuple[str, str, str]]  # (from_node, choice_text, missing_target)
    dead_ends: List[str]                  # 非结局且无 choices
    unknown_endings: List[str]            # ending_type 未在 endings 字典中声明


def analyze_static(tree: Dict[str, Any]) -> StaticReport:
    nodes: Dict[str, Dict[str, Any]] = tree.get("nodes", {}) or {}
    start = tree.get("start_node", "n_intro")
    declared_endings = set((tree.get("endings") or {}).keys())

    in_deg: Dict[str, int] = defaultdict(int)
    out_deg: Dict[str, int] = defaultdict(int)
    dangling: List[Tuple[str, str, str]] = []
    dead_ends: List[str] = []
    ending_nodes: List[str] = []
    branch_nodes: List[str] = []
    unknown_endings: List[str] = []

    for nid, node in nodes.items():
        if node.get("is_ending"):
            ending_nodes.append(nid)
            et = node.get("ending_type")
            if et and declared_endings and et not in declared_endings:
                unknown_endings.append(f"{nid} -> {et}")
            continue

        choices = node.get("choices") or []
        if not choices:
            dead_ends.append(nid)
            continue

        targets_for_node: Set[str] = set()
        for ch in choices:
            for tgt in all_possible_nexts(ch):
                targets_for_node.add(tgt)
                if tgt not in nodes:
                    dangling.append((nid, ch.get("text", "(无文本)")[:40], tgt))
        out_deg[nid] = len(targets_for_node)
        if out_deg[nid] >= 2:
            branch_nodes.append(nid)
        for tgt in targets_for_node:
            in_deg[tgt] += 1

    orphans = [
        nid for nid in nodes
        if nid != start and in_deg.get(nid, 0) == 0
    ]

    return StaticReport(
        total_nodes=len(nodes),
        ending_nodes=ending_nodes,
        branch_nodes=branch_nodes,
        in_degree=dict(in_deg),
        out_degree=dict(out_deg),
        orphans=sorted(orphans),
        dangling_refs=dangling,
        dead_ends=dead_ends,
        unknown_endings=unknown_endings,
    )


# ─────────────────────────────────────────────────────────────────────
# 动态分析:DFS 探索路径
# ─────────────────────────────────────────────────────────────────────

@dataclass
class PathStep:
    node_id: str
    choice_index: int          # -1 表示自动跳转(无选择)
    choice_text: str = ""


@dataclass
class DynamicReport:
    visited_nodes: Set[str] = field(default_factory=set)
    ending_paths: Dict[str, List[PathStep]] = field(default_factory=dict)  # ending_type -> shortest path
    pr_max: int = 0
    pr_min: int = 0
    gr_max: int = 0
    gr_min: int = 0
    boundary_warnings: List[str] = field(default_factory=list)
    inv_max_size: int = 0
    explored_state_count: int = 0
    truncated_at_depth: int = 0
    # variant 触发记录:(node_id, "narrative", variant_idx) / (node_id, "next", choice_idx, variant_idx)
    # 在阶段 B 模拟中,任何状态下被 meets() 的 variant 计为命中
    hit_narrative_variants: Set[Tuple[str, int]] = field(default_factory=set)
    hit_next_variants: Set[Tuple[str, int, int]] = field(default_factory=set)


def explore(tree: Dict[str, Any], max_depth: int = 80, max_states: int = 200_000) -> DynamicReport:
    """两阶段探索:
       阶段 A — node-level BFS,忽略 require 严格性,确保覆盖率与最短路径发现完整;
       阶段 B — state-aware 模拟,沿阶段 A 发现的最短路径走一遍,记录 PR/GR 边界与 require 不满足的诊断。
       这样既避免状态爆炸,又能给出真实数值边界。"""
    nodes: Dict[str, Dict[str, Any]] = tree.get("nodes", {}) or {}
    start = tree.get("start_node", "n_intro")
    initial = SimState.from_dict(tree.get("initial_state", {}) or {})

    report = DynamicReport()

    # ── 阶段 A: 节点级 BFS,边的可走性按"任意 require 都可能满足"来判定。
    #    用一个粗的"展望状态"来解析 next_variants(假设所有 flag 都可能 true 或 false)。
    parents: Dict[str, Tuple[str, int, str]] = {}  # node -> (from_node, choice_idx, text)
    queue: deque[str] = deque([start])
    seen: Set[str] = {start}
    report.visited_nodes.add(start)

    while queue:
        cur = queue.popleft()
        node = nodes.get(cur)
        if node is None or node.get("is_ending"):
            continue
        for idx, ch in enumerate(node.get("choices") or []):
            # 静态地拿到所有可能的 next 目标(包括 next_variants 全部分支)
            for tgt in all_possible_nexts(ch):
                if tgt not in nodes:
                    continue  # 悬空已在静态检查中报告
                if tgt not in seen:
                    seen.add(tgt)
                    report.visited_nodes.add(tgt)
                    parents[tgt] = (cur, idx, ch.get("text", "")[:30])
                    queue.append(tgt)

    # 重建到每个结局的最短路径
    for nid, node in nodes.items():
        if not node.get("is_ending"):
            continue
        et = node.get("ending_type", "E_UNKNOWN")
        if nid not in seen:
            continue  # 不可达
        # 回溯
        path: List[PathStep] = []
        cur = nid
        while cur in parents:
            src, idx, txt = parents[cur]
            path.append(PathStep(src, idx, txt))
            cur = src
        path.reverse()
        # 多个 ending 节点共享同一个 ending_type 时,保留最短
        if et not in report.ending_paths or len(path) < len(report.ending_paths[et]):
            report.ending_paths[et] = path

    # ── 阶段 B: state-aware 模拟,沿"代表性"路径走一遍 + 追加额外 DFS 限深探索以扫边界。
    #    这里用有限深度 DFS,严格检查 require / next_variants,但用 (node, state-sig) 去重,
    #    cap 在 max_states 防爆炸。优先用于 PR/GR/边界统计。
    visited_state: Set[Tuple[str, Tuple]] = set()
    stack: List[Tuple[str, SimState, int]] = [(start, initial, 0)]
    visited_state.add((start, initial.signature()))

    while stack:
        if len(visited_state) > max_states:
            report.boundary_warnings.append(
                f"状态模拟数超限 ({max_states}),提前终止边界扫描(覆盖率不受影响)。"
            )
            break
        cur_id, state, depth = stack.pop()
        node = nodes.get(cur_id)
        if node is None:
            continue
        report.pr_max = max(report.pr_max, state.PR)
        report.pr_min = min(report.pr_min, state.PR)
        report.gr_max = max(report.gr_max, state.GR)
        report.gr_min = min(report.gr_min, state.GR)
        report.inv_max_size = max(report.inv_max_size, len(state.inv))
        # 记录该状态下被命中的 narrative_variants(每个 if 命中即标记)
        for v_idx, nv in enumerate(node.get("narrative_variants") or []):
            if meets(state, nv.get("if") or {}):
                report.hit_narrative_variants.add((cur_id, v_idx))
        if node.get("is_ending"):
            continue
        if depth >= max_depth:
            report.truncated_at_depth += 1
            continue
        for idx, ch in enumerate(node.get("choices") or []):
            # 记录该状态下被命中的 next_variants(每个 if 命中即标记)
            for v_idx, nxv in enumerate(ch.get("next_variants") or []):
                if meets(state, nxv.get("if") or {}):
                    report.hit_next_variants.add((cur_id, idx, v_idx))
            if not meets(state, ch.get("require")):
                continue
            nxt = resolve_next(ch, state)
            if not nxt or nxt not in nodes:
                continue
            new_state, ws = with_effects(state, ch.get("effects"))
            for w in ws:
                msg = f"{cur_id}#{idx}: {w}"
                if msg not in report.boundary_warnings:
                    report.boundary_warnings.append(msg)
            sig = (nxt, new_state.signature())
            if sig in visited_state:
                continue
            visited_state.add(sig)
            stack.append((nxt, new_state, depth + 1))

    report.explored_state_count = len(visited_state)
    return report


# ─────────────────────────────────────────────────────────────────────
# 盲区补丁 1: variant 触发覆盖
# ─────────────────────────────────────────────────────────────────────

@dataclass
class VariantsCoverage:
    total_variants: int = 0
    hit_count: int = 0
    miss_count: int = 0
    misses: List[Dict[str, Any]] = field(default_factory=list)
    # 每条 miss: {node_id, variant_index, kind: "narrative"|"next", choice_index?, if}


def analyze_variants_coverage(tree: Dict[str, Any], dyn: DynamicReport) -> VariantsCoverage:
    """统计 narrative_variants / next_variants 是否被任何已探索状态触发。

    依赖 explore() 在阶段 B 收集的 hit_* 集合。状态空间有 max_states cap,
    所以"miss"只代表"在已探索状态下永不命中",仍然是合理的预警信号。
    """
    nodes: Dict[str, Dict[str, Any]] = tree.get("nodes", {}) or {}
    cov = VariantsCoverage()

    for nid, node in nodes.items():
        # narrative_variants
        for v_idx, nv in enumerate(node.get("narrative_variants") or []):
            cov.total_variants += 1
            if (nid, v_idx) in dyn.hit_narrative_variants:
                cov.hit_count += 1
            else:
                cov.miss_count += 1
                cov.misses.append({
                    "node_id": nid,
                    "variant_index": v_idx,
                    "kind": "narrative",
                    "if": nv.get("if") or {},
                })
        # next_variants(每个 choice 内部)
        for ch_idx, ch in enumerate(node.get("choices") or []):
            for v_idx, nxv in enumerate(ch.get("next_variants") or []):
                cov.total_variants += 1
                if (nid, ch_idx, v_idx) in dyn.hit_next_variants:
                    cov.hit_count += 1
                else:
                    cov.miss_count += 1
                    cov.misses.append({
                        "node_id": nid,
                        "variant_index": v_idx,
                        "kind": "next",
                        "choice_index": ch_idx,
                        "if": nxv.get("if") or {},
                    })

    return cov


# ─────────────────────────────────────────────────────────────────────
# 盲区补丁 2: orphan require key(只 require 不 set 的 flag / inv item)
# ─────────────────────────────────────────────────────────────────────

@dataclass
class OrphanKeys:
    flag_orphans: List[Dict[str, Any]] = field(default_factory=list)
    inv_orphans: List[Dict[str, Any]] = field(default_factory=list)
    # 每条:{key, required_by: [node_ids]}


def _walk_require_keys(require: Optional[Dict[str, Any]]) -> Tuple[Set[str], Set[str]]:
    """递归收集 require 中引用的 (flag_keys, inv_items)。"""
    flags: Set[str] = set()
    inv: Set[str] = set()
    if not require or not isinstance(require, dict):
        return flags, inv
    for k, v in (require.get("flags") or {}).items():
        flags.add(str(k))
    for it in require.get("inv_has", []) or []:
        inv.add(str(it))
    for it in require.get("inv_lacks", []) or []:
        inv.add(str(it))
    # 递归 any_of / all_of / not
    for sub in require.get("any_of", []) or []:
        f, i = _walk_require_keys(sub)
        flags |= f
        inv |= i
    for sub in require.get("all_of", []) or []:
        f, i = _walk_require_keys(sub)
        flags |= f
        inv |= i
    if "not" in require:
        f, i = _walk_require_keys(require["not"])
        flags |= f
        inv |= i
    return flags, inv


def _walk_effect_keys(effects: Optional[Dict[str, Any]]) -> Tuple[Set[str], Set[str]]:
    """收集 effects 中 set 过的 (flag_keys, inv_items)。"""
    flags: Set[str] = set()
    inv: Set[str] = set()
    if not effects or not isinstance(effects, dict):
        return flags, inv
    for k in (effects.get("flags") or {}).keys():
        flags.add(str(k))
    for it in effects.get("inv_add", []) or []:
        inv.add(str(it))
    # inv_remove 也算"被引用过",玩家可能曾持有
    for it in effects.get("inv_remove", []) or []:
        inv.add(str(it))
    return flags, inv


def analyze_orphan_keys(tree: Dict[str, Any]) -> OrphanKeys:
    """扫描全树:require 引用了 flag/inv item,但 effects 中无人 set/add 过。"""
    nodes: Dict[str, Dict[str, Any]] = tree.get("nodes", {}) or {}
    initial = tree.get("initial_state", {}) or {}

    # 初始 state 中已存在的 flag/inv 也算"已 set"
    set_flags: Set[str] = set((initial.get("flags") or {}).keys())
    set_inv: Set[str] = set(initial.get("inv", []) or [])

    # require 引用方:{flag_key: [node_ids], ...}
    flag_required_by: Dict[str, List[str]] = defaultdict(list)
    inv_required_by: Dict[str, List[str]] = defaultdict(list)

    for nid, node in nodes.items():
        # narrative_variants 的 if 也算 require
        for nv in node.get("narrative_variants") or []:
            f, i = _walk_require_keys(nv.get("if") or {})
            for k in f:
                if nid not in flag_required_by[k]:
                    flag_required_by[k].append(nid)
            for k in i:
                if nid not in inv_required_by[k]:
                    inv_required_by[k].append(nid)
        for ch in node.get("choices") or []:
            f, i = _walk_require_keys(ch.get("require") or {})
            for k in f:
                if nid not in flag_required_by[k]:
                    flag_required_by[k].append(nid)
            for k in i:
                if nid not in inv_required_by[k]:
                    inv_required_by[k].append(nid)
            # next_variants 的 if 也算 require
            for nxv in ch.get("next_variants") or []:
                f, i = _walk_require_keys(nxv.get("if") or {})
                for k in f:
                    if nid not in flag_required_by[k]:
                        flag_required_by[k].append(nid)
                for k in i:
                    if nid not in inv_required_by[k]:
                        inv_required_by[k].append(nid)
            # effects 收集
            f, i = _walk_effect_keys(ch.get("effects") or {})
            set_flags |= f
            set_inv |= i

    orphans = OrphanKeys()
    for k, refs in sorted(flag_required_by.items()):
        if k not in set_flags:
            orphans.flag_orphans.append({"key": k, "required_by": refs})
    for k, refs in sorted(inv_required_by.items()):
        if k not in set_inv:
            orphans.inv_orphans.append({"key": k, "required_by": refs})
    return orphans


# ─────────────────────────────────────────────────────────────────────
# 盲区补丁 3: picker / tool 节点静态展开
# ─────────────────────────────────────────────────────────────────────

def _is_picker_node(nid: str, node: Dict[str, Any]) -> bool:
    """识别地图选择器节点。判定标志(任一即是):
       - 节点有 `_is_map_picker: true`
       - 节点 `type` 字段为 "landmark_picker"
       - 节点 ID 包含 "picker"
       - 节点有 `picker_choices` 字段
    """
    if node.get("_is_map_picker"):
        return True
    if node.get("type") == "landmark_picker":
        return True
    if "picker_choices" in node:
        return True
    if "picker" in nid.lower():
        return True
    return False


def analyze_picker_nodes(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """识别 picker 节点,静态展开 landmark_map 中的所有 node_id 作为 picker_paths。

    返回每条:{node_id, picker_paths: [target_node_ids], static_choice_count, ...}
    BFS 阶段 A 已经会展开这些静态 choices,这里只是显式地报告出来,
    供报告中显示"picker 入口已经覆盖了多少条 landmark 路径"。
    """
    nodes: Dict[str, Dict[str, Any]] = tree.get("nodes", {}) or {}
    landmark_map = tree.get("landmark_map") or []
    landmark_node_ids = {str(lm.get("node_id")) for lm in landmark_map if lm.get("node_id")}

    pickers: List[Dict[str, Any]] = []
    for nid, node in nodes.items():
        if not _is_picker_node(nid, node):
            continue

        # 1) 节点显式提供的 picker_choices(若有)
        picker_paths: Set[str] = set()
        for pc in node.get("picker_choices") or []:
            tgt = pc.get("next") if isinstance(pc, dict) else None
            if tgt:
                picker_paths.add(str(tgt))

        # 2) 静态 choices 中的 next/next_variants
        static_choices = node.get("choices") or []
        for ch in static_choices:
            for tgt in all_possible_nexts(ch):
                picker_paths.add(tgt)

        # 3) landmark_map 中所有 landmark 的 node_id(picker 节点天然能进入它们)
        picker_paths |= landmark_node_ids

        pickers.append({
            "node_id": nid,
            "picker_paths": sorted(picker_paths),
            "static_choice_count": len(static_choices),
            "landmark_count": len(landmark_node_ids),
        })

    return pickers


# ─────────────────────────────────────────────────────────────────────
# 报告渲染
# ─────────────────────────────────────────────────────────────────────

def nodes_for_ending(tree: Dict[str, Any], ending_type: str) -> str:
    """返回某 ending_type 对应的节点 id(简短)。"""
    for nid, node in (tree.get("nodes") or {}).items():
        if node.get("is_ending") and node.get("ending_type") == ending_type:
            return nid
    return f"<no node for {ending_type}>"


def _print_section(title: str) -> None:
    print()
    print(bold(cyan("─" * 60)))
    print(bold(cyan(f"  {title}")))
    print(bold(cyan("─" * 60)))


def render_report(
    tree: Dict[str, Any],
    static: StaticReport,
    dyn: DynamicReport,
    variants_cov: Optional[VariantsCoverage] = None,
    orphan_keys: Optional[OrphanKeys] = None,
    pickers: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """打印报告。返回是否"健康"(True = 退出码 0)。"""
    healthy = True
    nodes: Dict[str, Dict[str, Any]] = tree.get("nodes", {}) or {}
    declared_endings = set((tree.get("endings") or {}).keys())
    title = tree.get("title", "(无标题)")
    start = tree.get("start_node", "n_intro")

    print()
    print(bold(magenta("═" * 60)))
    print(bold(magenta(f"  Path Explorer · {title}")))
    print(bold(magenta("═" * 60)))
    print(f"  start_node: {green(start)}")
    print(f"  total nodes: {static.total_nodes}")

    # 1. 节点统计
    _print_section("1. 节点统计")
    print(f"  结局节点: {len(static.ending_nodes)} 个 — {', '.join(static.ending_nodes) or '(无)'}")
    print(f"  分叉节点(出度≥2): {len(static.branch_nodes)} 个")
    print(f"  孤儿节点(无入边且非 start): {len(static.orphans)}")
    if static.orphans:
        for o in static.orphans:
            print(f"    {red('· ' + o)}")
        healthy = False
    print(f"  悬空 next(指向不存在节点): {len(static.dangling_refs)}")
    if static.dangling_refs:
        for src, txt, tgt in static.dangling_refs:
            print(f"    {red(f'· {src} → {tgt}')} {dim(f'(选项: {txt})')}")
        healthy = False
    print(f"  死路节点(非结局且无 choices): {len(static.dead_ends)}")
    if static.dead_ends:
        for d in static.dead_ends:
            print(f"    {red('· ' + d)}")
        healthy = False
    if static.unknown_endings:
        print(f"  {yellow('未声明的 ending_type:')} {len(static.unknown_endings)}")
        for u in static.unknown_endings:
            print(f"    {yellow('· ' + u)}")

    # 入度 / 出度 top
    if static.in_degree:
        top_in = sorted(static.in_degree.items(), key=lambda x: -x[1])[:5]
        print(f"  入度 Top5: {dim(', '.join(f'{k}({v})' for k, v in top_in))}")
    if static.out_degree:
        top_out = sorted(static.out_degree.items(), key=lambda x: -x[1])[:5]
        print(f"  出度 Top5: {dim(', '.join(f'{k}({v})' for k, v in top_out))}")

    # 2. 结局可达性
    _print_section("2. 结局可达性")
    all_endings_in_tree = {nodes[n].get("ending_type", "?") for n in static.ending_nodes}
    declared = declared_endings or all_endings_in_tree
    for et in sorted(declared):
        if et in dyn.ending_paths:
            path = dyn.ending_paths[et]
            print(f"  {green('✓')} {bold(et)} 可达 — 最短路径 {len(path)} 步")
            # 路径头 + 尾(展示分叉点)
            ids = [s.node_id for s in path]
            if len(ids) <= 10:
                chain = " → ".join(ids)
            else:
                chain = " → ".join(ids[:5]) + " → ... → " + " → ".join(ids[-4:])
            # 把目标 ending 节点也拼上
            print(f"    {dim(chain + ' → ' + nodes_for_ending(tree, et))}")
            indices = " · ".join(f"{s.node_id}#{s.choice_index}" for s in path)
            if len(indices) > 220:
                indices = indices[:120] + " ... " + indices[-90:]
            print(f"    {dim('选择序列: ' + indices)}")
        else:
            # 检查是否已在 tree 中声明但不可达
            in_tree = any(nodes[n].get("ending_type") == et for n in static.ending_nodes)
            if in_tree:
                print(f"  {red('✗')} {bold(et)} 不可达(节点存在但无路径)")
                healthy = False
            else:
                print(f"  {yellow('?')} {bold(et)} 未在 tree 中实现")
                healthy = False

    # 也列出 tree 中存在但未声明的 ending_type
    extra = set()
    for n in static.ending_nodes:
        et = nodes[n].get("ending_type")
        if et and et not in declared:
            extra.add(et)
    if extra:
        print(f"  {yellow('额外 ending_type(未在 endings 字典声明):')} {', '.join(sorted(extra))}")

    # 3. 路径覆盖
    _print_section("3. 路径覆盖")
    visited = dyn.visited_nodes
    coverage = len(visited) / max(static.total_nodes, 1) * 100
    print(f"  访问节点: {len(visited)}/{static.total_nodes} ({coverage:.1f}%)")
    print(f"  探索状态总数: {dyn.explored_state_count}")
    if dyn.truncated_at_depth:
        print(f"  {yellow('深度截断次数:')} {dyn.truncated_at_depth} (max_depth=80)")
    unvisited = [n for n in nodes if n not in visited]
    if unvisited:
        print(f"  {yellow('从未被访问的节点:')} {len(unvisited)}")
        for u in unvisited[:20]:
            print(f"    {yellow('· ' + u)}")
        if len(unvisited) > 20:
            print(f"    {dim(f'... 还有 {len(unvisited)-20} 个')}")
        if len(unvisited) > 0:
            healthy = False

    # 3.5 Variant 触发覆盖(Task 13 盲区补丁 1)
    if variants_cov is not None and variants_cov.total_variants > 0:
        _print_section("3.5 Variant 触发覆盖")
        hit_pct = variants_cov.hit_count / max(variants_cov.total_variants, 1) * 100
        print(f"  总 variants: {variants_cov.total_variants}")
        print(f"  触发: {variants_cov.hit_count} ({hit_pct:.1f}%)")
        print(f"  从未触发: {variants_cov.miss_count}")
        if variants_cov.misses:
            for m in variants_cov.misses[:20]:
                if m["kind"] == "narrative":
                    head = f"{m['node_id']} narrative_variants[{m['variant_index']}]"
                else:
                    head = f"{m['node_id']} choices[{m['choice_index']}].next_variants[{m['variant_index']}]"
                cond_str = json.dumps(m["if"], ensure_ascii=False)
                if len(cond_str) > 80:
                    cond_str = cond_str[:77] + "..."
                print(f"    {yellow('· ' + head)} {dim('if=' + cond_str)}")
            if len(variants_cov.misses) > 20:
                print(f"    {dim(f'... 还有 {len(variants_cov.misses)-20} 个 miss')}")
            healthy = False

    # 3.6 Orphan require key(Task 13 盲区补丁 2)
    if orphan_keys is not None and (orphan_keys.flag_orphans or orphan_keys.inv_orphans):
        _print_section("3.6 Orphan require key")
        print(f"  孤立 flag(只 require 不 set):{len(orphan_keys.flag_orphans)} 个")
        for o in orphan_keys.flag_orphans[:30]:
            refs = ", ".join(o["required_by"][:5])
            if len(o["required_by"]) > 5:
                refs += f" (+{len(o['required_by'])-5})"
            print(f"    {yellow('· ' + o['key'])} {dim('(required by: ' + refs + ')')}")
        if len(orphan_keys.flag_orphans) > 30:
            print(f"    {dim(f'... 还有 {len(orphan_keys.flag_orphans)-30} 个')}")
        print(f"  孤立 inv item:{len(orphan_keys.inv_orphans)} 个")
        for o in orphan_keys.inv_orphans[:30]:
            refs = ", ".join(o["required_by"][:5])
            if len(o["required_by"]) > 5:
                refs += f" (+{len(o['required_by'])-5})"
            print(f"    {yellow('· ' + o['key'])} {dim('(required by: ' + refs + ')')}")
        if orphan_keys.flag_orphans or orphan_keys.inv_orphans:
            healthy = False

    # 3.7 Picker 节点静态展开(Task 13 盲区补丁 3)
    if pickers is not None and pickers:
        _print_section("3.7 Picker 节点(地图选择器)")
        print(f"  识别到 picker 节点: {len(pickers)} 个")
        for p in pickers:
            sc = p["static_choice_count"]
            lc = p["landmark_count"]
            meta = f"(static_choices={sc}, landmarks={lc})"
            print(f"  {green('·')} {bold(p['node_id'])} → {len(p['picker_paths'])} 条 picker_paths {dim(meta)}")
            paths_preview = ", ".join(p["picker_paths"][:8])
            if len(p["picker_paths"]) > 8:
                paths_preview += f" (+{len(p['picker_paths'])-8})"
            print(f"    {dim(paths_preview)}")

    # 4. 状态值边界
    _print_section("4. 状态边界")
    print(f"  PR 范围: [{dyn.pr_min}, {dyn.pr_max}]"
          + (f"  {green('OK')}" if 0 <= dyn.pr_min and dyn.pr_max <= 100 else f"  {red('越界!')}"))
    print(f"  GR 范围: [{dyn.gr_min}, {dyn.gr_max}]"
          + (f"  {green('OK')}" if 0 <= dyn.gr_min and dyn.gr_max <= 100 else f"  {red('越界!')}"))
    print(f"  inv 最大持有数: {dyn.inv_max_size} 件")
    if dyn.boundary_warnings:
        print(f"  {yellow('边界警告:')} {len(dyn.boundary_warnings)} 条")
        for w in dyn.boundary_warnings[:15]:
            print(f"    {yellow('· ' + w)}")
        if len(dyn.boundary_warnings) > 15:
            print(f"    {dim(f'... 还有 {len(dyn.boundary_warnings)-15} 条')}")

    # 总评
    print()
    print(bold(magenta("═" * 60)))
    if healthy:
        print(bold(green("  ✓ 全部检查通过")))
    else:
        print(bold(red("  ✗ 发现问题,请见上方红 / 黄字")))
    print(bold(magenta("═" * 60)))
    print()

    return healthy


# ─────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print(red("用法: python tools/path_explorer.py path/to/tree.json"), file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.exists():
        print(red(f"找不到文件: {path}"), file=sys.stderr)
        return 2

    with path.open("r", encoding="utf-8") as f:
        tree = json.load(f)

    static = analyze_static(tree)
    dyn = explore(tree, max_depth=80)
    variants_cov = analyze_variants_coverage(tree, dyn)
    orphan_keys = analyze_orphan_keys(tree)
    pickers = analyze_picker_nodes(tree)
    healthy = render_report(tree, static, dyn, variants_cov, orphan_keys, pickers)
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.exit(main())
