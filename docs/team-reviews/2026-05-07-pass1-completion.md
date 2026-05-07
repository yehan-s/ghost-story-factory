# Pass 1 状态空间审计 + Flag 降级清扫 — 完成报告

> 完成日期:2026-05-07
> 评审报告依据:`docs/team-reviews/2026-05-07-沙盒方向首个开发任务.md` § 9
> 实施 plan:`docs/superpowers/plans/2026-05-07-pass1-state-space-audit-and-flag-cleanup.md`
> ADR:`docs/architecture/ADR-007-state-contract.md`

---

## 1. 数据指标对比(基线 vs 现状)

| 指标 | 基线(Pass 1 启动前) | 现状(Pass 1 完成) | 变化 |
|---|---|---|---|
| flag_total | 234 | **71** | -163(-69.7%)✓ ≤ 80 目标达成 |
| namespace_violations | 334 | **0** | -334 ✓ |
| dead_set_flags | 154 | **0** | -154 ✓(全清零) |
| dead_require_flags | 7 | **5** | -2(剩 5 个真孤儿,需 Pass 2 故事侧补全) |
| State 字段数 | 14 | **11** | -3(删 `meta_flags` / `route`,`shifts_completed` 改 @property) |

> 校核命令:`.venv/bin/python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json`
>
> 残留 5 个孤立 require key:`asked_predecessor_name` / `oneshot.s2_followed_double_shadow` /
> `oneshot.s2_returned_shoes` / `oneshot.s6_grab_seven` / `saw_predecessor_map`。
> 它们是"剧本要求但内容侧没埋 set 点"的真缺口,不能在 Pass 1 直接删 require(否则伏笔/结局触发条件失真),
> 留待 Pass 2 故事侧补回(或评审后认为价值不足再删 require)。

---

## 2. ADR-007 落地清单

- [x] State 字段冻结清单(11 字段:`pr / gr / inv / flags / visit_count / landmarks_visited / shifts_skipped / story_progress / scene / story_id / save_manager` 等核心字段)
- [x] Flag 命名空间约定(6 个 namespace:`oneshot.* / arc.* / know.* / has.* / deduction.* / npc.*`)
- [x] `_SPOILER_KEYS` 提为正式契约(写在 ADR-007 与 lore_canon)
- [x] tree.json 顶层 `lore_canon` 白名单(31 个允许年份 + 5 个禁用术语)
- [x] `tools/audit_state.py` 上线(命名空间/死字段/红线一锅端)
- [x] `tools/audit_variants.py` 上线(narrative_variants 覆盖矩阵 + 不可达检测)
- [x] `tools/audit_reactions.py` 上线(伏笔/推论/母题契约 dead/unreachable/orphan 三红线)
- [x] `tools/_state_sim.py` 抽出(供 path_explorer / _state_sim 共用同一份解析)

---

## 3. 14 任务进度

| Task | 简述 | 状态 | 关键 Commit |
|---|---|---|---|
| Task 1 | `tools/_state_sim.py` 共用模块 | ✓ | `d3e2cd1` |
| Task 2 | ADR-007 State Contract | ✓ | `f9b84b4` |
| Task 3 | `tools/audit_state.py` | ✓ | `388eb23` |
| Task 4 | `tools/audit_variants.py` | ✓ | `7081da4` |
| Task 5 | tree.json `lore_canon` 白名单 | ✓ | `07eadf8` |
| Task 6 | 删 `meta_flags` 死字段 | ✓ | `932427b` |
| Task 7 | 删 `route` 字段(v7 已废) | ✓ | `90cc896` |
| Task 8 | `shifts_completed` 改 @property 派生 | ✓ | `3c9277a` |
| Task 9 | `landmark_skipped` 自动同步 `shifts_skipped` | ✓ | `1b2cebd` |
| Task 10 | s* 下沉 `oneshot.*/arc.*` + `*_revisit_*` 改 `visit_count_min` | ✓ | `ac325c4` → `13b7906`(7 批共 135 处) + `5009dbe` |
| Task 11 | 双写道具清理(A/B 两类) | ✓ | `c59b423`,`40dc145`,`68a8e49` |
| Task 12 | `know-*` 收编 `know.*` namespace + dead_set 第一波 | ✓ | `1a168ac` |
| Task 13 | path_explorer 三大盲区补丁(variants / key 一致性 / picker 展开) | ✓ | `54459e2` |
| Task 14 | 终末清扫 + 完成报告 | ✓ | **本 commit** |

