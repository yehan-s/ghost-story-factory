# TASK: 选择点 BMAD 评估器（多评委离线打分）

版本: v0.3  
状态: 部分完成（启发式路径 + CLI + 按幕聚合指标已落地）  
关联 ADR:  
- `docs/architecture/ADR-003-v4-workflow-staging-and-agents.md`  

---

## 0. 背景

在 `TASK_CHOICE_POINTS_QUALITY.md` 中，我们已经：

- 提升了选择点 JSON 稳健性（预修复 + salvage + 遥测）；
- 利用骨架节拍信息与最近几步上下文，减少选项重复；
- 为选择点建立基础指标（choice_metrics）并接入结构报告与可视化。

但目前这些指标仍然偏「统计向」，缺少从**叙事/结构/世界观**等多个维度对单个节点的选择集合做系统化评估的能力。  

本 Task 希望引入一个 **BMAD 风格（Brainstorm→Merge→Assess→Decide）** 的「多评委」工具，用于对**单个选择集合**做离线打分与诊断：

- 不直接干预 TreeBuilder 的实时生成；
- 作为开发者调参与审稿时的辅助工具。

---

## 1. 目标 / 非目标

### 1.1 目标

- [x] 提供一个可复用的 **Choice 质量评估器**（`ChoiceQualityEvaluator`），支持：
  - 输入：`scene_id` + `choices[]` + `GameState` + 可选的 `beat_info`；
  - 输出：多维评分（结构 / 世界观 / 节奏 / 多样性）与简短建议；
  - 内部可以用多 Agent（评委）或启发式实现 BMAD 风格的评估过程。（当前版本实现了启发式路径，LLM 多评委作为后续增强）
- [x] 提供一个 CLI 工具 `tools/eval_choice_quality.py`：
  - 可从对话树 JSON 中选择某个节点的 `choices`，调用评估器并输出报告；
  - 支持简单参数：`--tree-json` / `--node-id`。
- [x] 为评估器增加基础单元测试，确保：
  - 在无 CrewAI/LLM 环境下，启发式路径仍然能正常返回结构化评分；
  - 不破坏现有测试与流水线。

### 1.2 非目标

- 不在本 Task 中把 BMAD 评估结果接入 TreeBuilder gating（不阻断生成）；
- 不评估整棵树或整条故事，只聚焦在**单个节点的一组选项**；
- 不尝试在一次改动中解决所有主观「好不好看」的问题，主要关注结构/多样性/世界观一致性等客观维度。

---

## 2. 里程碑与任务拆分

### M1: 设计 ChoiceQualityEvaluator 接口与维度

- [x] M1-1 定义评估接口：

  ```python
  class ChoiceQualityEvaluator:
      def __init__(self, gdd_content: str = "", lore_content: str = "", main_story: str = ""): ...

      def evaluate(
          self,
          scene_id: str,
          choices: List[Choice],          # 或等价字典结构
          game_state: GameState,
          beat_info: Optional[Dict[str, Any]] = None,
      ) -> Dict[str, Any]:
          ...
  ```

- [x] M1-2 设计评估维度（至少包含）：
  - `structure`: 选项数量 / 差异度 / 是否有 critical / 是否在允许节拍下给出结局 flag；
  - `lore`: 是否违反世界书（可选，LLM 模式才充分使用）；
  - `pacing`: 是否符合 beat_type 所需的推进程度；
  - `diversity`: 文案与行为类型重复度。

- [x] M1-3 评估结果结构示例：

  ```json
  {
    "overall_score": 7.5,
    "dimensions": [
      {"name": "structure", "score": 8.0, "comment": "选项分布合理，有明确 critical。"},
      {"name": "lore", "score": 7.0, "comment": "基本符合世界书，无明显违背。"},
      {"name": "pacing", "score": 7.5, "comment": "节奏与当前 beat_type 匹配。"},
      {"name": "diversity", "score": 7.0, "comment": "选项存在一定差异，但仍可增加一条更激进路线。"}
    ],
    "suggestions": ["可以为结局节拍增加一条明确收束白娘子诅咒的选项。"]
  }
  ```

