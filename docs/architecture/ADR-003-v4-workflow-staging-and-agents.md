# ADR-003: v4 故事生成工作流分阶段 & Agent 编排收敛

- 状态: Draft
- 日期: 2025-11-17
- 作者: yehan（由 Codex 协助起草）

---

## 1. 背景

在 ADR-001 中，我们已经把故事生成从「LLM 随机游走」重构为 **骨架优先** 的 v4 流水线：

- Stage A：文档生成（Raw Materials / Lore v2 / GDD / 主线故事）  
- Stage B：PlotSkeleton（骨架生成）  
- Stage C：guided `DialogueTreeBuilder`（按骨架生成对话树）  
- Stage D：节点文本填充 + 结构报告 + 存库  

在这个基础上，近期的长跑暴露出一组**工作流层面**的问题：

1. **执行单元过大，调试/长跑成本高**
   - 当前 `generate_full_story.py` / `StoryGeneratorWithRetry` 默认“一键跑完” A→B→C→D：
     - 即便 docs、skeleton 已经稳定，调整 TreeBuilder/ChoicePrompt 时仍然要从头跑一轮；
     - 任意阶段出问题，都以“整轮失败”呈现，诊断粒度粗。

2. **Choice / Response Agent 状态割裂**
   - 选择点生成（`ChoicePointsGenerator`）和响应生成（`RuntimeResponseGenerator`）各自维护一套 Crew / Agent：
     - 彼此之间几乎没有共享「会话级记忆」，只能通过 prompt 文本临时拼上下文；
     - 对 LLM 来说，每次调用都像“新对话”，难以形成稳定的 JSON 输出习惯；
     - 相邻节点在同一场景反复调用 Choice agent 时，看到的 prompt 高度相似，导致选项语义和文本重复。

3. **关键工作流策略散落在 env + 代码中，不利于理解与演进**
   - 例如：
     - `FORCE_CRITICAL_INTERVAL` / `MAX_TOTAL_NODES` / `PROGRESS_PLATEAU_LIMIT` 等参数；
     - guided / legacy 不同模式下的 TimeValidator gating 策略；
   - 很多行为依赖动态修改 `os.environ[...]`，而不是集中在 config / ADR / Task 文档中声明。

4. **缺乏“事后诊断”视角**
   - 虽然已经有：
     - TreeBuilder 增量日志 `checkpoints/tree_incremental.jsonl`；
     - 结构报告 `build_story_report`；
   - 但对 Choice 这一层只有零散的日志与直觉，没有一个统一视角回答：
     - 这一轮生成中，JSON 是一次通过，还是严重依赖修复/挽救？
     - 默认选项 fallback 占比有多少？
     - 选项文本的重复度有多高？

总结：**结构骨架已经合理，但执行工作流仍然偏「一锅乱炖」**。需要一个专门的 ADR 收敛 v4 的工作流编排策略，把“长跑成本”和“可调试性”作为一等公民对待。

---

## 2. 决策

本 ADR 做出以下决策：

1. **把 v4 故事生成拆分为可独立执行的阶段入口，而不仅仅是内部 Stage**  
   - 在 CLI / 脚本层面提供可选的 stage 参数或独立入口，支持只跑：
     - Stage A：文档生成；
     - Stage B：骨架生成 + 骨架检查；
     - Stage C+D：对话树 + 文本填充 + 报告 + 存库。

2. **在 guided 模式下，将“结构达标与否”的判定逻辑完全上移到 StoryReport 层**  
   - `DialogueTreeBuilder` 在 `plot_skeleton is not None` 时：
     - 只负责在安全阈内尽可能拉深主线、覆盖结局；
     - 不再通过修改 env 或抛异常来驱动“扩展/重跑”；
   - 是否接受某个故事视为“结构合格”，统一通过 `build_story_report` 的 verdict (passes / depth_ok / duration_ok / endings_ok) 决定。

3. **Choice / Response 两类 Agent 共享“会话级导演脑子”，而不是两个完全孤立的 Crew**  
   - 在不破坏现有代码结构前提下：
     - 为选择点生成和响应生成设计一个共享的、轻量的“最近历史摘要”结构；
     - 提供给两个生成器一致的骨架节拍信息与最近几步行为摘要，用于：
       - 在 ChoicePrompt 中避免重复；
       - 在 ResponsePrompt 中延续前述行为和情绪节奏。

4. **把关键工作流策略（阈值/模式切换）从散落的 env 收敛到文档 + 配置对象中**  
   - 环境变量仍可用于本地实验和 CI 调参，但：
     - v4 的默认策略以 `PlotSkeleton.config` + Task 文档为主；
     - TreeBuilder / ChoiceGenerator 读取集中配置对象，而不是在函数内部到处 `os.getenv`。

