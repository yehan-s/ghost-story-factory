# ADR-001: 采用「骨架优先」的新故事生成流水线

- 状态: Accepted
- 日期: 2025-11-15
- 作者: （填写维护者）

---

## 1. 背景

现有 v3.x 流水线存在几个结构层面的问题：

- **结构与文案强耦合**
  - `DialogueTreeBuilder` 在同一阶段同时决定：
    - 对话树结构（节点、分支、结局）
    - 节点文案（叙事文本、选项文案）
  - 结果是：结构约束很弱，结构质量严重依赖 LLM 输出的“运气”。

- **主线深度和节奏「靠 heuristics + 重试」**
  - 主线深度、结局数量、时长由一堆启发式控制：
    - `EXTEND_ON_FAIL_ATTEMPTS`
    - `PROGRESS_PLATEAU_LIMIT`
    - `depth_booster.py` / `depth_orchestrator.py`
  - 不同层的“扩展/重试”叠加，调参困难，行为不可预测。

- **分支设计缺乏全局视角**
  - critical / normal / micro 分支混在一起生成，没有全局剧情节奏图；
  - 生成出来的树往往“深度够了，但节奏难看，分支意义不清晰”。

- **现在可以放弃旧故事数据**
  - 旧故事允许彻底作废，只对之后的“新故事模式”负责；
  - 是一次重构生成流水线的窗口期。

---

## 2. 决策

本 ADR 做出以下决策：

1. **采用「骨架优先」的故事生成模式**
   - 新增独立的数据结构 `PlotSkeleton`，用来描述：
     - 幕结构（acts）
     - 节拍（beats：setup / escalation / twist / climax / aftermath）
     - 分支类型与关键节点（critical / normal / micro，以及结局节点）
   - 对话树结构必须先由骨架确定，再映射为可玩的节点树。

2. **彻底解耦“结构生成”和“文本生成”**
   - Stage B：骨架生成（Skeleton Generator）
     - 输出严格 JSON 的 `PlotSkeleton`；
     - 不生成大段文案。
   - Stage C：在骨架锁定后，为每个节点生成叙事文本和选项文案；
   - Stage D（可选）：在结构固定前提下，对整棵树做风格统一和润色。

3. **停止依赖多层“扩展/重试”来硬凹深度**
   - 在骨架层控制主线深度 / 结局数量 / 节奏分布；
   - 新模式下：
     - `DialogueTreeBuilder` 不再使用 `EXTEND_ON_FAIL_ATTEMPTS` 等自动扩展作为主要手段；
     - `depth_booster.py` / `depth_orchestrator.py` 视为旧架构遗留，只保留历史参考；
     - `TimeValidator` 仅用于 sanity check，而不是扩展驱动器。

4. **不再兼容旧故事数据与旧 v1 CLI 流程**
   - 允许清空旧故事相关表与旧 deliverables 文件；
   - `set-city / get-struct / get-story` 旧命令视为 legacy，只保留在历史版本中；
   - 新模式以“城市 + 剧情概要 → 预生成对话树”为官方路径。

---

## 3. 方案细节

### 3.1 PlotSkeleton 数据结构（方向性）

骨架按「幕 → 节拍 → 分支」分层。

- Story 级字段：
  - `title`: 故事标题
  - `acts`: 幕列表
  - `config`:
    - `min_main_depth`
    - `target_main_depth`
    - `target_endings`
    - `max_branches_per_node`

- Act:
  - `index`
  - `label`: 如 `Act I / Act II / Act III`
  - `beats`: 该幕中的节拍列表

- Beat:
  - `id`
  - `act_index`
  - `beat_type`: `"setup" | "escalation" | "twist" | "climax" | "aftermath"`
  - `tension_level`: 1–10
  - `is_critical_branch_point`: bool
  - `leads_to_ending`: bool（可选）

- Branch（在 Beat 中）:
  - `branch_type`: `"CRITICAL" | "NORMAL" | "MICRO"`
  - `max_children`: 该节点预期的最大子节点数
  - `notes`: 分支意图简述

