# 故事生成流水线 v4（骨架优先模式，当前默认路径）

> 版本: v4  
> 日期: 2025-11-15  
> 状态: ✅ 已在代码中落地为 StoryGenerator 的默认生成路径（v3 作为兼容回退）

---

## 1. 总览

v4 版本的目标：在保持现有 v3 成熟组件的前提下，引入**骨架优先的故事结构生成模式**，并将其升级为**默认故事生成路径**，让：

- 主线深度、结局数量、节奏分布变成“可设计的约束”，而不是“事后硬凹的结果”；
- 分支类型与重要节点在骨架层就明确下来；
- 文案生成完全解耦结构决策，便于后续多风格尝试。

高层对比（现在以 v4 为主线，v3 为兼容层）：

- **v4 主路径（默认）**：  
  文档 → Skeleton Generator（PlotSkeleton）→ TreeBuilder（guided）→ 文本填充（NodeTextFiller）→ 校验（story_report）

- **v3 兼容路径**：  
  文档 → `DialogueTreeBuilder`（结构+文案一起生成）→ 校验 → 同轮扩展 / env 降级（legacy heuristics）

---

## 2. 阶段划分

### Stage A：文档生成（沿用 v3）

- 入口：`generate_full_story.py`
- 产物：
  - `{city}_{title}_lore_v2.md`
  - `{city}_{title}_gdd.md`
  - `{city}_{title}_story.md`
- 说明：
  - v4 不重写这一层，只在需要时做参数与接口清理；
  - 骨架生成直接复用这些文档作为上文。

### Stage B：骨架生成（Skeleton Generator，默认启用）

**新组件**：`SkeletonGenerator`

- 输入：
  - `city`
  - `StorySynopsis`（标题 / 主角 / 预期时长）
  - `lore_v2` 摘要（或全文）
  - `main_story` 摘要
- 输出：
  - `PlotSkeleton` JSON（结构由 ADR-001 中定义）
- 实现要点：
  - 使用模板 `templates/plot-skeleton.prompt.md`；
  - 限制输出为一个 JSON 代码块；
  - 解析失败直接报错，不 silent 修复；
  - 内部做基础指标校验：
    - 预估主线深度 ≥ `config.min_main_depth`
    - 预计结局数量 ≥ `config.target_endings` 的合理下界（例如至少 2 个）；
  - 配置：通过 `USE_PLOT_SKELETON` 控制：
    - 默认 `USE_PLOT_SKELETON=1`：必须先尝试骨架生成，进入 v4 骨架模式；
    - `USE_PLOT_SKELETON=0`：跳过本阶段，直接走 v3 兼容路径。

### Stage C：骨架驱动的 TreeBuilder（v4 guided）

**改造组件**：`DialogueTreeBuilder`

- 新增参数：

```python
def __init__(..., plot_skeleton: Optional[Dict[str, Any]] = None, ...):
    self.plot_skeleton = plot_skeleton
    self.guided_mode = plot_skeleton is not None
```

- Guided 模式行为（v4 正式策略）：
  - BFS 队列不再“见节点就全展开”，而是：
    - 根据当前节点所在的 beat（通过 depth 或显式映射）：
      - 决定允许的分支类型（critical / normal / micro）；
      - 限制子节点数量 `max_children`；
      - 判断是否可以生成结局节点。
  - 保留安全闸：`MAX_TOTAL_NODES` / `PROGRESS_PLATEAU_LIMIT` / Beam；
  - `TimeValidator` 仍可用于 sanity check，但不再触发 env 降级；
  - `EXTEND_ON_FAIL_ATTEMPTS` 等参数在 guided 模式下被硬收紧为最多 1 次；
  - 所有基于 env 的 heuristics（`MIN_DURATION_MINUTES` / `EXTEND_ON_FAIL_ATTEMPTS` / `FORCE_CRITICAL_INTERVAL`）仅在 v3 legacy 模式生效。

### Stage D：节点文本填充 + 结构验收

**新阶段**：节点内容填充器 + 骨架对照报告

