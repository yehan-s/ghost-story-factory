# AGENTS.md - Ghost Story Factory 项目初始化说明（Codex 专用）

## 1. 项目背景

Ghost Story Factory 是一个**交互式灵异故事工厂**，包含两大能力：

1. **Pregenerator（故事预生成器）**
   - 输入：城市 + 故事简介（title / protagonist / location / 预期时长）
   - 输出：世界观文档（Lore）、GDD、主线故事，以及多角色的完整对话树（存入 SQLite）
   - 目标：离线一次性生成高质量、多分支、可玩的对话树

2. **Runtime Engine（运行时引擎）**
   - 动态模式：`play_game_full.py`（游玩时实时调用 LLM）
   - 预生成模式：`play_game_pregenerated.py` / `start_pregenerated_game.sh`（零等待，直接读数据库里的对话树）
   - 目标：提供状态管理、分支选择和 CLI UI 的完整游戏体验

当前主线架构版本为 **v3**，并在此基础上设计了 **v4「骨架优先」故事生成流水线**。  
从现在开始：**v4 骨架流水线是默认故事生成路径，v3 仅作为兼容回退路径存在。**

---

## 2. 架构总览（v3 -> v4）

### 2.1 v3 关键模块

- 预生成（pregenerator）
  - `src/ghost_story_factory/pregenerator/synopsis_generator.py`
  - `src/ghost_story_factory/pregenerator/story_generator.py`
    - 调用模板生成：
      - Lore v1 / Lore v2
      - Protagonist
      - GDD
      - main story
    - 再调用 `DialogueTreeBuilder` 生成多角色对话树
  - `src/ghost_story_factory/pregenerator/tree_builder.py`
    - BFS 扩展对话树
    - 依赖：
      - `StateManager`：状态哈希 / 去重 / 剪枝
      - `ProgressTracker`：进度条 & 检查点
      - `TimeValidator`：主线深度 / 时长 / 结局数量校验
      - `ChoicePointsGenerator`（engine）+ `RuntimeResponseGenerator`（engine）

- 运行时（runtime + engine）
  - `src/ghost_story_factory/runtime/dialogue_loader.py`：从 DB 加载树
  - `src/ghost_story_factory/engine/state.py` / `choices.py` / `game_loop.py`
  - `src/ghost_story_factory/ui/cli.py`：Rich CLI UI

- 数据库
  - `database/ghost_stories.db`
  - `src/ghost_story_factory/database/db_manager.py`
  - `sql/schema.sql`

详细参考：
- `docs/specs/SPEC_V3.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/NEW_PIPELINE.md`
- `docs/architecture/GAME_ENGINE.md`

### 2.2 v4「骨架优先」流水线（设计 + 当前进展）

目标：把**故事结构**从 LLM 随机游走里解放出来，变成一个独立、可控的数据结构。

核心设计文档：
- 架构决策：`docs/architecture/ADR-001-plot-skeleton-pipeline.md`
- 流程草案：`docs/architecture/STORY_PIPELINE_V4.md`
- 任务拆解：`docs/tasks/TASK_STORY_STRUCTURE.md`

已落地代码（v4 为默认主路径）：

1. **骨架模型**
   - `src/ghost_story_factory/pregenerator/skeleton_model.py`
   - 核心类：
     - `PlotSkeleton`：故事骨架（acts + beats + config + metadata）
     - `SkeletonConfig`：`min_main_depth` / `target_main_depth` / `target_endings` 等约束
     - `ActConfig` / `BeatConfig` / `BranchSpec`
   - 提供：
     - `PlotSkeleton.from_dict()` / `to_dict()`
     - 统计属性：`num_acts` / `num_beats` / `num_critical_beats` / `num_ending_beats`

2. **骨架生成器**
   - `src/ghost_story_factory/pregenerator/skeleton_generator.py`
   - `SkeletonGenerator.generate(...) -> PlotSkeleton`
     - 使用模板：`templates/plot-skeleton.prompt.md`
     - 上下文：城市 + synopsis + Lore v2 + main story 摘要
     - LLM 输出一个 JSON，解析成 `PlotSkeleton`

3. **guided TreeBuilder**
   - `DialogueTreeBuilder` 新增：
     - 参数：`plot_skeleton: Optional[PlotSkeleton]`
     - 属性：`self.guided_mode = plot_skeleton is not None`
   - guided 行为：
     - 使用骨架的 `config.max_branches_per_node` 和各 beat 的 `branches.max_children` 限制分支数量；
     - 使用 `leads_to_ending` 控制结局出现深度：
       - 即使 `_check_ending` 判为结局，如果该深度对应的 beat 不允许结局，会强制继续扩展；
     - 保留安全闸（`MAX_TOTAL_NODES` / plateau / Beam），但在 guided 模式下：
       - 同轮扩展最多 1 次（`EXTEND_ON_FAIL_ATTEMPTS` 被裁剪为 1）；
       - 不再通过改 env（`MIN_DURATION_MINUTES` / `EXTEND_ON_FAIL_ATTEMPTS` / `FORCE_CRITICAL_INTERVAL`）来“死磕”。

