# Pass 1 状态空间审计 + Flag 降级清扫 实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把「杭州夜班保安」v7 的状态空间从 234 个 flags + 8 个互相重叠的 State 字段瘦下来,建立审计基线和命名契约,为后续沙盒化工作打干净的地基。

**Architecture:** 三层产出——(1) 共用模拟器 `tools/_state_sim.py` 解决 path_explorer 与 audit 工具的逻辑漂移;(2) 两个审计脚本 `audit_state.py` 与 `audit_variants.py` 输出引用矩阵和死字段清单;(3) 数据层清扫 `tree.json` 与 `player.py`,删死字段、合并重叠字段、把"知识类"flag 收编到 `know.*` 命名空间。零引擎扩展(除 `meta_flags` 删除),所有变更必须通过 path_explorer 回归(8 主结局 + 41 体验仍可达)。

**Tech Stack:** Python 3.12 标准库(json/dataclasses/typing),pytest。无新依赖。

**Spec 来源:** `docs/team-reviews/2026-05-07-沙盒方向首个开发任务.md` § 9

---

## File Structure

### 创建

| 路径 | 责任 |
|---|---|
| `tools/_state_sim.py` | SimState dataclass + meets() 模拟,与 `player.py:State.meets()` 行为一致。被 `path_explorer.py` 和两个 audit 脚本共用 |
| `tools/audit_state.py` | 输出 flags/inv/state 字段的引用矩阵 + 死字段清单 + Lore 红线 hard assertion |
| `tools/audit_variants.py` | 输出 narrative_variants 覆盖矩阵 + "重复访问无分化"节点清单 |
| `tests/test_state_sim.py` | _state_sim.py 单元测试,确保与 player.py 行为对齐 |
| `tests/test_audit_state.py` | audit_state.py 单元测试 + 真 tree.json 集成 |
| `tests/test_audit_variants.py` | audit_variants.py 单元测试 + 真 tree.json 集成 |
| `docs/architecture/ADR-007-state-contract.md` | 14 State 字段冻结清单 + flag 命名空间约定 + _SPOILER_KEYS 提为正式契约 |

### 修改

| 路径 | 改动范围 |
|---|---|
| `tools/path_explorer.py` | 删 `SimState`(lines 63-93)和重复的 require 解析,改为从 `_state_sim` import;加 picker 节点动态展开 + variants 触发追踪 + require-effects key 一致性 |
| `src/ghost_story_factory/v5/player.py` | 删 `meta_flags` 字段(line 90)+ `route` 字段(line 84)+ `_SPOILER_KEYS` 中的 `route_is`/`meta_flags`(lines 293-297);`shifts_completed` 改 `@property` 派生;合并 `skipped_landmarks` 和 `shifts_skipped` |
| `src/ghost_story_factory/v7/` | 同步删除/迁移上述字段在 v7 player 里的引用 |
| `stories/hangzhou_yebanbaoan/tree.json` | 顶层加 `lore_canon.years` 白名单;清空所有 `meta_flags`/`route` 引用;`s{1-7}_*` 局部 flag 下沉为 `visit_count_min`/`_foreshadow_slot`;`*_revisit_*` 合并为 `visit_count_min`;15 件 inv+flag 双写道具统一规则;`know-*` flag 重命名为 `know.*` |

---

## Phase 1:地基

### Task 1:抽出 `tools/_state_sim.py` 共用模块

**Files:**
- Create: `tools/_state_sim.py`
- Create: `tests/test_state_sim.py`
- Modify: `tools/path_explorer.py:60-200`(删除 `SimState` 类与 require 解析,改为 import)

- [ ] **Step 1: 写失败测试 — SimState 行为与 player.State 一致**

```python
# tests/test_state_sim.py
"""验证 _state_sim.SimState.meets() 与 player.py:State.meets() 行为一致。"""
import pytest
from tools._state_sim import SimState, meets
from ghost_story_factory.v5.player import State


@pytest.mark.parametrize("require,initial,expected", [
    # 基础原子条件
    ({"PR_min": 5}, {"PR": 10}, True),
    ({"PR_min": 5}, {"PR": 3}, False),
    ({"inv_has": ["羊符"]}, {"inv": ["羊符"]}, True),
    ({"inv_lacks": ["羊符"]}, {"inv": ["羊符"]}, False),
    ({"flags": {"radio_listened": True}}, {"flags": {"radio_listened": True}}, True),
    # 嵌套
    ({"any_of": [{"PR_min": 5}, {"GR_min": 5}]}, {"PR": 10, "GR": 0}, True),
    ({"all_of": [{"PR_min": 5}, {"GR_min": 5}]}, {"PR": 10, "GR": 0}, False),
    ({"not": {"PR_min": 5}}, {"PR": 3}, True),
    # visit_count
    ({"visit_count_min": {"n_x": 2}}, {"visit_counts": {"n_x": 3}}, True),
    ({"visit_count_min": {"n_x": 2}}, {"visit_counts": {"n_x": 1}}, False),
])
def test_meets_matches_player_state(require, initial, expected):
    sim = SimState.from_dict(initial)
    player = State(initial)
    assert meets(sim, require) == expected
    assert player.meets(require) == expected
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_state_sim.py -v`
Expected: ImportError (`tools._state_sim` 不存在)

- [ ] **Step 3: 实现 `tools/_state_sim.py`**

```python
# tools/_state_sim.py
"""共用状态模拟器。被 path_explorer 和 audit 工具共用,与 player.py:State.meets() 行为对齐。

设计:
- 不可变(dataclass frozen=True)便于 BFS 去重
- meets() 与 player.State.meets() 行为 1:1 对齐
- apply() 返回新实例,不修改原状态

注意:这里的字段集合是"player.State 现有字段的快照"。
Pass 1 清扫完成后,本文件需要同步更新(删 route/meta_flags 等)。
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
    flags: Tuple[Tuple[str, bool], ...] = ()  # frozenset 兼容
    route: Optional[str] = None
    visited_landmarks: Tuple[str, ...] = ()
    skipped_landmarks: Tuple[str, ...] = ()
    puzzle_pieces: Tuple[str, ...] = ()
    character: str = "G-273"
    meta_flags: Tuple[Tuple[str, bool], ...] = ()
    last_landmark_id: Optional[str] = None
    visit_counts: Tuple[Tuple[str, int], ...] = ()

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
            meta_flags=tuple(sorted((initial.get("meta_flags") or {}).items())),
            last_landmark_id=initial.get("last_landmark_id"),
            visit_counts=tuple(sorted((initial.get("visit_counts") or {}).items())),
        )

    def flags_dict(self) -> Dict[str, bool]:
        return dict(self.flags)

    def meta_flags_dict(self) -> Dict[str, bool]:
        return dict(self.meta_flags)

    def visit_counts_dict(self) -> Dict[str, int]:
        return dict(self.visit_counts)


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
    meta = state.meta_flags_dict()
    for k, v in (require.get("meta_flags") or {}).items():
        if bool(meta.get(k, False)) != bool(v):
            return False
    return True
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_state_sim.py -v`
Expected: 9 passed

