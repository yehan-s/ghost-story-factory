# ADR-008: 戏剧化反应机制 + 跨周目认知继承契约

## Status
Accepted

## Date
2026-05-07

## Context

元数据架构(14 伏笔 / 4 推论 / 6 母题 / 10 成就 / 3 路线)只在档案视图(`s` 键)可见,主流程节点 narrative 跟伏笔状态无关联。**架构是"死的成绩单"**。需要一套机制让"已解开的伏笔/推论/母题"驱动节点叙事切档,让玩家在主流程感受到世界"记得"自己做过什么。

7 人评审团对此任务给出意见,产出 `docs/team-reviews/2026-05-07-dramatic-reaction.md`,决议为"修改后放行"。本 ADR 固化关键决议。

## Decision

### 引擎层
扩展 `src/ghost_story_factory/v5/player.py::_meets_clause()` 加 3 个新条件:
- `deduction_resolved: str | list[str]`
- `foreshadow_resolved: str | list[str]`
- `theme_resolved: str | list[str]`(检查 `themes[id].manifestations ⊆ resolved_set`)

**list 是 ANY 语义**(任一满足即 True)。需要 ALL 用 `all_of` 显式。

### 状态注入
**State 持 `save_manager` + `story_id` + `tree` 引用**(单一真相源 = save_manager)。
`save_manager`/`story_id`/`tree` 任一缺失 → 三个新条件安全降级返回 False(向后兼容)。

**拒绝 `on_resolve_inject`**(镜像 flags = 两套账本,职责分离铁律)。

### 命名空间语义(文档级,不入变量名)
评审决议:**不上 `meta./run./motif.` 三命名空间前缀**(避免污染 prompt 创作)。
仅在本 ADR 文档说明语义分桶,实现层 `_meets_clause` 自然分桶:

| 语义 | 数据源 | 判定条件 | 写入路径 |
|---|---|---|---|
| **meta**(跨周目) | `save_manager` | `deduction_resolved` / `foreshadow_resolved` / `theme_resolved` | 只读 — 由 `save_manager.mark_*_resolved()` 写,不可被 effects 写 |
| **run**(per-run) | `state.flags` / `state.inv` | `flags` / `inv_has` / `visit_count_min` | effects 可写 |
| **motif**(母题累计) | 派生(留作未来) | `theme_resolved`(已实现 = 一次性) | 同 meta |

### 跨周目认知继承
- 玩家"知道"和角色"知道"必须分离
- 跨周目继承体现为:**叙述者口吻 / 选项措辞 / 隐藏选项可见性**变化
- **不是**改角色对话事实(否则角色失忆设定崩塌)
- 新角色剧本通过 `narrative_variants` 的 meta-aware 分支体现继承

### True Ending 解锁
**禁止**把"解开 N 推论"作为硬门槛(逼玩家刷周目违背单周目完整体验原则)。改为档案彩蛋。

### Variant 优先级
**列表序 = 优先级序**,specific → general。`_meets_clause` 返回首个匹配。
**default variant 必须保留**(`audit_reactions` 强制)。

### 守门契约
`tree.json` 顶层 `reaction_contracts` 字段:每个 deduction/foreshadow/theme 必须声明:
```json
"reaction_contracts": {
  "deductions": {
    "<deduction_id>": {
      "resolver_node": "<node_id_where_deduction_is_resolved>",
      "consumer_nodes": ["<node1>", "<node2>"]
    }
  },
  "foreshadows": { ... },
  "themes": { ... }
}
```

`tools/audit_reactions.py` 三红线检测:
- **DEAD_REACTION**(阻断):variant 引用了某 ID 但 contracts 无声明
- **UNREACHABLE_REACTION**(阻断):resolver 不可达 / consumer 走不到
- **ORPHAN_RESOLVE**(警告):声明了 resolver 但无 variant 消费(剧本浪费)

### 内容层守则
Phase 4 内容创作必须:
- 保留 default variant 同节点(独立可读,不依赖玩家"记得上次说了什么")
- 查 `data/lore_voice_matrix.json` 锚点(NPC 语气切档)
- 查 `data/motif_anchors.json` 锚点(母题氛围切档)
- 不许触碰 redlines(非杭州地标 / 非 80 年代物件 / 日式怨灵化)

### UX 守则
- **节点级 variant 静默切**(让玩家自己发现差异 = horror 体验核心快感)
- **母题级**首次过渡用 narration beat(`空气里的味道变了`)
- **拒绝** glitch 动画 / 弹窗(破坏氛围)
- 新选项无 UI 标记,通过文本暗示("你忽然想起前任的话…")

## Alternatives Considered

### Option A: `State.__init__(save_manager=None, story_id=None)` 注入 [✅ 采纳]
- Pros: 数据归属关系显式,单一真相源
- Cons: 测试 fixture 需更新(已用 `default=None` 缓解)

### Option B: `_meets_clause(self, require, save_manager, story_id)` 参数透传 [❌]
- Why rejected: 参数瘟疫,污染整条调用链(State Architect 评审反对)

### Option C: `on_resolve` 写镜像 flags(`_resolved_<id>=True`) [❌]
- Why rejected: 两套账本,任一处忘同步就是隐藏 bug。State Architect 强烈反对。

### Option D: 三命名空间前缀(`meta.* / run.* / motif.*`) [❌]
- Why rejected: 污染 prompt 创作,实现层自然分桶已够。仅在本 ADR 固化语义边界。

### Option E: variant schema 扩展 `voice_constraint / priority / fallback_to_default` [❌]
- Why rejected: 过度设计。优先级用列表序;立场约束用 Lore 锚点表 + 编剧纪律;default 由 `audit_reactions` 强制。

### Option F: True ending 解锁 = 解开 N 推论 [❌]
- Why rejected: 逼玩家刷周目违背单周目完整体验。改为档案彩蛋。

## Consequences

### Positive
- 玩家在主流程感受到世界"记得"自己做过什么
- 元数据架构从档案表变成活机制
- `audit_reactions` 守门,反应式 variant 不会成死代码
- Lore 锚点表 + ADR 文档,新内容可机械查表(降低创作随机性)

### Negative & Mitigation
- 新加 3 类条件 → audit_state 需识别新前缀
  - **Mitigation**: audit_state 已支持任意键名,无需改
- variant 增量 ~15-20(Topology Designer 评估)
  - **Mitigation**: 7 节点白名单(Chief Editor 评审定),不许扩张
- 跨 fragment 写 `reaction_contracts` 易漏
  - **Mitigation**: `audit_reactions` ORPHAN_RESOLVE 检测
- `lore_canon` 之前手加在 tree.json,re-merge 时被冲掉
  - **Mitigation**: 已落地 `tools/merge_fragments.py:STORY_META`(Phase 2 同步修复)

## 参考

- 评审报告: `docs/team-reviews/2026-05-07-dramatic-reaction.md`
- 实施 plan: `docs/superpowers/plans/2026-05-07-dramatic-reaction.md`
- Lore 锚点: `data/lore_voice_matrix.json` + `data/motif_anchors.json`
- 守门工具: `tools/audit_reactions.py`
- 关联 ADR: ADR-007(状态空间契约,本 ADR 增量)
