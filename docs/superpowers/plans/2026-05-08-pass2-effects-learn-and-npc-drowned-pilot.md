# Pass 2 首任务 — `know.*` 知识反馈条 + 林副科长 4 variant 试点 Implementation Plan

> **For agentic workers:** REQUIRED — Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让"知识获得"从隐式 flag 升格为玩家可感知的反馈条体验,并以林副科长 NPC(`n_npc_drowned_official`)作为 4 variant 矩阵试点,验证"NPC 对玩家已知信息的渐进反应"沙盒方向。

**Architecture:** 三层职责分离。
- **引擎层**:`State.apply` 在处理 `effects.flags` 时,检测 `key.startswith("know.")` 且发生 false→true 跳变 → emit 结构化事件 `{type: "knowledge_learned", key, source_node, is_first_time}`(复用 `_last_events` pipeline,**不新增字段**)。
- **UI 层**:CLI(`_render_apply_events`)+ TUI(`_render_apply_events_tui`)各自订阅 `knowledge_learned` 事件,按 Lore 文案规则渲染反馈条(默认 / 档案补遗 / 复读三种载体)。
- **剧本层**:`n_npc_drowned_official` 扩 4 variant(V4→V3→V2→V1 picker 顺序)+ 在赵周目侧补 4 个 `know.linmou_*` set 点(否则 V2/V3 永远不可达)。

**Tech Stack:** Python 3.11+ / pytest / 现有 v5 player.py + v7 tui_player.py + tree.json fragments

**Spec 来源:**
- 评审报告:`docs/team-reviews/2026-05-07-pass2-effects-learn-and-npc-drowned-pilot.md`(决议:**修改后放行**)
- 上游决策:ADR-007(状态契约)/ ADR-008(反应机制)/ ADR-009(linmou canon)

**项目铁律(实施全程必须遵守):**
1. **数据修订只改 `_fragment_v7_*.json`,不直接改 `tree.json`**(后者由 `tools/merge_fragments.py` 生成)
2. 每个 task 完成必须跑回归三件套:`path_explorer` + `audit_state` + `audit_reactions` + `audit_paths_linmou`
3. 林副科长节点在 `_fragment_v7_shared.json` 中
4. TDD 严格:测试先写并失败 → 实现后绿 → commit
5. 频繁 commit,**每个 task 一个 commit**(遵循 Conventional Commits)
6. 每行 diff 都必须可追溯到当前 task,**不要顺手改不相关的代码**

---

## 关键决议(评审报告固化,实施时不得偏离)

| 议题 | 决议 |
|---|---|
| 是否新增 `effects.learn` 字段 | **拒绝** — 复用 `set_flags` + `know.*` 命名空间识别 |
| 是否新增 `met.*` flag | **拒绝** — Codex met 信号走 `visit_counts.get(node_id, 0) > 0` 派生 |
| 反馈条载体 | Lore 物件优先(值班记录本 / 档案补遗),禁用 `▌▐` 等 HUD 符号 |
| 首次 vs 复读判定 | **引擎层**(`is_first_time` 字段),UI 层只订阅事件不查 flag |
| V4 触发条件 | **唯一**:`deduction.predecessor_loop == "resolved"`,不可由 know flag 替代 |
| picker 顺序 | V4 → V3 → V2 → V1(从严到松,首个匹配命中) |
| `asked_predecessor_name` set 点 | 补在 V2(清掉 Pass 1 残留 5 孤儿之一) |
| INV-5 语义 | 林周目所有 reachable terminal 必须有 `_lore_canon.intent ∈ {"释","悔","冤","曝光"}`(必死零退让) |

---

## 现状与评审假设差异(实施前必读)

> **来自探索阶段的核对结果**。评审报告的若干假设与代码现状有出入,plan 已在相应 task 中补齐。

### 差异 1:`know.linmou_*` 4 个 flag 当前**不存在**

**评审假设**(§ 7 Topology):"V2 / V3 / V4 的 require 都能从现有节点 set 端到达"
**实际现状**(`grep '"know\.' stories/hangzhou_yebanbaoan/`):
- 现存 know.* flag:`know.claimed_linmou` / `know.linked_to_eight_self` / `know.radio_listened` / `know.told_red_girl_truth` / `know.saw_underwater_coat` / `know.saw_27th_floor` / `know.saw_8_zhao` / `know.archive_visited` / `know.phone_called_1987`(共 9 个)
- **缺失**:`know.linmou_corruption` / `know.read_newspaper_1985_10_19` / `know.linmou_archive_1985` / `know.linmou_badge`(0 个 set 点,V2/V3 永远不可达)

**应对**:Phase 3 Task 3.0 — 在赵周目侧 `_fragment_v7_shared.json` 已有的"档案室访问"/"林副科长账本残页"/"工号牌"等 effect 点,挂上对应 `know.linmou_*: true`,作为 V2/V3 触发的 set 端。

### 差异 2:`linmou_dead` flag 不存在,INV-5 语义需重定义

**评审原话**(§ 8 QA):"`linmou_dead == False` 通过结局门 = 红线"
**实际现状**:项目里没有 `linmou_dead` flag。林必死靠的是 BFS reachable terminal 必为 4 ending(INV-1)+ canon must_die(INV-4)。

**应对**:INV-5 重定义为更精确的不变量(见 Phase 4 Task 4.2):
> **INV-5**:林周目 BFS reachable 范围内,所有 `_lore_canon.must_die: true` 的节点必须 `intent ∈ {"释","悔","冤","曝光"}`,且 4 个 intent **全部覆盖**(防止某 intent 路径不可达 = 路径塌陷 = 林必死语义弱化)。

### 差异 3:`predecessor_loop` deduction 已存在但本任务不创建新解锁路径

**实际现状**(`_fragment_v7_shared.json:337,1174`):`predecessor_loop` deduction 在 `n_npc_predecessor_voice` 和 `n_landmark_picker` 已有 `deduction_resolved` 引用作为 narrative_variants 触发条件。

**应对**:V4 if 直接复用现有 `deduction_resolved: "predecessor_loop"` clause,无需新建 deduction(§ 7 评审已确认此 deduction 节点存在)。

---

## File Structure

### Create

| 文件 | 用途 |
|---|---|
| `tests/test_effects_learn.py` | `knowledge_learned` 事件 capture 单测(first_learn / re_learn / 非 know 静默) |
| `tests/test_npc_drowned_official_variants.py` | 4 variant + V1 fallback 命中断言(5 用例) |

### Modify