- [ ] **Step 5: 重构 path_explorer.py 删除重复实现**

把 `tools/path_explorer.py:60-200` 的 `SimState` 与 require 解析逻辑全部删掉,顶部加:

```python
from tools._state_sim import SimState, meets
```

凡是用到 `state.meets(require)` 的地方改为 `meets(state, require)`。
凡是构造 `SimState(...)` 的地方改为 `SimState.from_dict(initial)`。

- [ ] **Step 6: 跑 path_explorer 回归**

Run: `python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json`
Expected: 输出与重构前一致(节点统计、结局可达性、PR/GR 边界都不变),exit code 0

- [ ] **Step 7: Commit**

```bash
git add tools/_state_sim.py tests/test_state_sim.py tools/path_explorer.py
git commit -m "refactor(tools): 抽出 _state_sim 共用模块,path_explorer 复用

把 path_explorer 中 SimState 与 require 解析逻辑提到 tools/_state_sim.py,
audit 工具与 path_explorer 共享同一套行为,杜绝两套解析漂移。
单元测试与 player.py:State.meets() 对照确保行为一致。"
```

---

### Task 2:写 ADR-007 state contract

**Files:**
- Create: `docs/architecture/ADR-007-state-contract.md`

- [ ] **Step 1: 创建文档骨架**

按项目 ADR 模板(见 `docs/architecture/ADR-004-core-llm-refactor.md`)写:

```markdown
# ADR-007: 状态空间契约与 Flag 命名规范

## Status
Accepted

## Date
2026-05-07

## Context
项目状态空间已严重失衡:
- `tree.json` 有 234 个 flags,其中 153 个只用一次(65%)
- `meta_flags` 字段全文 0 次写读(死字段)
- `shifts_completed` 与 `visited_landmarks` 计数语义重叠
- 15 件 inv 道具同时 set 同名 flag(双写)
- `route` 字段 v7 已废弃但代码未清理
- 200+ flags 没有命名规范、无生命周期登记、无谁清除的契约

继续往里堆字段(如新增 `knowledge: Set[str]`)会让维护成本指数爆炸。

## Decision
本 ADR 把 State 14 字段冻结成正式契约,并对 flags 命名空间作硬约定。

### State 字段冻结清单(Pass 1 完成后)

| 字段 | 类型 | 归类 | 用途 |
|---|---|---|---|
| `PR` | int | 仅本周目 | 个人共鸣值 |
| `GR` | int | 仅本周目 | 全局共鸣值 |
| `inv` | List[str] | 仅本周目 | 物品栏 |
| `flags` | Dict[str, bool] | 仅本周目 | 通用 flag(按下文命名空间分桶) |
| `shifts_skipped` | int | 仅本周目 | 跳过的班数 |
| `shifts_completed` | @property | 派生 | 由 `len([l for l in visited_landmarks if l in {S1..S6}])` 算出 |
| `visited_landmarks` | List[str] | 仅本周目 | 已访问地标 |
| `puzzle_pieces` | List[str] | 仅本周目 | 已收集谜题碎片 |
| `character` | str | 仅本周目 | 当前角色身份(G-273 / linmou_1985 等) |
| `last_landmark_id` | Optional[str] | 仅本周目 | 上一站地标 ID(给地图渲染) |
| `npc_locations` | Dict[str, str] | 仅本周目 | NPC 当前位置 |
| `visit_counts` | Dict[str, int] | 仅本周目 | 每个节点被访问次数 |
| `known_landmarks` | List[str] | 仅本周目 | 地图上可见地标 |
| `PR_peak` | int | 仅本周目 | PR 历史峰值(成就用) |

**Pass 1 删除的字段**:
- ❌ `meta_flags`(0 写 0 读,纯死字段。周目继承等真有需求时再加)
- ❌ `route`(v7 已废弃)
- ❌ `skipped_landmarks`(并入 shifts_skipped 计数)

### Flag 命名空间约定

所有 `flags` 字典的 key 必须遵循 `<namespace>.<name>` 格式,namespace 限定为下表 6 种:

| namespace | 用途 | 示例 | 生命周期 |
|---|---|---|---|
| `know.*` | 玩家知识 | `know.linmou_85_corruption` | 永久(本周目) |
| `oneshot.*` | 一次性事件触发标志 | `oneshot.s4_first_visit` | 永久(本周目) |
| `arc.*` | 故事弧线进度 | `arc.lin_act_2_done` | 永久(本周目) |
| `route.*` | 路线锁定 | `route.lin_arc_locked` | 永久(本周目) |
| `state.*` | 临时状态(可被 effects 清除) | `state.flashlight_on` | 短期 |
| `meta.*` | 跨周目继承(预留,Pass 1 不实现) | `meta.true_ending_seen` | 跨周目 |

**约束**:
- 任何 require 引用的 flag 必须在某处 effects 里被 set 过(`audit_state.py` hard assertion)
- 任何被 set 的 flag 必须至少被一处 require 读到(否则是死字段)
- 不允许出现在上述 6 个 namespace 之外的 key(如 `s1_threw_coat` 必须迁移到 `oneshot.s1_threw_coat`)

### `_SPOILER_KEYS` 提为正式契约

`player.py:_SPOILER_KEYS` 现在是一个隐式 tuple,新加 require 字段时容易漏。本 ADR 把它提为正式契约:

```python
# player.py 顶部
SPOILER_KEYS: Tuple[str, ...] = (
    "PR_min", "PR_max", "GR_min", "GR_max",
    "flags", "shifts_completed_min", "shifts_skipped_min",
    "landmark_visited", "character", "not",
)
```

任何新增 require 字段必须明确归入"玩家可知"或"spoiler",并在审计脚本里 hard assert。

### Lore Canon 白名单

`tree.json` 顶层新增:

```json
{
  "lore_canon": {
    "years": [1924, 1933, 1959, 1985, 1986, 1987, 1991, 1996, 2009],
    "forbidden_terms": ["管理委员会", "员工编号", "林先生", "林总", "委员会"]
  }
}
```

`audit_state.py` 在所有 narrative 里检查:
- 引用其他年份(1900-2030 范围内)直接 fail
- 出现 forbidden_terms 任一即 fail

## Alternatives Considered

### Option A: 加 State.knowledge: Set[str] + effects.learn(Chief Editor 初步倾向)
- **Pros**: 显式区分"玩家知道"vs flags
- **Why rejected**: 反加法者两轮一致反对(State + Topology):语义上等同 `flags["know.X"] = true`,加新维度只是语法糖。先治理现有 flags,真有需要再升级。

### Option B: 推倒重建 State 类
- **Pros**: 干净
- **Why rejected**: 破坏现有玩法,违反 Linus "Never break userspace"。

## Consequences

### Positive
- 状态空间从 14 字段降到 11 字段(删 3 个)
- flags 唯一键从 234 降到 ≤ 80(下沉局部 flag 后)
- 任何新加字段必须先论证为何不能用现有 14 字段表达
- audit_state.py 把命名空间约定固化为 CI 红线

### Negative & Mitigation
- `tree.json` 中所有现有 flag 名要重命名 → **Mitigation**: Task 12 集中处理,每改一批跑一次 path_explorer 回归
- 玩家通关录像作为视觉回归基线 → **Mitigation**: Pass 1 启动前 snapshot 一份 v7 通关录像,清扫完后跑同样选择对照
```

