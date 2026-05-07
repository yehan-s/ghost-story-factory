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

数据驱动证据:

| 来源 | 数据 |
|---|---|
| sync 版评审 | tree.json 234 flags,153 个只用一次(65%) |
| team 版评审 | meta_flags 0 引用,puzzle_pieces 8 处可能合并,_SPOILER_KEYS 隐式契约易漏 |
| QA 实测 | 71 个 npc/工具节点中估计 50+ 重复访问无 narrative_variants 分化 |

## Decision

本 ADR 把 State 字段冻结成正式契约,并对 flags 命名空间作硬约定。

### State 字段冻结清单(Pass 1 完成后)

| 字段 | 类型 | 归类 | 用途 |
|---|---|---|---|
| `PR` | int | 仅本周目 | 个人共鸣值 |
| `GR` | int | 仅本周目 | 全局共鸣值 |
| `inv` | List[str] | 仅本周目 | 物品栏 |
| `flags` | Dict[str, bool] | 仅本周目 | 通用 flag(按下文命名空间分桶) |
| `shifts_skipped` | @property | 派生 | 由 `len(skipped_landmarks)` 算出 |
| `shifts_completed` | @property | 派生 | 由 `len([l for l in visited_landmarks if l in {S1..S6}])` 算出 |
| `visited_landmarks` | List[str] | 仅本周目 | 已访问地标 |
| `skipped_landmarks` | List[str] | 仅本周目 | 跳过的地标列表(`shifts_skipped` 由它派生) |
| `puzzle_pieces` | List[str] | 仅本周目 | 已收集谜题碎片 |
| `character` | str | 仅本周目 | 当前角色身份(G-273 / linmou_1985 等) |
| `last_landmark_id` | Optional[str] | 仅本周目 | 上一站地标 ID(给地图渲染) |
| `npc_locations` | Dict[str, str] | 仅本周目 | NPC 当前位置 |
| `visit_counts` | Dict[str, int] | 仅本周目 | 每个节点被访问次数(引擎自动维护) |
| `known_landmarks` | List[str] | 仅本周目 | 地图上可见地标 |
| `PR_peak` | int | 仅本周目 | PR 历史峰值(成就用) |

**Pass 1 删除的字段**:

- ❌ `meta_flags`(0 写 0 读,纯死字段。周目继承等真有需求时再加 `meta.*` namespace)
- ❌ `route`(v7 已废弃,从 V6 遗留)

**Pass 1 改为派生属性的字段**:

- `shifts_completed` → `@property`,从 `visited_landmarks` 中 S1-S6 数量算出
- `shifts_skipped` → `@property`,等于 `len(skipped_landmarks)`

**总计**:14 个字段(原)→ 11 个真字段 + 2 个 `@property` 派生 + 删 1 个死字段(net 减 3 个真字段)。

### Flag 命名空间约定

所有 `flags` 字典的 key **必须**遵循 `<namespace>.<name>` 格式,namespace 限定为下表 6 种:

| namespace | 用途 | 示例 | 生命周期 |
|---|---|---|---|
| `know.*` | 玩家知识 | `know.linmou_85_corruption` | 永久(本周目) |
| `oneshot.*` | 一次性事件触发标志 | `oneshot.s4_first_visit` | 永久(本周目) |
| `arc.*` | 故事弧线进度 | `arc.lin_act_2_done` | 永久(本周目) |
| `route.*` | 路线锁定 | `route.lin_arc_locked` | 永久(本周目) |
| `state.*` | 临时状态(可被 effects 清除) | `state.flashlight_on` | 短期 |
| `meta.*` | 跨周目继承(预留,Pass 1 不实现) | `meta.true_ending_seen` | 跨周目 |

**约束**(由 `tools/audit_state.py` 强制):

- 任何 require 引用的 flag 必须在某处 effects 里被 set 过(orphan_require → CI 红)
- 任何被 set 的 flag 必须至少被一处 require 读到(否则是死字段 → CI 黄)
- 不允许出现在上述 6 个 namespace 之外的 key(如 `s1_threw_coat` 必须迁移到 `oneshot.s1_threw_coat`)

### `_SPOILER_KEYS` 提为正式契约