| 文件 | 改动点 |
|---|---|
| `src/ghost_story_factory/v5/player.py:161-162` | `apply_effects` 处理 `effects.flags` 时 emit `knowledge_learned` 事件(只对 `know.*` key) |
| `src/ghost_story_factory/v5/player.py:623-662` | `_render_apply_events` 加 `knowledge_learned` 分支(CLI 反馈条) |
| `src/ghost_story_factory/v7/tui_player.py:584-617` | `_render_apply_events_tui` 加 `knowledge_learned` 分支(TUI 反馈条) |
| `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json:242-294` | `n_npc_drowned_official` 扩 4 variant + V2 set `asked_predecessor_name` |
| `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json` 多个节点 | 补 4 个 `know.linmou_*` set 点(差异 1 应对) |
| `tools/audit_paths_linmou.py:101-118` | 加 INV-5 检查(intent 全覆盖) |
| `tests/test_audit_paths_linmou.py` | INV-5 用例(green + red) |

### **不要碰**

- `tree.json`(由 fragments 合并生成)
- `effects.*` schema(零新增字段)
- `State` dataclass 新字段(`_last_events` 已足够)
- 现有 192 测试(只能新增,不能改红)

---

## Phase 1:引擎层 — `knowledge_learned` 事件源

### Task 1.1:`State.apply` 检测 `know.*` 跳变并 emit 事件

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py`(第 161-162 行 `effects.flags` 处理块)
- Test: `tests/test_effects_learn.py`(新建)

- [ ] **Step 1: 写失败测试**

```python
# tests/test_effects_learn.py
"""
ADR/Spec: docs/team-reviews/2026-05-07-pass2-effects-learn-and-npc-drowned-pilot.md § 3 (State Architect)

测试 know.* false→true 跳变 → emit knowledge_learned 事件;
重复 set / 非 know.* flag / unset 静默。
"""
from ghost_story_factory.v5.player import State


def _new_state():
    """构造一个最小 State(不依赖 tree / save_manager)。"""
    return State(initial={"flags": {}}, character="G-273")


def test_know_first_set_emits_event():
    s = _new_state()
    s.apply({"flags": {"know.linmou_badge": True}})
    events = s._last_events
    learned = [e for e in events if e.get("type") == "knowledge_learned"]
    assert len(learned) == 1
    assert learned[0]["key"] == "know.linmou_badge"
    assert learned[0]["is_first_time"] is True


def test_know_repeat_set_emits_re_learn_event():
    s = _new_state()
    s.apply({"flags": {"know.linmou_badge": True}})  # first
    s.apply({"flags": {"know.linmou_badge": True}})  # repeat
    events = s._last_events
    learned = [e for e in events if e.get("type") == "knowledge_learned"]
    assert len(learned) == 1
    assert learned[0]["is_first_time"] is False


def test_non_know_flag_silent():
    s = _new_state()
    s.apply({"flags": {"oneshot.s1_signed_book": True}})
    events = s._last_events
    learned = [e for e in events if e.get("type") == "knowledge_learned"]
    assert learned == []


def test_know_set_false_silent():
    """know.X = False 不算 learn 事件(知识不会"unlearn")。"""
    s = _new_state()
    s.apply({"flags": {"know.linmou_badge": False}})
    events = s._last_events
    learned = [e for e in events if e.get("type") == "knowledge_learned"]
    assert learned == []


def test_multiple_know_in_one_apply():
    """单次 apply 多个 know 跳变,各自 emit 一个事件。"""
    s = _new_state()
    s.apply({"flags": {"know.a": True, "know.b": True, "oneshot.x": True}})
    learned = [e for e in s._last_events if e.get("type") == "knowledge_learned"]
    assert len(learned) == 2
    keys = {e["key"] for e in learned}
    assert keys == {"know.a", "know.b"}
```

- [ ] **Step 2: 跑测试,确认失败**

```bash
.venv/bin/pytest tests/test_effects_learn.py -v
# 预期: 5 个测试全 fail(knowledge_learned 事件不存在)
```

- [ ] **Step 3: 实现 — 修改 `player.py:161-162`**

将原来的:
```python
for k, v in (effects.get("flags") or {}).items():
    self.flags[k] = bool(v)
```

改为:
```python
for k, v in (effects.get("flags") or {}).items():
    new_v = bool(v)
    old_v = bool(self.flags.get(k, False))
    self.flags[k] = new_v
    # ADR-007 + Pass2 spec: know.* false→true 跳变 emit knowledge_learned 事件。
    # 复读触发也 emit(is_first_time=False),供 UI 渲染"已知"复读条。
    # know.X = False 不算 learn(知识不可遗忘),非 know.* flag 静默。
    if k.startswith("know.") and new_v:
        events.append({
            "type": "knowledge_learned",
            "key": k,
            "is_first_time": (not old_v),
        })
```

> **注意**:`source_node` 字段评审报告 § 8 提到,但 `apply` 不持有 node_id 上下文。两条路:
> - **路 A**(本 plan 选用):事件不带 source_node,UI 层用 `state.current_id`/调用方上下文补足。
> - 路 B:把 source_node 通过参数传入 `apply`(改函数签名,影响所有调用点)— **不采用**,违反"最小改动"。
>
> 测试用例不依赖 source_node。

- [ ] **Step 4: 跑测试,确认绿**

```bash
.venv/bin/pytest tests/test_effects_learn.py -v
# 预期: 5/5 passed
```

- [ ] **Step 5: 跑回归三件套确保无 side effect**

```bash
.venv/bin/pytest -x  # 全套 192 测试不变红
.venv/bin/python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json | tail -5
# 预期: 无 NEW 错误,variants 命中率 ≥ 37.7%(基线)
```

- [ ] **Step 6: Commit**

```bash
git add tests/test_effects_learn.py src/ghost_story_factory/v5/player.py
git commit -m "feat(engine): emit knowledge_learned event on know.* set"
```

**Acceptance(映射风险):**
- ✅ 风险 5(首次/复读引擎层判定):`is_first_time` 字段在引擎层产出,UI 层不查 flag — 通过 `test_know_first_set_emits_event` + `test_know_repeat_set_emits_re_learn_event`
- ✅ 风险 3(零新增字段):未新增任何 State 字段,未新增 effects schema 字段 — 通过 `git diff src/ghost_story_factory/v5/player.py` 人工 review

---

## Phase 2:UI 层 — 反馈条渲染(CLI + TUI)

### Task 2.1:CLI `_render_apply_events` 渲染反馈条

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:623-662`(`_render_apply_events`)
- Test: `tests/test_effects_learn.py`(同一文件,新增 UI 用例)