- [ ] **Step 2: Commit ADR**

```bash
git add docs/architecture/ADR-007-state-contract.md
git commit -m "docs(adr): ADR-007 状态空间契约与 Flag 命名规范

冻结 11 个 State 字段(删 meta_flags / route / skipped_landmarks),
flags 强制 6 namespace 命名(know./oneshot./arc./route./state./meta.),
_SPOILER_KEYS 提为正式契约,tree.json 加 lore_canon 白名单。"
```

---

## Phase 2:审计工具

### Task 3:`tools/audit_state.py` 基础版 — flags/inv 引用矩阵

**Files:**
- Create: `tools/audit_state.py`
- Create: `tests/test_audit_state.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_audit_state.py
import json
import pytest
from pathlib import Path
from tools.audit_state import audit_tree


@pytest.fixture
def minimal_tree(tmp_path):
    tree = {
        "initial_state": {"flags": {}},
        "nodes": {
            "n_a": {
                "narrative": "...",
                "effects": {"flags": {"oneshot.foo": True}},
                "next": "n_b",
            },
            "n_b": {
                "narrative": "...",
                "choices": [{"text": "X", "next": "n_a", "require": {"flags": {"oneshot.foo": True}}}],
            },
            "n_dead_set": {
                "narrative": "...",
                "effects": {"flags": {"oneshot.never_read": True}},
                "next": "n_b",
            },
            "n_dead_require": {
                "narrative": "...",
                "choices": [{"text": "Y", "next": "n_b", "require": {"flags": {"oneshot.never_set": True}}}],
            },
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree), encoding="utf-8")
    return p


def test_audit_finds_dead_set_flag(minimal_tree):
    """只 set 不 require 的 flag 应该被标记。"""
    report = audit_tree(minimal_tree)
    assert "oneshot.never_read" in report["dead_set_flags"]


def test_audit_finds_dead_require_flag(minimal_tree):
    """只 require 不 set 的 flag 应该被标记。"""
    report = audit_tree(minimal_tree)
    assert "oneshot.never_set" in report["dead_require_flags"]


def test_audit_healthy_flag_not_flagged(minimal_tree):
    """正常被 set 又被 require 的 flag 不应该出现在死字段清单。"""
    report = audit_tree(minimal_tree)
    assert "oneshot.foo" not in report["dead_set_flags"]
    assert "oneshot.foo" not in report["dead_require_flags"]


def test_audit_returns_flag_usage_matrix(minimal_tree):
    """每个 flag 都有 set_by + require_by 节点列表。"""
    report = audit_tree(minimal_tree)
    assert report["flags"]["oneshot.foo"]["set_by"] == ["n_a"]
    assert report["flags"]["oneshot.foo"]["require_by"] == ["n_b"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_audit_state.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 `tools/audit_state.py`**

```python
"""tools/audit_state.py — flags / inv / state 字段引用矩阵审计。

用法:
    python tools/audit_state.py path/to/tree.json [--strict]

输出 JSON 报告(stdout)+ exit code:
    0 = 全绿
    1 = 有警告(死字段、命名空间违规)
    2 = 有阻断(Lore 红线、悬空引用)

Linus 风格:数据说话,不掺合品味判断。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


# Lore 红线(从 tree.lore_canon 读)
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


def _flatten_flags_in_require(req: Any, out: Set[str]) -> None:
    """递归收集 require 中提到的 flag key。"""
    if not isinstance(req, dict):
        return
    for k, v in (req.get("flags") or {}).items():
        out.add(k)
    for sub in req.get("any_of", []) or []:
        _flatten_flags_in_require(sub, out)
    for sub in req.get("all_of", []) or []:
        _flatten_flags_in_require(sub, out)
    if "not" in req:
        _flatten_flags_in_require(req["not"], out)


def audit_tree(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    nodes = tree.get("nodes", {})
    canon = tree.get("lore_canon", DEFAULT_LORE_CANON)

    flag_set_by: Dict[str, List[str]] = defaultdict(list)
    flag_require_by: Dict[str, List[str]] = defaultdict(list)
    inv_add_by: Dict[str, List[str]] = defaultdict(list)
    inv_require_by: Dict[str, List[str]] = defaultdict(list)
    namespace_violations: List[Tuple[str, str]] = []
    year_violations: List[Tuple[str, int]] = []
    term_violations: List[Tuple[str, str]] = []

    for node_id, node in nodes.items():
        # effects.flags
        eff = node.get("effects") or {}
        for k in (eff.get("flags") or {}).keys():
            flag_set_by[k].append(node_id)
            if not k.startswith(NAMESPACE_PREFIXES):
                namespace_violations.append((node_id, k))
        for item in eff.get("inv_add", []) or []:
            inv_add_by[item].append(node_id)
        # require.flags / inv_has(递归收集)
        flags_req: Set[str] = set()
        for req in _walk_requires(node):
            _flatten_flags_in_require(req, flags_req)
            for item in req.get("inv_has", []) or []:
                inv_require_by[item].append(node_id)
        for k in flags_req:
            flag_require_by[k].append(node_id)
        # Lore 红线:narrative 文本内容扫描
        text = (node.get("narrative") or "") + " ".join(
            v.get("text", "") for v in (node.get("narrative_variants") or [])
        )
        for m in YEAR_RE.finditer(text):
            y = int(m.group(0))
            if y not in canon["years"] and 1900 <= y <= 2030:
                year_violations.append((node_id, y))
        for term in canon["forbidden_terms"]:
            if term in text:
                term_violations.append((node_id, term))

    all_flags = set(flag_set_by) | set(flag_require_by)
    dead_set_flags = sorted(set(flag_set_by) - set(flag_require_by))
    dead_require_flags = sorted(set(flag_require_by) - set(flag_set_by))
    all_inv = set(inv_add_by) | set(inv_require_by)
    dead_set_inv = sorted(set(inv_add_by) - set(inv_require_by))

    return {
        "tree_path": str(tree_path),
        "node_count": len(nodes),
        "flags": {
            k: {"set_by": flag_set_by.get(k, []), "require_by": flag_require_by.get(k, [])}
            for k in sorted(all_flags)
        },
        "flag_total": len(all_flags),
        "dead_set_flags": dead_set_flags,
        "dead_require_flags": dead_require_flags,
        "namespace_violations": namespace_violations,
        "inv": {
            k: {"add_by": inv_add_by.get(k, []), "require_by": inv_require_by.get(k, [])}
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
    parser = argparse.ArgumentParser()
    parser.add_argument("tree_path", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = audit_tree(args.tree_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return _exit_code(report, args.strict)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_audit_state.py -v`
Expected: 4 passed

- [ ] **Step 5: 跑真实 tree.json 看基线**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | tee /tmp/audit_state.before.json`
Expected: 输出现状报告(此时会有大量违规,正常)。**保留 `/tmp/audit_state.before.json` 作为清扫前基线**。

- [ ] **Step 6: Commit**

```bash
git add tools/audit_state.py tests/test_audit_state.py
git commit -m "feat(tools): audit_state.py 基础版 — flags/inv 引用矩阵 + Lore 红线"
```

---

### Task 4:`tools/audit_variants.py` — variants 覆盖矩阵

**Files:**
- Create: `tools/audit_variants.py`
- Create: `tests/test_audit_variants.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_audit_variants.py
import json
import pytest
from pathlib import Path
from tools.audit_variants import audit_variants


@pytest.fixture
def tree_with_undifferentiated_revisit(tmp_path):
    tree = {
        "initial_state": {},
        "nodes": {
            "n_revisitable": {
                "narrative": "你又来了。",
                # visit_count > 1 但没有 narrative_variants → 重复体验
                "choices": [{"text": "离开", "next": "n_end"}],
            },
            "n_end": {"narrative": "结束。", "ending_type": "test"},
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree), encoding="utf-8")
    return p


@pytest.fixture
def tree_with_dead_variant(tmp_path):
    tree = {
        "initial_state": {},
        "nodes": {
            "n_dead": {
                "narrative": "默认。",
                "narrative_variants": [
                    # 永假条件 — 不可能触发
                    {"if": {"PR_min": 9999}, "text": "你不可能看到这条。"},
                ],
            },
        },
    }
    p = tmp_path / "tree.json"
    p.write_text(json.dumps(tree), encoding="utf-8")
    return p


def test_finds_undifferentiated_revisit_node(tree_with_undifferentiated_revisit):
    """重访可达但无 variants 的节点应该被标记。"""
    report = audit_variants(tree_with_undifferentiated_revisit)
    assert "n_revisitable" in report["undifferentiated_revisit_nodes"]


def test_finds_unreachable_variant(tree_with_dead_variant):
    """永假 if 条件的 variant 应该被标记不可达。"""
    report = audit_variants(tree_with_dead_variant)
    flagged = [v for v in report["unreachable_variants"] if v["node_id"] == "n_dead"]
    assert len(flagged) == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_audit_variants.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 `tools/audit_variants.py`**

```python
"""tools/audit_variants.py — narrative_variants 覆盖矩阵 + 重复访问无分化检测。

