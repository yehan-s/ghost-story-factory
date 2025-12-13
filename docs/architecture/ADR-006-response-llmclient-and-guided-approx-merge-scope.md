# ADR-006: 响应生成默认切换到 LLMClient + guided 模式近似合并按 depth/beat 分桶

- 状态: Accepted (代码已实现，待生产验证)
- 日期: 2025-12-13
- 作者: yehan / Codex
- 关联:
  - `docs/architecture/ADR-004-core-llm-refactor.md` (本 ADR 是 M4 的具体实施方案)
  - `docs/architecture/ADR-002-v4-default-pipeline.md`
  - `docs/architecture/ADR-003-v4-workflow-staging-and-agents.md`
  - `docs/tasks/TASK_CORE_LLM_REFACTOR.md`
- 说明: 本 ADR 完成 ADR-004 的 M4 里程碑（Response 生成迁移到 LLMClient），同时修复 guided 模式结构塌陷问题

---

## 1. 背景与问题

目前 v4 骨架流水线（PlotSkeleton + guided TreeBuilder）已经成为默认路径，但真实长跑仍然存在一组「会让系统卡死、结构塌陷、不可诊断」的问题：

1) **响应生成仍依赖 CrewAI**
- `RuntimeResponseGenerator` 仍通过 `Agent/Task/Crew` 调用 LLM。
- 这会引入：
  - 黑盒异常（例如 format specifier / 403 时拿不到原始响应）；
  - 超时不可控（调用栈深，报错上下文缺失）；
  - 无法统一写入 LLMClient 的 request/response 日志。

2) **guided 模式下的“近似状态合并”会压扁结构**
- TreeBuilder 会对同场景的状态做 `_quantize_time` 等量化后进行近似合并。
- 在 guided 模式下，这种合并会把不同 depth 的节点合并到同一个节点上：
  - 主线深度增长被吃掉；
  - 结局分布被扭曲；
  - choices/response 看起来更重复。

结论：
- 这不是“Agent 不聪明”，而是 **核心 I/O 黑盒 + 错误的数据结构（状态空间被错误折叠）**。

---

## 2. 决策

1) **响应生成默认使用 LLMClient（CrewAI 仅作为回退）**
- `RuntimeResponseGenerator.generate_response()` 默认走 LLMClient；
- 若 LLMClient 不可用（例如缺少 API Key）或显式关闭，则回退到 CrewAI；
- 若两者都不可用，则回退到本地兜底叙事（保证不崩）。

2) **响应生成的 max_tokens 下调为“符合输出目标”的范围**
- 目标输出 200-400 字（Markdown 文本），不需要 16000 tokens；
- 默认使用 `RESPONSE_MAX_TOKENS`（建议 800-1200），降低超时概率与成本；
- 允许通过环境变量覆盖。

3) **guided 模式下的近似合并引入 scope（depth/beat 分桶）**
- 仍保留近似合并能力，但必须把 depth/beat 作为分桶维度：
  - 只有相同 depth（并且相同 beat id）才允许近似合并；
  - 避免跨 depth 合并导致结构塌陷。
- legacy（v3）路径保持原行为不变。

---

## 3. 方案概要

### 3.1 LLMClient 响应路径

- 新增/使用环境变量：
  - `USE_LLMCLIENT_RESPONSE=1`（默认启用）
  - `RESPONSE_MAX_TOKENS=800`（默认值）

- 生成策略：
  - 使用现有 `_build_prompt(...)` 生成完整 prompt；
  - 可选拼接精简版 backstory（避免超大 prompt 造成慢/超时）；
  - 调用 `LLMClient.call(prompt, max_tokens=RESPONSE_MAX_TOKENS, temperature=...)`。

### 3.2 guided 近似合并 scope

- 扩展 `StateManager.register_scene_index(...)` / `find_approximate(...)`：支持 `scope: Optional[str]`。
- guided 模式调用方（TreeBuilder）传入 scope：
  - `scope = f"depth={depth}|beat={beat_id}"`
- 近似匹配时，必须 scope 完全一致才允许合并。

---

## 4. 影响与风险

### 正面影响
- 响应生成可观测：所有调用统一进入 LLMClient 日志，便于诊断。
- 超时显著下降：max_tokens 收紧，prompt 规模可控。
- 结构更稳定：guided 模式不再被近似合并压扁深度。

### 风险
- 响应输出风格可能发生变化（从 CrewAI role/backstory 方式切换为纯 prompt）。
- 禁止跨 depth 合并后，节点数可能上升。

### 缓解
- 保留开关与回退：`USE_LLMCLIENT_RESPONSE=0` 可回退到旧实现。
- 维持硬闸：`MAX_TOTAL_NODES` / `PROGRESS_PLATEAU_LIMIT` 继续保护长跑。

---

## 5. 回滚策略

- 若新响应路径出现质量问题或兼容性问题：
  - 设置 `USE_LLMCLIENT_RESPONSE=0` 回退 CrewAI。
- 若节点数上涨过快：
  - 调整 `MAX_TOTAL_NODES` / `PROGRESS_PLATEAU_LIMIT`；
  - 或在 guided scope 内进一步收紧 near-merge 的量化维度（而不是重新允许跨 depth 合并）。