- [ ] **Step 1: 写失败测试 — 反馈条文案模板**

```python
# 追加到 tests/test_effects_learn.py
import io
import contextlib


def test_render_default_carrier_first_time(capsys):
    """默认载体:值班记录本(非 archive 类 know.*)。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": True}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "值班记录本上记下" in out
    assert "linmou_badge" in out  # know_text 是 key 去掉 "know." 前缀


def test_render_archive_carrier_first_time(capsys):
    """档案知识:archive / corruption 类走『档案补遗』前缀。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.linmou_archive_1985", "is_first_time": True}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "档案补遗" in out


def test_render_re_learn_dim_short(capsys):
    """复读:短 dim 文案『(已知 · X)』,不弹『记下』。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": False}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "已知" in out
    assert "记下" not in out


def test_render_no_hud_symbols(capsys):
    """禁用 ▌▐ HUD 符号(Lore R-L2 + UX R-U1)。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.x", "is_first_time": True}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "▌" not in out
    assert "▐" not in out
    assert "[get]" not in out
    assert "[unlock]" not in out
```

- [ ] **Step 2: 跑测试,确认 4 个 UI 测试 fail**

- [ ] **Step 3: 实现 — `_render_apply_events` 加 `knowledge_learned` 分支**

在 `_render_apply_events` 函数 `for ev in events:` 循环里追加:

```python
elif t == "knowledge_learned":
    key = ev["key"]
    know_text = key[len("know."):] if key.startswith("know.") else key
    is_first = ev.get("is_first_time", True)
    # 载体分流:archive / corruption 走"档案补遗",其他走"值班记录本"
    is_archive = ("archive" in key) or ("corruption" in key)
    if not is_first:
        # 复读:短 dim,不常驻
        print(dim(f"  (已知 · {know_text})"))
    elif is_archive:
        print(dim(f"  档案补遗 · {know_text}"))
    else:
        print(dim(f"  (你在值班记录本上记下:{know_text})"))
```

- [ ] **Step 4: 跑测试,确认绿**

- [ ] **Step 5: Commit**

```bash
git add tests/test_effects_learn.py src/ghost_story_factory/v5/player.py
git commit -m "feat(ui-cli): render knowledge_learned feedback bar (notebook/archive/relearn)"
```

**Acceptance(映射风险):**
- ✅ 风险 2(反馈条禁用游戏化符号):`test_render_no_hud_symbols` 强制不出现 `▌▐` / `[get]` / `[unlock]`
- ✅ 风险 5(首次/复读 UI 只订阅事件):`_render_apply_events` 不读 `state.flags`,完全靠 `event.is_first_time`

---

### Task 2.2:TUI `_render_apply_events_tui` 渲染反馈条

**Files:**
- Modify: `src/ghost_story_factory/v7/tui_player.py:584-617`
- Test: `tests/test_effects_learn.py`(追加 TUI 用例)

- [ ] **Step 1: 写失败测试 — 用 mock log 捕获 RichLog.write 调用**

```python
# 追加到 tests/test_effects_learn.py

class _MockLog:
    """模拟 RichLog,捕获所有 write 调用文本。"""
    def __init__(self):
        self.lines = []
    def write(self, text):
        self.lines.append(text)


def _make_tui_player_for_test():
    """构造一个最小 TUI player 实例(只用来调 _render_apply_events_tui)。"""
    from ghost_story_factory.v7.tui_player import GhostStoryApp
    app = GhostStoryApp.__new__(GhostStoryApp)  # 跳过 __init__
    app._important_items = set()
    return app


def test_tui_render_default_carrier_first_time():
    app = _make_tui_player_for_test()
    log = _MockLog()
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": True}]
    app._render_apply_events_tui(events, log)
    body = "\n".join(log.lines)
    assert "值班记录本上记下" in body
    assert "▌" not in body  # HUD 符号禁用


def test_tui_render_archive_carrier():
    app = _make_tui_player_for_test()
    log = _MockLog()
    events = [{"type": "knowledge_learned", "key": "know.linmou_corruption", "is_first_time": True}]
    app._render_apply_events_tui(events, log)
    body = "\n".join(log.lines)
    assert "档案补遗" in body


def test_tui_render_re_learn():
    app = _make_tui_player_for_test()
    log = _MockLog()
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": False}]
    app._render_apply_events_tui(events, log)
    body = "\n".join(log.lines)
    assert "已知" in body
    assert "记下" not in body
```

- [ ] **Step 2: 跑测试,确认 3 个 TUI 用例 fail**

- [ ] **Step 3: 实现 — `_render_apply_events_tui` 加 `knowledge_learned` 分支**

在 `_render_apply_events_tui` 的 `for ev in events:` 循环里追加:

```python
elif t == "knowledge_learned":
    key = ev["key"]
    know_text = key[len("know."):] if key.startswith("know.") else key
    is_first = ev.get("is_first_time", True)
    is_archive = ("archive" in key) or ("corruption" in key)
    if not is_first:
        # 复读:1 秒淡出走 dim 短文案(Textual 暂不支持自定义淡出动画,先 dim 替代)
        log.write(f"[dim]  (已知 · {know_text})[/]")
    elif is_archive:
        log.write(f"[dim]  档案补遗 · {know_text}[/]")
    else:
        log.write(f"[dim]  (你在值班记录本上记下:{know_text})[/]")
```

> **节奏规则的简化**:UX 报告要求"正文打字结束 → 400ms 停顿 → 反馈条整行淡入"。Textual `RichLog.write` 是同步即写,实现"400ms 停顿"需要异步 timer。**本 task 不实现节奏延迟**(节奏视觉细节降级处理),Phase 5 后续任务可以做(已超出 P0 范围)。Plan 在文档里登记此简化。

- [ ] **Step 4: 跑测试,确认绿**

- [ ] **Step 5: Commit**

```bash
git add tests/test_effects_learn.py src/ghost_story_factory/v7/tui_player.py
git commit -m "feat(ui-tui): render knowledge_learned feedback bar in RichLog"
```

**Acceptance(映射风险):**
- ✅ 风险 2(TUI 反馈条文案):3 个 TUI 测试全过
- ✅ 风险 5(UI 不查 flag):`_render_apply_events_tui` 只读 event 字段

---

## Phase 3:剧本层 — 林副科长 4 variant + know set 点补齐

### Task 3.0:补 4 个 `know.linmou_*` set 点(差异 1 应对)

> **必须先做这一步**,否则 V2/V3 的 if 永远不可达,Phase 3.1 的 variant 等于死代码。