实际 schema 由实现阶段在 `docs/tasks/TASK_STORY_STRUCTURE.md` 中进一步细化。

### 3.2 新流水线阶段划分

在 v4 架构中，故事生成流水线划分为：

1. Stage A：文档生成（已有完整生成器）
   - 原有 `generate_full_story.py` 流程不大改，仅做参数与接口清理。

2. Stage B：骨架生成（Skeleton Generator）
   - 新增 `SkeletonGenerator`：
     - 输入：`city + synopsis + lore_v2 + main_story 摘要`
     - 输出：`PlotSkeleton` JSON
   - 使用专门模板 `templates/plot-skeleton.prompt.md`；
   - 带严格 JSON 校验与基本结构指标检查。

3. Stage C：TreeBuilder 骨架驱动模式
   - `DialogueTreeBuilder.generate_tree()` 接受 `plot_skeleton` 参数；
   - 在 guided 模式下：
     - 不再自主决定何时生成 critical / normal / micro 分支，而是按骨架执行；
     - 结局节点只能出现在骨架标记允许的位置。

4. Stage D：节点文本填充与润色
   - 遍历对话树，根据所在 beat 的类型与 tension 生成节点叙事和选项文案；
   - 可在后续版本增加统一风格润色阶段，但不改变结构。

详细流程图见 `docs/architecture/STORY_PIPELINE_V4.md`。

---

## 4. 备选方案与取舍

### 4.1 保持现有 BFS + heuristics（拒绝）

- 做法：
  - 继续调大 `MAX_DEPTH` / `EXTEND_ON_FAIL_ATTEMPTS`；
  - 增强 `depth_booster` / `depth_orchestrator` 的策略。
- 问题：
  - 结构依旧不可预测，甚至更难 debug；
  - 分支与节奏缺乏全局设计，无法稳定产出好结构；
  - 启发式数量继续膨胀，违背“好品味”的简洁原则。

### 4.2 在现有 TreeBuilder 内增加更多 Agent（拒绝）

- 做法：
  - 直接在 `DialogueTreeBuilder` 内使用多 Agent、多 prompt，期望“顺便”把结构拉齐。
- 问题：
  - 没有独立骨架数据结构，各 Agent 无法共享明确的结构约束；
  - 复杂性继续上升，问题变成“prompt 調参地狱”。

### 4.3 骨架优先 + 分阶段文案（采纳）

- 优点：
  - 在骨架层就能控制主线深度 / 结局数量 / 节奏；
  - TreeBuilder 职责单一：把 `PlotSkeleton` 映射为对话树；
  - 文案层只负责表达，不再承担结构责任；
  - 便于后续引入不同风格/模型而不破坏结构。
- 缺点：
  - 一次性重构量较大，需要新增 Skeleton 层实现；
  - 需要为 `PlotSkeleton` 定义和维护清晰的 schema。

---

## 5. 影响与迁移

- 数据库与旧故事：
  - 允许通过迁移脚本清空现有 `stories / characters / dialogue_nodes / story_metadata`；
  - 旧故事默认不再支持游玩，仅保留作为开发期参考。

- 代码：
  - 新增 `SkeletonGenerator` 与相关 schema/model；
  - 扩展 `DialogueTreeBuilder` 支持 guided 模式；
  - 将 `depth_booster.py` / `depth_orchestrator.py` 标注为 legacy。

- 文档：
  - 本 ADR 归档在 `docs/architecture/ADR-001-plot-skeleton-pipeline.md`；
  - 实施任务拆分与进度跟踪见 `docs/tasks/TASK_STORY_STRUCTURE.md`；
  - v4 流程架构说明见 `docs/architecture/STORY_PIPELINE_V4.md`。

---

## 6. 回滚策略

- 打 tag：在引入骨架模式前打一个如 `v3-legacy-pipeline` 的 tag；
- 如 v4 流水线在实践中出现严重问题，可以回退到该 tag，恢复原有 v3 架构；
- 不提供“长期新旧共存”的支持路径：新模式一旦验证可用，旧模式仅存于历史版本。

