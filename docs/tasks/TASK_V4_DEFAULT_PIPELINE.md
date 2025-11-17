# TASK: 将 v4 骨架流水线升级为默认生成模式

版本: v0.1  
状态: 草案（可迭代）  
关联 ADR: `docs/architecture/ADR-001-plot-skeleton-pipeline.md`  
前置任务: `docs/tasks/TASK_STORY_STRUCTURE.md`

---

## 0. 背景

当前状态：
- v3 流水线已经稳定运行（完整文档 → TreeBuilder → TimeValidator → DB）；
- v4 骨架模式（PlotSkeleton + guided TreeBuilder + NodeTextFiller + story_report）已经完成第一版实现和测试，但仍然以“增量特性”形式接入：
  - `StoryGeneratorWithRetry` 优先尝试 SkeletonGenerator，失败则回退到 v3 行为；
  - v3 的 heuristics（扩展轮 + 部分 env 降级策略）仍然存在。

目标阶段：
- 将 v4 骨架流水线升级为默认路径，使“文档 → 骨架 → guided TreeBuilder → 文本填充 → 验收报告”成为主干；
- 同时保留 v3 行为作为兼容/回退路径（但不再主推）。

---

## 1. 目标 / 非目标

### 1.1 目标

- [x] StoryGeneratorWithRetry 的主路径显式以 v4 为核心（骨架生成 + guided TreeBuilder + 文本填充 + story_report）；
- [x] v3 TreeBuilder heuristics 降级为兼容路径（仅在骨架不可用或显式关闭 v4 时启用）；
- [x] 提供明确的开关/配置，让运行者可以：
  - 强制启用 v4 骨架模式；
  - 临时回退到 v3 模式（用于排查或对比）。
- [x] 更新相关文档（SPEC / NEW_PIPELINE / STORY_PIPELINE_V4）以反映“v4 为默认”。

### 1.2 非目标

- 不彻底删除 v3 TreeBuilder 的 heuristics 逻辑（短期仍保留为 fallback）；
- 不改变 DB schema 与对话树 JSON 结构；
- 不在本任务中做大规模 Prompt 重写或文案风格升级。

---

## 2. 里程碑与任务拆分

### M1: StoryGenerator v4 主路径切换

**目的**：在 `StoryGeneratorWithRetry` 中清晰区分 v4 主路径与 v3 回退路径。

- [x] M1-1 明确 v4 主路径流程（代码层）：
  - 文档生成（已存在）；
  - SkeletonGenerator（PlotSkeleton）；
  - guided TreeBuilder（带 plot_skeleton）；
  - NodeTextFiller（按骨架填充元数据与占位叙事）；
  - story_report（生成结构+时长报告，可用于日志）。
- [x] M1-2 在 `StoryGeneratorWithRetry.generate_full_story` 中：
  - 将骨架生成/使用路径重构为清晰的“v4 主路径”分支；
  - v3 模式明确放到“骨架不可用 / 显式禁用 v4”分支。
- [x] M1-3 增加环境变量/配置：
  - `USE_PLOT_SKELETON`（默认 1）；
  - 当 `USE_PLOT_SKELETON=0` 时，跳过 SkeletonGenerator / guided TreeBuilder / NodeTextFiller，完全走 v3 行为。

### M2: Heuristics 与回退策略梳理

**目的**：让 v4 下的行为更可预测、v3 行为退居“兼容层”，避免混乱。

- [x] M2-1 明确 TreeBuilder 内部 heuristics 的分层：
  - 安全闸（MAX_TOTAL_NODES / PROGRESS_PLATEAU_LIMIT / Beam）：始终保留；
  - 扩展轮（EXTEND_ON_FAIL_ATTEMPTS）：
    - guided 模式下限制为最多一轮；
    - v3 模式下可按现有逻辑工作；
  - env 降级策略（MIN_DURATION_MINUTES / EXTEND_ON_FAIL_ATTEMPTS / FORCE_CRITICAL_INTERVAL）：
    - guided 模式下禁用；
    - v3 模式下保留。
- [x] M2-2 在代码中加注释和日志，标明：
  - 哪些 heuristics 是“v3 legacy”；
  - 哪些逻辑是“v4 正式策略”；
  - 回退到 v3 模式的条件和日志提示。

### M3: 文档与可视化同步 v4 默认化

**目的**：确保文档与实现一致，便于维护和对外解释。

