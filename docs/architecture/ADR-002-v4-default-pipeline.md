# ADR-002: 将 v4 骨架流水线升级为默认故事生成路径

- 状态: Accepted  
- 日期: 2025-11-16  
- 作者: yehan / Codex  
- 关联文档:
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`
  - `docs/architecture/NEW_PIPELINE.md`
  - `docs/architecture/STORY_PIPELINE_V4.md`
  - `docs/specs/SPEC_V3.md`
  - `docs/tasks/TASK_V4_DEFAULT_PIPELINE.md`

---

## 1. 背景

在 ADR-001 中，我们已经确定：

- 引入 PlotSkeleton / SkeletonGenerator，将“幕/节拍/分支”结构从 TreeBuilder 中剥离出来；
- 在 v4 中，通过 guided TreeBuilder 按骨架控制主线深度 / 结局数量 / 节奏；
- 使用 NodeTextFiller / story_report / TimeValidator 作为结构与时长的验收层。

但在 ADR-001 时，v4 仍以“旁路特性”的形式接入：

- StoryGeneratorWithRetry 默认仍是 v3 行为，v4 只是尝试性路径；
- v3 的 heuristics（`EXTEND_ON_FAIL_ATTEMPTS`、环境降级、`depth_booster` 等）仍作为主导拉深手段；
- 文档中 v3/v4 的关系没有明确到“v4 为默认、v3 为兼容路径”的程度。

随着：

- `TASK_STORY_STRUCTURE.md` 落地了骨架模型 + guided TreeBuilder 的基础能力；
- `TASK_V4_DEFAULT_PIPELINE.md` 完成了 StoryGeneratorWithRetry 主路径切换与 heuristics 梳理；
- 自动化测试中加入了 v4 模式与回退模式的集成验证；

我们需要一个新的 ADR 来正式确认：**v4 骨架流水线取代 v3 成为默认故事生成路径，v3 仅作为兼容/回退路径存在。**

---

## 2. 决策

本 ADR 做出以下决策：

1. **StoryGeneratorWithRetry 的默认主路径为 v4 骨架流水线**
   - 在 `USE_PLOT_SKELETON!=0` 且骨架生成成功的前提下，主路径为：
     - 文档生成（Lore v1/v2、Protagonist、GDD、main story）；
     - PlotSkeleton（SkeletonGenerator）；
     - guided TreeBuilder（`plot_skeleton` 非空）；
     - NodeTextFiller（骨架驱动的元数据与占位叙事）；
     - story_report + TimeValidator（结构/时长/结局验收）；
     - DB 写入完整故事（城市 / 故事 / 角色 / 对话树 / 元数据）。

2. **v3 TreeBuilder 行为降级为兼容/回退路径**
   - 在以下情况才进入 v3 行为：
     - 显式关闭骨架模式：`USE_PLOT_SKELETON=0`；
     - SkeletonGenerator 硬失败（无法生成合理的 PlotSkeleton）；  
     - 调试/诊断需要对比 v3/v4 时。
   - 在 v3 路径下：
     - 保留原有 heuristics（`EXTEND_ON_FAIL_ATTEMPTS` / env 降级 / `depth_booster` 等）；
     - 但所有这类逻辑都必须在代码中明确标记为 `v3 legacy`；
     - 文档必须说明：v3 行为仅用于兼容/回退，不再是推荐路径。

3. **在 guided 模式下禁止“死磕式” heuristics**
   - 当 `plot_skeleton` 存在、`guided_mode=True` 时：
     - `EXTEND_ON_FAIL_ATTEMPTS` 被收紧为最多一轮轻量扩展；
     - 禁止在运行时通过修改 env（`MIN_DURATION_MINUTES` / `EXTEND_ON_FAIL_ATTEMPTS` / `FORCE_CRITICAL_INTERVAL` 等）来放宽阈值；
     - `TimeValidator` 用于 sanity check，而不是驱动“再生成一轮看看能不能长一点”的扩展。
   - 结构问题应优先在骨架层解决：
     - 通过调整 PlotSkeleton 的 `SkeletonConfig`（min/target depth、target_endings 等）；
     - 通过调整 guided TreeBuilder 的 depth→beat 映射与分支策略。

4. **自动化测试必须覆盖 v4 默认路径与 v3 回退路径**
   - `tests/test_story_generator_modes.py` 负责验证：
     - `USE_PLOT_SKELETON=0` 下不会调用 SkeletonGenerator / NodeTextFiller / story_report，TreeBuilder 以 `plot_skeleton=None` 运行；
     - `USE_PLOT_SKELETON=1` 下会调用 SkeletonGenerator，TreeBuilder 收到非空骨架，并触发 NodeTextFiller + story_report。
   - `tools/run_all_tests.py` 必须在统一测试脚本中包含该 pytest 套件，确保每次改动 StoryGenerator / TreeBuilder 时，v4/v3 两条路径一起回归。

---

## 3. 方案细节

### 3.1 StoryGeneratorWithRetry 路径拆分

- v4 主路径（默认）：
  - `USE_PLOT_SKELETON != 0`；
  - SkeletonGenerator 成功返回 `PlotSkeleton`；
  - TreeBuilder 构造时传入 `plot_skeleton`，`guided_mode=True`；
  - 节点生成后调用 NodeTextFiller / story_report 进行结构补充与验收。

- v3 回退路径：
  - `USE_PLOT_SKELETON = 0`，或骨架生成失败；
  - TreeBuilder 构造时传入 `plot_skeleton=None`，`guided_mode=False`；
  - 保留 v3 heuristics，允许通过 env 降级尝试拉深主线/时长；
  - 不调用 NodeTextFiller / story_report。

### 3.2 TreeBuilder 中 v4 / v3 行为区分

- 共用部分（v3/v4 都要遵守）：
  - BFS 扩展；
  - `MAX_TOTAL_NODES / PROGRESS_PLATEAU_LIMIT / Beam` 等安全闸；
  - ProgressTracker 进度记录 / 检查点保存。

- guided 模式（v4）：
  - 分支控制：
    - `max_branches_per_node` 从骨架的 `SkeletonConfig.max_branches_per_node` 派生；
    - 每一层 depth 的分支上限进一步受对应 beat 的 `branches.max_children` 限制；
  - 结局落点控制：
    - `_allow_ending_for_depth(depth)` 基于对应 beat 的 `leads_to_ending`；
    - 即使 `_check_ending` 判为结局，若当前 depth 不允许结局，则强制继续扩展；
  - 扩展策略：
    - 同轮扩展最多一轮（`EXTEND_ON_FAIL_ATTEMPTS` 在 guided 模式下被收紧）；
    - 不参与 v3 的 env 降级游戏。

- legacy 模式（v3）：
  - 保留 env 驱动的 heuristics：
    - 时长不足时允许降低 `MIN_DURATION_MINUTES`；
    - 主线深度不足时允许增加 `EXTEND_ON_FAIL_ATTEMPTS`；
    - 结局不足时允许加速 critical 注入（`FORCE_CRITICAL_INTERVAL`）。
  - 所有这类逻辑必须带有 `[v3 legacy]` 日志提示，且在注释中标明仅对 `guided_mode=False` 有效。

### 3.3 TimeValidator 与 PlotSkeleton 的对齐

- 在有骨架的情况下：
  - `build_story_report(tree, skeleton)` 调用 `TimeValidator(min_main_path_depth=skeleton.config.min_main_depth)`；
  - TimeValidator 的主线深度阈值优先使用 `SkeletonConfig.min_main_depth`，仅在没有骨架时使用 env 默认值。
- 时长与结局数量的阈值：
  - 默认 `MIN_DURATION_MINUTES=12`、`MIN_ENDINGS=1`；
  - 具体项目（如上海示例故事）在 Task 中可进一步给出更严格/合理的目标区间；
  - 但不再依赖“生成失败后再随手调阈值”的模式作为主方案。

---

## 4. 备选方案与取舍

### 4.1 保持 v3 为默认，v4 继续旁路（拒绝）

- 优点：
  - 风险小，旧行为不变；
  - 不需要大规模清理 heuristics 与 env 降级逻辑。
- 缺点：
  - 实际开发仍然围绕 v3 heuristics 调参，骨架层设计形同虚设；
  - 很难累积“骨架→TreeBuilder→TimeValidator”这一条链路上的经验与问题；
  - v4 沦为“研究项目”，违背我们重构的初衷。

### 4.2 立即删除 v3 TreeBuilder 及 heuristics（拒绝）

- 优点：
  - 代码更干净，避免 v3/v4 双路径的复杂性；
  - 所有人都被迫面对骨架层问题。
- 缺点：
  - 风险极大，一旦骨架生成/解析出问题，没有 fallback 可用；
  - 对现有故事与运行路径的兼容性风险不可控；
  - 不符合“Never break userspace”的原则。

### 4.3 v4 为默认，v3 为明确标注的回退路径（采纳）

- 优点：
  - 在不破坏现有运行路径的前提下，将开发重心切到 v4 骨架流水线；
  - v3 heuristics 完整保留，用于诊断/紧急回退，但不会再被“误用”为主要方案；
  - 便于在 Task/Issue 中围绕 v4 做迭代和验收。
- 缺点：
  - 短期仍要维护两套路径，文档和测试需要清晰地区分；
  - 开发者需要熟悉新旧模式的切换条件。

---

## 5. 影响与迁移

- StoryGeneratorWithRetry：
  - 代码已根据 `TASK_V4_DEFAULT_PIPELINE.md` 完成路径拆分和环境变量控制；
  - 新增/更新测试 `tests/test_story_generator_modes.py` 覆盖 v3/v4 模式。
- TreeBuilder：
  - guided 模式与 legacy 模式的 heuristics 行为在代码中显式区分；
  - 安全闸（MAX_TOTAL_NODES / PROGRESS_PLATEAU_LIMIT / Beam）保持共用。
- TimeValidator / story_report：
  - 在有骨架时使用骨架配置的最小深度阈值；
  - 文档中明确它们的角色是“验收工具”，而不是“扩展驱动器”。
- 文档：
  - `NEW_PIPELINE.md` / `STORY_PIPELINE_V4.md` 已更新为 v4 默认路径；
  - 本 ADR 补充了 v3/v4 的决策性描述，作为 ADR-001 的后续。

---

## 6. 回滚策略

- 若在实践中发现 v4 骨架流水线在多个真实故事上表现不佳，且修复成本过高：
  - 可将 `USE_PLOT_SKELETON` 默认值改为 0，将 StoryGeneratorWithRetry 主路径切回 v3；
  - 仍保留 v4 相关代码，以便后续诊断与小范围试验；
  - 同时在 Task/Issue 中记录回滚原因，并重新评估骨架方案的设计。

