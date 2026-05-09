# TASK: v4 生成器对齐 GameTree v1 沙盒拓扑

版本: v0.2
状态: Active
关联:
- `docs/tasks/TASK_GAMETREE_V1.md`
- `docs/tasks/TASK_STORY_STRUCTURE.md`
- `docs/architecture/ADR-001-plot-skeleton-pipeline.md`
- `docs/architecture/ADR-010-sandbox-topology-contract.md`
- GitHub Issue: `#23`

---

## 0. 背景

`TASK_GAMETREE_V1.md` 已把正式杭州树收敛成可审计的 `GameTree v1` 基线:

- 坏跳转 / 死路 / 结局识别由 `tools/audit_playability.py` 守门;
- 正式节点具备 `presentation` 文本兜底;
- v7 沙盒拓扑以 picker hub / landmark connections / tool / stay / reaction variants 为核心。

但 v4 骨架生成流水线仍偏“剧情树”思维。`PlotSkeleton` 目前更像 act/beat 大纲,还没有足够信息生成可玩的沙盒地图、NPC 出没、工具节点和演出槽。

本任务专门承接从 `TASK_GAMETREE_V1` 拆出的两项遗留:

- 让 v4 生成输出逐步靠近 `GameTree v1`;
- 为 `PlotSkeleton` 增加 `location_id / npc_ids / event_slots / asset_cues` 等内容大纲字段。

---

## 1. 目标 / 非目标

### 目标

- [x] 扩展 `PlotSkeleton` 数据模型,让 beat 能表达沙盒所需的最小定位信息;
- [x] 更新 `plot-skeleton.prompt.md`,要求 LLM 输出地标、NPC、工具节点和演出提示;
- [x] 增加一个 `GameTreePlan` 或等价中间层,把骨架大纲转成 `GameTree v1` 形状前的结构计划;
- [ ] 让生成链路产物能被 `audit_playability.py` 和后续 `audit_sandbox.py` 检查;
- [ ] 保持 v3 legacy / 当前手写 v7 正式树兼容。

### 非目标

- 不一次性要求 LLM 写出完整高质量正式剧本文案;
- 不修改 DB schema;
- 不替换 `hangzhou_yebanbaoan` 手写树;
- 不引入真实图片 / 音频素材;
- 不把沙盒拓扑退化成线性 act 分支。

---

## 2. 数据结构方向

### 2.1 PlotSkeleton 扩展字段

优先考虑给 `BeatConfig` 增加可选字段:

- `location_id`:该 beat 归属的地标或场景 ID;
- `npc_ids`:该 beat 主要出场 NPC;
- `event_slots`:该 beat 贡献的事件槽,例如 `tool`, `npc_meet`, `revisit`, `ending_gate`;
- `asset_cues`:演出提示,例如 `background`, `sprite`, `sfx`, `cg_unlock`;
- `sandbox_role`:该 beat 在沙盒拓扑里的角色,例如 `hub`, `landmark`, `tool`, `payoff`, `ending`;
- `revisit_hooks`:重访时可切换的状态钩子。

这些字段必须可空,避免破坏旧 skeleton JSON。

### 2.2 GameTreePlan 中间层

建议新增中间数据结构,不要让 `PlotSkeleton` 直接承担可玩树所有细节:

- `locations`:地图地标与 connections;
- `tools`:可反复访问的工具节点;
- `npc_routes`:NPC 初始位置和可能迁移;
- `beats`:beat 到节点候选的映射;
- `presentation_defaults`:按 scene/role 推导的演出兜底;
- `acceptance`:本轮生成必须满足的最小审计条件。

理由:骨架是内容大纲,`GameTreePlan` 才是可玩拓扑计划。把两者混在一起,后面会变成又一坨胶水。

---

## 3. 里程碑

### M1: 模型与兼容

- [x] 扩展 `skeleton_model.py`;
- [x] 更新 `tests/test_skeleton_model.py`,确保 `to_dict/from_dict` 往返不丢字段;
- [x] 老 skeleton JSON 缺字段时仍能加载。

### M2: Prompt 与生成

- [x] 更新 `templates/plot-skeleton.prompt.md`;
- [x] 更新 `skeleton_generator.py` 的解析 / 校验;
- [x] 为新字段加最小单测。

### M3: GameTreePlan 草案

- [x] 新增 `pregenerator/gametree_plan.py`;
- [x] 从 `PlotSkeleton` 生成最小 `GameTreePlan`;
- [x] 为 hub / landmark / tool / ending_gate 建最小结构测试。

### M4: 审计接入

- [ ] 让 `GameTreePlan` 或其导出树能被 `audit_playability.py` 检查;
- [ ] 新增 `audit_sandbox.py` 或扩展现有审计,验证 ADR-010 最小沙盒骨架;
- [ ] 将相关测试挂入 `tools/run_all_tests.py`。

---

## 4. 验收标准

- `venv/bin/python tools/run_all_tests.py` 通过;
- 新字段往返不破坏旧 skeleton;
- v4 生成链路能明确产出“沙盒计划”,而不是只产出线性 act/beat;
- 文档明确 `PlotSkeleton` 和 `GameTreePlan` 的职责边界;
- 不影响正式 `hangzhou_yebanbaoan/tree.json` 的运行与审计结果。

---

## 5. 进展记录

### 2026-05-09: M1-M3 第一批落地

- `BeatConfig` 增加 `location_id / npc_ids / event_slots / asset_cues / sandbox_role / revisit_hooks`,全部为可选字段;
- `PlotSkeleton.from_dict()` 继续兼容旧 JSON,缺少新字段时默认给空值;
- `plot-skeleton.prompt.md` 已要求 LLM 输出地标、NPC、工具节点、演出提示和重访钩子;
- 新增 `pregenerator/gametree_plan.py`,把内容骨架转换成计划层的 `locations / tools / npc_routes / beats / presentation_defaults / acceptance`;
- `GameTreePlan.to_minimal_tree()` 只用于内存测试和后续生成器对齐,不写正式树、不改 DB schema、不接入正式审计链;
- M4 仍保留为后续工作:新增或接入 `audit_sandbox.py`,并决定何时挂入 `tools/run_all_tests.py`。