- [x] M3-1 更新规格与架构文档：
  - `docs/specs/SPEC_V3.md` 中新增一节说明 v4 骨架模式已为默认生成路径；
  - `docs/architecture/NEW_PIPELINE.md` 与 `STORY_PIPELINE_V4.md` 中：
    - 明确“v4 为主线，v3 为兼容路径”的关系；
    - 更新流程图与模块映射。
- [x] M3-2 在 `docs/tasks/TASK_STORY_STRUCTURE.md` 中增加一小节，标注：
  - v4 已升级为默认流水线；
  - 后续对结构相关的改动应优先考虑骨架 + guided 模式。
- [x] M3-3（可选）提供一张简单的差异图：
  - v3：文档 → TreeBuilder(v3) → TimeValidator → DB；
  - v4：文档 → PlotSkeleton → TreeBuilder(v4 guided) → NodeTextFiller → story_report → DB；
  - 并标明回退诊断路径（发生结构异常时，可通过 `USE_PLOT_SKELETON=0` 暂时切回 v3，对比结构差异，并结合 `tools/view_tree_progress.py` / `tools/report_story_structure.py` 做诊断）。

### M4: 自动化回归保障 v4 默认化

**目的**：确保切换默认路径后不会引入隐性回归。

- [x] M4-1 增加/更新集成测试：
  - 新增 `tests/test_story_generator_modes.py`：
    - 在 `USE_PLOT_SKELETON=0` 下，验证不会调用 `SkeletonGenerator` / `NodeTextFiller` / `story_report`，TreeBuilder 以 `plot_skeleton=None` 运行（v3 兼容路径）；  
    - 在 `USE_PLOT_SKELETON=1` 下，验证会调用 `SkeletonGenerator`，TreeBuilder 收到非空骨架（guided 模式），并触发 `NodeTextFiller + story_report`，同时确保填充后的对话树被写入 DB。  
  - 该测试通过 monkeypatch/fake 依赖（避免真实 LLM 调用），在 venv 下快速验证 v4 默认路径与 v3 回退路径的基本行为。
- [x] M4-2 在 `tools/run_all_tests.py` 中加入一项 v4 集成测试（如果运行时间可接受）：
  - 已将 `tests/test_story_generator_modes.py` 纳入统一测试脚本的 pytest 套件；
  - 脚本会在 CI/本地统一运行：Skeleton 模型 / SkeletonGenerator / guided TreeBuilder / StoryGenerator 模式 / 文本填充 / 报告单元与集成测试；
  - 确保每次改动 StoryGenerator / TreeBuilder 时，v4 默认/回退两条路径一起被回归。
- [x] M4-3 更新 `AGENTS.md`：
  - 明确“默认流水线为 v4 骨架模式”的条目；
  - 要求未来改动优先遵循骨架设计。

---

## 3. 依赖与协作

- 依赖文档：
  - `docs/specs/SPEC_V3.md`
  - `docs/architecture/ARCHITECTURE.md`
  - `docs/architecture/NEW_PIPELINE.md`
  - `docs/architecture/STORY_PIPELINE_V4.md`
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`
  - `docs/tasks/TASK_STORY_STRUCTURE.md`

- 依赖代码：
  - `src/ghost_story_factory/pregenerator/story_generator.py`
  - `src/ghost_story_factory/pregenerator/tree_builder.py`
  - `src/ghost_story_factory/pregenerator/skeleton_model.py`
  - `src/ghost_story_factory/pregenerator/skeleton_generator.py`
  - `src/ghost_story_factory/pregenerator/text_filler.py`
  - `src/ghost_story_factory/pregenerator/story_report.py`

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- 默认配置下（USE_PLOT_SKELETON=1）：
  - StoryGenerator 主流程走的是 v4 骨架模式；
  - 至少有一个真实城市/故事在该模式下完整生成成功，并通过结构+时长+结局验收；
  - 自动化测试（包括 v4 集成测试）全部通过。
- 回退配置下（USE_PLOT_SKELETON=0）：
  - 仍可走 v3 TreeBuilder 路径生成故事，用于对比和诊断；
  - 文档中清晰标明 v3 的角色是“兼容/回退”，而非推荐路径。
- 相关 Task/Spec/Architecture 文档已经同步更新，AGENT 流程要求已反映“v4 默认化”这一事实。  
