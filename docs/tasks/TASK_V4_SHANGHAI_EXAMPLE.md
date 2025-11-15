# TASK: v4 上海示例故事结构验收（虹口电台）

版本: v0.1  
状态: 草案（可迭代）  
关联 ADR: `docs/architecture/ADR-001-plot-skeleton-pipeline.md`  
前置任务:  
- `docs/tasks/TASK_STORY_STRUCTURE.md`  
- `docs/tasks/TASK_V4_DEFAULT_PIPELINE.md`

---

## 0. 背景

- v4 骨架流水线已作为默认生成路径接入（StoryGeneratorWithRetry 主路径走：文档 → PlotSkeleton → guided TreeBuilder → NodeTextFiller → story_report）。  
- 结构与时长验收工具链已具备：
  - `TimeValidator`：深度/时长/结局阈值校验；
  - `story_report.build_story_report`：单角色情况下的综合报告；
  - `tools/report_story_structure.py`：CLI 验收脚本。
- 目前真实样本情况：
  - 杭州《断桥残血-MVP测试》：结构过浅、无结局，仅适合作为 MVP 流水线 smoke，不适合作为“合格样本”。  
  - 上海《午夜频率·虹口电台》（story_id=2）：  
    - 主角「深夜电台主播」的对话树：总节点 ≈ 67，主线深度 ≈ 8，时长 ≈ 10 分钟，结局 ≈ 14 个；  
    - 结构验收脚本 verdict：`depth_ok=False` / `duration_ok=False` / `endings_ok=True`；  
    - 说明：目前骨架/TreeBuilder/TimeValidator 的组合对该故事仍偏“短浅”，不能算通过。

本任务的目标是：**以上海《午夜频率·虹口电台》为固定示例，打通一条从 v4 骨架流水线 → 结构验收全绿的黄金样本链路**，作为后续调优与回归的基准。

---

## 1. 目标 / 非目标

### 1.1 目标

- [ ] 选定并固定一个“上海示例故事”：  
  - 城市：上海；  
  - 故事：`午夜频率·虹口电台`（现有 story_id=2，可重新生成一版 v4 流水线产物作为新版 example）。  
- [ ] 在 `USE_PLOT_SKELETON=1`、默认配置下，通过 v4 骨架流水线重新生成该故事，使其满足：
  - 结构验收脚本 `tools/report_story_structure.py` 对主角树的 verdict：  
    - `depth_ok=True` / `duration_ok=True` / `endings_ok=True` / `passes=True`；  
  - 不依赖 v3 legacy heuristics 的 env 降级（MIN_DURATION_MINUTES / EXTEND_ON_FAIL_ATTEMPTS / FORCE_CRITICAL_INTERVAL 等）。  
- [ ] 把“上海示例故事结构验收”的流程固化为脚本/example：
  - 提供一份最小命令序列（或 `tools/` 下的辅助脚本），可以一键从 0 生成 + 验收上海示例故事；
  - 为后续改动 v4 骨架流水线提供一个固定的回归样本。

### 1.2 非目标

- 不在本任务中保证“所有城市/故事”都能一次性通过同样的结构验收；这里只锁定一个上海示例故事。  
- 不在本任务中彻底重写 PlotSkeleton 提示词或故事文案 prompt；如需大改 prompt，需另起 ADR/Task。  
- 不引入新的 v3 风格 heuristics（例如更多环境变量魔法），只允许在骨架配置 / guided TreeBuilder / TimeValidator 的参数空间内调优。

---

## 2. 里程碑与任务拆分

### M1: 上海示例故事基线测量

**目的**：明确当前上海示例故事在 v4 流水线下的真实结构表现，并固定测量与数据路径。

- [ ] M1-1 明确并记录当前示例 story 的身份：
  - 城市：上海（cities.name="上海"）；  
  - 故事：标题 `午夜频率·虹口电台`；  
  - StoryGenerator 配置：`USE_PLOT_SKELETON=1` / `MAX_RETRIES=0` / `AUTO_RESTART_ON_FAIL=0`。  
- [ ] M1-2 编写（或文档化）导出对话树的最小脚本：
  - 从 SQLite 中导出主角「深夜电台主播」的对话树为 `checkpoints/story_<id>_上海_深夜电台主播_tree.json`；  
  - 保证脚本幂等、可重复。  
- [ ] M1-3 使用 `tools/report_story_structure.py` 对该树跑一次验收，记录当前指标（节点数/主线深度/时长/结局数以及 verdict）。

### M2: 骨架配置与 TimeValidator 对齐

**目的**：在不引入新 heuristics 的前提下，让骨架配置与 TreeBuilder/TimeValidator 的阈值更吻合，使上海示例故事有机会自然达标。