- 目标：在对话树结构固定后，为每个节点生成合适的叙事与选项文案，并给出结构验收报告；
- 输入：
  - `dialogue_tree`（结构已稳定）
  - `plot_skeleton`
  - 文档（`lore_v2`, `gdd`, `main_story`）
- 策略示意：
  - 根据 beat 类型控制文本长度与张力：
    - setup：铺垫信息，长度适中；
    - escalation / twist：增强紧张感、引入新信息；
    - climax：密集冲突和决断；
    - aftermath：收束情绪与信息。
  - 对 critical 分支的选项文案要求：
    - 策略/立场明显不同；
    - 清晰体现对后续结构的影响（哪条主线分支）。

当前实现（第一阶段）已经接入到 `StoryGeneratorWithRetry` 主路径中：
- `NodeTextFiller(skeleton).fill(dialogue_tree)`：
  - 为节点追加 beat 元数据；
  - 对 narrative 为空或全空白的节点填充占位叙事，不覆盖已有文案。
- `build_story_report(tree, skeleton)`：
  - 利用 `TimeValidator` + 骨架指标生成结构+时长+结局综合报告；
  - 至少打印主角 `depth_ok / duration_ok / endings_ok` 摘要，作为人工验收入口。

---

## 3. 结构约束与指标

配合 `PlotSkeleton`，v4 流水线需要定义一批清晰的结构指标，用于自动检查：

- 主线深度：最长路径长度是否在 `[min_main_depth, target_main_depth_max]`；
- 结局数量：是否在合理范围（例如 3–6 个）；
- 结局分布：结局是否集中在后 1/3 深度区域；
- critical 节点分布：是否在 act II / act III 适当位置出现；
- 分支复杂度：每层非叶节点数量与平均分支数。

建议在 `tools/check_structure_metrics.py` 中实现一份基础检查脚本，供开发调试使用。

---

## 4. 与 v3 的关系（默认路径 vs 兼容路径）

- v3 文档（`NEW_PIPELINE.md`, `SPEC_V3.md`）描述的是历史基线架构，现在主要用于理解 legacy 行为与兼容路径；
- v4 在此基础上演进，并已经在代码中成为默认主路径：
  - Stage A 与 v3 基本一致；
  - Stage B 是新增的骨架层（默认启用，可通过 `USE_PLOT_SKELETON=0` 关闭）；
  - Stage C 是对现有 TreeBuilder 的 guided 扩展；
  - Stage D 是新增的文本填充 + 结构验收阶段。

运行时策略：

1. 默认模式（推荐）  
   - `USE_PLOT_SKELETON=1`（或未设置）  
   - StoryGenerator：文档 → Skeleton → guided TreeBuilder → NodeTextFiller → story_report → DB  
   - env heuristics 不参与结构“救火”，仅作为 v3 legacy 行为的历史记录。

2. 兼容/排错模式  
   - `USE_PLOT_SKELETON=0`，或 SkeletonGenerator 抛错；  
   - StoryGenerator：文档 → v3 TreeBuilder（`plot_skeleton=None`）→ TimeValidator + legacy heuristics → DB；  
   - 适用于排查问题、对比 v3/v4 行为，但不作为长期推荐路径。

落地顺序参考：

1. 按 `docs/tasks/TASK_STORY_STRUCTURE.md` / `docs/tasks/TASK_V4_DEFAULT_PIPELINE.md` 拆分任务；  
2. 已完成：最小可用的 `PlotSkeleton` + guided TreeBuilder + NodeTextFiller + story_report，并切换为默认主路径；  
3. 后续：在更多真实故事上做结构验收与集成测试，逐步弱化 v3 heuristics 的使用场景。

---

## 5. 相关文档

- 决策文档：`docs/architecture/ADR-001-plot-skeleton-pipeline.md`
- 任务拆分：`docs/tasks/TASK_STORY_STRUCTURE.md`
- 现有架构：
  - `docs/architecture/ARCHITECTURE.md`
  - `docs/architecture/NEW_PIPELINE.md`
  - `docs/specs/SPEC_V3.md`