4. **结构检查工具**
   - `tools/check_structure_metrics.py`
     - 输入：骨架 JSON
     - 输出：幕数 / 节拍数 / 关键节拍数 / 结局节拍数 / 粗略主线深度估算等

---

## 3. v4 骨架流水线（黄金流程视角，默认路径）

以下 v4 流程视为**黄金流水线**，也是 StoryGenerator 的**默认主路径**，在实现/重构故事生成时不得违背或跳过：

1. **文档阶段（v3/v4 共用）**
   - 使用完整生成器生成：
     - Lore v1 / Lore v2
     - Protagonist
     - GDD
     - main story
   - 可选：对 Lore v2 / GDD / 主线做预分析（质量告警，不阻断）。

2. **Stage B：PlotSkeleton（骨架生成）**
   - 使用 `SkeletonGenerator` + `plot-skeleton.prompt.md` 生成 `PlotSkeleton`：
     - 默认：`USE_PLOT_SKELETON=1` → 必须先尝试骨架生成，进入 v4 骨架模式；
     - 仅在调试 / 兼容场景下，才允许显式配置 `USE_PLOT_SKELETON=0` 关闭 v4，强制走 v3 legacy 模式。
   - 骨架生成失败 → 明确日志 + 回退 v3 TreeBuilder；不能无声退回。

3. **Stage C：guided TreeBuilder（按骨架生成树）**
   - `DialogueTreeBuilder(plot_skeleton=...)`：
     - depth → beat 映射控制每层分支数（`branches.max_children` + `config.max_branches_per_node`）；
     - `leads_to_ending` 控制在哪些深度允许结局；
   - 安全闸：
     - 始终保留 `MAX_TOTAL_NODES / PROGRESS_PLATEAU_LIMIT / Beam`；
   - heuristics 限制：
     - guided 模式下，同轮扩展最多 1 次（`EXTEND_ON_FAIL_ATTEMPTS` 收紧为 1）；
     - guided 模式下禁止通过修改 env（`MIN_DURATION_MINUTES` / `EXTEND_ON_FAIL_ATTEMPTS` / `FORCE_CRITICAL_INTERVAL`）来“死磕”；
     - v3 heuristics 仅在回退路径中生效。

4. **Stage D：节点文本填充 + 验收报告**
   - `NodeTextFiller(skeleton).fill(tree)`：
     - 为节点追加 beat 元数据（`beat_type / tension_level / act_index`）；
     - 对 narrative 为空或全空白的节点填充占位叙事，不覆盖已有文案。
   - `build_story_report(tree, skeleton)` + `tools/report_story_structure.py`：
     - 用 `TimeValidator` + 骨架指标生成结构+时长+结局综合报告；
     - 作为人工检查与回归工具。

> 总结：任何改动故事生成结构的操作，Codex 都必须按「文档 → 骨架 → guided TreeBuilder → 文本填充 → 报告」这条链路思考与实现。

---

## 4. Codex 开发流程约定

### 4.1 修改前阅读

作为 Codex，在动核心逻辑前，至少要读：

- 全局：
  - `README.md`
  - `docs/INDEX.md`
- 架构 & 规格：
  - `docs/specs/SPEC_V3.md`
  - `docs/architecture/ARCHITECTURE.md`
  - `docs/architecture/NEW_PIPELINE.md`
