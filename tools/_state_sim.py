"""共用状态模拟器。被 path_explorer 和 audit 工具共用,与 player.py:State.meets() 行为对齐。

设计:
- 不可变(dataclass frozen=True)便于 BFS 去重
- meets() 与 player.State.meets() 行为 1:1 对齐
- apply() 返回新实例,不修改原状态

来源 & bug 修复:
- Pass 1 期间从 path_explorer.py 抽出。原 path_explorer 的 require 检查使用
  `route` 键(误),数据约定中实际为 `route_is`(见 player.py:225)。
  本模块对齐 player.py,修复了这个静默忽略 route 检查的 bug。
- 同时,原 path_explorer 用 `visited_landmarks_has`,player.py 用 `landmark_visited`,
  本模块以 player.py 为准。

注意:这里的字段集合是"player.State 现有字段的快照"。
Pass 1 清扫完成后,本文件需要同步更新(删 route 等)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SimState:
    PR: int = 0
    GR: int = 0
    shifts_completed: int = 0
    shifts_skipped: int = 0
    inv: Tuple[str, ...] = ()
    flags: Tuple[Tuple[str, bool], ...] = ()  # hashable for BFS dedup
    route: Optional[str] = None
    visited_landmarks: Tuple[str, ...] = ()
    skipped_landmarks: Tuple[str, ...] = ()
    puzzle_pieces: Tuple[str, ...] = ()
    character: str = "G-273"
    last_landmark_id: Optional[str] = None
    visit_counts: Tuple[Tuple[str, int], ...] = ()  # hashable for BFS dedup

    @classmethod
    def from_dict(cls, initial: Dict[str, Any]) -> "SimState":
        return cls(
            PR=int(initial.get("PR", 0)),
            GR=int(initial.get("GR", 0)),
            shifts_completed=int(initial.get("shifts_completed", 0)),
            shifts_skipped=int(initial.get("shifts_skipped", 0)),
            inv=tuple(initial.get("inv", [])),
            flags=tuple(sorted((initial.get("flags") or {}).items())),
            route=initial.get("route"),
            visited_landmarks=tuple(initial.get("visited_landmarks", [])),
            skipped_landmarks=tuple(initial.get("skipped_landmarks", [])),
            puzzle_pieces=tuple(initial.get("puzzle_pieces", [])),
            character=str(initial.get("character", "G-273")),
            last_landmark_id=initial.get("last_landmark_id"),
            visit_counts=tuple(sorted((initial.get("visit_counts") or {}).items())),
        )

    def flags_dict(self) -> Dict[str, bool]:
        return dict(self.flags)

    def visit_counts_dict(self) -> Dict[str, int]:
        return dict(self.visit_counts)

    def signature(self) -> Tuple:
        """用作访问去重(忽略 visited 节点列表,仅快照游戏状态)。"""
        return (
            self.PR, self.GR,
            self.shifts_completed, self.shifts_skipped,
            self.inv, self.flags, self.route,
            self.visited_landmarks, self.skipped_landmarks, self.puzzle_pieces,
            self.character, self.last_landmark_id, self.visit_counts,
        )


def meets(state: SimState, require: Optional[Dict[str, Any]]) -> bool:
    """递归检查 require,行为对齐 player.State.meets()。"""
    if not require:
        return True
    if not _meets_clause(state, require):
        return False
    if "any_of" in require:
        sub = require["any_of"] or []
        if sub and not any(meets(state, c) for c in sub):
            return False
    if "all_of" in require:
        sub = require["all_of"] or []
        if not all(meets(state, c) for c in sub):
            return False
    if "not" in require:
        if meets(state, require["not"]):
            return False
    return True


def _meets_clause(state: SimState, require: Dict[str, Any]) -> bool:
    """单层 require 子句检查,与 player.py:_meets_clause 1:1 对齐。"""
    if "PR_min" in require and state.PR < int(require["PR_min"]):
        return False
    if "PR_max" in require and state.PR > int(require["PR_max"]):
        return False
    if "GR_min" in require and state.GR < int(require["GR_min"]):
        return False
    if "GR_max" in require and state.GR > int(require["GR_max"]):
        return False
    for item in require.get("inv_has", []) or []:
        if item not in state.inv:
            return False
    for item in require.get("inv_lacks", []) or []:
        if item in state.inv:
            return False
    flags = state.flags_dict()
    for k, v in (require.get("flags") or {}).items():
        if bool(flags.get(k, False)) != bool(v):
            return False
    if "shifts_skipped_min" in require and state.shifts_skipped < int(require["shifts_skipped_min"]):
        return False
    if "shifts_completed_min" in require and state.shifts_completed < int(require["shifts_completed_min"]):
        return False
    if "route_is" in require and state.route != require["route_is"]:
        return False
    for lm in require.get("landmark_visited", []) or []:
        if lm not in state.visited_landmarks:
            return False
    if "puzzle_pieces_min" in require and len(state.puzzle_pieces) < int(require["puzzle_pieces_min"]):
        return False
    visit_counts = state.visit_counts_dict()
    for node_id, n in (require.get("visit_count_min") or {}).items():
        if visit_counts.get(node_id, 0) < int(n):
            return False
    if "last_landmark" in require:
        expected = require["last_landmark"]
        if isinstance(expected, str):
            if state.last_landmark_id != expected:
                return False
        elif isinstance(expected, list):
            if state.last_landmark_id not in expected:
                return False
    if "character" in require:
        expected = require["character"]
        if isinstance(expected, str):
            if state.character != expected:
                return False
        elif isinstance(expected, list):
            if state.character not in expected:
                return False
    return True
