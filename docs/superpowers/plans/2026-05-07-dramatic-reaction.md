# 戏剧化反应机制 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让"已解开的伏笔/推论/母题"驱动节点 narrative 切档,把元数据架构(14 伏笔 / 4 推论 / 6 母题)从档案视图(`s` 键)激活到主流程,让玩家在叙事中感受到世界"记得"自己做过什么。

**Architecture:** 三层职责分离。① **引擎层**:扩展 `_meets_clause()` 加 3 个新条件(`deduction_resolved` / `foreshadow_resolved` / `theme_resolved`),通过 State 持 `save_manager + story_id` 引用查询单一真相源(拒绝镜像 flags)。② **守门层**:新建 `audit_reactions.py` 检测 DEAD_REACTION / UNREACHABLE_REACTION / ORPHAN_RESOLVE 三红线,接入 CI。③ **内容层**:用 Lore 锚点表约束 7 个反应节点的 variant 创作。default variant 保留 + 独立可读 = 硬约束。

**Tech Stack:** Python 3.11+ / pytest / 现有 v5 player.py + v7 save_manager.py + tree.json fragments

**评审依据**:`docs/team-reviews/2026-05-07-dramatic-reaction.md`(决议:修改后放行)

---

## 关键决议(评审报告固化)

| 议题 | 决议 |
|---|---|
| State 注入方案 | **A** — `State.__init__(..., save_manager=None, story_id=None)`,None 时新条件返回 False(向后兼容) |
| `on_resolve_inject` 镜像 flags | **拒绝** — 单一真相源 = save_manager,职责分离铁律 |
| variant schema 扩展(`voice_constraint`/`priority`/`fallback_to_default`) | **不加新字段** — 优先级用列表序;默认 variant 由 audit 强制;立场约束用 Lore 锚点表 |
| list 语义 | **ANY** — `["D-001","D-002"]` 任一解开即满足;ALL 用 `all_of` 显式 |
| meta./run./motif. 命名空间前缀 | **不上前缀** — 仅 ADR 文档说明语义 |
| `archive_view` 反向影响索引 | **采纳** |
| true ending 解锁 = 解开 N 推论 | **拒绝**作为硬门槛,改档案彩蛋 |
| 切换动画(glitch/弹窗) | **拒绝** — 节点级静默切;母题级首次过渡 narration |

---

## File Structure

**Create**:
- `tools/audit_reactions.py` — 反应式 variant 死代码 / 不可达 / 孤儿 resolver 检测
- `tests/test_reaction_engine.py` — `_meets_clause` 三新条件单元测试
- `tests/test_reaction_coverage.py` — 反应式 variant 全可达测试
- `data/lore_voice_matrix.json` — 4 NPC × 2 状态语气矩阵(Lore Keeper 出表)
- `data/motif_anchors.json` — 6 母题 × 18 视听嗅锚点
- `docs/architecture/ADR-008-reaction-mechanism.md` — 反应机制契约 + 跨周目认知继承

**Modify**:
- `src/ghost_story_factory/v7/save_manager.py` — 加 `get_resolved_foreshadows(story_id) -> set` 方法
- `src/ghost_story_factory/v5/player.py:73-100` — `State.__init__` 加 `save_manager` + `story_id` 参数
- `src/ghost_story_factory/v5/player.py:199-252` — `_meets_clause` 加 3 个新条件分支
- `src/ghost_story_factory/v5/player.py` 主循环入口 — 构造 State 时传入 save_manager + story_id
- `src/ghost_story_factory/v7/tui_player.py` 主循环入口 — 同上
- `src/ghost_story_factory/v7/archive_view.py` — 加反向影响索引
- `tools/merge_fragments.py` STORY_META — 加 `reaction_contracts` 字段(剧本契约)
- `stories/hangzhou_yebanbaoan/_fragment_v7_*.json` — 7 节点新增反应式 variant
- `tests/conftest.py` — 已存在,无需改

**审计前提**:`audit_reactions.py` 必须**先于**内容填充(Phase 4)上 CI,否则反应式 variant 容易写成死代码。

---

## Phase 1:引擎扩展(单一真相源 + 三条件)

### Task 1.1:SaveManager 暴露 `get_resolved_foreshadows`

**Files:**
- Modify: `src/ghost_story_factory/v7/save_manager.py`(在 `is_foreshadow_resolved` 方法附近,~365 行)
- Test: `tests/test_save_manager_query.py`(新建)

- [ ] **Step 1: 写失败测试**

```python
# tests/test_save_manager_query.py
from ghost_story_factory.v7.save_manager import SaveManager
import tempfile, json
from pathlib import Path

def _save_with(data):
    p = Path(tempfile.mkdtemp()) / "save.json"
    with p.open("w") as f:
        json.dump(data, f)
    return SaveManager(p)

def test_get_resolved_foreshadows_returns_set():
    sm = _save_with({
        "version": 4,
        "foreshadows_resolved": {"杭州_v7": ["F-001", "F-002"]},
    })
    result = sm.get_resolved_foreshadows("杭州_v7")
    assert result == {"F-001", "F-002"}
    assert isinstance(result, set)

def test_get_resolved_foreshadows_empty_story_returns_empty_set():
    sm = _save_with({"version": 4, "foreshadows_resolved": {}})
    assert sm.get_resolved_foreshadows("不存在") == set()
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_save_manager_query.py -v`
Expected: FAIL with "AttributeError: 'SaveManager' object has no attribute 'get_resolved_foreshadows'"

- [ ] **Step 3: 实现方法**

在 `src/ghost_story_factory/v7/save_manager.py` 的 `is_foreshadow_resolved` 方法之后(~373 行)加:

```python
def get_resolved_foreshadows(self, story_id: str) -> set:
    """返回某 story 已解开的所有 foreshadow id 的 set(给 theme_resolved 检查用)。"""
    return set(self.data.get("foreshadows_resolved", {}).get(story_id, []))
```

- [ ] **Step 4: 测试通过**