用法:
    python tools/audit_variants.py path/to/tree.json [--strict]

输出 JSON 报告 + exit code:
    0 = 全绿
    1 = 有警告(无分化重访节点 / 不可达 variant)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools._state_sim import SimState, meets


def _is_node_revisitable(node_id: str, nodes: Dict[str, Any]) -> bool:
    """节点是否可能被多次访问 — 简单判断:有任何节点 next/choice → 它,且它本身不是 ending。"""
    if nodes[node_id].get("ending_type"):
        return False
    inbound = 0
    for other_id, other in nodes.items():
        if other.get("next") == node_id:
            inbound += 1
        for ch in other.get("choices") or []:
            if ch.get("next") == node_id:
                inbound += 1
        for v in other.get("next_variants") or []:
            if v.get("next") == node_id:
                inbound += 1
        # 节点指向自己 → 必然 revisit
        if other_id == node_id:
            for ch in other.get("choices") or []:
                if ch.get("next") == node_id:
                    return True
    return inbound >= 2


def _is_clause_obviously_unreachable(req: Dict[str, Any]) -> bool:
    """启发式:if 条件明显不可能满足(不需 BFS,纯静态)。"""
    if "PR_min" in req and "PR_max" in req:
        if int(req["PR_min"]) > int(req["PR_max"]):
            return True
    return False


