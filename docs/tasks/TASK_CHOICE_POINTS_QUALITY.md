# TASK: 提升选择点生成质量（JSON稳健性 + 去重复）

版本: v0.1  
状态: 草案（新建）  
关联 ADR:  
- `docs/architecture/ADR-001-plot-skeleton-pipeline.md`（骨架优先流水线）  
- `docs/architecture/NEW_PIPELINE.md`（整体预生成架构）  

---

## 0. 背景

当前 v4 骨架流水线已经接入 `DialogueTreeBuilder` 的 guided 模式，主线深度与结局数量改为由 `PlotSkeleton` 约束，并且：

- TreeBuilder 在 guided 模式下不再“硬挂死”，结构校验只做告警；
- 选择点与响应生成增加了基础兜底（默认选项 / 默认响应）；
- 检查点更密集，失败重跑成本下降。

但在真实长跑中暴露出一组 **选择点层面的质量问题**：

1. **JSON 半残导致频繁退回默认选项**
   - 典型日志：
     - `Expecting ',' delimiter`（键名跨行：`immediate_\nconsequences` 等）；
     - `Expecting value: line 1 column 1`（result 是空行 / 对象包装，解析不到主体）。
   - `_parse_result` 失败后，`ChoicePointsGenerator.generate_choices()` 会直接回退到 `_get_default_choices()`：
     - “继续调查 / 原地观察 / 直面关键线索（可能触发结局）” 三连。
   - 结果：一旦当前层 JSON 有问题，后续多层节点都在重复同一组默认选项。

2. **场景停留 + 状态变化弱 → 选择点语义高度重复**
   - 很多 guided 的树在 `S1` 场景附近打转，`current_scene / time / flags` 变化极小；
   - ChoicePointsGenerator 的 prompt 主要依赖：
     - `scene_id`、该场景的 GDD 片段；
     - 世界书摘要；
     - 当前 PR/时间/道具；
   - 当这些几乎不变时，LLM 每次看见的 prompt 近乎相同，即使 JSON 正常，也容易产出“前一轮的变体”。

3. **骨架 beats 信息在选择点层使用不足**
   - 现有 guided 模式主要用骨架来限制：
     - 每层最大分支数；
     - 哪些深度允许结局出现；
   - 但 `BeatConfig.beat_type / tension_level / is_critical_branch_point` 等并未被 ChoicePrompt 显式利用：
     - 没有告知 LLM “这是一个关键节拍 / 高张力节点”；
     - 没有对“不重复前一节拍的行为类型”给出明确限制。

综上：**结构层已经有了骨架约束，但选择点内容层仍然比较“散”和“脆弱”，需要一个专门的 Task 来收敛。**

---

## 1. 目标 / 非目标

### 1.1 目标

- [x] 提升 LLM 选择点输出的 **JSON 稳健性**，显著减少退回默认选项的次数；
- [x] 减少同一场景 / 相邻节点间的 **选项文案与语义重复度**；
- [x] 在选择点层更好地利用骨架信息（PlotSkeleton / Beats），让不同节拍有差异化策略；
- [x] 为选择点质量建立基础指标和可视化入口（方便回归和调参）。

### 1.2 非目标

- 不重写整套游戏引擎（`engine/game_loop.py` / runtime CLI）；
- 不在本 Task 中大改 DB schema 或对话树 JSON 结构；
- 不试图在一次迭代中解决所有“文案审美”问题（先解决结构与多样性，再谈风格）。

---

## 2. 里程碑与任务拆分

### M1: JSON 解析稳健性提升

**目的**：让优秀但“略脏”的 JSON 不轻易被判死刑，减少 fallback 触发频率。

- [x] M1-1 针对典型格式问题增加预修复逻辑
  - 示例问题：
    - 键名断行：`immediate_\nconsequences` → `immediate_consequences`；
    - 软换行导致的 `","` / `": "` 被拆开。
  - 方案：
    - 在 `_parse_result` 前增加一层轻量正则清洗：
      - 合并行尾为 `_` 的键名；
      - 统一 `immediate_consequences` → `consequences` 映射。

- [x] M1-2 提升对“数组主体”与“嵌套 JSON”场景的容错
  - 若顶层解析失败但能找到 `choices: [...]` 结构，则尝试直接构造 `{ "scene_id": "...", "choices": [...] }`。

- [x] M1-3 日志与指标
  - 在 `ChoicePointsGenerator` 中统计：
    - 总调用次数；
    - JSON 一次通过 / 通过修复 / 彻底失败三类数量；
  - 输出到 `logs/full_generation_*.log`，便于后续评估改动效果。

### M2: 去重复与状态驱动的 Prompt 设计

**目的**：让相邻节点的选项不再像“缝同一个螺丝”，而是随骨架节拍和状态变化有明显差异。

- [x] M2-1 Prompt 注入“最近几步”上下文
  - 在 ChoicePrompt 中追加：
    - 前 1–2 个节点的已选选项摘要；
    - 最近一轮的选项文本列表（作为负例描述：避免简单重复）。
  - 要求 LLM：
    - 不要重复上一节点中已出现的行动方式；
    - 至少提供一个明显“更激进/更保守/更超自然”的分支。

