# TASK: v4 故事生成工作流分阶段 & Agent 编排优化

版本: v0.1  
状态: 草案（新建）  
关联 ADR:  
- `docs/architecture/ADR-003-v4-workflow-staging-and-agents.md`  

---

## 0. 背景

在 `TASK_STORY_STRUCTURE` / `ADR-001` 的基础上，v4 骨架流水线已经落地，并成为默认主路径。但在实际长跑中：

- 一次完整生成动辄 2–4 小时，即使只想调整 Choice/TreeBuilder；
- 任何阶段报错都表现为“整轮失败”，诊断粒度不足；
- Choice/Response 两类 Agent 缺乏共享的会话级上下文，容易产生重复选项和割裂感；
- 关键工作流策略散落在 env + 代码中，理解与调参成本高。

本 Task 聚焦于**工作流编排层面**的优化，而不是新增结构或改 DB。

---

## 1. 目标 / 非目标

### 1.1 目标

- [ ] 提供明确的 **分阶段执行入口**（Stage A/B/C+D 可独立运行），降低长跑调试成本；
- [ ] 在 v4 guided 模式下，将“结构达标判定”统一收敛到 `build_story_report`，TreeBuilder 只做生成与安全闸控制；
- [ ] 为 Choice/Response 引入共享的“导演上下文”，缓解选项/响应重复与节奏割裂问题；
- [ ] 将关键工作流策略从散落的 env 收敛到文档 + 配置对象；
- [ ] 为一次完整生成提供基础的“工作流诊断报告”，便于快速评估一轮的质量。

### 1.2 非目标

- 不在本 Task 中大改 DB schema 或对话树 JSON 结构；
- 不推翻现有 v4 PlotSkeleton / guided TreeBuilder 设计，只在其之上优化工作流；
- 不实现“单 Agent 端到端生成整棵树”的激进方案；
- 不在这里处理所有 Choice 文案审美问题（那属于 `TASK_CHOICE_POINTS_QUALITY`）。

---

## 2. 里程碑与任务拆分

### M1: 分阶段入口（Stage-aware StoryGenerator）

**目的**：让开发者和 CI 能只跑需要的阶段，而不是每次都从 Stage A 开始。

- [ ] M1-1 StoryGenerator 支持按 stage 调用
  - 在 `StoryGeneratorWithRetry.generate_full_story` 中引入 `stage` 或等价参数：
    - `"full"`：默认行为，A+B+C+D；
    - `"docs"`：仅执行文档生成，结束后返回；
    - `"skeleton"`：在已有 docs 基础上，仅执行骨架生成与基础检查；
    - `"tree"`：在已有 docs+skeleton 基础上，仅执行 TreeBuilder + 文本填充 + 报告 + 存库。
  - 保证：
    - 不破坏现有 CLI 的默认行为（不传 stage 时等价于 `"full"`）；
    - 日志中清晰标记当前 stage。

- [ ] M1-2 CLI/脚本包装
  - 为调试友好，可以考虑在 `generate_full_story.py` 中暴露简单的 CLI 参数：

    ```bash
    python generate_full_story.py --city 成都 --title 九眼桥末班网约车 --stage tree
    ```

  - 或提供单独的辅助脚本（如 `tools/run_stage.py`），具体形式可在实现时权衡。

### M2: guided TreeBuilder 结构判定职责下沉

**目的**：让 TreeBuilder 在 guided 模式下只负责生成，不负责“判决”，避免重复 heuristics。

- [ ] M2-1 明确 guided / legacy 模式下的行为差异
  - 在 `DialogueTreeBuilder.generate_tree` 中：
    - 保留 v3 legacy 模式下的 strict gating 行为（抛异常、env 降级等）；
    - 在 guided 模式中：
      - 仍调用 `TimeValidator` 输出结构指标；
      - 只在安全闸（如节点数上限/平台期）触发时主动终止；
      - 对“深度/结局未达标”仅打印告警，不再抛异常。

- [ ] M2-2 StoryReport 成为唯一结构判定来源
  - 确保：
    - 任何上层逻辑（包括 CLI）若要判断“结构是否达标”，都依赖 `build_story_report` 的 verdict；
    - TreeBuilder 本身不再新增关于“结构好坏”的判断逻辑。