def audit_variants(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    nodes = tree.get("nodes", {})

    variants_total = 0
    variants_reachable_static: List[Dict[str, Any]] = []
    unreachable_variants: List[Dict[str, Any]] = []
    undifferentiated_revisit_nodes: List[str] = []
    coverage_matrix: Dict[str, Dict[str, int]] = {}

    for node_id, node in nodes.items():
        nv = node.get("narrative_variants") or []
        next_v = node.get("next_variants") or []
        coverage_matrix[node_id] = {
            "narrative_variants": len(nv),
            "next_variants": len(next_v),
            "is_revisitable": _is_node_revisitable(node_id, nodes),
        }
        # 重访无分化
        if coverage_matrix[node_id]["is_revisitable"] and not nv and not next_v:
            undifferentiated_revisit_nodes.append(node_id)
        # 静态不可达 variant
        for v in nv + next_v:
            variants_total += 1
            cond = v.get("if") or {}
            if _is_clause_obviously_unreachable(cond):
                unreachable_variants.append({"node_id": node_id, "if": cond, "reason": "static_dead"})

    return {
        "tree_path": str(tree_path),
        "node_count": len(nodes),
        "variants_total": variants_total,
        "coverage_matrix": coverage_matrix,
        "undifferentiated_revisit_nodes": sorted(undifferentiated_revisit_nodes),
        "unreachable_variants": unreachable_variants,
    }


def _exit_code(report: Dict[str, Any], strict: bool) -> int:
    if strict and (report["undifferentiated_revisit_nodes"] or report["unreachable_variants"]):
        return 1
    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tree_path", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = audit_variants(args.tree_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return _exit_code(report, args.strict)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_audit_variants.py -v`
Expected: 2 passed

- [ ] **Step 5: 跑真实 tree.json,保存基线**

Run: `python tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json | tee /tmp/audit_variants.before.json`

- [ ] **Step 6: Commit**

```bash
git add tools/audit_variants.py tests/test_audit_variants.py
git commit -m "feat(tools): audit_variants.py — variants 覆盖矩阵 + 重复访问无分化检测"
```

---

### Task 5:`tree.json` 加 `lore_canon` 白名单

**Files:**
- Modify: `stories/hangzhou_yebanbaoan/tree.json`(顶层)

- [ ] **Step 1: 在 tree.json 顶层加 lore_canon**

用 jq 或手动编辑,在 `nodes` 同级加:

```json
{
  "lore_canon": {
    "years": [1924, 1933, 1959, 1985, 1986, 1987, 1991, 1996, 2009],
    "forbidden_terms": ["管理委员会", "员工编号", "林先生", "林总", "委员会"]
  },
  "nodes": { ... }
}
```

- [ ] **Step 2: 跑 audit_state 验证 — 应该没有 year_violations 阻断**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json`
Expected: 输出报告,`year_violations` 字段为空数组(或仅有应该修复的少量异常),exit code 不为 2

- [ ] **Step 3: 如果有 year_violations,逐一手动核查**

每条违规要么是合理的额外年份(加进白名单),要么是 typo(改 narrative)。这一步不能跳过——Lore 红线必须真的红。

- [ ] **Step 4: Commit**

```bash
git add stories/hangzhou_yebanbaoan/tree.json
git commit -m "data: tree.json 加 lore_canon 白名单 — 9 个年份锚点 + 5 个禁用术语"
```

---

## Phase 3:数据修订

> 关键纪律:每个清扫任务**完成后必须跑 path_explorer + audit_state + audit_variants**,确保 8 主结局 + 41 体验仍可达 + 没引入新违规。每个 commit 单独可回滚。

### Task 6:删除 `meta_flags` 死字段

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:90` 删除 `self.meta_flags` 初始化
- Modify: `src/ghost_story_factory/v5/player.py:253-255` 删除 `_meets_clause` 中 `meta_flags` 检查
- Modify: `src/ghost_story_factory/v5/player.py:296` 删除 `_SPOILER_KEYS` 中 `"meta_flags"`
- Modify: `tools/_state_sim.py` 同步删除 `meta_flags` 字段
- Modify: `src/ghost_story_factory/v7/`(grep 后逐个清理引用)
- Modify: `stories/hangzhou_yebanbaoan/tree.json` 删除 `initial_state.meta_flags = {}` 与所有 require 中的 `meta_flags` 块(若有)

- [ ] **Step 1: 先 grep 看影响范围**

Run:
```bash
grep -rn "meta_flags" src/ tools/ tests/ stories/ docs/
```
Expected: 列出所有引用。

- [ ] **Step 2: 写"删除后状态"的回归测试**

```python
# tests/test_meta_flags_removed.py(临时,Pass 1 完成后可删)
def test_state_does_not_have_meta_flags():
    from ghost_story_factory.v5.player import State
    s = State({})
    assert not hasattr(s, "meta_flags")
```

- [ ] **Step 3: 跑测试确认失败(因为字段还在)**

Run: `pytest tests/test_meta_flags_removed.py -v`
Expected: FAIL (`hasattr` 为 True)

- [ ] **Step 4: 删除 player.py 中所有 `meta_flags` 引用**

按 grep 结果逐个删除。`State.__init__` 中那一行删掉,`_meets_clause` 中那个循环删掉,`_SPOILER_KEYS` 中删掉那一项。

- [ ] **Step 5: 删除 _state_sim.py 中的 meta_flags 字段 + 相关检查**

- [ ] **Step 6: 跑测试**

Run:
```bash
pytest tests/test_meta_flags_removed.py tests/test_state_sim.py tests/test_audit_state.py -v
```
Expected: All pass

- [ ] **Step 7: 删除 tree.json 中 meta_flags 引用**(若有)

Run: `grep -n "meta_flags" stories/hangzhou_yebanbaoan/tree.json`
逐处删除(应该很少,可能只有 `initial_state.meta_flags`)。

- [ ] **Step 8: 最关键 — 跑 path_explorer 回归**

Run: `python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json`
Expected: 8 主结局可达性输出与之前一致,exit code 0。

- [ ] **Step 9: 实跑游戏简单冒烟**

Run: `GHOST_FAST=1 python play.py`(主菜单选默认剧本,玩到第一个选项,退出即可)
Expected: 不报 AttributeError 或类似异常。

- [ ] **Step 10: Commit + 删除临时测试**

```bash
rm tests/test_meta_flags_removed.py
git add -A
git commit -m "refactor(state): 删除 meta_flags 死字段(0 写 0 读)

ADR-007 依据。reduces State from 14 to 13 fields.
v7 自由继承机制如真的需要再单独加 meta.* namespace。"
```

---

### Task 7:删除 `route` 字段(v7 已废弃)

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:84` 删除 `self.route` 初始化
- Modify: `src/ghost_story_factory/v5/player.py:225-226` 删除 `route_is` 检查
- Modify: `src/ghost_story_factory/v5/player.py:296` 删除 `_SPOILER_KEYS` 中 `"route_is"`
- Modify: `tools/_state_sim.py` 同步
- Modify: `src/ghost_story_factory/v7/`
- Modify: `stories/hangzhou_yebanbaoan/tree.json` 删除所有 `set_route` effects 与 `route_is` require

- [ ] **Step 1: grep 影响范围**

Run: `grep -rn "route" src/ tools/ stories/ | grep -v ".pyc" | grep -v "node_modules"`(注意 "route" 是常见字符串,要人眼区分 State.route vs URL route 等)

- [ ] **Step 2: 写删除后回归测试**

类似 Task 6 Step 2,断言 `not hasattr(state, "route")`。

- [ ] **Step 3: 跑失败,然后删除 player.py 引用,跑通过**

- [ ] **Step 4: 删除 tree.json 中 `route_is` / `set_route`**

```bash
grep -n "route_is\|set_route" stories/hangzhou_yebanbaoan/tree.json
```
逐处删除。

- [ ] **Step 5: path_explorer + audit + 冒烟**

- [ ] **Step 6: Commit**

```bash
git commit -m "refactor(state): 删除 route 字段(v7 已废弃)

ADR-007 依据。reduces State from 13 to 12 fields。"
```

---

### Task 8:`shifts_completed` 改 `@property` 派生

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:79` 删除 `self.shifts_completed` 字段初始化
- Modify: `src/ghost_story_factory/v5/player.py:165-169`(apply 中 +1 shifts_completed 的逻辑)→ 改为只更新 `visited_landmarks`,shifts_completed 自动从 visited_landmarks 派生
- Modify: `tools/_state_sim.py` 同步改 property

- [ ] **Step 1: 写测试 — shifts_completed 应该自动等于 visited_landmarks 中 S1-S6 的数量**

```python
# tests/test_shifts_completed_derived.py
def test_shifts_completed_derived_from_visited():
    from ghost_story_factory.v5.player import State
    s = State({"visited_landmarks": ["S1", "S2", "S3"]})
    assert s.shifts_completed == 3

def test_shifts_completed_ignores_non_S_landmarks():
    from ghost_story_factory.v5.player import State
    s = State({"visited_landmarks": ["S1", "S2", "extra_node"]})
    assert s.shifts_completed == 2
```

- [ ] **Step 2: 跑失败**

Expected: AttributeError 或值不对

- [ ] **Step 3: 实现 @property**

在 State 类里:
```python
@property
def shifts_completed(self) -> int:
    return len([l for l in self.visited_landmarks if l in {"S1", "S2", "S3", "S4", "S5", "S6"}])
```
删掉 `__init__` 中 `self.shifts_completed`。
检查 `apply()` 里所有 `self.shifts_completed += 1`(line 165-169 附近)的地方,改为只 `visited_landmarks.append(...)`,派生属性会自动更新。

- [ ] **Step 4: 跑测试**

Run: `pytest tests/test_shifts_completed_derived.py -v && pytest tests/test_state_sim.py -v`

- [ ] **Step 5: path_explorer + 冒烟**

特别注意:之前可能有玩法靠 effects 直接 set `shifts_completed`(如关底强制 +1),现在它是 property 不能赋值。要么改为派生兼容,要么这种 effects 改写 visited_landmarks。

- [ ] **Step 6: Commit**

```bash
git commit -m "refactor(state): shifts_completed 改 @property 派生

ADR-007 依据。从 visited_landmarks 中 S1-S6 数量自动算,
消除两处计数可能不一致的边界情况。"
```

---

### Task 9:合并 `skipped_landmarks` 与 `shifts_skipped`

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:80, 85` — 选一个保留(推荐保留 `skipped_landmarks: List[str]`,`shifts_skipped` 改 @property)
- Modify: `tools/_state_sim.py`
- Modify: `stories/hangzhou_yebanbaoan/tree.json` — 把所有 `shifts_skipped += 1` 改为 `skipped_landmarks` append;`shifts_skipped_min: N` 留作 player.py 派生属性比较

- [ ] **Step 1: grep 看哪个用得多**

Run: `grep -rn "shifts_skipped\|skipped_landmarks" stories/hangzhou_yebanbaoan/tree.json | wc -l`

- [ ] **Step 2: 写测试**

```python
def test_shifts_skipped_derived_from_skipped_landmarks():
    from ghost_story_factory.v5.player import State
    s = State({"skipped_landmarks": ["S2", "S5"]})
    assert s.shifts_skipped == 2
```

- [ ] **Step 3: 跑失败**

- [ ] **Step 4: 实现:`shifts_skipped` 改 @property,`skipped_landmarks` 留**

- [ ] **Step 5: 迁移 tree.json — `shifts_skipped += 1` 改为 push 到 skipped_landmarks**

具体 effects 形式可能是:
```json
{"effects": {"shifts_skipped": 1}} → {"effects": {"skip_landmark": "S3"}}
```
需要在 player.apply 里加 `skip_landmark` 处理(append 到 skipped_landmarks)。

- [ ] **Step 6: 全套回归**

- [ ] **Step 7: Commit**

```bash
git commit -m "refactor(state): 合并 shifts_skipped 到 skipped_landmarks(派生)"
```

---

### Task 10:下沉 `s{1-7}_*` 局部 flag + 合并 `*_revisit_*` 系列

**Files:**
- Modify: `stories/hangzhou_yebanbaoan/tree.json` — 大批量重命名

> 这是 Pass 1 最大的 commit,也是最容易出错的。**严格分批做,每批 ≤ 20 个 flag 就跑一次完整回归**。

- [ ] **Step 1: 用 audit_state 列出所有 `s\d+_` 前缀的 flag**

Run:
```bash
python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | python -c "
import json, sys, re
report = json.load(sys.stdin)
pat = re.compile(r'^s[1-7]_')
for k in report['flags']:
    if pat.match(k):
        print(k)
" | tee /tmp/s_prefix_flags.txt
```
Expected: 60+ 行 flag 名。

- [ ] **Step 2: 决定每个 flag 的归宿**(人工判断,但自动化辅助)

把 `/tmp/s_prefix_flags.txt` 拆成三类:
- **下沉为 `oneshot.*`**:大部分一次性事件(`s1_threw_coat` → `oneshot.s1_threw_coat`)
- **替换为 visit_count**:重访型(`s3_revisit_temple` → `visit_count_min: {"n_s3_arrive": 2}`)
- **保留但加 namespace**:跨节点引用的少数(改为 `arc.s1_xxx`)

写在 `/tmp/s_flag_migration_plan.md`。

- [ ] **Step 3: 写迁移脚本(一次性,放在 tools/ 不 commit)**

```python
# tools/_migrate_s_flags.py(临时,不 commit 进 git)
import json, re
from pathlib import Path

p = Path("stories/hangzhou_yebanbaoan/tree.json")
data = json.loads(p.read_text())

# 从 /tmp/s_flag_migration_plan.md 读取 mapping
# 这里给一个示意 dict;实际从外部文件读
mapping = {
    "s1_threw_coat": ("oneshot", "s1_threw_coat"),
    # ... 60+ 项
}

def rewrite(obj):
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k == "flags" and isinstance(v, dict):
                new[k] = {}
                for fk, fv in v.items():
                    if fk in mapping:
                        ns, name = mapping[fk]
                        new[k][f"{ns}.{name}"] = fv
                    else:
                        new[k][fk] = fv
            else:
                new[k] = rewrite(v)
        return new
    if isinstance(obj, list):
        return [rewrite(x) for x in obj]
    return obj

data = rewrite(data)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2))
```

- [ ] **Step 4: 分 3 批跑迁移脚本,每批后跑回归**

每批 ≤ 20 个 flag:
1. 改 mapping 加 20 项
2. `python tools/_migrate_s_flags.py`
3. `python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json`
4. `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json`
5. 实跑游戏冒烟
6. **Commit**(单独一个 commit,`refactor(data): 下沉 s* flag 第 N 批,共 X 个`)
7. 下一批

- [ ] **Step 5: 处理 `*_revisit_*` 系列**

类似流程,但 mapping 是把 `s6_revisit_well` 这类 flag 替换为 `visit_count_min: {"n_s6_arrive": 2}` 形式的 require —— **这个不是 rename,是结构改写**,需要写更复杂的 transform。建议:

```python
# 搜出所有引用 s6_revisit_well 的 require
# 把 require["flags"] 中删除该项
# 同时在 require 里加 visit_count_min: {"n_s6_arrive": 2}
# 同时在原本 set 这个 flag 的 effects 里删除该项(因为 visit_counts 是引擎自动维护的)
```

每改 1 个 *_revisit_* 跑一次完整回归。

- [ ] **Step 6: 全部完成后,确认 audit_state 的 flag 总数**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | jq '.flag_total'`
Expected: 数字明显下降(预期从 234 降到 ~120,本任务只清掉一部分;Task 11-12 还会再降)