- [x] M2-2 与骨架节拍类型对齐
  - 若当前 depth 映射到的 `BeatConfig.beat_type` 为：
    - `setup`：更多信息收集 /安全尝试；
    - `escalation`：提高风险 / 推进冲突；
    - `twist`：提供颠覆玩家预期的选项；
    - `climax`：至少一个选项直指核心冲突或结局；
    - `aftermath`：收束与结算。
  - 将这些要求写入 ChoicePrompt，使得不同节拍选项分布本身就有节奏感。

- [x] M2-3 明确禁止“无视场景”的选项
  - 在 Prompt 中加一条硬约束：
    - 禁止生成与当前场景描述明显无关或重复上一节拍文本的选项。

### M3: 选择点质量指标与可视化

**目的**：为之后的调参与对比提供量化视角。

- [x] M3-1 选择点级别统计
  - 在预生成结束时，为每个故事记录：
    - 平均每节点选项数；
    - 默认选项使用占比；
    - 重复选项文本比率（简单基于字符串相似度或哈希）。

- [x] M3-2 与结构报告集成
  - 在 `story_report.build_story_report` 的输出中增加简单的选择点统计入口（或旁路脚本），用于后续在 `tools/report_story_structure.py` 中展示。

- [x] M3-3 进度可视化整合
  - 与 `TASK_PROGRESS_VISUALIZATION.md` 的工作协同：
    - 在生成进度可视化（HTML/终端）中标记“重复度高”的节点，便于肉眼扫出问题段。

### M4: 节点级质量问题的离线修复流程（避免在 TreeBuilder 中死磕）

**目的**：当某些节点的选择点因为 LLM/JSON 问题质量不佳时，不在 TreeBuilder 主循环里“现场死磕”，而是通过离线工具有计划地修复，兼顾稳定性与质量。

- [ ] M4-1 明确运行时与离线修复的职责边界
  - 运行时（TreeBuilder.generate_tree）：
    - 捕获所有 ChoicePointsGenerator 的异常（包括 LLM 内部格式化错误，如 `Invalid format specifier ' true'`）；
    - 记录清晰日志（包括场景 ID / 节点 ID / 异常摘要）；
    - 立即退回 `_get_default_choices()` 确保结构可继续生成，不在主循环中多次重试单节点。
  - 离线修复阶段：
    - 通过工具扫描对话树，识别“默认选择占比过高 / BMAD 评分显著偏低”的节点或幕；
    - 针对这些节点重新调用 ChoicePointsGenerator，生成更高质量的选择集合，并回写树。

- [ ] M4-2 在 `tools/repair_dialogue_trees.py` 中实现节点级离线修复流程
  - 输入：
    - 对话树 JSON（或 checkpoint）；
    - 可选过滤条件：`scene_id` / `min_repetition_rate` / `bmad_score_threshold` 等。
  - 行为：
    - 扫描选择点质量指标（可复用 `story_report` 与 BMAD 结果，见 `TASK_CHOICE_EVAL_BMAD.md`）；
    - 对满足条件的节点：
      - 重新构造 `GameState` 与节拍信息；
      - 调用 ChoicePointsGenerator.generate_choices（脱离 TreeBuilder 主循环）；
      - 用新 choices 替换节点中的旧 choices（必要时保留快照）。
  - 输出：
    - 修复后的新树 JSON；
    - 简要报告：修复节点数 / 每个节点前后质量差异摘要。

- [ ] M4-3 与 BMAD 评估器集成
  - 在离线修复前后，对目标节点调用 `ChoiceQualityEvaluator.evaluate`：
    - 比较修复前后的 `overall_score` 与各维度（structure / diversity / pacing / lore）评分；
    - 在修复报告中记录这些差异，用于验证该次修复对质量的实际提升。

- [ ] M4-4 文档化“不要在 TreeBuilder 中死磕单节点”的准则
  - 在本 Task 与 `TASK_STORY_STRUCTURE.md` 中补充说明：
    - 节点级质量问题（包括 LLM 格式化错误 / JSON 半残 / BMAD 低分）优先通过离线修复链路解决；
    - TreeBuilder 主循环只负责结构生成与基础兜底，不在其中堆叠多轮重试和复杂 heuristics；
    - 任何需要“多次重试单个节点”的需求，应转化为离线 repair 工具或专门的诊断脚本，而不是注入到 BFS 生成逻辑中。

---

## 3. 依赖与协作

- 依赖文档：
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`
  - `docs/architecture/STORY_PIPELINE_V4.md`
  - `docs/tasks/TASK_STORY_STRUCTURE.md`

- 依赖代码：
  - `src/ghost_story_factory/engine/choices.py`
  - `src/ghost_story_factory/engine/response.py`
  - `src/ghost_story_factory/pregenerator/tree_builder.py`
  - `src/ghost_story_factory/pregenerator/skeleton_model.py`
  - `tests/test_tree_builder_guided.py`

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- 在一组真实城市（至少 2–3 个故事）上：
  - 选择点 JSON 解析失败率显著下降（有 log 支撑）；
  - 默认选择兜底占比明显降低；
  - 玩家从日志与 CLI 中主观感受“重复选择点”情况得到缓解。
- ChoicePrompt 中已经显式使用骨架节拍信息（beat_type / is_critical_branch_point），并在代码中有对应实现与测试；
- 存在至少一个工具或报告，可以帮助开发者：
  - 查看每个故事的选择点统计；
  - 快速定位重复度高或结构薄弱的区域。

之后若再对选择点策略做改动，应优先通过本 Task 的 M1/M2 路线（JSON 稳健 / 去重复）演进，而不是在 TreeBuilder 层继续堆 heuristics。  