Run: `pytest tests/test_save_manager_query.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add src/ghost_story_factory/v7/save_manager.py tests/test_save_manager_query.py
git commit -m "feat(save-manager): 加 get_resolved_foreshadows 查询方法"
```

---

### Task 1.2:State 接受 `save_manager` + `story_id` 引用

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:73-100`(State 类 `__init__`)
- Test: `tests/test_state_save_binding.py`(新建)

- [ ] **Step 1: 写失败测试**

```python
# tests/test_state_save_binding.py
from ghost_story_factory.v5.player import State

def test_state_default_save_manager_is_none():
    """向后兼容:不传 save_manager 仍能构造。"""
    s = State({})
    assert s.save_manager is None
    assert s.story_id is None

def test_state_accepts_save_manager_injection():
    """新引擎入口可传入 save_manager + story_id。"""
    sentinel = object()
    s = State({}, save_manager=sentinel, story_id="杭州_v7")
    assert s.save_manager is sentinel
    assert s.story_id == "杭州_v7"
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_state_save_binding.py -v`
Expected: FAIL with TypeError(`__init__` 不接受 `save_manager` 参数)

- [ ] **Step 3: 修改 State.__init__**

在 `src/ghost_story_factory/v5/player.py:76` 修改签名,在末尾追加属性:

```python
def __init__(self, initial: Dict[str, Any], save_manager=None, story_id: Optional[str] = None):
    # ... 现有所有字段保持不变 ...
    # 在 self._last_events 之后(~line 100)追加:
    # 反应机制:跨周目持久化层引用(单一真相源 = save_manager)
    self.save_manager = save_manager
    self.story_id = story_id
```

- [ ] **Step 4: 测试通过 + 全套回归**

```bash
pytest tests/test_state_save_binding.py -v
# Expected: 2 PASS
pytest tests/ -x -q
# Expected: 全套回归通过(向后兼容验证)
```

- [ ] **Step 5: Commit**

```bash
git add src/ghost_story_factory/v5/player.py tests/test_state_save_binding.py
git commit -m "feat(state): State 持 save_manager+story_id 引用(单一真相源)"
```

---

### Task 1.3:`_meets_clause` 加 `deduction_resolved` 分支

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:199-252`(`_meets_clause` 方法)
- Test: `tests/test_reaction_engine.py`(新建)

- [ ] **Step 1: 写失败测试**

```python
# tests/test_reaction_engine.py
from ghost_story_factory.v5.player import State

class FakeSave:
    def __init__(self, resolved_d=None, resolved_f=None):
        self._resolved_d = set(resolved_d or [])
        self._resolved_f = set(resolved_f or [])
    def is_deduction_resolved(self, sid, did): return did in self._resolved_d
    def is_foreshadow_resolved(self, sid, fid): return fid in self._resolved_f
    def get_resolved_foreshadows(self, sid): return set(self._resolved_f)

def test_deduction_resolved_str_match():
    s = State({}, save_manager=FakeSave(resolved_d=["D-001"]), story_id="杭州_v7")
    assert s.meets({"deduction_resolved": "D-001"}) is True
    assert s.meets({"deduction_resolved": "D-999"}) is False

def test_deduction_resolved_list_any_semantic():
    """list 是 ANY 语义:任一解开即满足。"""
    s = State({}, save_manager=FakeSave(resolved_d=["D-001"]), story_id="杭州_v7")
    assert s.meets({"deduction_resolved": ["D-001", "D-999"]}) is True
    assert s.meets({"deduction_resolved": ["D-998", "D-999"]}) is False

def test_deduction_resolved_no_save_manager_returns_false():
    """save_manager None 时安全降级:新条件返回 False。"""
    s = State({})  # 无 save_manager
    assert s.meets({"deduction_resolved": "D-001"}) is False
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_reaction_engine.py -v -k deduction`
Expected: 3 FAIL(条件被忽略,所有 meets() 都返回 True)

- [ ] **Step 3: 在 _meets_clause 加分支**

在 `src/ghost_story_factory/v5/player.py:251`(`character` 检查之后,`return True` 之前)加:

```python
        # 反应机制:已解开的推论(单条 / list ANY 语义)
        if "deduction_resolved" in require:
            sm = self.save_manager
            if sm is None or self.story_id is None:
                return False  # 安全降级:无 save 引用 = 条件不满足
            ids = require["deduction_resolved"]
            ids = [ids] if isinstance(ids, str) else list(ids or [])
            if not any(sm.is_deduction_resolved(self.story_id, x) for x in ids):
                return False
```

- [ ] **Step 4: 测试通过**

Run: `pytest tests/test_reaction_engine.py -v -k deduction`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add src/ghost_story_factory/v5/player.py tests/test_reaction_engine.py
git commit -m "feat(engine): _meets_clause 加 deduction_resolved 条件(ANY 语义)"
```

---

### Task 1.4:`_meets_clause` 加 `foreshadow_resolved` 分支

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py`(在 `deduction_resolved` 之后)
- Test: `tests/test_reaction_engine.py`(append)

- [ ] **Step 1: 加测试**

```python
# tests/test_reaction_engine.py(追加)
def test_foreshadow_resolved_str_match():
    s = State({}, save_manager=FakeSave(resolved_f=["F-001"]), story_id="杭州_v7")
    assert s.meets({"foreshadow_resolved": "F-001"}) is True
    assert s.meets({"foreshadow_resolved": "F-999"}) is False

def test_foreshadow_resolved_list_any():
    s = State({}, save_manager=FakeSave(resolved_f=["F-002"]), story_id="杭州_v7")
    assert s.meets({"foreshadow_resolved": ["F-001", "F-002"]}) is True
    assert s.meets({"foreshadow_resolved": []}) is False

def test_foreshadow_resolved_no_save_returns_false():
    s = State({})
    assert s.meets({"foreshadow_resolved": "F-001"}) is False
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_reaction_engine.py -v -k foreshadow`
Expected: 3 FAIL

- [ ] **Step 3: 加分支(deduction 块之后)**

