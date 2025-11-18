# TASK: 核心结构化 LLM 调用重构（去 Crew，直连 LLM 客户端）

版本: v0.1  
状态: 草案（新建）  
关联 ADR:  
- `docs/architecture/ADR-004-core-llm-refactor.md`  

---

## 0. 背景

在 v4 骨架流水线中，核心结构化决策点包括：

- 故事骨架生成：`SkeletonGenerator.generate(...) -> PlotSkeleton`；  
- 选择点生成：`ChoicePointsGenerator.generate_choices(...) -> List[Choice]`；  
- 关键响应生成：`RuntimeResponseGenerator.generate_response(...)` 的主线段落。

当前这些路径均依赖 CrewAI 封装的 `Agent/Task/Crew/LLM` 调用。  
在真实长跑中暴露出以下问题：

1. **无法获取某些错误场景下的原始响应文本**  
   - 例如 `Invalid format specifier ' true' for object of type 'str'`：  
     - 错误发生在 Crew 内部 `format` 调用之前；  
     - 无法通过现有 `_extract_llm_text` 拿到原始 LLM 输出做日志/诊断。

2. **结构化 JSON 的质量与可控性受到上游黑盒行为影响**  
   - `PlotSkeleton` 与 `choices` 需要极高的结构稳定性与可解释性；  
   - 但当前调用链的大部分行为（分句、截断、输出格式）由 Crew 决定，本项目只能在外围做 patch 与兜底。

3. **与 v4「骨架优先 + 可诊断」目标存在偏差**  
   - 越来越多的结构问题需要通过 story_report/BMAD/repair 工具做离线分析；  
   - 没有完整的 request/response 日志，会显著阻碍这类诊断工作。

为此，需要一个专门的 Task 推动「核心结构化 LLM 调用从 Crew 重构为轻量客户端」的落地工作。

---

## 1. 目标 / 非目标

### 1.1 目标

- [ ] 为核心结构化调用引入统一的 `LLMClient`，直接通过 HTTP/官方 SDK 调用 Kimi/OpenAI；  
- [ ] 将 `SkeletonGenerator` / `ChoicePointsGenerator` / 关键响应路径从 Crew 重构为基于 `LLMClient` 的实现；  
- [ ] 为所有这类调用建立统一的 request/response 日志格式（包含 prompt/响应片段与错误信息）；  
- [ ] 保持现有 JSON 解析、salvage、BMAD 等逻辑不变，并扩展必要的测试用例。

### 1.2 非目标

- 不在本 Task 中完全移除 Crew：  
  - 文档生成（完整故事 / 世界书 / GDD）仍可使用 Crew；  
  - 本任务仅针对骨架/选择点/关键响应等核心结构化路径。  
- 不在本 Task 中强制引入新的 workflow 框架（如 LangGraph）作为前置依赖；  
  - 该部分可在后续专门 ADR/Task 中考虑。

---

## 2. 里程碑与任务拆分

### M1: 设计与实现 LLMClient

- [ ] M1-1 定义基础接口与配置：

  ```python
  class LLMClient:
      def __init__(self, provider: str = "kimi"): ...

      def call(
          self,
          prompt: str,
          model: str,
          max_tokens: int = 16000,
          temperature: float = 0.7,
      ) -> str:
          ...
  ```

- [ ] M1-2 支持至少 Kimi / OpenAI 两种 provider：
  - 从环境变量读取对应的 `API_KEY` / `BASE_URL` / 默认模型名；  
  - 以最小依赖（requests 或官方 SDK）实现；  
  - 统一错误处理与超时策略（例如：超时重试一次、记录错误日志）。

- [ ] M1-3 日志与诊断：
  - 使用 `logging_utils.get_logger()` 在每次 call 时记录：  
    - provider / model / 请求 ID；  
    - prompt snippet（截断到 400–800 字符）；  
    - response snippet；  
    - 错误信息与异常栈（若有）。  

### M2: SkeletonGenerator 重构