---

### Task 11:处理 15 件 `inv+flag` 双写道具

**Files:**
- Modify: `stories/hangzhou_yebanbaoan/tree.json`

- [ ] **Step 1: 用 audit_state 找双写道具**

写一个临时小脚本:

```python
# tools/_find_double_write.py(临时,不 commit)
import json
from pathlib import Path
from tools.audit_state import audit_tree

report = audit_tree(Path("stories/hangzhou_yebanbaoan/tree.json"))
# inv name 与 flag name 在同一节点 effects 出现 → 双写
for node_id in report["inv"]:
    add_by = report["inv"][node_id]["add_by"]
    for n in add_by:
        # 看该节点的 effects 是不是同时 set 了同名 flag
        ...
print("...")
```

输出 15 件双写道具清单 + 每件涉及节点。

- [ ] **Step 2: 每件道具决定 inv-only 还是 flag-only**

判定规则(写进 ADR-007 附录):
- 物理道具(可丢弃/可消耗):**inv-only**(删伴生 flag)
- 信号性道具("看过/听过"标记):**flag-only**(删 inv,纯 flag 表达,且 flag 名进 `know.*` namespace)

- [ ] **Step 3: 分批迁移(每批 ≤ 5 件)**

每件改完跑一次回归,commit 一次。

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor(data): 处理 N 件 inv+flag 双写道具,统一为 inv-only / know.*"
```

---

### Task 12:重命名 `know-*` 类 flag 为 `know.*` namespace

**Files:**
- Modify: `stories/hangzhou_yebanbaoan/tree.json`

- [ ] **Step 1: 用 audit_state 列出 namespace_violations**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | jq '.namespace_violations'`
Expected: 每个未 namespace 化的 flag 出现一次。