**Files:**
- Modify: `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`(在 4 个赵周目节点的 effects 里挂 know flag)
- Test: 用 `path_explorer` 验证 4 flag 都有 set 点

**待 set 的 flag → 推荐挂载点**(实施前再次确认这些节点的 effects 字段位置):

| flag | 挂载节点 | 节点定位标准 |
|---|---|---|
| `know.linmou_badge` | 赵周目"林副科长账本残页"道具获得节点 | grep `"林副科长账本残页"` 找到 inv_add 处 |
| `know.linmou_archive_1985` | 赵周目档案室访问节点(已有 `know.archive_visited`) | grep `"know.archive_visited": true` 找出 set 处 |
| `know.linmou_corruption` | 同上档案室 / 27F 走廊节点(发现"未结"印章场景) | grep `"piece_linmou_full"` 处 |
| `know.read_newspaper_1985_10_19` | **新建 mini scene 节点 / 或挂在工具节点 `n_lore_*` 之一**(本 plan 取后者最小改动) | grep `"_is_tool": true` 内容相关节点 |

- [ ] **Step 1: 实施前精确定位 4 个挂载节点**

```bash
# 找出每个挂载点的当前 effects 字段位置(在 fragment 里跳到具体行)
grep -n '"林副科长账本残页"' stories/hangzhou_yebanbaoan/_fragment_v7_*.json
grep -n '"know.archive_visited": true' stories/hangzhou_yebanbaoan/_fragment_v7_*.json
grep -n '"piece_linmou_full"' stories/hangzhou_yebanbaoan/_fragment_v7_*.json
# read_newspaper_1985_10_19 若无现成挂点,在 _fragment_v7_shared.json 找 lore tool 节点(_is_tool: true)
```

记录精确行号到本 task 的临时笔记,确保后续编辑无歧义。

- [ ] **Step 2: 写失败测试 — 4 set 点存在性**

```python
# 追加到 tests/test_npc_drowned_official_variants.py(暂时建空文件)
import json
from pathlib import Path

TREE_PATH = Path("stories/hangzhou_yebanbaoan/tree.json")
FRAG_SHARED = Path("stories/hangzhou_yebanbaoan/_fragment_v7_shared.json")


def _all_set_flags_in_fragments():
    """扫所有 fragments,返回所有被 set 过的 flag key 集合。"""
    flags = set()
    for f in Path("stories/hangzhou_yebanbaoan").glob("_fragment_v7_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        for node in (data.get("nodes") or {}).values():
            for choice in node.get("choices") or []:
                eff = choice.get("effects") or {}
                for k in (eff.get("flags") or {}).keys():
                    flags.add(k)
    return flags


def test_know_linmou_flags_have_set_points():
    """V2/V3 的前置 know.linmou_* 必须有 set 端,否则 variant 不可达。"""
    flags = _all_set_flags_in_fragments()
    required = {
        "know.linmou_badge",
        "know.linmou_archive_1985",
        "know.linmou_corruption",
        "know.read_newspaper_1985_10_19",
    }
    missing = required - flags
    assert not missing, f"缺 set 点: {missing}"
```

- [ ] **Step 3: 跑测试 fail**

```bash
.venv/bin/pytest tests/test_npc_drowned_official_variants.py::test_know_linmou_flags_have_set_points -v
# 预期: 4 个 flag 全 missing
```

- [ ] **Step 4: 修改 `_fragment_v7_shared.json` 加挂 4 个 know flag**

按 Step 1 定位的精确节点,在每个节点 effects.flags 字典里追加对应 key。例如:

```jsonc
// 林副科长账本残页道具节点 effects:
"effects": {
  "inv_add": ["林副科长账本残页"],
  "flags": {
    "know.linmou_badge": true   // ← 新增
  }
}
```

> **手术式纪律**:每行新增的 `"know.linmou_*": true` 都要能追溯到本 task。**不要顺手改其他行**。

- [ ] **Step 5: 重新合并 fragments → tree.json**

```bash
.venv/bin/python tools/merge_fragments.py stories/hangzhou_yebanbaoan
```

- [ ] **Step 6: 跑测试,确认绿**

- [ ] **Step 7: 跑回归三件套**

```bash
.venv/bin/pytest -x
.venv/bin/python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json | tail -10
.venv/bin/python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json
.venv/bin/python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json
.venv/bin/python tools/audit_paths_linmou.py stories/hangzhou_yebanbaoan/tree.json
# 预期: variants 命中率不降(≥37.7%);total flag 数 +4(71→75 — 这是 V2/V3 必需,后续 Pass 2 任务再清旧)
```

> **关于 flag 总数 71 → 75**:评审 § 7 R-T1 红线写"flag_total = 71 是底线,Pass 2 只能降不能升"。但 V2/V3 require 这 4 个 know,**没法不加**。两条路:
> - 路 A(本 plan):接受 flag_total 短期 +4 至 75,在 Phase 4 验收时记录新基线 = 75。
> - 路 B:把这 4 个改成 `inv_has` 检查现成的"林副科长账本残页"道具(部分覆盖)+ deduction(`linmou_corruption` 当作新 deduction)。
>
> **决定走路 A**,理由:V2/V3 的语义是"玩家**知道**了什么",不是"玩家**有**什么",`know.*` 命名空间正是为此设计;同时 R-T1 红线本意是反对"重新增新维度",而 `know.*` 已是 Pass 1 接受的现有命名空间(只是新 key)。**实施前与用户确认此偏离**。

- [ ] **Step 8: Commit**

```bash
git add stories/hangzhou_yebanbaoan/_fragment_v7_shared.json stories/hangzhou_yebanbaoan/tree.json tests/test_npc_drowned_official_variants.py
git commit -m "feat(script): add 4 know.linmou_* set points to enable V2/V3 variants"
```

---

### Task 3.1:`n_npc_drowned_official` 扩 4 variant + V2 set `asked_predecessor_name`

**Files:**
- Modify: `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json:242-294`(节点 `n_npc_drowned_official`)
- Test: `tests/test_npc_drowned_official_variants.py`(同一文件继续追加)

- [ ] **Step 1: 写失败测试 — 4 variant + fallback 命中断言**