- [ ] M2-1 在 `SkeletonGenerator` 中注入 LLMClient：
  - 替换现有的 `Agent/Task/Crew/LLM` 调用为 `LLMClient.call()`；  
  - 保留 `_load_prompt` 与 `_try_parse_json` / `PlotSkeleton.from_dict` / `_validate_skeleton` 逻辑不变。

- [ ] M2-2 验证骨架生成路径：
  - 在不依赖真实 LLM 的情况下，用 Dummy client（返回固化 JSON）跑现有 `tests/test_skeleton_generator.py`；  
  - 在真实环境下，用一两个故事生成骨架，确认：  
    - 日志中有完整 prompt/response 片段；  
    - 骨架校验与 v4 guided TreeBuilder 路径行为与预期一致。

### M3: ChoicePointsGenerator 重构

- [ ] M3-1 将 `ChoicePointsGenerator.generate_choices()` 内部对 Crew 的依赖替换为 LLMClient 调用：  
  - prompt 仍由 `_build_prompt` 生成；  
  - `result_text = client.call(prompt, model=self._kimi_model_choices, ...)`；  
  - 继续使用 `_parse_result` 与 `_normalize_choice_fields`；  
  - 保持 JSON 遥测统计（`get_json_metrics`）不变。

- [ ] M3-2 错误处理与日志：
  - 对 JSON 解析错误/半残输出继续做 salvage；  
  - 对 LLM 调用异常（包括网络/配额/格式问题）记录详细日志；  
  - 对需要 fallback 的情况（退回默认 choices）在日志中显式标记，便于后续分析。

- [ ] M3-3 测试与回归：
  - 扩展 `tests/test_choices_llm_wrapper.py`：  
    - 增加模拟 LLMClient 的 fake，实现常见错误路径（空输出、半残 JSON、异常抛出）；  
    - 验证 generate_choices 总是返回结构合理的 Choice 列表且不抛异常到上层。  

### M4: RuntimeResponseGenerator 渐进重构（可选扩展）

- [ ] M4-1 为响应生成部分新增基于 LLMClient 的实现：  
  - 与骨架/选择点路径一致，记录 prompt/response 片段；  
  - 允许通过环境变量选择使用 Crew 版或 LLMClient 版响应生成。  

- [ ] M4-2 增量迁移：  
  - 在部分故事/模式下切换到 LLMClient 版响应生成，观察故事整体质量与日志情况；  
  - 保留 Crew 版作为回退路径，直到新实现稳定。

---

## 3. 依赖与协作

- 依赖 ADR：  
  - `docs/architecture/ADR-004-core-llm-refactor.md`

- 依赖 Task：  
  - `docs/tasks/TASK_STORY_STRUCTURE.md`（骨架与 guided TreeBuilder 约束）  
  - `docs/tasks/TASK_CHOICE_POINTS_QUALITY.md`（选择点 JSON 稳健性与质量指标）  
  - `docs/tasks/TASK_CHOICE_EVAL_BMAD.md`（BMAD 评估器与离线诊断）

- 依赖代码：  
  - `src/ghost_story_factory/pregenerator/skeleton_generator.py`  
  - `src/ghost_story_factory/engine/choices.py`  
  - `src/ghost_story_factory/engine/response.py`  
  - `src/ghost_story_factory/utils/logging_utils.py`

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- 存在一个可复用的 `LLMClient`，被 `SkeletonGenerator` 与 `ChoicePointsGenerator` 用于核心结构化 LLM 调用；  
- 至少有一个完整故事（例如上海或西安示例）在使用 LLMClient 路径生成时：
  - 骨架/选择点生成过程中，无无法诊断的 Crew 内部错误；  
  - 日志中可看到清晰的 prompt/response 片段；  
  - story_report/BMAD/repair 工具能利用这些信息做质量分析；  
- 核心测试（骨架/选择点/结构报告相关）全部通过，并针对 LLMClient 行为补充了必要的单元测试；  
- 相关文档（ADR-004 / 本 Task / STORY_PIPELINE_V4）已更新，明确记录新旧路径的关系与迁移策略。  