5. **引入一次性“工作流诊断报告”，而非只盯运行时日志**  
   - 对每次完整故事生成（尤其是长跑）：
     - 生成一份附加的“工作流诊断”结构，以 JSON 或 Markdown 存入 `logs/` 或 metadata 中；
     - 重点包括：Choice JSON 稳定性指标、默认选项占比、重复选项比率、TreeBuilder 安全闸触发情况等。

---

## 3. 方案细节

### 3.1 分阶段入口（Stage-aware CLI / API）

在保持现有 CLI 用户体验的前提下，引入更细粒度的执行入口：

- `generate_full_story.py` / `StoryGeneratorWithRetry`：
  - 新增 `stage` 或等价参数，支持：
    - `"full"`（默认）：A+B+C+D 全流程；
    - `"docs"`：只执行 Stage A，生成/缓存 Lore v2 / GDD / 主线；
    - `"skeleton"`：在已存在文档基础上，只执行 Stage B；
    - `"tree"`：在已有 docs + skeleton 的前提下，只执行 Stage C+D。
  - 这些入口应该：
    - 重用已有缓存与 deliverables；
    - 在日志中明确标记当前运行的 stage；
    - 在失败时输出“下一步可单独重跑的 stage 建议”，避免用户总是从头来过。

好处：

- 调整 Choice/TreeBuilder 行为时，不必反复重跑世界书/骨架；
- 集成测试可以选择性地覆盖某一 stage，缩短 CI 时间；
- 更接近 ADR-001 中“分阶段生成”的精神，而不是只在内部标注 Stage。

### 3.2 guided 模式下 TreeBuilder 的职责收敛

针对 `DialogueTreeBuilder.generate_tree()`：

- 在 guided 模式（`plot_skeleton is not None`）下：
  - `TimeValidator` 用于生成过程中打印结构指标与安全闸状态；
  - 不对“未达标”做 env 降级或异常抛出；
  - 最终只返回“尽力而为”的对话树，以及日志中的结构告警。

- 在 legacy 模式（`plot_skeleton is None`）下：
  - 仍保留 v3 的 `strict_mode` 行为，确保原有 heuristics 不被破坏。

这意味着：

- “故事是否合格”的最终判断，从 TreeBuilder 内部上移到 StoryReport / 调用层；
- 任何改变结构判定标准的行为，都应该体现在：
  - `TimeValidator` 的配置；
  - `build_story_report` 的 verdict 逻辑；
  - 或上层任务/ADR，而不是在 TreeBuilder 里“偷偷改 env 再抛异常”。

### 3.3 Agent 编排：共享会话级上下文

现状：

- `ChoicePointsGenerator.generate_choices()` 和 `RuntimeResponseGenerator.generate_response()` 各自维护 LLM 与 Crew；
- 仅通过 `narrative_context` 和少量状态字段把上下文压进 prompt；
- 对 LLM 来说，这是两条互不相干的“流水线”，容易造成：
  - 输出格式不收敛；
  - 文案节奏不连续；
  - 选项/响应间缺乏真正的“对话感”。

方案（本 ADR 范围内给出方向，不要求一次性实现完所有细节）：

1. 引入一个轻量级的“导演上下文对象”（可为简单的 dataclass 或 dict），例如：

   ```python
   DirectorContext = {
       "recent_choices": [...],
       "recent_responses": [...],
       "recent_beats": [...],
   }
   ```

2. `DialogueTreeBuilder` 在扩展节点时：
   - 更新 DirectorContext（例如记录最近 N 步的节拍类型/关键事件）；
   - 调用 Choice / Response 时同时传入该上下文。

3. Choice / Response 两个生成器的 prompt 结构中：
   - 清晰区分：
     - 当前节点局部状态；
     - 来自骨架的节拍意图；
     - 最近几步的行动与反馈（避免重复、保持节奏）。

这一决策不强制切换到“单一 Crew 多 Task”的实现，但要求在设计上把它们视为**共享同一导演脑子**的两个角色，而不是互相不知道对方存在的脚本。

### 3.4 策略从 env → 文档 + 配置对象

代表性参数：

- `FORCE_CRITICAL_INTERVAL`
- `MAX_TOTAL_NODES`
- `PROGRESS_PLATEAU_LIMIT`
- 针对 guided/v3 模式不同的 depth / endings 阈值

约束：

- v4 模式的默认行为应主要受以下来源控制：
  - `PlotSkeleton.config`；
  - `docs/tasks/TASK_STORY_STRUCTURE.md` / `TASK_CHOICE_POINTS_QUALITY.md` 等 Task 文档；
  - 少数明确的配置对象（例如 `TreeBuilderConfig`）。

- 环境变量用于：
  - 本地调试；
  - CI / Benchmark 时的统一 override；
  - 不应被当作“长期行为定义”的唯一来源。

实现上，这意味着逐步将散落在各模块中的 `os.getenv` 调用收敛到集中配置加载函数/类中，并在文档中注明其默认值和用途。