`player.py:_SPOILER_KEYS` 现在是一个隐式 tuple,新加 require 字段时容易漏。本 ADR 把它提为正式契约:

```python
# player.py 顶部(模块级常量,大写)
SPOILER_KEYS: Tuple[str, ...] = (
    "PR_min", "PR_max", "GR_min", "GR_max",
    "flags", "shifts_completed_min", "shifts_skipped_min",
    "landmark_visited", "character", "not",
)
```

任何新增 require 字段必须明确归入"玩家可知"或"spoiler",并在审计脚本里 hard assert(若 require 用了不在列表里的 key,审计 → CI 红)。

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

`audit_state.py` 在所有 narrative 文本里检查:

- 引用其他年份(1900-2030 范围内)直接 fail
- 出现 forbidden_terms 任一即 fail

理由(Lore Keeper 评审):杭州夜班的"国营单位"质感是项目最不可替代的特色,新增内容若把"评议会"写成"管理委员会"、把"工号"写成"员工编号",一秒钟出戏。

## Alternatives Considered

### Option A: 加 `State.knowledge: Set[str]` + `effects.learn`(Chief Editor 初步倾向)

- **Pros**: 显式区分"玩家知道"vs flags
- **Why rejected**: 反加法者两轮一致反对(State Architect + Topology Designer):
  - 语义上等同 `flags["know.X"] = true`,加新维度只是语法糖
  - meets() 已支持嵌套 any_of/all_of/not + flags 判断,knowledge_has/lacks 是冗余 API
  - 现有 200+ flags 已经无规范、无生命周期。再加新维度会让那 153 个一次性 flag 永远清理不掉(变成无人维护的化石层)
  - 真问题是"flag 命名混乱+一次性 flag 占 65%",不是"缺一个 knowledge 维度"

先治理现有 flags,如果之后发现真不够用再升级。YAGNI。

### Option B: 推倒重建 State 类

- **Pros**: 干净
- **Why rejected**: 破坏现有玩法,违反 Linus "Never break userspace"。109 节点 5.6 万字内容资产不容浪费。

### Option C: 用 `inv` 模拟 knowledge(现状一部分)

- **Pros**: 复用现有维度
- **Why rejected**: 已经有 15 件 signaling-only 道具(7 工人速写 / 武林门 7 人录音 / 1987 告示残页等),它们事实上在用 inv 模拟 knowledge,但语义混乱(物品 vs 知识不可区分)。Pass 1 的清扫目标之一就是把这部分迁出 inv。

## Consequences

### Positive

- 状态空间从 14 字段降到 11 字段(删 3 个,净减)
- flags 唯一键从 234 降到 ≤ 80(下沉局部 flag + 合并双写道具)
- 任何新加字段必须先论证为何不能用现有 11 字段表达
- audit_state.py 把命名空间约定固化为 CI 红线
- `_SPOILER_KEYS` 不再隐式,新增 require 字段不会漏

### Negative & Mitigation

- **`tree.json` 中所有现有 flag 名要重命名** → **Mitigation**: Task 10-12 集中处理,每改一批跑一次 path_explorer 回归
- **玩家通关录像作为视觉回归基线** → **Mitigation**: Pass 1 启动前 snapshot 一份 v7 通关录像,清扫完后跑同样选择对照
- **现有 effects 里 `set_route` / `meta_flags` 副作用要删除** → **Mitigation**: Task 6 + Task 7 由 audit 脚本守门,有遗漏自动报红

### 决策有效期

- Pass 1 完成 → 本 ADR 生效
- Pass 2 评审若启动 PKG 升级,可由 ADR-008 修订或 supersede 本 ADR
- 在 Pass 1 落地前,本 ADR 是"Proposed";落地后转 Accepted

## 相关文档

- 评审报告:`docs/team-reviews/2026-05-07-沙盒方向首个开发任务.md`
- Pass 1 实施计划:`docs/superpowers/plans/2026-05-07-pass1-state-space-audit-and-flag-cleanup.md`
- 上游设计:`docs/superpowers/specs/2026-05-07-PROJECT-STATE-AND-FORESHADOW-REGISTRY.md`(伏笔注册表 = "草版 PKG")