- [ ] **Step 2: 决定 namespace 归属**

每个 flag 决定:
- 玩家知识 → `know.*`(如 `claimed_linmou` → `know.linmou_claimed`)
- 一次性事件 → `oneshot.*`(如 `radio_listened` → `oneshot.radio_listened`)
- 故事弧线 → `arc.*`(如 `lin_arc_done` → `arc.lin_act_2_done`)
- 临时状态 → `state.*`(如 `flashlight_on` → `state.flashlight_on`)

- [ ] **Step 3: 同样用 mapping 脚本批量改**

(参考 Task 10 Step 3-4 的脚本)

- [ ] **Step 4: 验证 audit_state 的 namespace_violations 为 0**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | jq '.namespace_violations | length'`
Expected: 0

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(data): 所有 flag 收编进 6 namespace(know./oneshot./arc./route./state./meta.)"
```

---

## Phase 4:path_explorer 三大盲区补丁

### Task 13:path_explorer 加 variants 触发追踪 + key 一致性 + picker 展开

**Files:**
- Modify: `tools/path_explorer.py`

> 这一步在 audit 工具完工后做,因为 path_explorer 已经改用 `_state_sim`(Task 1),现在补三大盲区。

- [ ] **Step 1: 写测试 — variants 触发追踪**

```python
# tests/test_path_explorer_variants.py
def test_explorer_reports_variant_hit_or_miss(tmp_path):
    """探索完成后,每个 narrative_variant 应该有一个 hit/miss 标记。"""
    # ... 构造一棵带 variants 的小 tree,跑 explorer,断言报告有 variant_hits 字段
```

