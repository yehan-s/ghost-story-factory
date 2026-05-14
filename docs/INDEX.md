# 文档索引

**项目版本**:v2.0.0(VN 沙盒播放器)
**最后更新**:2026-05-14

---

## 🚀 上手

| 文档 | 用途 |
|------|------|
| [../README.md](../README.md) | 项目主入口,玩法/控制/剧情结构/装包说明 |
| [SCRIPTING.md](SCRIPTING.md) | 想自己写剧本?数据形态 + 13 项 audit 速查 + 11 项 checklist |
| [../CLAUDE.md](../CLAUDE.md) | 项目级 Claude Code 配置(沙盒第一公理 + 开发任务流程) |

---

## 🧠 架构决策(ADR)

位于 `docs/architecture/`。

### LLM 流水线 ADR(已归档到 `legacy/llm-pipeline` 分支)

| 文档 | 状态 | 说明 |
|------|------|------|
| [ADR-001-plot-skeleton-pipeline.md](architecture/ADR-001-plot-skeleton-pipeline.md) | 🔴 Superseded by ADR-012 | 采用「骨架优先」的新故事生成流水线 |
| [ADR-002-v4-default-pipeline.md](architecture/ADR-002-v4-default-pipeline.md) | 🔴 Superseded by ADR-012 | v4 骨架流水线升级为默认生成路径 |
| [ADR-003-v4-workflow-staging-and-agents.md](architecture/ADR-003-v4-workflow-staging-and-agents.md) | 🔴 Superseded by ADR-012 | v4 分阶段入口与 Agent 编排收敛 |
| [ADR-004-core-llm-refactor.md](architecture/ADR-004-core-llm-refactor.md) | 🔴 Superseded by ADR-012 | 核心结构化 LLM 调用从 Crew 重构为 LLMClient |
| [ADR-005-langgraph-agent-orchestration.md](architecture/ADR-005-langgraph-agent-orchestration.md) | 🔴 Superseded by ADR-012 | 用 LangGraph 收敛 Agent 编排 |
| [ADR-006-response-llmclient-and-guided-approx-merge-scope.md](architecture/ADR-006-response-llmclient-and-guided-approx-merge-scope.md) | 🔴 Superseded by ADR-012 | 响应生成走 LLMClient + guided 分桶 |

### 当前主线 ADR(运行时契约,`main` 上有效)

| 文档 | 状态 | 说明 |
|------|------|------|
| [ADR-007-state-contract.md](architecture/ADR-007-state-contract.md) | ✅ Accepted | 状态空间契约与 Flag 命名规范 |
| [ADR-008-reaction-mechanism.md](architecture/ADR-008-reaction-mechanism.md) | ✅ Accepted | 戏剧化反应机制 + 跨周目认知继承契约 |
| [ADR-009-linmou-arc-canon.md](architecture/ADR-009-linmou-arc-canon.md) | ✅ Accepted | linmou_1985 角色周目契约(Act 2/3 sandbox debt 在偿) |
| [ADR-010-sandbox-topology-contract.md](architecture/ADR-010-sandbox-topology-contract.md) | ✅ Accepted | 沙盒拓扑契约 — 这是沙盒不是死剧本(第一公理) |
| [ADR-011-persona-inertia.md](architecture/ADR-011-persona-inertia.md) | ✅ Accepted | 人格惯性 ending_seen.last 协议(Pass 25/26) |
| [ADR-012-pivot-to-player.md](architecture/ADR-012-pivot-to-player.md) | ✅ Accepted | **项目转型为 VN 沙盒播放器,LLM 流水线归档**(2026-05-14) |

---

## 📌 任务文档(Pass 索引)

位于 `docs/tasks/`。按 Pass 号粗略排序。

### 项目级
| 文档 | 说明 |
|------|------|
| [TASK_PROJECT_PIVOT_TO_PLAYER.md](tasks/TASK_PROJECT_PIVOT_TO_PLAYER.md) | **项目转型计划**(配 ADR-012) |
| [TASK_PROJECT_SYNC_WORKFLOW.md](tasks/TASK_PROJECT_SYNC_WORKFLOW.md) | 项目同步工作流 |
| [TASK_NEXT_VN_SANDBOX_GOALS.md](tasks/TASK_NEXT_VN_SANDBOX_GOALS.md) | 下一阶段目标 |
| [TASK_V4_GAMETREE_ALIGNMENT.md](tasks/TASK_V4_GAMETREE_ALIGNMENT.md) | v4 生成器对齐 GameTree v1 |
| [TASK_V7_AUDIT_DEBT_CLEANUP.md](tasks/TASK_V7_AUDIT_DEBT_CLEANUP.md) | v7 审计 debt 清理 |