### M3: Agent 编排优化（共享导演上下文）

**目的**：让 Choice / Response 共享最近几步的行为与节拍信息，减少重复与割裂。

- [ ] M3-1 设计最小的 DirectorContext 结构
  - 形式可以是 dataclass 或简单 dict，例如：

    ```python
    class DirectorContext:
        recent_choices: List[str]
        recent_responses: List[str]
        recent_beats: List[Dict[str, Any]]
    ```

  - 重点是为 Choice/Response 提供统一的“最近 N 步摘要”，而非完整历史。

- [ ] M3-2 TreeBuilder 集成 DirectorContext
  - 在 `DialogueTreeBuilder` 中维护一个 DirectorContext 实例：
    - 每扩展一个节点：
      - 记录所在 beat 的类型 / 紧张度 / 是否 critical；
      - 将当前选择文本和响应摘要写入上下文；
    - 调用 Choice/Response 时，把该上下文作为额外参数传入。

- [ ] M3-3 Prompt 层使用导演上下文
  - 在 `ChoicePointsGenerator` / `RuntimeResponseGenerator` 的 prompt 构建函数中：
    - 增加“最近几步行为摘要”段落；
    - 明确要求避免重复最近出现的具体行为和措辞；
    - 在适当位置利用 beat 信息调整节奏（与 `TASK_CHOICE_POINTS_QUALITY` 保持一致）。

### M4: 策略收敛 & 工作流诊断

**目的**：统一管理关键阈值/策略，并能够事后快速看出一轮生成质量。

- [ ] M4-1 策略收敛
  - 把以下关键参数的默认值和行为描述写入文档，并在代码中集中读取：
    - `MAX_TOTAL_NODES`
    - `PROGRESS_PLATEAU_LIMIT`
    - `FORCE_CRITICAL_INTERVAL`
  - 在 v4 模式下：
    - 优先从 `PlotSkeleton.config` + 显式配置对象读取策略；
    - 仅在无配置时才 fall back 到 env。

- [ ] M4-2 工作流诊断报告
  - 整合：
    - Choice 层 JSON 解析遥测（见 `ChoicePointsGenerator.get_json_metrics`）；
    - story_report 中的 choice_metrics；
    - TreeBuilder 的安全闸触发（平台期、节点上限）统计；
  - 形成一份结构化的诊断字典，并：
    - 写入 `logs/full_generation_*.log`；
    - 或附加到故事 metadata（如 `metadata["workflow_diagnostics"]`）。

---

## 3. 依赖与协作

- 依赖文档：
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`
  - `docs/architecture/ADR-002-v4-default-pipeline.md`
  - `docs/architecture/ADR-003-v4-workflow-staging-and-agents.md`
  - `docs/architecture/STORY_PIPELINE_V4.md`
  - `docs/tasks/TASK_STORY_STRUCTURE.md`
  - `docs/tasks/TASK_CHOICE_POINTS_QUALITY.md`

- 依赖代码：
  - `src/ghost_story_factory/pregenerator/story_generator.py`
  - `src/ghost_story_factory/pregenerator/tree_builder.py`
  - `src/ghost_story_factory/pregenerator/story_report.py`
  - `src/ghost_story_factory/engine/choices.py`
  - `src/ghost_story_factory/engine/response.py`

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- StoryGenerator 支持按 stage 执行，CLI 可以显式只跑 docs / skeleton / tree；
- v4 guided 模式下：
  - TreeBuilder 不再对“结构不达标”抛异常或暗中调 env；
  - 结构判定统一走 `build_story_report` 的 verdict；
- Choice/Response 已共享最小的导演上下文，实际跑出的长树中：
  - 选项文本重复度明显下降（choice_metrics 中 repetition_rate 有可测下降）；
  - 默认选项 fallback 占比降低；
- 至少有 1–2 次完整生成，其“工作流诊断报告”显示：
  - Choice JSON 一次通过 + 轻量修复为主，salvage/失败比例显著下降；
  - 平台期次数和安全闸触发情况在合理范围内（无长时间“原地打转”）。

后续若再对 v4 工作流做改动，应优先通过本 Task 所确立的“分阶段 + 诊断 + Agent 编排”思路演进，而不是简单增加 heuristics 或隐藏逻辑。  

