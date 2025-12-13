# ADR-005: 用 LangGraph 收敛 Agent 编排，保留 LLMClient 与 v4 骨架主路径

> **✅ 文档状态**: ADR-006 已完成，本 ADR M1-M2 已完成。
> **前置条件**: ✅ ADR-004 M1-M4 完成 + ✅ ADR-006 代码已实现

- 状态: **Accepted** (M1-M2 完成, 2025-12-13)
- 日期: 2025-11-20
- 作者: yehan（由 Codex 协助起草）
- 关联: ADR-001/002（v4 骨架与默认流水线）、ADR-003（工作流分阶段 & Agent 编排收敛）、ADR-004（核心 LLM 重构为 LLMClient）

## 1. 背景与问题

1) CrewAI 路径在核心结构化调用上仍有黑盒行为：  
   - 403/格式化异常时拿不到原始报文，影响诊断与修复。  
   - Agent/Crew 的调用链难以在节点级别挂钩遥测（prompt/response/raw JSON）。

2) v4 流水线已经骨架化（ADR-001/002），工作流分阶段也在推进（ADR-003），但 Agent 编排仍割裂：  
   - Choice/Response 等“导演层”上下文难以共享。  
   - 无法在运行时精确观测每个节点的 prompt/response、fallback、修复情况。

3) 需求：在保持多 Agent 角色分工的前提下，引入一个可观测、可控的编排框架，优先满足结构化 JSON 稳定性，并能落地节点级遥测。

## 2. 决策

引入 LangGraph 作为编排层，替代 CrewAI 在“核心结构化生成链路”上的 orchestrator，但坚持：

- **LLMClient 仍是唯一的 LLM I/O 通道**（见 ADR-004）；LangGraph 只负责节点编排与状态传递，不直接包 HTTP。  
- **v4 骨架主路径不变**（Stage A/B/C/D 仍按 ADR-001/002）；LangGraph 负责把各 Agent 的调用串成可观测的图。  
- **多 Agent 分工保留**：Doc/Lore、Skeleton、Choice、Response 等职责不被合并成“大超 Agent”，只是换成 LangGraph Node。  
- **节点级遥测必选**：每个 LangGraph 节点必须记录 prompt snippet、raw response、解析/修复路径、故障类型，供日志/诊断使用。  
- **逐步迁移**：先以旁路方式落地一条 LangGraph 流水线，与现有 CLI 并存；验证后再考虑切为默认。

## 3. 范围与非目标

### 范围（要做）
- 用 LangGraph 定义一个最小可运行图：Docs -> Skeleton -> Tree (Choice/Response) -> Report/DB。  
- Graph 内部节点调用仍用现有模块（SkeletonGenerator、ChoicePointsGenerator、RuntimeResponseGenerator），但通过统一的上下文传递导演信息。  
- 增加节点级遥测/日志：包括请求 ID、provider/model、prompt/response 片段、解析/修复结果、错误分类。  
- 提供禁用开关：默认仍走现有 pipeline，开发/CI 可通过 env 切到 LangGraph 路径。

### 非目标（本 ADR 不做）
- 不改 DB schema / 对话树 JSON 结构。  
- 不移除现有 CLI；不强行一次性切换为默认。  
- 不引入新的 LLM provider；仍以 Kimi/Kimi-coding/OpenAI（通过 LLMClient）为主。  
- 不把多 Agent 合并为单一 Agent。

## 4. 方案概要

### 4.1 Graph 拆分（初版）
- Node: `StageDocs`（可复用现有文档生成或直接加载 deliverables）。  
- Node: `StageSkeleton`（SkeletonGenerator + LLMClient，记录 raw JSON）。  
- Node: `StageTreeChoice`（ChoicePointsGenerator），输入导演上下文，输出 choices JSON。  
- Node: `StageTreeResponse`（RuntimeResponseGenerator），与 Choice 节点共享导演上下文。  
- Node: `StageReport`（story_report + diagnostics），决定是否接受/告警。  
- 可选并行/回退：在 Graph 中显式建分支/回退逻辑，而不是散落的 `os.environ` 魔法。

### 4.2 状态与上下文
- 全局 Context（运行一轮故事）：city/title/synopsis/skeleton/导演上下文。  
- 节点局部 Context：当前 beat + game state + 最近 N 步 summary。  
- 导演上下文包含：recent_choices / recent_responses / recent_beats（与 ADR-003 指定一致）。

### 4.3 遥测
- 每个节点输出结构化日志：`request_id / provider / model / prompt_len / response_len / error_kind`。  
- 对 JSON 节点（skeleton/choices）：记录一次成功/修复/salvage/失败计数，写入 diagnostics。  
- 把 diagnostics 写入 `logs/full_generation_*.log`，可选写入 story metadata。

### 4.4 开关与兼容
- 新增 env：`USE_LANGGRAPH_PIPELINE=1` 时启用 LangGraph 路径；默认保留现有路径。  
- CLI 保持不变；后续可加 `--engine langgraph` 选项。  
- 现有 LLMClient 配置、prompt 模板保持可复用。

## 5. 迁移计划

- **M0（当前）**：ADR 草案（本文件）。  
- **M1**：在分支实现最小 Graph（Docs->Skeleton->Tree->Report），不移除旧路径。  
- **M2**：接入导演上下文共享，补充节点级遥测；对齐 `TASK_V4_WORKFLOW_STAGING_AND_AGENTS` 目标。  
- **M3**：在至少 1 条完整故事上跑通，诊断报告可用；评估 JSON 稳定性与重复度指标。  
- **M4**：评估切换为默认的条件，保留原 pipeline 作为 `USE_LANGGRAPH_PIPELINE=0` 回退。

## 6. 风险与缓解

- **引入新依赖**：LangGraph 体积/兼容性风险 —— 仅在开发/CI 路径启用，保留旧路径回滚。  
- **调试复杂度**：Graph 节点过多 —— 初版控制在必要节点，避免无谓分裂。  
- **性能**：Graph 本身开销 —— LangGraph 主要做编排，LLM 调用仍占主导，预计影响可忽略。  
- **团队习惯迁移**：CrewAI 习惯转 LangGraph —— 提供最小示例与 CLI 开关，逐步迁移。

## 7. 回滚策略

- 保留现有 Crew/手写 orchestrator 路径为默认，LangGraph 路径可一键关闭（`USE_LANGGRAPH_PIPELINE=0`）。  
- 如出现严重问题，删除新入口，保留本 ADR 记录，待问题解决后再尝试。  