- v4 骨架相关：
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`
  - `docs/architecture/STORY_PIPELINE_V4.md`
  - `docs/tasks/TASK_STORY_STRUCTURE.md`

### 4.2 代码修改的优先级和边界

- 优先改动范围：
  - 预生成流水线：`src/ghost_story_factory/pregenerator/*`
  - 骨架模型与 guided TreeBuilder
- 慎重改动：
  - Runtime engine 接口（`engine/*` + `runtime/dialogue_loader.py`）——要保持 DB schema & 对话树结构兼容；
- Legacy：
  - v1 CLI / 文档已清理（旧 `SPEC.md` 等），不要再依赖；
  - `depth_booster.py` / `depth_orchestrator.py` 视为历史参考，不作为 v4 主策略。

### 4.3 Good Taste 原则（本项目的应用）

- 结构优先：
  - 改故事“深度/节奏”时，先看骨架（PlotSkeleton），再考虑 heuristics。
- 减少魔法行为：
  - 不在运行后期悄悄改 env 然后让用户“重跑一轮试试”；
  - 把策略写在 ADR 和 config，而不是散落在一堆 `os.environ[...] = ...`。
- 可恢复 / 可调试：
  - 任何新逻辑要有清晰的日志和检查点（复用 `ProgressTracker`）。

---

### 4.4 Task / Issue / 里程碑（黄金流程）

每一个新的模块或 feature，必须满足：

1. **Task 文档**  
   - 在 `docs/tasks/` 下创建或更新对应的 `TASK_*.md`：  
     - 目标 / 非目标  
     - 里程碑拆分（M1/M2/M3/…）  
     - 代码入口和测试计划  
   - Codex 在动手改代码前，必须先对齐 Task 文档。

2. **GitHub Issue / 里程碑**  
   - 为每个 Task 创建对应的 GitHub issue（标题建议带 `[v4]` / `[feature]` 等前缀）；  
   - Issue 描述中引用 `TASK_*.md`（作为技术说明的单一真相源）；  
   - 可选：将多个相关 Task/issue 归入同一个 milestone（例如 “v4 默认流水线”）。

3. **实现 → 测试 → 文档 → Issue 更新**  
   - 实现完成后：
     - 必须新增或更新对应自动化测试（单元 + 集成）；  
     - 必须在项目 venv 中执行 `venv/bin/python tools/run_all_tests.py`，确保全绿；  
     - 必须回写 Task 文档（勾选完成的 M，调整剩余工作）；  
     - 必须在 Issue 中更新 checklist / 进度（避免“文档好看但 Issue 没动”的分裂）。  
     - 必须执行 git 提交：每个 feat 至少一个 commit，推荐将“文档 / 实现 / 测试”拆成独立提交（具体拆分原则见下文）。  
     - 如果本地环境已配置 GitHub CLI（`gh`），Codex 必须实际调用 `gh issue edit` / `gh issue comment` 来同步 Issue 状态，而不是只在回答里“建议”人工更新。  
   - 这几步是**黄金流程的一部分，不允许跳过或颠倒顺序**。

---

## 5. 必须的自动化流程

**原则：以后每加一个 feat，都必须跑自动化测试。**

### 4.1 测试入口

项目提供统一测试脚本：

- 文件：`tools/run_all_tests.py`
- 推荐命令（使用项目自带 venv）：
  ```bash
  venv/bin/python tools/run_all_tests.py
  ```

### 4.2 统一测试脚本做了什么

1. 脚本型集成测试：
   - `test_database.py`：数据库系统测试
   - `test_full_flow.py`：完整流程测试（从 synopsis 到 DB）
   - `test_engine_integration.py`：GameEngine 集成测试

2. Pytest 单元测试（骨架 & guided TreeBuilder）：
   - `tests/test_skeleton_model.py`：
     - 验证 `PlotSkeleton` 及其子模型的基础行为和统计属性；
     - 验证 `to_dict` / `from_dict` 的往返不丢信息。
   - `tests/test_tree_builder_guided.py`：
     - 用 Dummy TreeBuilder 验证：
       - guided 模式下，根节点子节点数受骨架 `max_children` 限制；
       - 结局不会出现在过浅的 depth（例如 depth=1），而会在更深层出现。

统一测试脚本会逐个执行这些测试，并用 Rich 生成彩色报告。**所有测试必须通过**，Feat 才算落地完成。

### 4.3 快速单测命令（本地调试用）

- 只跑骨架模型 + guided TreeBuilder：
  ```bash
  venv/bin/python -m pytest tests/test_skeleton_model.py tests/test_tree_builder_guided.py -q
  ```

- 后续如果增加新的骨架相关测试，用相同模式挂到 `tools/run_all_tests.py` 的 Pytest 部分。

---

## 6. 重要文件速查

- 架构与规格：
  - `docs/specs/SPEC_V3.md`
  - `docs/specs/SPEC_TODO.md`
  - `docs/architecture/ARCHITECTURE.md`
  - `docs/architecture/NEW_PIPELINE.md`
  - `docs/architecture/STORY_PIPELINE_V4.md`
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`
  - `docs/tasks/TASK_STORY_STRUCTURE.md`
  - `docs/INDEX.md`

- 预生成核心：
  - `generate_full_story.py`
  - `src/ghost_story_factory/pregenerator/story_generator.py`
  - `src/ghost_story_factory/pregenerator/tree_builder.py`
  - `src/ghost_story_factory/pregenerator/state_manager.py`
  - `src/ghost_story_factory/pregenerator/progress_tracker.py`
  - `src/ghost_story_factory/pregenerator/time_validator.py`
  - `src/ghost_story_factory/pregenerator/skeleton_model.py`
  - `src/ghost_story_factory/pregenerator/skeleton_generator.py`

- Runtime：
  - `play_game_pregenerated.py`
  - `src/ghost_story_factory/runtime/dialogue_loader.py`
  - `src/ghost_story_factory/engine/*`
  - `src/ghost_story_factory/ui/cli.py`

- 测试与工具：
  - `tools/run_all_tests.py`
  - `tools/check_structure_metrics.py`
  - `tools/view_tree_progress.py`（生成过程中或中断后，用于诊断对话树深度/结局分布与“高重复选项”节点）
  - `tests/test_skeleton_model.py`
  - `tests/test_tree_builder_guided.py`
  - 其它 `test_*.py` 脚本（集成测试）

---

## 7. 对 Codex 的具体要求（总结）

1. **改结构先看骨架**  
   - 不要再堆新的 heuristics 来“凹深度”，优先改 `PlotSkeleton` 的设计与 guided 行为。

2. **任何 feat 必须配（或更新）测试**
   - 新增骨架字段 / guided 策略 → 对应在 `tests/` 增加或更新用例；
   - 修改 TreeBuilder / StoryGenerator → 至少跑 `tools/run_all_tests.py`。

3. **不要破坏现有运行路径**
   - 动态模式 / 预生成模式的 CLI 行为保持稳定；
   - DB schema 不要在无 ADR 的前提下变更；
   - 若必须临时关闭骨架，使用 `USE_PLOT_SKELETON=0` 切到 v3 legacy 模式，但**不能**以此为理由长期绕过 v4 设计。

4. **文档和代码都用中文注释 / 说明**
   - 注释、API 文档、技术文档统一用中文；
   - 新的架构决策或大改动，先写 ADR / TASK，再改代码。

5. **新增模块必须先有 Task 文档，完成 feat 必须回写 Task / Issue / 里程碑**
   - 每次新增一个模块（例如新的生成器 / 骨架阶段 / CLI 功能）前，必须先在 `docs/tasks/` 下写或更新对应的 `TASK_*.md`，明确：
     - 目标 / 非目标；
     - 里程碑拆分（M1/M2/...）；
     - 代码入口和测试计划。
   - 完成一个 feat 时，必须同步更新：
     - 相关 specs / 架构文档（如 `SPEC_V3.md` / `STORY_PIPELINE_V4.md`）；
     - 该模块对应的 `TASK_*.md`（标记已完成的 M、调整剩余工作）；
     - GitHub Issue / 里程碑（例如 `#1 [v4] 将骨架流水线升级为默认故事生成路径`），保持 checklist 与 Task 一致。
   - 这是**黄金流程**，Codex 不允许跳过：先 Task，再 Issue/里程碑，再实现，再测试，再文档 & Issue 回写。
   - 提交 git 时按模块粒度拆分：
     - 文档变更（ADR / TASK / SPEC）一组；
     - 代码实现一组；
     - 测试新增/修改一组（可以和实现合并，但不要把无关改动混在一个 commit 里）。

### 4.5 Git 提交规范（Commit Message）

所有提交必须使用统一的前缀风格：

- 使用 `type: <subject>` 形式，常见 `type` 包括：
  - `feat`: 新功能 / 新能力落地（包括 CLI、生成器、引擎能力等）；
  - `fix`: 明确的 bug 修复；
  - `docs`: 纯文档变更（SPEC / ADR / TASK / README 等）；
  - `refactor`: 重构，行为不变、结构调整；
  - `chore`: 杂项（脚本、CI、依赖更新、数据库快照等）；
  - `test`: 只改测试；
  - `style`: 纯格式/排版调整，不改变行为。
- Task / Issue 号放在 `type` 之后作为 scope 或补充信息，而不是替代 `type`：
  - ✅ `feat(choice-eval): BMAD 选择点评估器与离线诊断 CLI`
  - ✅ `docs(task_story_structure): 更新 STORY_PIPELINE_V4 与 TASK_STORY_STRUCTURE.md`
  - ❌ `[TASK_CHOICE_EVAL_BMAD] BMAD 选择点评估器与离线诊断 CLI`（缺少 type）
- 一条提交只做一件有意义的事情：
  - 新功能落地：`feat(...)` + 对应测试（必要时可以在同一个 commit）；
  - 文档补全：`docs(...)`；
  - 数据库快照：`chore(db): 更新故事与测试数据库快照`（不要混入代码改动）。

后续所有自动化或由 Codex 生成的 commit message 必须遵守上述规范。

只要在这个项目里遵守以上约定，就能在不制造新坑的前提下，把 v4 骨架流水线一点点演进到可用状态。  
