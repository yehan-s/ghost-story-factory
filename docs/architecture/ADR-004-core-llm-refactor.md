# ADR-004: 核心结构化 LLM 调用从 Crew 重构为轻量客户端

- 状态: Draft  
- 日期: 2025-11-17  
- 作者: yehan（由 Codex 协助起草）  

---

## 1. 背景

当前 Ghost Story Factory 在多个关键路径上依赖 CrewAI 封装的 LLM 调用：

- 骨架生成：`SkeletonGenerator` 使用 `Agent/Task/Crew/LLM` 调用 Kimi 生成 `PlotSkeleton` JSON；  
- 选择点生成：`ChoicePointsGenerator.generate_choices()` 通过 Crew 调用 Kimi 输出 JSON 结构的 `choices`；  
- 响应生成：`RuntimeResponseGenerator.generate_response()` 使用类似模式生成叙事文本。

在「文案型」场景（完整故事、世界书、GDD 等）这一套 agent/crew 抽象尚可接受，但在**强结构化 JSON** 场景下暴露出一组难以绕过的问题：

1. **上游黑盒异常难以诊断**  
   - 典型日志：`Invalid format specifier ' true' for object of type 'str'`。  
   - 该错误发生在 Crew/Kimi 内部对输出调用 `format` 时，**在返回任何 result/raw_output 之前就抛出**：  
     - 我们拿不到原始 response body；  
     - `_extract_llm_text` 只能看到异常对象本身，没有可供记录的「原始报文」。  
   - 结果：无法从本项目代码层面复现/诊断，只能通过「禁用本轮 LLM + 默认选项兜底」的方式减轻影响。

2. **关键路径对 JSON 质量要求极高**  
   - `PlotSkeleton` / `choices` / 关键响应等结构，不仅要 JSON 合法，还要与骨架/状态严格对齐；  
   - 这些调用需要：
     - 对 request/response 有完整可控的日志；  
     - 明确的重试策略与 salvage 逻辑；  
     - 可与 BMAD、story_report、离线 repair 工具联动做 root-cause 诊断。  
   - 将这些责任交给一个「不透明的 Agent/Crew 流水线」，本身就与 v4「骨架优先、结构可控」的目标冲突。

3. **框架抽象与项目需求错位**  
   - Crew 更适合做「多 Agent 协作 + 长文本文案」这类问题：  
     - 例如完整故事生成、世界观构建、GDD 等。  
   - 但对我们来说，最关键的一条是「稳健的结构化引擎」，而不是「自带复杂 orchestrator 的 Agent 框架」。  
   - 在骨架/选择点/响应这几个环节，Crew 带来的复杂性与黑盒性已经超过收益。

综上：**继续在这些核心路径上堆 Crew 级别的抽象，已经阻碍了结构化流水线的演进和质量问题的诊断**。需要一个专门的 ADR 来收敛下一步框架方向。

---

## 2. 决策

本 ADR 做出以下决策：

1. **在核心结构化路径上，从 Crew 重构为「轻量 LLM 客户端 + 纯 Python 函数」**  
   - 涉及路径：
     - `SkeletonGenerator.generate(...) -> PlotSkeleton`；  
     - `ChoicePointsGenerator.generate_choices(...) -> List[Choice]`；  
     - `RuntimeResponseGenerator.generate_response(...)` 中与结构强相关的主线响应生成。  
   - 新模式：
     - 引入一个极薄的 LLM 客户端（HTTP 或官方 SDK，单一职责：`prompt -> str`）；  
     - 上述生成器改为直接调用该客户端，并在本项目内处理 JSON 解析、salvage、BMAD 评估等逻辑。

2. **Crew 仍可在「文档/素材生成」层使用，但与核心引擎解耦**  
   - 如 `generate_full_story.py` 中的多 Agent 流程，可继续使用 Crew 提供的工具；  
   - 但骨架/选择点/响应这些强结构化环节不得再在新路径中依赖 Crew 的 Agent/Crew/LangChain 封装。

3. **新实现优先在独立分支上演进，不立即替换现有路径**  
   - 使用已创建的 `feat/langgraph-core-refactor`（或后续命名）分支：  
     - 先在该分支中实现「直连 LLM + 轻量 orchestrator」的核心路径；  
     - 在至少一个完整故事（例如上海或西安示例）上验证：  
       - story_report 全链路可用；  
       - LLM 调用日志中有完整的 request/response 片段；  
       - 不再出现 Crew 内部 format 崩溃导致的不可诊断错误。  
   - 验证通过后，再考虑：
     - 将该路径切换为 v4 的默认核心实现；  
     - 将现有 Crew 版路径保留为 legacy/兼容路径，或移除。