```python
        if "foreshadow_resolved" in require:
            sm = self.save_manager
            if sm is None or self.story_id is None:
                return False
            ids = require["foreshadow_resolved"]
            ids = [ids] if isinstance(ids, str) else list(ids or [])
            if not any(sm.is_foreshadow_resolved(self.story_id, x) for x in ids):
                return False
```

- [ ] **Step 4: 测试通过**

Run: `pytest tests/test_reaction_engine.py -v -k foreshadow`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add src/ghost_story_factory/v5/player.py tests/test_reaction_engine.py
git commit -m "feat(engine): _meets_clause 加 foreshadow_resolved 条件"
```

---

### Task 1.5:`_meets_clause` 加 `theme_resolved` 分支

**关键点**:theme_resolved 检查 `themes[id].manifestations ⊆ resolved_set`,需要 tree 引用。把 tree 通过 State 传入(`State.tree`,默认 None)。

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py`(State.__init__ 加 `tree` 参数 + _meets_clause 加分支)
- Test: `tests/test_reaction_engine.py`(append)

- [ ] **Step 1: 加测试**

```python
# tests/test_reaction_engine.py(追加)
def _tree_with_themes(themes):
    return {"themes": themes}

def test_theme_resolved_all_manifestations_resolved():
    """6 母题"通透":所有 manifestations 全部解开。"""
    tree = _tree_with_themes({
        "hangzhou_constant": {"manifestations": ["F-001", "F-002"]},
    })
    sm = FakeSave(resolved_f=["F-001", "F-002"])
    s = State({}, save_manager=sm, story_id="杭州_v7")
    s.tree = tree
    assert s.meets({"theme_resolved": "hangzhou_constant"}) is True

def test_theme_resolved_partial_returns_false():
    tree = _tree_with_themes({"t1": {"manifestations": ["F-1", "F-2", "F-3"]}})
    sm = FakeSave(resolved_f=["F-1"])  # 只解开 1/3
    s = State({}, save_manager=sm, story_id="杭州_v7")
    s.tree = tree
    assert s.meets({"theme_resolved": "t1"}) is False

def test_theme_resolved_list_any():
    """list ANY:任一母题通透即可。"""
    tree = _tree_with_themes({
        "t1": {"manifestations": ["F-1"]},
        "t2": {"manifestations": ["F-2"]},
    })
    sm = FakeSave(resolved_f=["F-2"])  # t2 通透,t1 没
    s = State({}, save_manager=sm, story_id="杭州_v7")
    s.tree = tree
    assert s.meets({"theme_resolved": ["t1", "t2"]}) is True

def test_theme_resolved_no_tree_returns_false():
    s = State({})
    assert s.meets({"theme_resolved": "t1"}) is False
```

- [ ] **Step 2: 跑测试验证失败**

Run: `pytest tests/test_reaction_engine.py -v -k theme`
Expected: 4 FAIL

- [ ] **Step 3: 加 tree 字段 + 分支**

修改 `State.__init__` 末尾(在 self.story_id 之后):

```python
        # tree 引用(给 theme_resolved 查 manifestations 用)。默认 None,引擎入口处注入。
        self.tree: Optional[Dict[str, Any]] = None
```

在 `_meets_clause` 的 `foreshadow_resolved` 块之后加:

```python
        if "theme_resolved" in require:
            sm = self.save_manager
            if sm is None or self.story_id is None or self.tree is None:
                return False
            ids = require["theme_resolved"]
            ids = [ids] if isinstance(ids, str) else list(ids or [])
            themes = (self.tree.get("themes") or {})
            resolved = sm.get_resolved_foreshadows(self.story_id)
            def _theme_done(tid):
                meta = themes.get(tid) or {}
                manif = set(meta.get("manifestations") or [])
                return bool(manif) and manif.issubset(resolved)
            if not any(_theme_done(x) for x in ids):
                return False
```

- [ ] **Step 4: 测试通过**

Run: `pytest tests/test_reaction_engine.py -v`
Expected: 全部 13 PASS(deduction 3 + foreshadow 3 + theme 4 + state binding 2 + 1 句号)

- [ ] **Step 5: Commit**

```bash
git add src/ghost_story_factory/v5/player.py tests/test_reaction_engine.py
git commit -m "feat(engine): _meets_clause 加 theme_resolved 条件(manifestations 全集检查)"
```

---

### Task 1.6:引擎入口处注入 save_manager + tree 到 State

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py` 主循环 `play()` 函数(找到 `State(...)` 构造点)
- Modify: `src/ghost_story_factory/v7/tui_player.py` State 构造点

- [ ] **Step 1: 定位构造点**

```bash
grep -n "State(" src/ghost_story_factory/v5/player.py src/ghost_story_factory/v7/tui_player.py
```

记录所有 `State(...)` 构造调用的行号。

- [ ] **Step 2: 修改构造调用**

在 v5/player.py 的 play() 函数里,找到 `state = State(initial)` 的地方,改为:

```python
state = State(initial, save_manager=save_manager, story_id=story_id)
state.tree = tree
```

(`save_manager`/`story_id`/`tree` 在 play() 函数内已是局部变量。)

v7/tui_player.py 同改。

- [ ] **Step 3: 端到端 smoke 测试**

```bash
# 不打开实际游戏,只验证 import + 构造无异常
python -c "from ghost_story_factory.v5.player import State; State({})"
# Expected: 无异常
pytest tests/ -x -q
# Expected: 全套回归通过
```

- [ ] **Step 4: Commit**

```bash
git add src/ghost_story_factory/v5/player.py src/ghost_story_factory/v7/tui_player.py
git commit -m "feat(engine): play()/tui 入口给 State 注入 save_manager+tree"
```

---

## Phase 2:audit 工具 + CI(QA 守门)

### Task 2.1:`tree.json` 加 `reaction_contracts` 字段

**Files:**
- Modify: `tools/merge_fragments.py`(STORY_META section)
- Modify: 重新跑合并器,生成新 tree.json
- Test: `tests/test_reaction_contracts_schema.py`(新建)

`reaction_contracts` 是顶层字段,声明每个 deduction/foreshadow/theme 的 resolver 节点(在哪些节点 on_resolve)+ consumer 节点(哪些节点的 variants 消费它)。

- [ ] **Step 1: 加 schema 测试**

```python
# tests/test_reaction_contracts_schema.py
import json
from pathlib import Path