### M2: BMAD 评估流程实现（LLM + 启发式双路径）

- [ ] M2-1 LLM 评估路径（如 CrewAI 在环境可用时）：
  - 内部起 3–4 个评委 Agent（结构评委 / 世界观评委 / 节奏评委 / 多样性评委），分别输出维度评分与点评；
  - 汇总为统一结果 dict；
  - 注意：此路径不在单元测试中强依赖，仅在真实环境下可选使用。

- [x] M2-2 启发式评估路径（无 LLM 时）：
  - 基于 choices 的简单统计：
    - 数量是否在 2–4 范围；
    - 行为类型/文本重复度（基于字符串相似或去重计数）；
    - 是否存在 critical choice / 是否在 `beat_info.leads_to_ending=True` 时打出结局 flag；
  - 生成基础评分与简短 comment，保证在无 LLM 环境下也能返回有用结果。

- [ ] M2-3 `evaluate()` 根据环境自动选择：
  - 尝试 LLM 评估，失败时自动回退到启发式评估；
  - 保证不会抛异常到调用方。

### M3: CLI 工具与测试

- [x] M3-1 `tools/eval_choice_quality.py`：
  - 参数：
    - `--tree-json`: 对话树 JSON 路径；
    - `--node-id`: 要评估的节点 ID；
  - 行为：
    - 从树中取出指定节点的 `choices` 与 `game_state`（若有），构造 `GameState` 对象；
    - 调用 `ChoiceQualityEvaluator.evaluate`；
    - 在终端打印总体评分 + 各维度评分与 comment；
    - 可选：输出为 JSON/Markdown 文件，方便离线查看。

- [x] M3-2 单元测试：
  - 新增 `tests/test_choice_evaluator_bmad.py`：
    - 使用手工构造的一组选项，直接调用评估器的启发式路径（不依赖 LLM），验证输出结构与基本评分逻辑；
  - 将该测试文件纳入 `tools/run_all_tests.py` 的 Pytest 部分。

### M4: 故事级按幕聚合与结构报告集成

- [x] M4-1 在 `build_story_report` 中引入按幕聚合的 BMAD 选择点质量指标：
  - 为有骨架的故事计算按 `act_index` 聚合的平均 overall_score 与各维度平均分；
  - 输出结构示例：
    ```json
    {
      "choice_quality_by_act": {
        "acts": [
          {
            "act_index": 1,
            "label": "Act I",
            "num_nodes_evaluated": 12,
            "avg_overall_score": 7.3,
            "dimensions": [
              {"name": "structure", "avg_score": 7.8},
              {"name": "diversity", "avg_score": 7.1},
              {"name": "pacing", "avg_score": 6.9},
              {"name": "lore", "avg_score": 7.0}
            ]
          }
        ]
      }
    }
    ```
  - 要求：
    - 仅在传入 `PlotSkeleton` 且能确定 act_index 时启用；
    - 评估失败不阻断主流程，不影响 verdict；
    - 计算代价与故事幕数线性相关，适合在每次完整生成后作为离线诊断。

---

## 3. 依赖与协作

- 依赖文档：
  - `docs/tasks/TASK_CHOICE_POINTS_QUALITY.md`
  - `docs/architecture/ADR-003-v4-workflow-staging-and-agents.md`

- 依赖代码：
  - `src/ghost_story_factory/engine/choices.py`
  - `src/ghost_story_factory/engine/response.py`
  - `src/ghost_story_factory/engine/state.py`
  - `src/ghost_story_factory/pregenerator/tree_builder.py`

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- 存在一个稳定的 `ChoiceQualityEvaluator` 实现，支持在无 LLM 环境下的启发式评估，并在有 LLM 环境下可选启用 BMAD 风格多评委评估；
- 提供可用 CLI 工具 `tools/eval_choice_quality.py`，能对任意树节点的选择集合进行离线质量评估；
- 至少有一个手工构造或真实故事节点的评估示例（可为 JSON/Markdown 报告），展示如何解读各维度评分与建议；
- 新增测试已纳入 `tools/run_all_tests.py`，并全部通过。