---

## 4. 试点节点 `n_npc_predecessor_voice` 知识门控可行性

节点已在 v7 中实现,且**正好是 ADR-007 所定义"visit_count + know.* + 派生计数"组合的范本**。

抽样 4 个 narrative_variants 的门控写法:

| variant# | 门控 if 条件 | 触发语义 |
|---|---|---|
| 0 | `deduction_resolved: predecessor_loop` | 玩家完成"前任循环"推论后,NPC 喊出主角姓 |
| 1 | `visit_count_min.n_npc_predecessor_voice: 5` | 听够 5 次,出现"自己声音"诡异回放 |
| 2 | `flags.know.radio_listened: true` + `shifts_completed_min: 5` | 听过磁带 + 跑完 5 班,NPC 直接报出"第 13 任"事实 |
| 3 | `flags.know.radio_listened: true` + `shifts_completed_min: 3` | 听过磁带 + 跑完 3 班,警告"超过 5 就回不来" |

`_scene_details` 还挂了 5 次访问的 `_foreshadow_clue.G272_predecessor_identity.self_voice` 触发器。
**结论**:Pass 1 把 `know.*` namespace 与 `shifts_completed` @property 派生准备好后,
该节点已具备"听过磁带 / 见过湿鞋 / 认出工号"三态门控的字面能力,后续 Pass 2 可以直接拓展更多分支,**无需再改引擎**。

---

## 5. 教训(Linus 视角)

### 5.1 真相源 vs 衍生文件 — 中途事故

`tree.json` 是 8 个 `_fragment_v7_*.json` 经 `tools/merge_fragments.py` 合并而成。
Pass 1 中途(commit `c193f32` 前后)曾因一次直接编辑 `tree.json` 然后再次 merge,
导致改动被 merge 全量 wipe,大半天工作量回到 fragments 层重做(`a305bd7` 重做)。

**纠正**:plan 写在最显眼位置——"数据修订**只改 fragments**,不直接改 `tree.json`"。
Task 14 严格执行该纪律,未触碰 tree.json 直接改写。

### 5.2 数据 bug 的隐蔽性

工具 Task 13 的 path_explorer 三盲区补丁直接揪出两处嵌套结构错误:

- `n_scene_morning_lakeside.narrative_variants[2].if`:`puzzle_pieces_min: 3` 错嵌套到 `flags: {...}` 内(应在 `if` 顶层)。
- `n_scene_27th_floor_corridor.narrative_variants[3].if`:`shifts_completed_min: 4` 错嵌套到 `flags: {...}` 内(同上)。

LLM 写剧本 / 人手编辑都不容易在阅读时识别这种结构错位 — 因为 `flags: { puzzle_pieces_min: 3 }`
在 JSON 层面合法,只是引擎从来不会把它当 require 关键字来检查。
工具值得做,Task 13 即时回本。

### 5.3 dead_set 清扫的级联效应

Task 10 完成 s* 下沉 / namespace 化后,一批本来就没人 require 的 oneshot.* set 点变得"看起来活了"
(因为命名空间合规),但 audit 矩阵化(Task 12+)后立刻暴露 93 个纯死字段。
Task 14 一次性删除全部 93 个 set 点(实际删 95 处,因为部分 flag 在不同节点多次 set),
flag_total 从 166 降到 71。

**启示**:命名空间统一是清扫的前提条件;直接清扫"看起来活的"代码会留下大批漏网之鱼。
Linus 链表删除范例的现实版——先把数据结构对齐,死字段自然显形。

---

## 6. Pass 2 候选清单

按沙盒评审 §11 "不同意见记录":

- **Meta-Game Designer**:CG Codex(玩家可见的结局/伏笔收集本)
  — sync 版优先 / team 版 PKG 优先,Pass 2 评审会决定。
- **UX Designer**:`effects.learn` + `▌ 知道 · X ▐` 反馈条
  — 让 `know.*` flag 切换可见、可反查。
- **Lore Keeper**:PKG 字段 source/confidence 维度
  — 区分"亲历 / 道听途说 / 推论"。
- **共识**:试点 NPC 锁定 `n_npc_drowned_official`(林副科长)。