### 剧本 Pass(Pass 1–9)
| Pass | 文档 |
|------|------|
| Pass 1 | [TASK_SCRIPT_SANDBOX_PASS1.md](tasks/TASK_SCRIPT_SANDBOX_PASS1.md) — 沙盒化深层迭代 |
| Pass 2 | [TASK_SCRIPT_SANDBOX_PASS2.md](tasks/TASK_SCRIPT_SANDBOX_PASS2.md) — 人物弧线深挖 |
| Pass 3 | [TASK_SCRIPT_SANDBOX_PASS3.md](tasks/TASK_SCRIPT_SANDBOX_PASS3.md) — 群像深挖 |
| Pass 4 | [TASK_SCRIPT_PROTAGONIST_UX_PASS4.md](tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md) — 主角体验与 VN 演出 |
| Pass 5 | [TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md](tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md) — 行为反馈与功能 NPC 人格化 |
| Pass 6 | [TASK_SCRIPT_BEHAVIOR_FEEDBACK_PASS6.md](tasks/TASK_SCRIPT_BEHAVIOR_FEEDBACK_PASS6.md) — 行为反馈闭环 |
| Pass 7 | [TASK_VN_PRESENTATION_CONTRACT_PASS7.md](tasks/TASK_VN_PRESENTATION_CONTRACT_PASS7.md) — VN 演出契约 |
| Pass 8 | [TASK_SCRIPT_NPC_ACCOUNTABILITY_PASS8.md](tasks/TASK_SCRIPT_NPC_ACCOUNTABILITY_PASS8.md) — NPC 账本制 |
| Pass 9 | [TASK_SCRIPT_DEPTH_BREADTH_PASS9.md](tasks/TASK_SCRIPT_DEPTH_BREADTH_PASS9.md) — 深度与广度补强 |

### 运行时 Pass(Pass 10–16)
| Pass | 文档 |
|------|------|
| Pass 10 | [TASK_VN_PRESENTATION_RUNTIME_PASS10.md](tasks/TASK_VN_PRESENTATION_RUNTIME_PASS10.md) — VN 演出契约进入运行时 |
| Pass 11 | [TASK_CHOICE_AFFORDANCE_PASS11.md](tasks/TASK_CHOICE_AFFORDANCE_PASS11.md) — 选择意图与风险提示 |
| Pass 12 | [TASK_VN_SANDBOX_IMPROVEMENT_PLAN_PASS12.md](tasks/TASK_VN_SANDBOX_IMPROVEMENT_PLAN_PASS12.md) — VN 沙盒体验改进总方案 |
| Pass 13 | [TASK_BEHAVIOR_PROFILE_PASS13.md](tasks/TASK_BEHAVIOR_PROFILE_PASS13.md) — 选择后反馈与行为画像 |
| Pass 14 | [TASK_TUI_EXPERIENCE_PASS14.md](tasks/TASK_TUI_EXPERIENCE_PASS14.md) — TUI 体验收束 |
| Pass 15 | [TASK_TUI_SCENE_VIEW_PASS15.md](tasks/TASK_TUI_SCENE_VIEW_PASS15.md) — TUI 场景视图 |
| Pass 16 | [TASK_TUI_PRESENTER_BOUNDARY_PASS16.md](tasks/TASK_TUI_PRESENTER_BOUNDARY_PASS16.md) — TUI 表达层边界 |

### 剧本契约 Pass(Pass 17–26)
| Pass | 文档 |
|------|------|
| Pass 17 | [TASK_SCRIPT_ROOT_CAUSE_PASS17.md](tasks/TASK_SCRIPT_ROOT_CAUSE_PASS17.md) — 剧本病根深改 |
| Pass 18 | [TASK_SCRIPT_THIN_NODES_PASS18.md](tasks/TASK_SCRIPT_THIN_NODES_PASS18.md) — 薄节点压缩 |
| Pass 19 | [TASK_SCRIPT_PROTAGONIST_LEAK_PASS19.md](tasks/TASK_SCRIPT_PROTAGONIST_LEAK_PASS19.md) — G-273 主角身份泄漏清扫 |
| Pass 20 | [TASK_SCRIPT_REACTION_PROFILE_PASS20.md](tasks/TASK_SCRIPT_REACTION_PROFILE_PASS20.md) — 跨周目联动 + 行为画像反喂 |
| Pass 21 | [TASK_LINMOU_SANDBOX_PASS21.md](tasks/TASK_LINMOU_SANDBOX_PASS21.md) — linmou Act 1 沙盒骨架 |
| Pass 22 | [TASK_AUDIT_SEMANTIC_PASS22.md](tasks/TASK_AUDIT_SEMANTIC_PASS22.md) — audit 语义化三件套 |
| Pass 23 | [TASK_SCRIPT_CROSS_RUN_FINALE_PASS23.md](tasks/TASK_SCRIPT_CROSS_RUN_FINALE_PASS23.md) — 主结局跨周目反咬 |
| Pass 24 | [TASK_LINMOU_FINALE_REACTIONS_PASS24.md](tasks/TASK_LINMOU_FINALE_REACTIONS_PASS24.md) — linmou ending 跨周目反咬 |
| Pass 25 | [TASK_PERSONA_INERTIA_PASS25.md](tasks/TASK_PERSONA_INERTIA_PASS25.md) — 人格惯性 `.last` 协议 |
| Pass 26 | [TASK_PERSONA_INERTIA_PASS26.md](tasks/TASK_PERSONA_INERTIA_PASS26.md) — 人格惯性 debt 清零 + 阻断升级 |

---

## 🎭 评审报告

位于 `docs/team-reviews/`,见 [INDEX.md](team-reviews/INDEX.md)。

---

## 🔍 找历史代码 / 文档

LLM 流水线时代的代码、ADR-001~006 的实施细节、旧 README/CHANGELOG/QUICK_START 等
都冻结在 [`legacy/llm-pipeline`](https://github.com/yehan-s/ghost-story-factory/tree/legacy/llm-pipeline) 分支,
含 [LEGACY.md](https://github.com/yehan-s/ghost-story-factory/blob/legacy/llm-pipeline/LEGACY.md) 说明。