4. **不在本 ADR 中引入新的大型框架（如 LangGraph）作为前置依赖**  
   - LangGraph 等 workflow 框架在需要可视化状态机或复杂多 Agent 流程时可以考虑；  
   - 但本 ADR 的重点是：**简化核心引擎，恢复 request/response 的可见性与可控性**，而非再套一层新的黑盒 orchestrator。

---

## 3. 方案概要

### 3.1 轻量 LLM 客户端设计

在 `src/ghost_story_factory/utils/` 下新增一个模块（例如 `llm_client.py`），提供：

- 一个简单的同步接口：

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
        """发送请求并返回原始文本响应，同时打结构化日志。"""
```

- 特性：
  - 直接使用 HTTP 或官方 SDK（Kimi/OpenAI），不引入 Crew；  
  - 日志中记录：
    - provider / model / 请求 ID；  
    - prompt snippet（可控长度）；  
    - 响应 snippet；  
    - 错误时完整异常栈。  
  - 不做 JSON 解析，仅负责「可靠地拿回一段文本」。

### 3.2 SkeletonGenerator 重构

- 将 `SkeletonGenerator` 中对 `Agent/Task/Crew/LLM` 的依赖替换为 `LLMClient`：  
  - 保留现有 `plot-skeleton.prompt.md` 模板和 `PlotSkeleton.from_dict` 解析逻辑；  
  - 调用路径变为：

```python
client = LLMClient(provider="kimi")
result_text = client.call(prompt=prompt, model=...)
data = _try_parse_json(result_text)
skeleton = PlotSkeleton.from_dict(data)
_validate_skeleton(skeleton)
```

- 这样一来：
  - `result_text` 始终可用，能完整记录；  
  - JSON 解析与校验全部在本模块内掌控。

### 3.3 ChoicePointsGenerator 重构

- 替换当前 `Agent/Task/Crew` 调用链为 `LLMClient` 调用：  
  - 使用 `_build_prompt` 生成 prompt；  
  - `result_text = client.call(prompt, model=KIMI_MODEL_CHOICES, ...)`；  
  - 使用 `_parse_result` 和现有 salvage 逻辑解析 JSON；  
  - 继续沿用当前的 JSON 遥测计数和 default choices 兜底机制。  
- 错误处理：
  - 所有解析错误、LLM 调用异常，都能用同一套日志结构记录 prompt/output；  
  - 不再出现「内部 format 崩溃、没有返回文本」的黑盒情况。

### 3.4 RuntimeResponseGenerator 渐进重构

- 对响应生成部分，采用相同思路分阶段替换：  
  - 先保留 Crew 路径作为 fallback；  
  - 为关键路径新增基于 `LLMClient` 的实现，逐步迁移调用方。

---

## 4. 影响分析

### 4.1 正面影响

- **可观测性显著提升**  
  - 所有核心结构化调用都有 request/response 日志；  
  - 便于复现和诊断像 `Invalid format specifier` 这类上游问题（至少知道请求和响应长什么样）。

- **简化核心引擎的依赖关系**  
  - 骨架/选择点/响应不再耦合 Crew 特定的 Agent/Crew API；  
  - 流水线逻辑更接近「普通 Python 程序」，更容易维护。

- **更符合 v4 骨架优先与诊断优先的设计哲学**  
  - 核心结构决策不再受上游 orchestrator 随机行为影响；  
  - story_report / BMAD / repair 工具有完整的上下文可用。

### 4.2 负面影响 / 风险

- **短期内需要维护两套调用路径**  
  - 新分支中会存在 Crew 版与 LLMClient 版并存的情况，需要明确开关/环境变量控制；  
  - 部分测试需要补上新的调用模式。

- **需要自己处理重试与节流策略**  
  - Crew 目前在一定程度上帮我们做了调用封装；  
  - 替换后需要在 LLMClient 内部设计合理的重试和并发控制（可参考现有 `_sem` 实现）。

- **与上游 SDK 的兼容性维护回到本项目**  
  - 例如 Kimi/OpenAI 的 API 变更需要本项目跟进；  
  - 不过这也是换来可控性与透明度的代价。

---

## 5. 迁移策略与后续工作

1. 在 `feat/langgraph-core-refactor` 分支中实现 `LLMClient` 与 SkeletonGenerator 重构；  
2. 在同一分支中重构 ChoicePointsGenerator，保留现有 JSON 解析与 BMAD 流程；  
3. 在至少一个完整故事上验证新路径（包括结构报告与选择点质量）；  
4. 更新相关 Task 文档：  
   - 新增 `TASK_CORE_LLM_REFACTOR.md`（见 docs/tasks）；  
   - 在 `TASK_STORY_STRUCTURE.md` / `TASK_CHOICE_POINTS_QUALITY.md` 中引用 ADR-004 作为实现基础；  
5. 视验证结果决定是否将新路径合并进 main，并将 Crew 版路径标记为 legacy。