- [ ] **Step 2: 写测试 — require/effects key 一致性**

```python
def test_explorer_reports_orphan_require_key():
    """如果 require 引用 flags['x'] 但全树没有 effects.flags.x 写入,explorer 应该报。"""
```

- [ ] **Step 3: 写测试 — picker 节点动态展开**

```python
def test_explorer_walks_into_picker_choices():
    """node.is_map_picker 节点应该被识别,picker_choices 静态展开。"""
```

- [ ] **Step 4: 实现三块功能**

具体改动较大,核心:
1. 在 BFS 探索时,每访问一个节点,模拟 `meets()` 评估每个 variant 的 if,记录 hit/miss
2. 报告末尾输出 orphan flag(被 require 但没人 set)
3. 识别 picker 节点(`_is_map_picker` / `_is_tool` 之类标记),把它的 picker_choices(从 known_landmarks 派生)展开为伪 choices

- [ ] **Step 5: 跑全套测试**

```bash
pytest tests/test_path_explorer_variants.py tests/test_state_sim.py tests/test_audit_*.py -v
```

- [ ] **Step 6: 跑真实 tree.json 看新输出**

Run: `python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json`
Expected: 多了 variant_hits / orphan_keys / picker_paths 三个新节,exit code 0

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(tools): path_explorer 补 variants 追踪 / key 一致性 / picker 展开

修复 QA Path Tester 指出的三大盲区:
- variants 是否能被任何路径触发(hit/miss 矩阵)
- require 引用的 flag 是否在某 effects 里 set 过(orphan_keys)
- picker / tool 节点的动态选项静态展开(picker_paths)"
```

---

## Phase 5:最终验收

### Task 14:全套回归 + flags 唯一键 ≤ 80 验收

**Files:** (无新增,只跑命令)

- [ ] **Step 1: 跑 audit_state 看 flag 总数**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | jq '.flag_total'`
Expected: ≤ 80

- [ ] **Step 2: 死字段清单清零**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | jq '.dead_set_flags, .dead_require_flags'`
Expected: 空数组(或极少数 intentional dead branch,且都标在 ADR-007 附录里)

- [ ] **Step 3: namespace 违规清零**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | jq '.namespace_violations | length'`
Expected: 0

- [ ] **Step 4: Lore 红线清零**

Run: `python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json | jq '.year_violations, .term_violations'`
Expected: 全部空数组

- [ ] **Step 5: variants 重访无分化清单 — 有基线对比**

Run: `python tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json | jq '.undifferentiated_revisit_nodes | length'`

记下数字,与 `/tmp/audit_variants.before.json` 中的同字段对比。**Pass 1 不要求清零,但要求不增加**(变化 ≤ 0)。这个清零是 Pass 2 的目标。

- [ ] **Step 6: path_explorer 全套回归**

Run: `python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json`
Expected: 8 个主结局可达,41 体验全通过,exit code 0,与 Pass 1 启动前的输出对照(可达性 diff = 空)。

- [ ] **Step 7: 全 pytest 跑过**

Run: `pytest tests/ -v --tb=short`
Expected: All pass

- [ ] **Step 8: 实跑游戏 — 至少跑通一条结局**

```bash
GHOST_FAST=1 python play.py
```
玩到 E_TRUE(最容易达成的真结局之一),或玩到任意 ending,确认无运行时异常。

- [ ] **Step 9: 写 Pass 1 完成报告**

Create: `docs/team-reviews/2026-05-XX-pass1-completion.md`
内容:
- audit_state 前后对比(flag_total / dead_set / dead_require / namespace_violations 各项数字)
- audit_variants 前后对比
- path_explorer 可达性 diff
- ADR-007 落地清单(14 字段 → 11 字段)
- Pass 2 候选清单(CG Codex / PKG / UX learn 反馈)

- [ ] **Step 10: Final commit + 标 tag**

```bash
git add -A
git commit -m "chore: Pass 1 完成 — 状态空间从 234 flags 降到 ≤ 80,死字段清零

ADR-007 全面落地,所有 audit 脚本通过,8 主结局 + 41 体验仍可达。
完整对比报告见 docs/team-reviews/2026-05-XX-pass1-completion.md。

下一步:Pass 2 候选评审(由 script-review-team 决定)。"

git tag -a pass1-complete -m "Pass 1: 状态空间审计 + Flag 降级清扫完成"
```

---

## 验收 checklist 总览(从评审报告 § 9 抄过来,逐项核对)

- [ ] `tools/audit_variants.py` 与 `tools/audit_state.py` 输出 JSON 报告 + exit code
- [ ] `tree.json` 全局 flags 唯一键从 **234 降到 ≤ 80**
- [ ] 死字段清单至少标记 5 个,可执行删除
- [ ] **`meta_flags` 字段从 State 删除**
- [ ] **`shifts_completed` 改为 `@property` 派生**
- [ ] 抽出 `tools/_state_sim.py`,与 `path_explorer.py` 共享解析逻辑
- [ ] **commit `docs/architecture/ADR-007-state-contract.md`**
- [ ] State 类签名(除 `meta_flags` 删除外)保持不变,零引擎新增字段
- [ ] **`tree.json` 顶层 `lore_canon.years` 白名单建立**(9 个年份)
- [ ] audit 脚本在年份越界 / 现代化术语污染时返回非零
- [ ] `path_explorer` 跑过 → 8 个主结局 + 41 种结局体验全部仍可达
- [ ] `pytest tests/test_audit_*.py` 全绿
- [ ] **path_explorer 三大盲区补丁:variants 触发追踪 / require-effects key 一致性 / picker 节点动态展开**
- [ ] 不破坏 17 ending 可达性(Lore 红线)

---

## Pass 2 候选(供 script-review-team 在 Pass 1 完成后再评)

按评审报告"不同意见记录":
- **Meta-Game Designer**:CG Codex(玩家可见的结局/伏笔收集本)— sync 版优先 / team 版 PKG 优先,Pass 2 评审决定
- **UX Designer**:`effects.learn` + `▌ 知道 · X ▐` 反馈条
- **Lore Keeper**:PKG 字段 source/confidence 维度
- **共识**:试点 NPC 锁定 `n_npc_drowned_official`(林副科长)

每个候选独立走一次 script-review-team 评审 → spec → plan → 实施。