- [ ] M2-1 设计上海示例故事的目标结构范围（记录在 Task 或 ADR 补充说明中）：
  - 主线深度目标区间（例如 18–24）；  
  - 预计时长目标区间（例如 20–35 分钟）；  
  - 目标结局数量范围（例如 3–6 个）。  
- [ ] M2-2 调整 PlotSkeleton 生成策略 / SkeletonConfig：
  - 优先通过骨架配置中的 `min_main_depth` / `target_main_depth` / `target_endings` 对结构施加约束；  
  - 避免在 TreeBuilder 后期再“硬凹”深度。  
- [ ] M2-3 调整 TimeValidator 默认阈值或其与骨架的对齐方式：
  - 如果骨架给出的 `min_main_depth` 比当前环境阈值更高，应优先使用骨架值；  
  - `MIN_DURATION_MINUTES` 的默认值可适度放宽，但必须在 Task 中记录理由。  
- [ ] M2-4 在 guided TreeBuilder 中，必要时微调：  
  - 每层分支数上限（`max_branches_per_node` + beat-level `branches.max_children`）；  
  - 结局落点深度控制（通过 `leads_to_ending` 与 `_allow_ending_for_depth` 的组合）。

### M3: 上海示例故事重新生成与验收

**目的**：用调优后的 v4 流水线，从 0 重新生成上海示例故事，并验证结构达标。

- [ ] M3-1 在清晰的环境配置下（记录所有相关 env）重新跑一次上海示例故事的完整 v4 流水线生成：  
  - 确保 StoryGenerator 主路径走骨架模式（可以通过日志确认 `Step 1.8` 与 `Step 3.5`）。  
- [ ] M3-2 导出主角「深夜电台主播」的最新对话树 JSON，并使用 `tools/report_story_structure.py` 进行结构 + 时长 + 结局验收：  
  - 要求 `depth_ok=True` / `duration_ok=True` / `endings_ok=True` / `passes=True`。  
- [ ] M3-3 视情况补充一次人工结构评审（简单走一遍分支），确认没有明显“乱树”感。

### M4: 固化上海示例验收流程（脚本 / 文档 / 测试）

**目的**：让“上海示例故事结构验收”变成一个可靠的回归用例。

- [ ] M4-1 在 `tools/` 下增加一个轻量脚本或文档化命令序列，例如：  
  - `tools/accept_shanghai_example.py` 或一段可复制的 bash 步骤；  
  - 脚本内容只做：设置 env → 调用 StoryGenerator → 导出树 → 调用 `report_story_structure.py`。  
- [ ] M4-2 在 `tests/` 中增加一个最小集成测试（可选）：  
  - 不要求真的生成完整上海故事（避免测试过慢），但可以通过 fixtures/模拟数据验证“结构验收脚本能正确读取 example JSON 并给出 passes=True 的 verdict”。  
- [ ] M4-3 更新相关文档：  
  - 在 `NEW_PIPELINE.md` 或 `STORY_PIPELINE_V4.md` 中加入“上海示例故事结构验收”一节；  
  - 在 `TASK_STORY_STRUCTURE.md` / `TASK_V4_DEFAULT_PIPELINE.md` 的 Done 定义中引用该示例故事作为“已通过验收的真实样本”。

---

## 3. 依赖与协作

- 依赖 ADR：  
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`（骨架流水线整体设计）  
- 依赖 Task：  
  - `docs/tasks/TASK_STORY_STRUCTURE.md`（骨架模型与 guided TreeBuilder 基础能力）  
  - `docs/tasks/TASK_V4_DEFAULT_PIPELINE.md`（v4 作为默认生成路径的 wiring 与回退策略）
- 依赖代码与工具：  
  - `src/ghost_story_factory/pregenerator/story_generator.py`  
  - `src/ghost_story_factory/pregenerator/tree_builder.py`  
  - `src/ghost_story_factory/pregenerator/skeleton_model.py`  
  - `src/ghost_story_factory/pregenerator/skeleton_generator.py`  
  - `src/ghost_story_factory/pregenerator/time_validator.py`  
  - `src/ghost_story_factory/pregenerator/story_report.py`  
  - `tools/report_story_structure.py`

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- 以 v4 骨架流水线（`USE_PLOT_SKELETON=1`，不依赖 v3 legacy 降级）从 0 生成的上海《午夜频率·虹口电台》故事：  
  - 主角对话树在 `tools/report_story_structure.py` 下的结构验收 verdict 为：  
    - `depth_ok=True` / `duration_ok=True` / `endings_ok=True` / `passes=True`；  
  - 至少通过一次人工结构评审（分支层级清晰，无明显“随机乱树”感）。  
- 上海示例故事的生成与验收流程已经被固化为脚本或文档步骤，后续可重复执行用于回归。  
- 相关 Task/Spec/Architecture 文档已更新，将“上海示例故事”标注为 v4 骨架流水线的第一个正式结构样本。

