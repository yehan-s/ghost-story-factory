# TASK: LangGraph 接管 Agent 编排（保留 LLMClient + v4 骨架）

> **⚠️ 任务状态**: 本任务为计划草案，待 ADR-006 (Response LLMClient) 稳定后再启动实施。
> **前置条件**: ADR-004/006 代码稳定运行，节点级遥测可用。

版本: v0.1
状态: 草案（待 ADR-006 稳定后启动）
关联 ADR:
- `docs/architecture/ADR-005-langgraph-agent-orchestration.md`
- `docs/architecture/ADR-003-v4-workflow-staging-and-agents.md`
- `docs/architecture/ADR-004-core-llm-refactor.md`  

---

## 0. 背景

CrewAI 在核心结构化调用上存在黑盒与报文不可见问题（403/格式化异常拿不到原始响应），而 v4 骨架 + LLMClient 已是默认主路径。需要一个可观测、可控的编排层把现有多 Agent 职责（Docs/Skeleton/Choice/Response/Report）串成图，同时保留 LLMClient 为唯一 I/O。

---

## 1. 目标 / 非目标

### 1.1 目标
- 用 LangGraph 编排现有 Agent 职责（Docs、Skeleton、Choice、Response、Report），**不合并角色**，仅换调度壳。  
- 统一使用 LLMClient（Kimi/Kimi-coding/OpenAI），LangGraph 不直接发 HTTP。  
- 节点级遥测：prompt/response 片段、请求 ID、错误分类、重试/修复路径；输出工作流诊断。  
- 提供开关 `USE_LANGGRAPH_PIPELINE=1`（默认 0），旧 CLI/流程保持可用。  

### 1.2 非目标
- 不改 DB schema / 对话树 JSON 结构。  
- 不一次性切换默认；先旁路验证。  
- 不引入新的 LLM provider；沿用现有 env（`KIMI_API_BASE`/`KIMI_MODEL` 等）。  

---

## 2. 里程碑

- **M1 最小图**：LangGraph 定义 Docs→Skeleton→Tree(Choice+Response)→Report，复用现有模块；开关控制，旧路径保留。  
- **M2 导演上下文 & 遥测**：recent_choices/responses/beats 贯穿 Choice/Response 节点；节点级遥测写入日志/metadata；JSON 稳定性指标收集。  
- **M3 验证**：至少一条完整故事（固定城市示例）跑通 LangGraph 路径，产出工作流诊断（JSON 稳定性、重复度、安全闸触发）；与旧路径对比。  
- **M4 切换评估**：制定“切默认”的条件（质量/稳定性阈值），保留 `USE_LANGGRAPH_PIPELINE=0` 回退。  

---

## 3. 入口与配置

- Env 开关：`USE_LANGGRAPH_PIPELINE=1` 启用 LangGraph；默认 0 使用现有 pipeline。  
- 可选 CLI 参数（后续）：`--engine langgraph`。  
- LLM：统一走 LLMClient，沿用 env（`KIMI_API_BASE=https://api.kimi.com/coding/v1`, `KIMI_MODEL=kimi-for-coding` 等）。  

---

## 4. 测试计划

- 单元：每个 LangGraph 节点可调用，遥测结构存在（含 prompt/response 片段、错误分类）。  
- 集成：完整故事生成通过（选固定城市/示例），日志有诊断输出；开关关闭时行为与旧路径等价。  
- 回归：对比 JSON 稳定性/重复度/默认兜底占比，与旧 pipeline 基线。  

---

## 5. 风险与回滚

- 新依赖/心智负担：保持旁路，出现异常可一键关闭开关。  
- 节点并发/状态错误：保留旧流程，必要时删除 LangGraph 入口，日志用于诊断。  
- 若节点遥测或解析不稳定，先修节点或降级到旧路径再迭代。  