```python
# 追加到 tests/test_npc_drowned_official_variants.py
import json
from pathlib import Path
from ghost_story_factory.v5.player import State, resolve_narrative


TREE = json.loads(Path("stories/hangzhou_yebanbaoan/tree.json").read_text(encoding="utf-8"))
NODE_ID = "n_npc_drowned_official"


def _state_with_flags(flags=None, save_manager=None, story_id=None):
    s = State(initial={"flags": dict(flags or {})}, character="G-273")
    if save_manager:
        s.save_manager = save_manager
        s.story_id = story_id or "杭州_v7"
        s.tree = TREE
    return s


class _FakeSaveManager:
    """最小 SaveManager 替身,只支撑 is_deduction_resolved。"""
    def __init__(self, deductions=None):
        self._d = set(deductions or [])
        self.data = {}
    def is_deduction_resolved(self, story_id, did):
        return did in self._d


def _node():
    return TREE["nodes"][NODE_ID]


def _hit_variant_index(state):
    """返回当前 state 下命中的 narrative_variants 索引(无命中返回 None,fallback 走 narrative)。"""
    node = _node()
    for idx, v in enumerate(node.get("narrative_variants") or []):
        if state.meets(v.get("if")):
            return idx
    return None


def test_v1_fallback_empty_flags_hits_no_variant():
    """V1 = fallback,V4/V3/V2 都不满足时 narrative_variants 全 miss → 走 default narrative。"""
    s = _state_with_flags()
    idx = _hit_variant_index(s)
    # V1 是 fallback = 命中"无 if 的最后一个"或"narrative 兜底"
    # 实施时 V1 要么放在 narrative_variants 最末(无 if),要么用现有 narrative 字段。
    # 本测试断言:如果 V1 在 narrative_variants 内,索引 = 最后一个;否则 idx is None(fallback to narrative)
    node = _node()
    variants = node.get("narrative_variants") or []
    assert variants, "n_npc_drowned_official 必须有 narrative_variants"
    if idx is not None:
        assert idx == len(variants) - 1, "fallback 必须在 narrative_variants 末尾"
    # narrative 字段必须仍然存在(V1 文案要么在 narrative_variants 末尾,要么在 narrative)
    assert node.get("narrative") or any(not v.get("if") for v in variants)


def test_v2_alert_on_know_linmou_badge():
    """V2: know.linmou_badge → 命中 V2(『小鬼,你翻那箱子做什么』)。"""
    s = _state_with_flags({"know.linmou_badge": True})
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "翻那箱子" in text or "小鬼" in text


def test_v2_alert_on_know_linmou_archive_1985():
    """V2: know.linmou_archive_1985(OR 关系)→ 同样命中 V2。"""
    s = _state_with_flags({"know.linmou_archive_1985": True})
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "翻那箱子" in text or "小鬼" in text


def test_v3_self_defense():
    """V3: know.linmou_corruption AND know.read_newspaper_1985_10_19 → 命中 V3。"""
    s = _state_with_flags({
        "know.linmou_corruption": True,
        "know.read_newspaper_1985_10_19": True,
    })
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "报纸都登了" in text or "你说我冤不冤" in text


def test_v4_truth_requires_deduction():
    """V4: deduction.predecessor_loop=resolved → 命中 V4(『小赵。这次轮到你了』)。"""
    sm = _FakeSaveManager(deductions={"predecessor_loop"})
    s = _state_with_flags(save_manager=sm)
    idx = _hit_variant_index(s)
    assert idx is not None
    text = _node()["narrative_variants"][idx]["text"]
    assert "小赵" in text and "这次轮到你了" in text


def test_v4_priority_over_v3():
    """风险 1: V4 priority 必须 > V3。即同时满足 V3 + V4 时,picker 命中 V4。"""
    sm = _FakeSaveManager(deductions={"predecessor_loop"})
    s = _state_with_flags({
        "know.linmou_corruption": True,
        "know.read_newspaper_1985_10_19": True,
    }, save_manager=sm)
    idx = _hit_variant_index(s)
    text = _node()["narrative_variants"][idx]["text"]
    assert "小赵" in text  # V4 优先


def test_v4_NOT_triggered_by_know_alone():
    """风险 1 红线: know.* 单独不能触发 V4。"""
    s = _state_with_flags({
        "know.linmou_corruption": True,
        "know.read_newspaper_1985_10_19": True,
        "know.linmou_badge": True,
        "know.linmou_archive_1985": True,
    })  # 全 know set,但无 deduction
    idx = _hit_variant_index(s)
    text = _node()["narrative_variants"][idx]["text"]
    assert "小赵。这次轮到你了" not in text  # V4 不该命中


def test_v2_sets_asked_predecessor_name():
    """风险 6: V2 必须 set_flags asked_predecessor_name=True(清孤儿 require)。
    检查方式: V2 if 后面的『effects』(narrative_variants 不直接挂 effects,
    所以需要在 V2 命中时通过其他机制 set —— 设计:
    把 set_flags 挂在节点级 narrative_effects(如果 schema 允许)
    或挂在选项 effects(玩家进入此节点选第一个选项时 set)。
    本测试: 直接 grep fragment,确认 asked_predecessor_name 在 n_npc_drowned_official 子树里至少 set 一次。
    """
    frag = Path("stories/hangzhou_yebanbaoan/_fragment_v7_shared.json").read_text(encoding="utf-8")
    # 在 n_npc_drowned_official 节点定义块内查找 asked_predecessor_name
    start = frag.find('"n_npc_drowned_official"')
    end = frag.find('"n_npc_', start + 30)  # 下一个 n_npc_* 节点开始
    block = frag[start:end if end > 0 else len(frag)]
    assert "asked_predecessor_name" in block, "V2 必须在 n_npc_drowned_official 子树内 set asked_predecessor_name"
```

- [ ] **Step 2: 跑测试,确认 8 个测试全 fail**

- [ ] **Step 3: 改 `_fragment_v7_shared.json:244-261` `n_npc_drowned_official.narrative_variants`**

替换原来的 2 个 variant(`oneshot.s1_signed_book` / `oneshot.s1_wore_shoes`)为 4 个新 variant,**保留原 narrative 字段做 V1 fallback**:

```jsonc
"narrative_variants": [
  {
    "_variant_id": "V4_truth",
    "if": {
      "deduction_resolved": "predecessor_loop"
    },
    "text": "湖水自己漫上岸。\n\n中山装的男人从湖里走出来,脚下青石板是干的。\n\n他抬头看你,眼睛非常黑。\n\n他认出你了。\n\n「……小赵。\n  这次轮到你了。」"
  },
  {
    "_variant_id": "V3_defense",
    "if": {
      "all_of": [
        {"flags": {"know.linmou_corruption": true}},
        {"flags": {"know.read_newspaper_1985_10_19": true}}
      ]
    },
    "text": "湖水漫上来。\n\n中山装的男人站在水里看你。\n\n他知道你看过那张报纸。\n\n他的语气不再温和——\n\n「……报纸都登了。\n\n  小同志,你说我冤不冤?\n\n  那 27 笔,我只签了 13 笔。\n  其余 14 笔,是别人借我的章。\n  报纸只敢登 13 笔——剩下的 14 笔,登出来要塌的。\n\n  小同志,你说我冤不冤?」"
  },
  {
    "_variant_id": "V2_alert",
    "if": {
      "any_of": [
        {"flags": {"know.linmou_badge": true}},
        {"flags": {"know.linmou_archive_1985": true}}
      ]
    },
    "text": "湖水漫上来。\n\n中山装的男人站在长椅旁看你。\n\n他没有指长椅,他指着**你的胸口**——\n\n你胸口工牌反光抖了一下。\n\n「小鬼,你翻那箱子做什么。\n\n  那箱子是我留给**第 14 任**的。\n  你今晚翻的不是档案——\n  你翻的是你自己的位置。」"
  }
],
```

> **关键决定**:V1 走原 `narrative` 字段(fallback),不放进 narrative_variants 里。这样:
> - 玩家初见 = `narrative` 字段 = 长版"湖水自己漫上岸..."(原版),自然 = V1
> - 后续访问 know flag 累积 → V2 / V3 触发
> - 推理完成后访问 → V4 真相
>
> 这与 picker 顺序"V4→V3→V2→V1"一致(V1 是 narrative_variants 全 miss 后 fallback to narrative)。

- [ ] **Step 4: V2 触发的副作用 — `asked_predecessor_name`**

> **设计难点**:`narrative_variants` 现 schema **不挂 effects**(看 player.py 的 `resolve_narrative` 确认)。set 点必须在 V2 命中时的下游 — 最干净的做法:**给 V2 文本对应的"追问"选项加 effect**。
>
> 现有 `n_npc_drowned_official.choices` 三个选项("认领"/"不认领"/"我也是 G-273")是 V1 时代设定。V2 / V3 / V4 玩家会有不同的对话选项。**最小改动方案**:在 3 个现有 choice 之外加一个 V2 专属 choice(`require: any_of [know.linmou_badge | know.linmou_archive_1985]`),效果含 `asked_predecessor_name`。

修改 `n_npc_drowned_official.choices` 追加:

```jsonc
{
  "text": "你怎么知道我胸口的工牌反光?",
  "next": "n_landmark_picker",
  "require": {
    "any_of": [
      {"flags": {"know.linmou_badge": true}},
      {"flags": {"know.linmou_archive_1985": true}}
    ]
  },
  "effects": {
    "PR": 5,
    "flags": {
      "asked_predecessor_name": true
    }
  }
}
```

> **风险 6 acceptance**:`test_v2_sets_asked_predecessor_name` 通过 grep 验证。

- [ ] **Step 5: 重新合并 + 跑测试**

```bash
.venv/bin/python tools/merge_fragments.py stories/hangzhou_yebanbaoan
.venv/bin/pytest tests/test_npc_drowned_official_variants.py -v
# 预期: 8/8 passed
```

- [ ] **Step 6: 跑回归三件套**

```bash
.venv/bin/pytest -x
.venv/bin/python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json | tail -10
.venv/bin/python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json
.venv/bin/python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json
.venv/bin/python tools/audit_paths_linmou.py stories/hangzhou_yebanbaoan/tree.json
# 预期: variants 命中率 ≥ 40%(目标 > 36.9% 基线);孤儿 require 从 5 降到 4(asked_predecessor_name 清掉)
```

- [ ] **Step 7: Commit**

```bash
git add stories/hangzhou_yebanbaoan/_fragment_v7_shared.json stories/hangzhou_yebanbaoan/tree.json tests/test_npc_drowned_official_variants.py
git commit -m "feat(script): n_npc_drowned_official 4 variant matrix (V4 truth via deduction, V2 sets asked_predecessor_name)"
```

**Acceptance(映射风险):**
- ✅ 风险 1(V4 必须经 deduction):`test_v4_NOT_triggered_by_know_alone` + `test_v4_priority_over_v3` 双重证明
- ✅ 风险 4(picker 顺序 + V1 fallback):`test_v1_fallback_empty_flags_hits_no_variant` + V4 索引在 [0]
- ✅ 风险 6(`asked_predecessor_name` set 在 V2):`test_v2_sets_asked_predecessor_name` + `path_explorer` 孤儿数 -1

---

## Phase 4:守门 — `audit_paths_linmou` 扩 INV-5

### Task 4.1:重定义 INV-5 + 加测试

**Files:**
- Modify: `tools/audit_paths_linmou.py`(在 INV-4 后追加 INV-5)
- Test: `tests/test_audit_paths_linmou.py`(追加 INV-5 用例)

- [ ] **Step 1: 写失败测试 — INV-5 green + red 双向断言**