TREE = Path("stories/hangzhou_yebanbaoan/tree.json")

def test_tree_has_reaction_contracts_field():
    tree = json.loads(TREE.read_text())
    assert "reaction_contracts" in tree, "tree.json 顶层缺 reaction_contracts"
    rc = tree["reaction_contracts"]
    assert isinstance(rc, dict)
    assert "deductions" in rc
    assert "foreshadows" in rc
    assert "themes" in rc

def test_reaction_contracts_deductions_have_resolver_and_consumers():
    tree = json.loads(TREE.read_text())
    for ded_id, contract in (tree["reaction_contracts"]["deductions"] or {}).items():
        assert "resolver_node" in contract, f"{ded_id} 缺 resolver_node"
        assert "consumer_nodes" in contract, f"{ded_id} 缺 consumer_nodes"
        assert isinstance(contract["consumer_nodes"], list)
```

- [ ] **Step 2: 跑测试验证失败**

```bash
pytest tests/test_reaction_contracts_schema.py -v
# Expected: FAIL(reaction_contracts 字段不存在)
```

- [ ] **Step 3: 在 merge_fragments.py STORY_META 加 reaction_contracts 字段**

定位 `tools/merge_fragments.py` 的 STORY_META 字典,加:

```python
"reaction_contracts": {
    "deductions": {
        # 每个 deduction id → {resolver_node, consumer_nodes}
        # 初始为空,Phase 4 内容填充时逐条加
    },
    "foreshadows": {},
    "themes": {},
},
```

- [ ] **Step 4: 重新合并 + 测试**

```bash
python tools/merge_fragments.py
pytest tests/test_reaction_contracts_schema.py -v
# Expected: 2 PASS
```

- [ ] **Step 5: Commit**

```bash
git add tools/merge_fragments.py stories/hangzhou_yebanbaoan/tree.json tests/test_reaction_contracts_schema.py
git commit -m "feat(meta): tree.json 加 reaction_contracts 字段(剧本契约)"
```

---

### Task 2.2:`tools/audit_reactions.py` — 三红线检测

**Files:**
- Create: `tools/audit_reactions.py`
- Test: `tests/test_audit_reactions.py`(新建)

**三红线**(QA Path Tester 定义):
- **DEAD_REACTION**:variant 的 require 引用了某 ID(`X_resolved=Y`),但 `reaction_contracts.{type}.{Y}` 不存在(无 resolver)
- **UNREACHABLE_REACTION**:resolver 节点存在,但 BFS 从 root → resolver → 该 variant 宿主节点 不可达
- **ORPHAN_RESOLVE**:`reaction_contracts` 声明了 resolver,但全树无 variant 消费它(剧本浪费)

- [ ] **Step 1: 写测试 fixture(假 tree)**

```python
# tests/test_audit_reactions.py
import json
from pathlib import Path
import tempfile
from tools.audit_reactions import audit

def _write_tree(tree):
    p = Path(tempfile.mkdtemp()) / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    return p

