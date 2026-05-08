# ADR-010: 沙盒拓扑契约 — 这是沙盒,不是死剧本

## Status
Accepted

## Date
2026-05-08

## Context

项目早期围绕 `PlotSkeleton`(线性 act/beat)+ branching dialogue tree 设计,默认是"分支剧本"思维 — 节点像一棵树,玩家走完叶子就结束。

但 v7 阶段(`hangzhou_yebanbaoan` 周目)实质已演化为**沙盒**:

- **G-273 周目沙盒原语已落地**:`n_landmark_picker` 56 入边 hub,7 地标 × `connections` 邻接,9 个 `_is_tool` × 9 处 `stay: True` 自循环,11 个状态化反应 variants(`deduction_resolved`/`foreshadow_resolved`/`theme_resolved`/`ending_seen`),`reaction_contracts` 注册 + `ending_seen` 跨周目联动。
- **map_view.py 546 行 + archive_view.py 339 行**:玩家不是"看一遍剧本就完",而是"探索一夜班 + 反复回访工具节点 + 拼伏笔档案"。

但 ADR-001 / ADR-009 / 旧 spec / 7 角色 prompt 仍隐含"分支树"语境。**下一次写剧本时如果没人盯着,大概率写成"线性 act + 分叉 ending"**(linmou Act 1 已经犯了这个错 — 27 节点 / 0 工具 / 单向辐射)。

## Decision

**把"沙盒"作为项目拓扑的第一公理固化下来。**任何新角色周目 / 新场景 / 新机制,默认必须遵守沙盒原语;偏离需要在 PR 描述里写"为什么这次不沙盒"并被评审团驳回前置。

### 沙盒原语(必须复用,不许重造)

| 原语 | 实现位置 | 含义 | 禁用反模式 |
|---|---|---|---|
| **picker hub** | `_is_map_picker: true` 节点 + `landmark_map` | 中央枢纽,所有地标从此辐射 | 把 entry → s1 → s2 → s3 → ending 串成单链 |
| **landmark connections** | `landmark_map[].connections: [sid]` | 地标间双向邻接,玩家从地标 A 可直走 B(不必回 hub) | 全部地标只能从 picker 进 — 这是"辐射"不是"网" |
| **`_is_tool` 工具节点** | `_is_tool: true` + `tools` 元数据 | 可反复访问,内容随 flag/班次/伏笔状态切换 narrative_variants | 工具节点访问一次后内容不变(浪费回访) |
| **`stay: true` effect** | `effects.stay: true` | 选项不消耗夜班 / 不离开当前节点,反复触发 flag | 工具节点访问 = 消耗一班(惩罚探索) |
| **反应契约** | `reaction_contracts.{deductions,foreshadows,themes}` + `narrative_variants[].if.{deduction_resolved\|foreshadow_resolved\|theme_resolved\|ending_seen}` | 推论/伏笔/主题/前次结局解开 → 后续节点叙述切档 | 用 `flags` 镜像兑现状态(违反 ADR-008 单一真相源) |
| **跨周目联动** | `ending_seen` clause + `endings_seen[story_id]: list` | 角色 A 通关影响角色 B 的同节点叙述 | 加 `character_played` 之类冗余字段 |

### 必须存在的"沙盒最小骨架"(任何新可玩角色)

1. ≥ 1 个 `_is_map_picker` hub
2. ≥ 4 地标,**每个地标至少 1 条 connections 邻边**(网,不是辐射)
3. ≥ 2 个 `_is_tool` 节点(物件/对讲/档案 任选,可反复访问)
4. ≥ 1 处 `stay: true` 工具自循环
5. 至少 1 个 `narrative_variants` 用反应 clause(让"已知"影响"叙述")

少于这个骨架的提案,直接打回 — 不是"沙盒不足",是"还没成沙盒"。

### "死剧本"反模式黑名单(评审一票否决)

- ❌ entry → 单链 → ending(没有 picker)
- ❌ 地标只能从 picker 进 + 不能横向跳(没有 connections)
- ❌ 工具节点 `next` 直接跳走(应该 `stay: true` 反复触发)
- ❌ NPC 只在某个特定剧情节点出现一次(应该绑 landmark + variants 切档)
- ❌ 同一 NPC 反复访问 narrative 不变(没有 `narrative_variants` + 反应 clause)
- ❌ 用 `flags` 手动镜像伏笔/推论解开(违反 ADR-007 / ADR-008)
- ❌ 新加 state 字段去表达"玩家见过 X"(查 `endings_seen` / `foreshadows_seen` / `deductions_resolved` 即可)

### 工具锁(machine-checkable)

- `tools/audit_tree.py`:hub 入边 ≥ N、孤儿地标 0
- `tools/audit_reactions.py`:`reaction_contracts` 全注册 + DEAD/UNREACHABLE 0
- `tools/audit_variants.py`:重复访问无分化检测
- `tools/audit_state.py`:flag 命名规范 + 不许镜像兑现状态
- `tools/audit_playability.py`:验证 GameTree 可玩闭环(坏 next / 非结局死路 / 动态 picker 目标 / 结局识别)
- (P1) `tools/audit_sandbox.py`:验证骨架 5 项(picker / connections / tool / stay / 反应 clause)

`tools/audit_all.sh` 链入,CI 阻断不合规 PR。

## Alternatives Considered

### A. 维持现状(ADR-001 PlotSkeleton 默认线性)
- **拒绝原因**:实质已演化成沙盒,文档语境跟代码反向 — 下次写剧本必踩坑。

### B. 把沙盒作为可选模式(用 flag 切换)
- **拒绝原因**:沙盒不是 feature,是当前游戏拓扑本身。"可选"= 默认还是死剧本。

### C. 新写一个"沙盒 SDK"层
- **拒绝原语**:已经有了 — `map_view.py` / `archive_view.py` / `_meets_clause` / `picker_choices` 就是 SDK。问题是文档没把它叫"SDK"。

## Consequences

### Positive
- 任何下次"加新角色 / 加新场景"任务,都自动按沙盒走 — 不会回退线性
- 评审团 7 人(尤其 Topology Designer)有明确判定标准
- `linmou Act 1` 的 sandbox debt 浮出水面(本 ADR 之前是隐性,现在显性)

### Negative & Mitigation
- **现有 ADR-001 / ADR-009 / spec 文档语境过时** → 在各 ADR 加 superseded by/related to ADR-010 引用
- **新作者上手成本高** → 用 G-273 周目作为参考实现,新手抄 hub + 工具节点结构
- **"沙盒最小骨架"门槛阻塞短期任务**(如 linmou Act 1 已合入)→ 列入 sandbox debt 清单(ADR-009 补充)逐项还

## 开放点

- 隐藏地标作为"扩展沙盒"还是"动态触发原语" — 默认前者,等第二个隐藏地标提案时再 ADR
- AI 生成的剧本(`generate_full_story.py` 路径)如何强制沙盒骨架 — 留待 v8

## Related

- **ADR-001 PlotSkeleton 流水线**:技术上仍生成 skeleton,但 v7 周目骨架 = 沙盒,skeleton 退化为"骨架内容大纲",非节点拓扑
- **TASK_GAMETREE_V1**:`docs/tasks/TASK_GAMETREE_V1.md` 将 ADR-010 落成机器可检查的 GameTree v1 可玩契约
- **ADR-007 状态空间契约**:flag 命名规范是沙盒契约的子集
- **ADR-008 反应机制**:`reaction_contracts` 是沙盒原语之一
- **ADR-009 linmou 周目**:本 ADR 让其 sandbox debt 显式化