```python
# 追加到 tests/test_audit_paths_linmou.py
import json
import tempfile
from pathlib import Path
from tools.audit_paths_linmou import audit


def _save_tree(data):
    p = Path(tempfile.mkdtemp()) / "tree.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def _minimal_linmou_tree(intents):
    """构造一个最小 linmou 树,4 ending 各带 must_die + 指定 intent。
    intents 是 dict: {ending_id: intent_or_None}
    """
    tree = {
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
        "nodes": {
            "n_l1985_entry": {
                "scene": "SCENE",
                "narrative": "...",
                "choices": [
                    {"text": "A", "next": "E_LINMOU_GRIEVANCE"},
                    {"text": "B", "next": "E_LINMOU_REGRET"},
                    {"text": "C", "next": "E_LINMOU_RELEASE"},
                    {"text": "D", "next": "E_LINMOU_EXPOSED"},
                ],
            },
            "E_LINMOU_GRIEVANCE": {
                "scene": "ENDING",
                "narrative": "...",
                "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_GRIEVANCE")},
            },
            "E_LINMOU_REGRET": {
                "scene": "ENDING", "narrative": "...", "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_REGRET")},
            },
            "E_LINMOU_RELEASE": {
                "scene": "ENDING", "narrative": "...", "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_RELEASE")},
            },
            "E_LINMOU_EXPOSED": {
                "scene": "ENDING", "narrative": "...", "choices": [],
                "_lore_canon": {"must_die": True, "intent": intents.get("E_LINMOU_EXPOSED")},
            },
        },
    }
    return tree


def test_inv5_green_when_all_4_intents_covered():
    """INV-5 绿: 4 ending 各带 4 个不同 intent。"""
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": "曝光",
    })
    p = _save_tree(tree)
    report = audit(p)
    inv5_problems = [x for x in report["problems"] if x.get("code", "").startswith("INV5")]
    assert inv5_problems == []


def test_inv5_red_when_intent_missing():
    """INV-5 红: 其中 1 ending 缺 intent。"""
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": None,  # 缺 intent
    })
    p = _save_tree(tree)
    report = audit(p)
    inv5_problems = [x for x in report["problems"] if x.get("code", "").startswith("INV5")]
    assert len(inv5_problems) >= 1
    assert "E_LINMOU_EXPOSED" in inv5_problems[0].get("msg", "")


def test_inv5_red_when_intent_not_in_canon_set():
    """INV-5 红: intent 不在 4 canon 集合内(野字段)。"""
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": "逃出生天",  # 野 intent
    })
    p = _save_tree(tree)
    report = audit(p)
    inv5_problems = [x for x in report["problems"] if x.get("code", "").startswith("INV5")]
    assert len(inv5_problems) >= 1


def test_inv5_red_when_one_intent_unreachable():
    """INV-5 红: 4 intent 必须全部覆盖(防止某 intent 路径塌陷,例如 release 节点不可达)。
    构造法: 把 RELEASE 从 entry 的 choices 里去掉(模拟不可达)。
    """
    tree = _minimal_linmou_tree({
        "E_LINMOU_GRIEVANCE": "冤",
        "E_LINMOU_REGRET": "悔",
        "E_LINMOU_RELEASE": "释",
        "E_LINMOU_EXPOSED": "曝光",
    })
    # 移除 RELEASE 的可达边
    tree["nodes"]["n_l1985_entry"]["choices"] = [
        c for c in tree["nodes"]["n_l1985_entry"]["choices"]
        if c["next"] != "E_LINMOU_RELEASE"
    ]
    p = _save_tree(tree)
    report = audit(p)
    inv5_problems = [x for x in report["problems"] if x.get("code", "").startswith("INV5")]
    # RELEASE 不可达 = "释" intent 缺失
    assert len(inv5_problems) >= 1
    assert any("释" in (x.get("msg") or "") for x in inv5_problems)
```

- [ ] **Step 2: 跑测试,确认 4 个 INV-5 用例 fail**

- [ ] **Step 3: 实现 — `tools/audit_paths_linmou.py:101-118` 后追加 INV-5**

```python
# 紧跟 INV-4 块,在 `return {...}` 之前插入:

# INV-5 (Pass 2 评审): 林必死零退让 — 4 canon intent 必须全部覆盖。
# 语义: reachable 范围内,所有 must_die 节点的 intent 必须 ⊆ {"释","悔","冤","曝光"};
# 且这 4 个 intent 必须各自至少有一个 reachable ending 承载(防止某 intent 路径塌陷)。
CANON_INTENTS = {"释", "悔", "冤", "曝光"}
covered_intents: Set[str] = set()
for nid in reachable:
    node = nodes[nid] or {}
    canon = node.get("_lore_canon") or {}
    if not canon.get("must_die"):
        continue
    intent = canon.get("intent")
    if not intent:
        problems.append({
            "code": "INV5_MISSING_INTENT",
            "node": nid,
            "msg": f"{nid} must_die=True 但缺 _lore_canon.intent(必须 ∈ {sorted(CANON_INTENTS)})",
        })
        continue
    if intent not in CANON_INTENTS:
        problems.append({
            "code": "INV5_INTENT_NOT_IN_CANON",
            "node": nid,
            "msg": f"{nid} intent={intent!r} 不在 canon 集 {sorted(CANON_INTENTS)}",
        })
        continue
    covered_intents.add(intent)

missing_intents = CANON_INTENTS - covered_intents
if missing_intents:
    problems.append({
        "code": "INV5_INTENT_NOT_REACHABLE",
        "node": "<global>",
        "msg": f"以下 canon intent 无 reachable ending 承载: {sorted(missing_intents)}(林必死零退让,4 intent 必须全覆盖)",
    })
```

- [ ] **Step 4: 跑测试,确认绿**

```bash
.venv/bin/pytest tests/test_audit_paths_linmou.py -v
# 预期: 全过(含 INV-5 4 个新用例)
```

- [ ] **Step 5: 跑生产 tree 验证 INV-5 在真实数据上绿**

```bash
.venv/bin/python tools/audit_paths_linmou.py stories/hangzhou_yebanbaoan/tree.json
# 预期: problems == [] (INV-1~5 全绿)
```

> **若不绿**:说明真实 tree 里某 ending 缺 intent,需先补全 `_lore_canon.intent` 字段。已知 `_fragment_v7_linmou_1985.json:445/453/461/469` 已有 4 个 must_die,只需确认 intent 字段是否齐全。

- [ ] **Step 6: Commit**

```bash
git add tools/audit_paths_linmou.py tests/test_audit_paths_linmou.py
git commit -m "feat(audit): audit_paths_linmou INV-5 — 4 canon intent must be covered (linmou must die)"
```

**Acceptance(映射风险):**
- ✅ 风险 7(林必死零退让):INV-5 实施 + 4 测试 + 生产 tree 绿

---

## Phase 5:全套回归 + 验收

### Task 5.1:跑完整回归套件

- [ ] **Step 1: 跑 192 测试 + 新增测试,确认全绿**

```bash
.venv/bin/pytest -x --tb=short
# 预期: 192 + 新增测试(估 17 个) 全绿
```

- [ ] **Step 2: 跑回归四件套对比基线**

```bash
.venv/bin/python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json > /tmp/explorer_after.txt
.venv/bin/python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json > /tmp/audit_state_after.txt
.venv/bin/python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json > /tmp/audit_reactions_after.txt
.venv/bin/python tools/audit_paths_linmou.py stories/hangzhou_yebanbaoan/tree.json > /tmp/audit_linmou_after.txt
```

逐项核对:

| 指标 | 基线(Pass 1 完成时) | 目标 | 验收 |
|---|---|---|---|
| variants 触发率 | 37.7% | ≥ 40% | path_explorer 输出 |
| 孤儿 require key | 5 个 | ≤ 4(`asked_predecessor_name` 清掉) | path_explorer "Orphan require key" 节 |
| flag 总数 | 71 | 75(±0.5,新增 4 个 know.linmou_*) | audit_state 输出 + 文档登记新基线 |
| audit_paths_linmou | INV-1~4 全绿 | INV-1~5 全绿 | audit_paths_linmou 退出码 0 |
| audit_reactions | 全绿 | 全绿 | audit_reactions 退出码 0 |