### 3.5 工作流诊断报告

在每次完整故事生成结束时（尤其是非 test_mode）：

- 除已有的结构报告（`build_story_report`）以外，增加一份“工作流诊断”信息，包括但不限于：
  - Choice 层：
    - JSON 解析总调用次数；
    - 一次成功 / 修复成功 / salvage 成功 / 最终失败的计数；
    - 默认选项 fallback 次数；
    - 选项文本重复率等（可与 story_report 中的 choice_metrics 对齐）。
  - TreeBuilder 层：
    - 平台期次数；
    - 安全闸触发（如 `MAX_TOTAL_NODES` / `progress_plateau_limit` 到顶）情况；
  - 运行时：
    - 总 token 粗略估计；
    - 每 stage 耗时。

这些诊断信息可以：

- 写入 `logs/full_generation_*.log`；
- 或附加到存库故事的 metadata 中（不影响 DB schema，只是 JSON 附加字段）。

这样，调参时可以不依赖人肉 grep 全量日志，而是直接比较两轮的诊断摘要。

---

## 4. 备选方案与取舍

### 4.1 保持“一键 full pipeline”，只靠更多 heuristics（拒绝）

- 继续只提供单一入口，遇到长跑成本问题就：
  - 再加缓存；
  - 再加 heuristics；
  - 或者把 checkpoint 调得更密。
- 问题：
  - 调试/调参体验继续很差；
  - 结构和选择质量问题难以精确定位在哪个 stage；
  - 违背“好品味”的设计——明明已经有 Stage 概念，却不把它升格为一等公民。

### 4.2 重写引擎为“单一超 Agent”（拒绝）

- 做法：
  - 用一个超大的 Agent + Prompt 直接从世界书生成完整对话树 JSON；
  - 理论上能避免中间多 agent/多 stage 协调。
- 问题：
  - 完全背离现有骨架 + TreeBuilder 架构；
  - 不利于调试和控制结构；
  - 成本高、风险大，且与目前 v4 累积成果不兼容。

### 4.3 轻量分阶段 + Agent 编排收敛（采纳）

- 优点：
  - 最大限度复用现有 v4 实现；
  - 工作流颗粒度变小，便于针对性优化；
  - Agent 之间共享上下文后，Choice/Response 质量有望同步提升；
  - 策略收敛到文档+配置，有助于长期维护。
- 缺点：
  - 需要为 stage/诊断/上下文设计额外的接口；
  - 短期内增加少量复杂度，但属于“结构性复杂度”，而非 heuristics 堆叠。

---

## 5. 影响与迁移

- 对 CLI 用户：
  - 默认“一键完整生成”入口保持不变；
  - 额外提供面向开发/调试/CI 的 stage 参数或子命令；
  - 日志中会更明确地区分每一阶段的时间与结果。
- 对离线诊断与 BMAD 评估：
  - 新增 `ChoiceQualityEvaluator` 作为**纯离线**的 BMAD 风格选择点评估器（结构 / 节奏 / 多样性 / 世界观占位），不参与 TreeBuilder 实时决策；
  - 提供 CLI 工具 `tools/eval_choice_quality.py`，支持：
    - 从对话树 JSON / checkpoint 中选定某个节点（`--tree-json` + `--node-id`）；
    - 调用评估器输出多维评分和建议，用于精确诊断“某个节点的选项是否伪选择/缺结局/过于重复”；
  - 该工具与 `tools/view_tree_progress.py` / `tools/report_story_structure.py` 共同构成 v4 的三层诊断视角：
    - 结构层（整棵树 / 主线深度 / 结局数量）；
    - 进度层（各层节点分布、结局分布、重复选项数量）；
    - 节点层（单节点选择集合的 BMAD 质量评估）。

- 对 v3 legacy 路径：
  - 不做额外承诺，仍作为临时回退选项；
  - 所有新的工作流优化优先适配 v4 guided 模式。

- 对代码结构：
  - `StoryGeneratorWithRetry` 需要支持按 stage 拆分；
  - `DialogueTreeBuilder` / Choice / Response 需要引入共享的导演上下文结构；
  - 部分 env 读取逻辑会收敛到集中配置。
  - 新增 `ChoiceQualityEvaluator`（`src/ghost_story_factory/engine/choice_evaluator.py`）及其配套单元测试 / CLI，不影响运行时路径，只在开发与调参时使用。

---

## 6. 回滚策略

- 本 ADR 主要引入的是“工作流上的分解与收敛”，而非对现有结构/存储的破坏性变更；
- 若某个具体实现（例如 stage 参数、DirectorContext 设计）在实践中证明不合适：
  - 可以单独回滚该实现，保留“分阶段入口 + StoryReport 判定”这一方向不变；
  - 相关 Task 文档需同步更新当前采用的策略。