def test_dead_reaction_detected():
    """variant require D-X 但 reaction_contracts 没声明 resolver。"""
    tree = {
        "start_node_id": "n1",
        "nodes": {
            "n1": {"narrative_variants": [
                {"if": {"deduction_resolved": "D-MISSING"}, "text": "..."},
                {"text": "default"},
            ], "choices": []}
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "DEAD_REACTION" and "D-MISSING" in p["msg"]
               for p in report["problems"])

def test_orphan_resolve_detected():
    """contracts 声明了 resolver,但无 variant 消费。"""
    tree = {
        "start_node_id": "n1",
        "nodes": {"n1": {"narrative_variants": [{"text": "x"}], "choices": []}},
        "reaction_contracts": {
            "deductions": {"D-001": {"resolver_node": "n1", "consumer_nodes": []}},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "ORPHAN_RESOLVE" for p in report["problems"])

def test_clean_tree_zero_problems():
    """有 reaction 的 variant + 已声明的 contract,无问题。"""
    tree = {
        "start_node_id": "n1",
        "nodes": {
            "n1": {"choices": [{"text": "go", "next": "n2"}]},
            "n2": {
                "narrative_variants": [
                    {"if": {"deduction_resolved": "D-001"}, "text": "reaction"},
                    {"text": "default"},
                ],
                "choices": [],
            },
        },
        "reaction_contracts": {
            "deductions": {"D-001": {"resolver_node": "n1", "consumer_nodes": ["n2"]}},
            "foreshadows": {}, "themes": {},
        },
    }
    report = audit(_write_tree(tree))
    assert report["problems"] == []
```

- [ ] **Step 2: 跑测试验证失败**

```bash
pytest tests/test_audit_reactions.py -v
# Expected: FAIL(模块不存在)
```

- [ ] **Step 3: 实现 audit_reactions.py**

```python
# tools/audit_reactions.py
"""反应式 variant 死代码 / 不可达 / 孤儿 resolver 检测。

用法:
    python tools/audit_reactions.py path/to/tree.json
退出码:0=全绿, 2=有阻断
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Set


REACTION_KEYS = ("deduction_resolved", "foreshadow_resolved", "theme_resolved")
KEY_TO_CONTRACT = {
    "deduction_resolved": "deductions",
    "foreshadow_resolved": "foreshadows",
    "theme_resolved": "themes",
}


def _walk_requires(node):
    for v in node.get("narrative_variants") or []:
        if "if" in v:
            yield ("variant", v["if"])
    for ch in node.get("choices") or []:
        if "require" in ch:
            yield ("choice", ch["require"])


def _collect_ids(req, key):
    val = req.get(key)
    if val is None:
        return []
    return [val] if isinstance(val, str) else list(val or [])


def _bfs_reachable(nodes: Dict[str, Any], start: str) -> Set[str]:
    seen = {start}
    q = deque([start])
    while q:
        cur = q.popleft()
        node = nodes.get(cur) or {}
        for ch in node.get("choices") or []:
            nxt = ch.get("next")
            if nxt and nxt not in seen and nxt in nodes:
                seen.add(nxt)
                q.append(nxt)
    return seen


def audit(tree_path: Path) -> Dict[str, Any]:
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    contracts = tree.get("reaction_contracts") or {}
    start = tree.get("start_node_id") or next(iter(nodes), None)
    reachable = _bfs_reachable(nodes, start) if start else set()
    problems: List[Dict[str, Any]] = []

    # 收集所有 reaction 引用 + 宿主
    consumed: Dict[str, Set[str]] = {"deductions": set(), "foreshadows": set(), "themes": set()}
    consumer_map: Dict[tuple, Set[str]] = {}  # (type, id) -> {host_node_id}
    for nid, node in nodes.items():
        for ctx, req in _walk_requires(node):
            for key in REACTION_KEYS:
                if key not in req:
                    continue
                ctype = KEY_TO_CONTRACT[key]
                for x in _collect_ids(req, key):
                    consumed[ctype].add(x)
                    consumer_map.setdefault((ctype, x), set()).add(nid)
                    # DEAD_REACTION: 没声明 contract
                    if x not in (contracts.get(ctype) or {}):
                        problems.append({
                            "code": "DEAD_REACTION",
                            "node": nid,
                            "ctx": ctx,
                            "msg": f"{key}={x!r} 但 reaction_contracts.{ctype} 无声明",
                        })

    # UNREACHABLE_REACTION: resolver 不可达 / 从 resolver 走不到 consumer
    for ctype in ("deductions", "foreshadows", "themes"):
        for ref_id, contract in (contracts.get(ctype) or {}).items():
            resolver = contract.get("resolver_node")
            if not resolver or resolver not in nodes:
                continue
            if resolver not in reachable:
                problems.append({
                    "code": "UNREACHABLE_REACTION",
                    "node": resolver,
                    "msg": f"{ctype}.{ref_id} resolver_node 从 root 不可达",
                })
                continue
            from_resolver = _bfs_reachable(nodes, resolver)
            for host in consumer_map.get((ctype, ref_id), set()):
                if host not in from_resolver:
                    problems.append({
                        "code": "UNREACHABLE_REACTION",
                        "node": host,
                        "msg": f"{ctype}.{ref_id} 解开后回不到 consumer {host}",
                    })

    # ORPHAN_RESOLVE: 声明了但无人消费
    for ctype in ("deductions", "foreshadows", "themes"):
        for ref_id in (contracts.get(ctype) or {}).keys():
            if ref_id not in consumed[ctype]:
                problems.append({
                    "code": "ORPHAN_RESOLVE",
                    "node": (contracts[ctype][ref_id] or {}).get("resolver_node", "?"),
                    "msg": f"{ctype}.{ref_id} 声明了 resolver 但无 variant 消费",
                })

    return {
        "tree": str(tree_path),
        "consumed_count": {k: len(v) for k, v in consumed.items()},
        "problems": problems,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    args = ap.parse_args()
    report = audit(args.tree)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "UNREACHABLE_REACTION")]
    sys.exit(2 if blockers else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 测试通过**

```bash
pytest tests/test_audit_reactions.py -v
# Expected: 3 PASS
python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json
# Expected: 0 problems(因为现在还没有反应式 variant,空 contracts 也没人消费)
```

- [ ] **Step 5: Commit**

```bash
git add tools/audit_reactions.py tests/test_audit_reactions.py
git commit -m "feat(audit): audit_reactions.py 检测 DEAD/UNREACHABLE/ORPHAN 三红线"
```

---

### Task 2.3:可达性测试套件 `test_reaction_coverage.py`

**Files:**
- Create: `tests/test_reaction_coverage.py`

- [ ] **Step 1: 写"主 tree 全绿"测试**

```python
# tests/test_reaction_coverage.py
"""保证反应式 variant 不是死代码。CI 必跑。"""
from pathlib import Path
from tools.audit_reactions import audit

TREE = Path("stories/hangzhou_yebanbaoan/tree.json")

def test_main_tree_no_dead_reactions():
    report = audit(TREE)
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "UNREACHABLE_REACTION")]
    assert blockers == [], f"反应式 variant 死代码:\n{blockers}"

def test_main_tree_no_orphan_resolves():
    """ORPHAN_RESOLVE 是 WARN 级,但作者每加一条 contract 就该有 variant 消费。"""
    report = audit(TREE)
    orphans = [p for p in report["problems"] if p["code"] == "ORPHAN_RESOLVE"]
    assert orphans == [], f"声明了 resolver 但无消费:\n{orphans}"
```

- [ ] **Step 2: 跑测试**

```bash
pytest tests/test_reaction_coverage.py -v
# Expected: 2 PASS(空 contracts 是 trivial 通过)
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_reaction_coverage.py
git commit -m "test(reaction): 反应式 variant 全可达性测试"
```

---

### Task 2.4:CI 接入(本地脚本)

**Files:**
- Create: `tools/audit_all.sh`(本地一键 audit + test)
- Modify: `CLAUDE.md`(简单提一句)

- [ ] **Step 1: 写脚本**

```bash
# tools/audit_all.sh
#!/usr/bin/env bash
set -e
echo "=== 1/4 audit_tree ==="
python tools/audit_tree.py stories/hangzhou_yebanbaoan/tree.json
echo "=== 2/4 audit_state ==="
python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json
echo "=== 3/4 audit_variants ==="
python tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json
echo "=== 4/4 audit_reactions ==="
python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json
echo "=== 全套审计通过 ✅ ==="
```

加可执行权限:`chmod +x tools/audit_all.sh`。

- [ ] **Step 2: 跑全套验证**

```bash
./tools/audit_all.sh
# Expected: 4 项全过
pytest tests/ -x -q
# Expected: 全套回归通过
```

- [ ] **Step 3: Commit**

```bash
git add tools/audit_all.sh
git commit -m "chore(ci): audit_all.sh 一键跑 4 项审计"
```

---

## Phase 3:Lore 锚点表落地(Lore Keeper 守门)

### Task 3.1:`data/lore_voice_matrix.json`(NPC 语气矩阵)

**Files:**
- Create: `data/lore_voice_matrix.json`

- [ ] **Step 1: 创建文件**

```json
{
  "_comment": "Lore Keeper 评审产出 — NPC 语气切档锚点。Phase 4 内容创作必须查表替换,禁止自由发挥。",
  "version": 1,
  "matrix": {
    "linmou_1985": {
      "before": {"address": "小同志/小鬼", "tone": "公事公办的关心", "era_words": []},
      "after":  {"address": "小赵/小张", "tone": "迟疑的具名", "era_words": ["副科长", "登记表"]}
    },
    "old_grandma": {
      "before": {"address": "后生", "tone": "陌生敷衍", "era_words": []},
      "after":  {"address": "后生家", "tone": "亲近", "era_words": ["伐", "晓得伐"]}
    },
    "red_dress_girl": {
      "before": {"address": "(不语)", "tone": "凝视", "era_words": []},
      "after":  {"address": "(开口,1985 年代腔)", "tone": "幼稚而陈旧", "era_words": ["的确良", "搪瓷缸", "广播体操"]}
    },
    "worker_1986": {
      "before": {"address": "师傅", "tone": "工地客气", "era_words": []},
      "after":  {"address": "老法师", "tone": "工友", "era_words": ["盾构井", "8 班倒"]}
    }
  },
  "redlines": [
    "禁止非杭州地标(外滩/长城/胡同/陆家嘴)",
    "禁止非 80 年代物件(智能手机/扫码/微信)",
    "禁止非国营夜班用语(打工人/内卷/996)",
    "禁止把红衣女子写成日式怨灵(贞子式/白裙)",
    "红衣女子是西湖溺亡叙事谱系,不是日式怨灵"
  ]
}
```

- [ ] **Step 2: 加 schema 测试**

```python
# tests/test_lore_data.py
import json
from pathlib import Path

def test_lore_voice_matrix_schema():
    p = Path("data/lore_voice_matrix.json")
    assert p.exists()
    data = json.loads(p.read_text())
    assert "matrix" in data and "redlines" in data
    for npc_id, m in data["matrix"].items():
        assert "before" in m and "after" in m, f"{npc_id} 缺 before/after"
        for state in ("before", "after"):
            assert "address" in m[state]
            assert "tone" in m[state]
            assert "era_words" in m[state]
```

```bash
pytest tests/test_lore_data.py -v
```

- [ ] **Step 3: Commit**

```bash
git add data/lore_voice_matrix.json tests/test_lore_data.py
git commit -m "feat(lore): NPC 语气切档矩阵 v1"
```

---

### Task 3.2:`data/motif_anchors.json`(母题锚点)

**Files:**
- Create: `data/motif_anchors.json`

- [ ] **Step 1: 创建文件**

```json
{
  "_comment": "6 母题 × 视/听/嗅 18 条锚点。Phase 4 内容创作直接查表。",
  "version": 1,
  "anchors": {
    "hangzhou_constant": {
      "visual": "西湖水汽",
      "audio":  "远处轮渡汽笛",
      "scent":  "桂花潮味"
    },
    "scapegoat": {
      "visual": "旧棉袄",
      "audio":  "煤炉灰",
      "scent":  "樟脑丸味"
    },
    "time_loop": {
      "visual": "搪瓷盆碰撞",
      "audio":  "老式挂钟滴答",
      "scent":  "磁带倒带声"
    },
    "datafication": {
      "visual": "G-273 工牌反光",
      "audio":  "打卡机咔哒",
      "scent":  "荧光灯频闪"
    },
    "thirteen_curse": {
      "visual": "平海街 13 号门牌",
      "audio":  "13 路公交报站",
      "scent":  "旧日历撕到 13"
    },
    "folklore": {
      "visual": "苏堤夜雾",
      "audio":  "雷峰塔风铃 / 灵隐钟声远闻",
      "scent":  "石阶湿气"
    }
  }
}
```

- [ ] **Step 2: 加 schema 测试**

```python
# tests/test_lore_data.py(append)
def test_motif_anchors_schema():
    p = Path("data/motif_anchors.json")
    data = json.loads(p.read_text())
    assert "anchors" in data
    for motif_id, a in data["anchors"].items():
        for sense in ("visual", "audio", "scent"):
            assert sense in a, f"{motif_id} 缺 {sense}"
```

```bash
pytest tests/test_lore_data.py -v
```

- [ ] **Step 3: Commit**

```bash
git add data/motif_anchors.json tests/test_lore_data.py
git commit -m "feat(lore): 6 母题 × 视听嗅锚点表 v1"
```

---

### Task 3.3:ADR-008 反应机制契约文档

**Files:**
- Create: `docs/architecture/ADR-008-reaction-mechanism.md`

- [ ] **Step 1: 写 ADR**

```markdown
# ADR-008: 戏剧化反应机制 + 跨周目认知继承契约

## Status
Accepted

## Date
2026-05-07

## Context
元数据架构(14 伏笔 / 4 推论 / 6 母题)只在档案视图(`s` 键)可见,主流程节点 narrative 跟伏笔状态无关联。架构是"死的成绩单"。需要一套机制让"已解开的伏笔/推论/母题"驱动节点叙事切档。

## Decision

### 引擎层
扩展 `_meets_clause` 加 3 个新条件:
- `deduction_resolved: str | list[str]` — list 是 ANY 语义
- `foreshadow_resolved: str | list[str]` — 同上
- `theme_resolved: str | list[str]` — 检查 themes[id].manifestations ⊆ resolved_set

### 状态注入
**State 持 save_manager + story_id + tree 引用**(单一真相源 = save_manager)。
**拒绝 on_resolve_inject 镜像 flags**(职责分离铁律)。

### 命名空间语义(文档级,不入变量名)
- **meta.\***(只读 SaveManager,跨周目持久化):`deduction_resolved` / `foreshadow_resolved` / `theme_resolved`
- **run.\***(per-run 状态):现有 flags / inv / visit_counts
- **motif.\***(母题累计触达,留作未来扩展)

### 跨周目认知继承
- 玩家"知道"和角色"知道"必须分离
- 跨周目继承体现为:**叙述者口吻 / 选项措辞 / 隐藏选项可见性**变化
- **不是**改角色对话事实(否则角色失忆设定崩塌)
- 新角色剧本通过 `narrative_variants` 的 meta-aware 分支体现继承

### True Ending 解锁
**禁止**把"解开 N 推论"作为硬门槛(逼玩家刷周目违背单周目完整体验原则)。改为档案彩蛋。

### Variant 优先级
**列表序 = 优先级序**,specific → general。`_meets_clause` 返回首个匹配。
**default variant 必须保留**(audit_reactions 强制)。

## Alternatives Considered

### Option A: State.__init__(save_manager=None, story_id=None) [✅ 采纳]
- Pros: 数据归属关系显式,单一真相源
- Cons: 测试 fixture 需更新(已用 default=None 缓解)

### Option B: _meets_clause(self, require, save_manager=None, story_id=None) 参数透传 [❌]
- Why rejected: 参数瘟疫,污染整条调用链

### Option C: on_resolve 写镜像 flags [❌]
- Why rejected: 两套账本,任一处忘同步就是隐藏 bug。State Architect 强烈反对。

## Consequences

### Positive
- 玩家在主流程感受到世界"记得"自己做过什么
- 元数据架构从档案表变成活机制
- audit_reactions 守门,反应式 variant 不会成死代码

### Negative & Mitigation
- 新加 3 类条件 → audit_state 需识别新前缀(Mitigation: audit_state 已支持任意键名,无需改)
- variant 增量 ~15-20(Topology Designer 评估可控)
- 跨 fragment 写 reaction_contracts 易漏(Mitigation: audit_reactions ORPHAN_RESOLVE 检测)

## 参考
- 评审报告: `docs/team-reviews/2026-05-07-dramatic-reaction.md`
- 实施 plan: `docs/superpowers/plans/2026-05-07-dramatic-reaction.md`
- Lore 锚点: `data/lore_voice_matrix.json` + `data/motif_anchors.json`
```

- [ ] **Step 2: Commit**

```bash
git add docs/architecture/ADR-008-reaction-mechanism.md
git commit -m "docs(adr): ADR-008 戏剧化反应机制+跨周目认知继承契约"
```

---

## Phase 4:内容填充(7 反应节点)

**重要**:Phase 4 每加一个反应式 variant,都要先在 `tree.json` 的 `reaction_contracts` 里声明 resolver_node + consumer_nodes,然后写 variant,最后 `./tools/audit_all.sh` 必须全绿。

**节点白名单**(Chief Editor 出):
1. picker(储物间初见)
2. 对讲机异响
3. 老人讲述往事
4. 红衣女子二次照面
5. 监控回放
6. 钥匙串细节
7. 食堂留字

每个节点 1 个 contract + 1-2 个反应 variant + 必须有 default。

### Task 4.1:对讲机节点反应(`n_npc_predecessor_voice`)

**Files:**
- Modify: `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`(找到对讲机节点)
- Modify: `tools/merge_fragments.py` STORY_META `reaction_contracts` 加一条
- 重新合并 + audit + 测试

**对应**:推论 `D_predecessor_chain`(假设已存在,如不存在用 `foreshadow_resolved` 替代)。

- [ ] **Step 1: 定位节点 + 选择 reaction trigger**

```bash
grep -n "n_npc_predecessor_voice\|predecessor" stories/hangzhou_yebanbaoan/_fragment_v7_shared.json | head -10
# 看现有 narrative_variants 结构
python -c "
import json
t = json.load(open('stories/hangzhou_yebanbaoan/tree.json'))
print(list((t.get('deductions') or {}).keys()))
print(list((t.get('foreshadows') or {}).keys())[:5])
"
```

记录:可用的 deduction/foreshadow id,选一个语义匹配的(如 `D_predecessor_chain` 或 `1998_predecessor_workid`)。

- [ ] **Step 2: 在 reaction_contracts 加声明**

修改 `tools/merge_fragments.py` STORY_META:

```python
"reaction_contracts": {
    "deductions": {
        "D_predecessor_chain": {
            "resolver_node": "n_lore_archive",  # 或实际 resolver
            "consumer_nodes": ["n_npc_predecessor_voice"],
        },
    },
    "foreshadows": {},
    "themes": {},
},
```

- [ ] **Step 3: 加反应式 variant(查 Lore voice_matrix)**

在 `_fragment_v7_shared.json` 的 `n_npc_predecessor_voice` 节点 `narrative_variants` 数组开头(优先级最高)插入:

```json
{
  "if": {"deduction_resolved": "D_predecessor_chain"},
  "text": "对讲机另一头先沉默了一拍。\n\n那个声音变了——不再是值班员的公事公办,而是带着一点迟疑的具名:\n\n「……小赵?」\n\n他知道你的姓。荧光灯频闪了一下,你工牌上的 G-273 反光抖了抖。\n\n他从来不该知道你的姓。"
}
```

(Lore 锚点已用:`小赵`(linmou after)、`荧光灯频闪`(datafication audio)、`工牌反光`(datafication visual))

- [ ] **Step 4: 重合并 + audit + Commit**

```bash
python tools/merge_fragments.py
./tools/audit_all.sh
# Expected: 全绿(若 D_predecessor_chain 不存在 → DEAD_REACTION → 换可用 id)
pytest tests/test_reaction_coverage.py -v
git add stories/hangzhou_yebanbaoan/_fragment_v7_shared.json stories/hangzhou_yebanbaoan/tree.json tools/merge_fragments.py
git commit -m "content(reaction): 对讲机节点 — 推论解开后揭具名"
```

---

### Task 4.2-4.7:其余 6 节点反应

**复制 Task 4.1 的 5 步流程**,每个节点:

| # | 节点 | reaction trigger | Lore 锚点(参考) |
|---|---|---|---|
| 4.2 | n_landmark_picker(储物间 picker) | `theme_resolved: hangzhou_constant` | 西湖水汽 + 桂花潮味 + 轮渡汽笛 |
| 4.3 | n_npc_old_grandma(老人讲述) | `deduction_resolved: <时间循环推论>` | 后生家 + 伐 + 老式挂钟滴答 |
| 4.4 | n_npc_red_dress_girl(红衣女子) | `foreshadow_resolved: 1985_redgirl_*` | 的确良 + 搪瓷缸 + 广播体操 |
| 4.5 | n_scene_cctv_replay(监控回放) | `deduction_resolved: <时间循环>` | 13 路公交报站 + 13 号门牌 |
| 4.6 | n_npc_keychain(钥匙串细节) | `foreshadow_resolved: 1986_workers_drowning` | 老法师 + 盾构井 |
| 4.7 | n_scene_canteen_note(食堂留字) | `theme_resolved: scapegoat` | 樟脑丸味 + 旧棉袄 + 煤炉灰 |

**每个 task 独立 commit**:

- [ ] Task 4.2 picker 反应(主题通透切档)
- [ ] Task 4.3 老人反应(时间循环推论)
- [ ] Task 4.4 红衣女子反应(伏笔解开)
- [ ] Task 4.5 监控回放反应
- [ ] Task 4.6 钥匙串反应
- [ ] Task 4.7 食堂留字反应

每个 task 模板:
```bash
# 1. 定位节点 + 现有 narrative_variants
# 2. 在 reaction_contracts 加 contract
# 3. 加反应 variant(查 Lore 锚点表)
# 4. python tools/merge_fragments.py
# 5. ./tools/audit_all.sh && pytest tests/ -x
# 6. git add . && git commit -m "content(reaction): <节点> — <反应描述>"
```

---

### Task 4.8:`archive_view.py` 加反向影响索引

**Files:**
- Modify: `src/ghost_story_factory/v7/archive_view.py`

UX Designer 提议:每条已解锁伏笔/推论下显示"影响节点:n_xxx, n_yyy"。

- [ ] **Step 1: 加渲染逻辑**

在 `render_archive_cli()` 函数,推论解开后那段 print 之后(~line 100)插入:

```python
# 反向影响索引(已解锁的推论显示影响哪些节点)
contracts = (tree or {}).get("reaction_contracts") or {}
ded_contracts = contracts.get("deductions") or {}
if ded_id in deductions_resolved and ded_id in ded_contracts:
    consumers = (ded_contracts[ded_id] or {}).get("consumer_nodes") or []
    if consumers:
        print(f"    {dim('↳ 影响节点:')} {dim(', '.join(consumers))}")
```

伏笔同理(在 resolved 的 print 之后)。

- [ ] **Step 2: smoke 测试**

```bash
# 跑游戏 → 解开一个推论 → 按 s 键看档案
# Expected: 推论下方多一行"↳ 影响节点:n_xxx"
# 这步要手测,但可以加单元测试
```

- [ ] **Step 3: Commit**

```bash
git add src/ghost_story_factory/v7/archive_view.py
git commit -m "feat(archive): 推论/伏笔下显示反向影响节点(UX trace 价值)"
```

---

### Task 4.9:端到端验收

- [ ] **Step 1: 全套审计**

```bash
./tools/audit_all.sh
# Expected: 4 项全绿
```

- [ ] **Step 2: 全套测试**

```bash
pytest tests/ -v
# Expected: 全套 PASS,新增 ~10 个 test 全绿
```

- [ ] **Step 3: 手动验证 1 条玩家路径**

```
启动游戏 → G-273 主线 → 解开某推论 → 回到反应节点
看到反应式 variant 切档
按 s 键 → 看到推论下方"↳ 影响节点"
```

- [ ] **Step 4: 最终 Commit + 推送**

```bash
git status   # 确认全部已 commit
git log --oneline -20   # 看 Phase 1-4 提交历史
# 如果在 worktree,可以发起 PR;否则提示用户
```

---

## Validation Checklist(实施完成判定)

| 项 | 验证 |
|---|---|
| State.save_manager + story_id + tree 注入 | `pytest tests/test_state_save_binding.py -v` 通过 |
| `_meets_clause` 三新条件 | `pytest tests/test_reaction_engine.py -v` 13 PASS |
| `audit_reactions` 三红线 | `pytest tests/test_audit_reactions.py -v` 3 PASS |
| 主 tree 全绿 | `./tools/audit_all.sh` 4 项全绿 |
| 7 节点反应 variant | `git log --grep "content(reaction)"` 7 条 commit |
| ADR-008 + Lore 锚点表 | `data/lore_voice_matrix.json` + `data/motif_anchors.json` + `docs/architecture/ADR-008-*.md` |
| archive 反向索引 | 手测:解开推论后档案显示"↳ 影响节点" |

---

## 风险 & 回滚

- **风险 1**:Task 1.6 修改 State 构造调用,可能破坏 v5/v7 的其他启动路径(test 路径或 CLI 子命令)
  - **缓解**:`pytest tests/ -x` 是必跑步骤;`save_manager=None` 是默认,旧路径不受影响
- **风险 2**:Phase 4 反应 variant 可能因为推论 id 不存在而 DEAD_REACTION
  - **缓解**:Task 4.1 第 1 步先列已有 deduction id,选可用的;不强行新增推论
- **回滚**:每个 task 一 commit,出问题 `git revert <sha>` 即可

---

## 后续(本 plan 范围之外)

- **变异测试**:Topology 提议的 8 种条件叠加测试(不阻塞本期)
- **多角色 meta-aware variants**:linmou_1985 解锁后的剧本(`docs/superpowers/specs/2026-05-07-v8-character-roster-spec.md`)
- **CI 工作流**:GitHub Actions 跑 `./tools/audit_all.sh`(本期只做本地脚本)
- **变化感知动画**:UX Designer 想要的"母题级过渡 narration"(比 variant 更复杂,留作 v8 的"事件层")