- [ ] **Step 3: 玩通三条人工验收路径(可选,但强烈建议)**

```bash
.venv/bin/python -m ghost_story_factory.v7.menu_cli  # 进入主菜单
```

- 路径 A(V1 fallback):新存档 → 直接走到林副科长长椅,不进档案室不读报纸不查推理 → 看到原版长 narrative + 反馈条不弹("奇怪,你刚记下『签了赵某 G-273』...")
- 路径 B(V2 警觉):访问档案室拿"林副科长账本残页" → 看到反馈条`(你在值班记录本上记下:linmou_badge)` → 走到长椅 → V2 文本"小鬼,你翻那箱子做什么"
- 路径 C(V4 真相):打通 `predecessor_loop` deduction → 走到长椅 → V4 文本"……小赵。这次轮到你了"

**人工感受核验**:
- 反馈条字符样式不出现 `▌▐` / 不出现 `[get]` / 不出现 `(知道)` 等 HUD 风格 — 否则风险 2 触发
- variant 切换"隐形"(玩家感觉是 NPC 自然反应,不是台词被替换)

- [ ] **Step 4: 不写 commit,仅人工验证 + 写验收报告片段**

把回归数据(基线对比表 + 4 个 audit 退出码)粘贴到 PR/issue 描述里,作为"实施完成"证据。

---

## 验收 Checklist(13 项)

实施完成时,逐项打勾:

### 引擎层
- [ ] **C1**: `tests/test_effects_learn.py` 5 个事件用例全绿(first / repeat / non-know / unset / multi)
- [ ] **C2**: `State` dataclass / `effects.*` schema **零新增字段**(`git diff` 验证)
- [ ] **C3**: `apply_effects` 只对 `key.startswith("know.")` 且 `new_v=True` 的 flag emit `knowledge_learned` 事件(非 know / unset 静默)

### UI 层
- [ ] **C4**: CLI `_render_apply_events` 三种载体文案正确(默认 / 档案补遗 / 复读),`test_render_*` 4 个测试全绿
- [ ] **C5**: TUI `_render_apply_events_tui` 三种载体文案正确,3 个 TUI 测试全绿
- [ ] **C6**: 反馈条文案 **不含** `▌▐` / `[get]` / `[unlock]` / 任何"未来可解锁"暗示

### 剧本层
- [ ] **C7**: `n_npc_drowned_official` 包含 V4 / V3 / V2 三个 narrative_variants(V1 走 narrative fallback)
- [ ] **C8**: V4 if = `deduction_resolved: predecessor_loop`,**唯一**触发条件;`test_v4_NOT_triggered_by_know_alone` 绿
- [ ] **C9**: V2 命中时通过新增的"追问"choice 把 `asked_predecessor_name` set 为 True(`path_explorer` 孤儿数 5 → 4)
- [ ] **C10**: 4 个 `know.linmou_*` flag 都有 set 端(`test_know_linmou_flags_have_set_points` 绿)

### 守门 + 回归
- [ ] **C11**: `audit_paths_linmou` INV-1~5 全绿(退出码 0),tests 含 INV-5 4 用例
- [ ] **C12**: 192 + 新测试(估 17)全绿,回归基线无漂移(`audit_reactions` 全绿)
- [ ] **C13**: `path_explorer` variants 触发率 ≥ 40%(目标值,基线 37.7%);若未达 40% 但 ≥ 37.7% 也接受(评审 R-Q2 是 ≥ 36.9%)

---

## 7 条风险 → Acceptance Criteria 映射总表

| 风险 | 严重度 | 实施 task | Acceptance 测试 / 检查 |
|---|---|---|---|
| 1. V4 必须经 deduction | 🔴 | Task 3.1 | `test_v4_NOT_triggered_by_know_alone` + `test_v4_priority_over_v3` |
| 2. 反馈条禁用游戏化符号 | 🔴 | Task 2.1 + 2.2 | `test_render_no_hud_symbols` (CLI) + TUI 用例字符串断言 + Step 5.3 人工验收 |
| 3. 零新增字段,Codex met 走 visit_counts | 🔴 | Task 1.1 + C2 验收 | `git diff` review + 不引入 `met.*` 关键字 grep 检查 |
| 4. fallback V1 必须存在 + picker 顺序 | 🟡 | Task 3.1 | `test_v1_fallback_empty_flags_hits_no_variant` + path_explorer 命中率 |
| 5. 首次/复读引擎层判定 | 🟡 | Task 1.1 | `test_know_repeat_set_emits_re_learn_event` + `is_first_time` 字段断言 |
| 6. asked_predecessor_name set 在 V2 | 🟡 | Task 3.1 | `test_v2_sets_asked_predecessor_name` + path_explorer 孤儿数 |
| 7. 林必死零退让 INV-5 | 🟡 | Task 4.1 | `tests/test_audit_paths_linmou.py` 4 个 INV-5 用例 + 生产 tree 退出码 0 |

---

## 实施前用户确认事项(开工前 reply)

执行此 plan 之前,请用户对以下两点显式回复确认:

1. **flag_total 偏离**:Phase 3 Task 3.0 会让 flag 总数从 71 → 75(新增 4 个 `know.linmou_*`)。
   评审 R-T1 红线本意是"不重新增维度",而 `know.*` 已是 Pass 1 接受的命名空间。是否接受新基线 = 75?
   - 接受 → 按 plan 路 A 执行
   - 不接受 → 改走路 B(把 V2/V3 require 改成 inv_has + 新建 deduction),代价更大

2. **节奏延迟降级**:Phase 2 Task 2.2 不实现"400ms 停顿 → 整行淡入"动画(Textual 异步 timer 改造非本期范围)。
   反馈条用 `[dim]...[/]` 同步即写代替。是否接受此简化?
   - 接受 → 按 plan 执行
   - 不接受 → Phase 2 多加一个 task 5.4 实现 Textual reactive timer

确认后,可以进入 `executing-plans` skill 开工。

---

## Plan 完成标记

- 路径:`docs/superpowers/plans/2026-05-08-pass2-effects-learn-and-npc-drowned-pilot.md`
- 状态:**待用户开工确认**
- Phase 数:5 个(引擎事件源 / UI 反馈条 / 剧本 4 variant + know set 点补齐 / INV-5 守门 / 全套回归)
- Task 数:8 个(1.1 / 2.1 / 2.2 / 3.0 / 3.1 / 4.1 / 5.1 / 验收)
- 估算 commit 数:7 个(每 task 一个,加 Task 3.0 一个 = 7;5.1 不 commit 仅验收)
