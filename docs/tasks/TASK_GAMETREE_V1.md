# TASK: GameTree v1 可玩闭环与 VN/沙盒契约收敛

版本: v0.1
状态: Active
关联 ADR:
- `docs/architecture/ADR-010-sandbox-topology-contract.md`
- `docs/architecture/ADR-001-plot-skeleton-pipeline.md`

---

## 0. 背景

项目当前有三套互相分裂的数据模型:

- v3/v4 预生成树: `PlotSkeleton -> DialogueTreeBuilder -> SQLite dialogue_tree`
- engine runtime: `GameState + Choice + GameEngine`
- v5/v7 手写沙盒树: `tree.json nodes + require/effects + State + SaveManager`

这导致同一个概念出现多份实现:状态字段、选择跳转、结局判断、可达性校验、伏笔反应。结果是旧 DB 资产能生成但不可保证可玩,运行时甚至会为坏分支创建占位结局。这不是内容问题,是数据结构问题。

本任务把 `stories/hangzhou_yebanbaoan/tree.json` 作为当前产品基线,抽象出 `GameTree v1` 的最低可玩契约。v4 `PlotSkeleton` 继续保留,但只能作为内容大纲;最终可玩拓扑必须符合 ADR-010 沙盒契约。

---

## 1. 目标 / 非目标

### 1.1 目标

- [ ] 定义 `GameTree v1` 最小契约:
  - `nodes`
  - `choices`
  - `require`
  - `effects`
  - `narrative_variants`
  - `endings`
  - `foreshadows`
  - `deductions`
  - `npcs`
  - `landmark_map`
  - `assets`(可空,为 VN 演出预留)
- [ ] 新增可玩性守门工具,阻断坏树:
  - 非结局节点不能无出路;
  - choice 不能指向不存在节点;
  - 结局节点必须可识别;
  - v7 `_is_map_picker` 可以通过 `landmark_map` 动态生成目标,不能被旧树检查误判为死路。
- [ ] 禁止运行时修坏树:
  - runtime 不再创建 `missing_branch` 占位结局;
  - 坏数据必须在生成/导入/审计阶段暴露。
- [ ] 修正现有工具对 v7 `tree.json` 的误读:
  - `tools/view_tree_progress.py` 必须识别 `{"nodes": {...}}` 结构;
  - 不能把顶层 metadata 当成节点统计。
- [ ] 将 `GameTree v1` 审计挂入测试入口。

### 1.2 非目标

- 不在本任务一次性重写完整 VN 图形界面;
- 不直接引入 Ren'Py 等外部引擎;
- 不用通用好感度系统替代现有 `flags/know/met/helped/betrayed` 语义化状态;
- 不把实时 LLM 当作开放沙盒的核心机制。开放感来自状态组合、地图调度、重访变体和跨周目反应。

---

## 2. GameTree v1 最小契约

### 2.1 树结构

`GameTree v1` 支持两种输入形态:

1. 旧预生成树:

```json
{
  "root": {"node_id": "root", "choices": [{"next_node_id": "node_0001"}]},
  "node_0001": {"is_ending": true}
}
```

2. v7 沙盒树:

```json
{
  "start_node": "n_intro",
  "nodes": {
    "n_intro": {"choices": [{"next": "n_landmark_picker"}]},
    "n_landmark_picker": {"_is_map_picker": true}
  },
  "landmark_map": [
    {"id": "S1", "node_id": "n_s1_arrive", "connections": ["S2"]}
  ]
}
```

### 2.2 选择跳转

合法跳转来源:

- `choice.next_node_id`
- `choice.next`
- `choice.next_variants[].next`
- v7 `_is_map_picker` 通过 `landmark_map[].node_id` 和 `landmark_map[].connections` 动态生成

### 2.3 结局识别

结局节点必须满足至少一项:

- `is_ending: true`
- `ending_type` 存在且 `choices` 为空

第二条只作为兼容历史数据的最低识别规则。新数据必须显式写 `is_ending: true`。

---

## 3. 里程碑

### M1: 可玩性守门工具

- [x] 新增 `tools/audit_playability.py`
- [x] 支持旧预生成树与 v7 `nodes` 树
- [x] 支持 `_is_map_picker` 动态目标
- [x] 新增 `tests/test_audit_playability.py`
- [x] 修正 `tools/view_tree_progress.py` 对 v7 树的读取

### M2: 运行时不再补洞

- [x] 移除 `DialogueTreeLoader` 创建 `missing_branch` 占位结局的路径
- [x] 更新对应测试,把坏跳转视为失败而不是自动修复

### M3: 现有 v7 剧本数据修复

- [x] 修正 linmou 1985 结局节点缺少 `is_ending: true` 的数据债
- [x] 对 `stories/hangzhou_yebanbaoan/_fragment_v7_*.json` 修改后重新运行 `tools/merge_fragments.py`
- [x] 跑 `tools/audit_all.sh` 和 `tools/audit_playability.py`

### M4: GameTree v1 schema 与生成链路

- [x] 新增 `src/ghost_story_factory/runtime/contracts.py`
- [x] 定义统一 `RequirementEvaluator / EffectApplier / EndingResolver`
- [x] 正式播放器 `v5/player.py` 改为调用契约层,不再把 require/effects/ending 规则全部写死在 `State`
- [x] 修正正式地图 picker 调用,传入当前 node,让 `_picker_endshift_choice` 生效
- [x] 修正 `SaveManager.check_achievements()` 对 `endings_seen` dict 的计数错误
- [x] 修正正式树的 `ending_seen.ending_id`:统一使用 `E_TRUTH` / `E_DATA` 等 ending_type,不再使用 `n_end_*` 节点 ID
- [x] 修正正式树 `n_landmark_picker` 静态 choices 与 `landmark_map` 的 S6/S7 解锁阈值错位
- [x] 为 `n_l1985_landmark_picker` 补显式 L1-L4 + 湖边结束 choices,动态 picker 继续作为正式运行路径
- [ ] 让 v4 生成输出逐步靠近 `GameTree v1`
- [ ] `PlotSkeleton` 增加 `location_id / npc_ids / event_slots / asset_cues` 等内容大纲字段

### M5: VN 演出契约

- [x] 顶层增加可空 `assets` manifest
- [x] 节点支持可空 `presentation` 字段:
  - `background`
  - `bgm`
  - `sfx`
  - `sprite`
  - `expression`
  - `cg_unlock`
  - `transition`
- [x] `tools/merge_fragments.py` 合并正式树时按 scene 自动补默认 presentation
- [x] `tools/audit_playability.py` 新增 presentation/assets 引用审计,缺资源时允许文本 fallback,但不允许悬空引用

---

## 4. 验收标准

本任务完成时,至少满足:

- `tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json` 不出现 error;
- `tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json` 显示 `演出节点: 145/145`;
- `tools/view_tree_progress.py --checkpoint stories/hangzhou_yebanbaoan/tree.json` 统计节点来自 `nodes`,不是顶层 metadata;
- runtime 不再生成 `missing_branch` 占位结局;
- `tools/run_all_tests.py` 包含可玩性审计测试;
- 文档明确: `PlotSkeleton` 是内容大纲,`GameTree v1` / ADR-010 才是可玩拓扑契约。

---

## 5. 后续路线

优先级从高到低:

1. `GameTree v1` 审计阻断坏树;
2. 现有《断桥残雪》数据债修复;
3. v5/v7 播放器继续拆 `PlayerSession / EndingService / ChoiceVisibility / MapChoiceBuilder`;
4. v4 生成器输出沙盒拓扑;
5. 用真实素材替换 `assets.*.text_fallback`,并实现回看/收集本。