每个候选**独立**走一次 `script-review-team` 评审 → spec → plan → 实施。
Pass 1 已为这些 Pass 2 候选铺好基础设施(audit/state/lore_canon/namespace),不再有数据层卡点。

---

## 7. 验收 checklist

| 项 | 达成 | 备注 |
|---|---|---|
| `tools/audit_variants.py` + `tools/audit_state.py` 输出 JSON 报告 + exit code | ✓ | exit code 用于 CI 集成 |
| tree.json 全局 flags 唯一键 ≤ 80 | ✓ | 71(目标 ≤ 80) |
| 死字段清单可执行删除 + 至少 5 个 | ✓ | 删除 95 个 set 点(覆盖 93 个唯一 flag) |
| `meta_flags` 字段从 State 删除 | ✓ | Task 6(`932427b`) |
| `shifts_completed` 改 @property 派生 | ✓ | Task 8(`3c9277a`) |
| `tools/_state_sim.py` 与 path_explorer.py 共享解析 | ✓ | Task 1(`d3e2cd1`) |
| commit ADR-007 | ✓ | `f9b84b4` |
| State 类零引擎新增字段(只删不加) | ✓ | 仅删除 + @property 派生,无新增 |
| tree.json `lore_canon.years` 白名单 | ✓ | Task 5(`07eadf8`) |
| audit 脚本年份/术语红线 | ✓ | `audit_state.py` 检测 |
| path_explorer 8 主结局可达 | ✓ | E_BAD_1987 / E_BAD_DROWN / E_BROADCAST / E_DATA / E_HIDDEN / E_NEUTRAL / E_TRUE / E_TRUTH 全部最短 4 步可达 |
| `pytest tests/test_audit_*.py` 全绿 | ✓ | 24 passed(audit_state 10 + audit_variants 7 + audit_reactions 7) |
| path_explorer 三大盲区补丁 | ✓ | Task 13(`54459e2`) |
| 17 ending 可达性不变(Lore 红线) | ✓ | merge 后 endings count = 17,unreachable_variants = 0 |

---

## 8. 残余项与下一步

### 8.1 5 个孤立 require key

| flag | 引用节点 | 处置建议 |
|---|---|---|
| `asked_predecessor_name` | `n_npc_ghost_guard` | Pass 2 在 NPC 对话流程里 set,语义对应"问过前任名字" |
| `oneshot.s2_followed_double_shadow` | `n_npc_piano_ghost` | Pass 2 在 S2 内容补 set 点 |
| `oneshot.s2_returned_shoes` | `n_npc_red_dress_girl` | Pass 2 在 S2 鞋反馈分支补 set 点 |
| `oneshot.s6_grab_seven` | `n_end_bad_drown` | Pass 2 在 S6 第七工号交互补 set 点 |
| `saw_predecessor_map` | `n_landmark_picker` | Pass 2 看是否值得做地图发现机制 |

不在本 Pass 处理。Pass 2 的故事内容补全任务会一并解决,或评审后认为价值不足再删 require。

### 8.2 path_explorer 624 条 GR 上溢警告

正常的 clamp 行为(GR 100 上限),不是 bug。Pass 2 调奖励数值时一并复核。

### 8.3 variants 触发率 36.9% (52/141)

Lore + S* 节点的"重复访问 variant"在 path_explorer 自动 BFS 里很难全部跑到(需要的访问次数过深)。
Task 13 已为 picker 节点拓展过路径。剩余的低触发率多数在 `_lore_*` 节点(玩家选择性访问),
Pass 2 加 codex / 反馈条后会自然提高。

---

## 9. 不在本 Pass 范围内的发现

执行 Task 14 全量 pytest 时发现 `src/ghost_story_factory/pregenerator/story_generator.py:268`
存在已有语法错误(`f\"...\"` 反斜杠转义),由先前 commit `47550d9`(LangGraph M1)引入。
**未触碰**——不是本 Pass 的范围,且修复需要单独评估对 pregenerator 流程的影响。
建议下次重构 pregenerator 或 LangGraph M2 时一并修。

---

> 报告完。Pass 1 阶段产出 14 commit + 4 工具 + 1 ADR + 1 完成报告,
> 状态空间从 234 flags 降到 71,死字段近清零,8 主结局 + 17 ending 可达性保持。
> 准备进入 Pass 2 候选评审环节。
