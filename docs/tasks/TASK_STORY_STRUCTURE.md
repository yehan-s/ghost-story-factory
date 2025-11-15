# TASK: 新故事结构化生成流水线（骨架优先模式）

版本: v0.1  
状态: 草案（可迭代）  
关联 ADR: `docs/architecture/ADR-001-plot-skeleton-pipeline.md`  

---

## 0. 背景

- 放弃旧故事数据与旧 v1 CLI 流程，只为“新故事模式”负责；
- v3 流水线已经可以稳定预生成对话树，但：
  - 主线深度/节奏仍依赖 heuristics 与多层重试；
  - 分支结构难以控制，整体结构偶尔“乱/碎”；
- 本任务聚焦于：**把故事结构本身的“好品味”做扎实**，在此基础上再谈文案审美。

---

## 1. 目标 / 非目标

### 1.1 目标

- [ ] 定义 `PlotSkeleton` 数据模型及其校验规则；
- [ ] 实现 `SkeletonGenerator`，可稳定生成符合约束的骨架；
- [ ] 将 `DialogueTreeBuilder` 改造为可接受骨架指导的 guided 模式；
- [ ] 在 guided 模式下，生成对话树结构满足：
  - 主线深度在配置范围内；
  - 结局数量合理；
  - 分支节奏清晰（critical 节点分布合理）。

### 1.2 非目标

- 不再维护 v1 CLI 的 `set-city / get-struct / get-story` 流程；
- 不保证旧故事数据可继续游玩；
- 不在本任务中解决所有文案风格问题（只做结构相关的最小保障）。

---

## 2. 里程碑与任务拆分

### M1: PlotSkeleton 模型与结构指标

**目的**：把“好结构”具体化为可编码的数据结构和检查逻辑。

- [ ] M1-1 定义 `PlotSkeleton` 模型（Python + JSON Schema 草稿）
  - 文件位置建议：
    - `src/ghost_story_factory/pregenerator/skeleton_model.py`
  - 内容：
    - Story-level: `title`, `config`, `acts`
    - Act: `index`, `label`, `beats`
    - Beat: `id`, `act_index`, `beat_type`, `tension_level`,
      `is_critical_branch_point`, `leads_to_ending`
    - Branch: `branch_type`, `max_children`, `notes`

- [ ] M1-2 结构指标脚本 `tools/check_structure_metrics.py`
  - 输入：骨架或对话树 JSON；
  - 输出：
    - 主线深度；
    - 结局数量及大致分布；
    - 每幕节点数 / beats 数量；
    - critical 节点位置。

- [ ] M1-3 为指标定义默认阈值（配置化）：
  - `MIN_MAIN_DEPTH`、`TARGET_MAIN_DEPTH` 范围；
  - `MIN_ENDINGS` / `MAX_ENDINGS`；
  - 至少 1–2 个 critical 节点落在 act II / act III。

### M2: SkeletonGenerator（Stage B）

**目的**：独立的骨架生成阶段，只负责输出结构，不掺和文案。

- [ ] M2-1 新增模板 `templates/plot-skeleton.prompt.md`
  - 输入占位：
    - `city`
    - `synopsis`
    - `lore_v2_summary`
    - `main_story_summary`
  - 输出要求：
    - 单个 ```json 代码块；
    - 严格遵守 `PlotSkeleton` 结构。

- [ ] M2-2 新增模块 `src/ghost_story_factory/pregenerator/skeleton_generator.py`
  - 类 `SkeletonGenerator`：

    ```python
    class SkeletonGenerator:
        def __init__(self, llm, city: str): ...
        def generate(self, synopsis, lore_v2, main_story) -> Dict[str, Any]: ...
    ```

  - 行为：
    - 调用 LLM 生成骨架；
    - 解析 JSON，应用 schema 校验；
    - 校验失败时抛出明确异常。

- [ ] M2-3 测试：
  - `test_skeleton_generator_smoke`：能跑通并返回合法骨架（可用 fake LLM / 伪数据）。

### M3: TreeBuilder guided 模式（Stage C）

**目的**：让 `DialogueTreeBuilder` 不再“自己瞎长”，而是按骨架行事。

- [ ] M3-1 扩展 `DialogueTreeBuilder` 接口
  - 在构造函数中加入 `plot_skeleton: Optional[Dict[str, Any]]`；
  - 在 `generate_tree()` 里根据 `self.plot_skeleton` 决定是否进入 guided 模式。

- [ ] M3-2 guided 模式调度逻辑
  - 基于 depth / beat 映射，给每个节点分配“所属 beat”；
  - 根据 beat 的 `is_critical_branch_point` / `branch_type`：
    - 控制该节点允许的 `max_branches_per_node`；
    - 决定是否可以生成结局节点。

- [ ] M3-3 与现有 heuristics 的关系
  - guided 模式下：
    - 忽略 `EXTEND_ON_FAIL_ATTEMPTS` 类扩展轮参数；
    - `TimeValidator` 只做最终 sanity check；
    - `depth_booster` / `depth_orchestrator` 不主动调用。

- [ ] M3-4 回退策略
  - 如果骨架模式在开发早期不稳定，可通过环境变量关闭：
    - `USE_PLOT_SKELETON=0` → 回退到 v3 行为。

### M4: 节点文本填充（Stage D）

**目的**：在结构锁定前提下生成节点叙事与选项文案。

- [ ] M4-1 设计节点填充 API

  ```python
  def fill_dialogue_texts(tree, skeleton, docs, llm) -> dict:
      ...
  ```

- [ ] M4-2 文本生成策略
  - 基于 beat 类型 / tension 控制文本长度；
  - 对 critical 分支强制选项差异化；
  - 对 micro 分支只做气氛微调。

- [ ] M4-3 验收脚本
  - 利用 `TimeValidator` + 结构指标脚本，生成一份结构+时长综合报告；
  - 作为人工评审入口。

---

## 3. 依赖与协作

- 依赖文档：
  - `docs/specs/SPEC_V3.md`
  - `docs/architecture/NEW_PIPELINE.md`
  - `docs/architecture/STORY_PIPELINE_V4.md`
  - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`

- 依赖代码：
  - `src/ghost_story_factory/pregenerator/story_generator.py`
  - `src/ghost_story_factory/pregenerator/tree_builder.py`
  - `src/ghost_story_factory/pregenerator/time_validator.py`

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- 使用骨架模式从 0 生成的故事：
  - 主线深度、结局数量、时长均在配置阈值内；
  - 不依赖 `EXTEND_ON_FAIL_ATTEMPTS` / `depth_booster` 等扩展轮硬凹；
  - 结构检查脚本通过（或只给出轻微 warning）。
- 至少 1–2 个故事通过人工结构评审：
  - 分支层级清晰，critical 节点位置合理；
  - 不出现明显“随机乱树”的观感。

