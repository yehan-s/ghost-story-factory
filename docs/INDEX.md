# Ghost Story Factory - 文档索引

**最后更新**: 2025-10-25
**项目版本**: v3.0

---

## 📚 快速导航

### 🚀 快速开始
- [../README.md](../README.md) - **从这里开始！** 项目主文档
  - 动态模式：`python3 play_game_full.py`
  - 预生成模式：`./start_pregenerated_game.sh` / `python3 play_game_pregenerated.py`

### 📋 规格文档 (Specifications)
位于 `docs/specs/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| **[SPEC_V3.md](specs/SPEC_V3.md)** ⭐ | **架构 v3.0 完整规格** | 所有人（推荐） |
| [SPEC_TODO.md](specs/SPEC_TODO.md) | 待开发功能完整规格 | 开发者、项目管理 |
| [PREGENERATION_DESIGN.md](../docs/PREGENERATION_DESIGN.md) | 预生成系统设计 | 工程师、设计师 |
| [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md) | **命令行游戏开发路线图** | 游戏引擎开发者 |

**推荐阅读顺序**: SPEC_V3 → NEW_PIPELINE → SPEC_TODO

---

### 📖 使用指南 (Guides)
位于 `docs/guides/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [USAGE.md](guides/USAGE.md) | 详细使用说明 | 所有用户 |
| [WORKFLOW.md](guides/WORKFLOW.md) | 完整工作流程 | 内容创作者 |
| [QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md) | 命令速查卡 | 经常使用者 |
| 预生成模式：参见 [PREGENERATION_DESIGN.md](../docs/PREGENERATION_DESIGN.md) | 模式说明 | 所有用户 |

**推荐阅读顺序**: USAGE → WORKFLOW → QUICK_REFERENCE

---

### 🏗️ 架构文档 (Architecture)
位于 `docs/architecture/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 项目整体架构（v3.x 总览） | 开发者、架构师 |
| [GAME_ENGINE.md](architecture/GAME_ENGINE.md) | 游戏引擎设计 | 游戏引擎开发者 |
| [NEW_PIPELINE.md](architecture/NEW_PIPELINE.md) | **预生成流水线 v3.0 流程图谱** ⭐ | 开发者、维护者 |
| [STORY_PIPELINE_V4.md](architecture/STORY_PIPELINE_V4.md) | 故事生成流水线 v4（骨架模式草案） | 架构师、核心开发 |

**推荐阅读顺序**: ARCHITECTURE → NEW_PIPELINE → GAME_ENGINE

---

### 🔧 技术文档 (Technical)
位于 `docs/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [PROTAGONIST_CONSTRAINTS.md](PROTAGONIST_CONSTRAINTS.md) | 主角强约束机制 ⭐ | 开发者、内容创作者 |

**重要**：如果遇到主角生成错误（如使用了"保安"而非真实主角），请阅读此文档

---

### 🧠 架构决策 (ADR)
位于 `docs/architecture/`

| 文档 | 状态 | 说明 |
|------|------|------|
| [ADR-001-plot-skeleton-pipeline.md](architecture/ADR-001-plot-skeleton-pipeline.md) | Accepted | 采用「骨架优先」的新故事生成流水线 |
| [ADR-002-v4-default-pipeline.md](architecture/ADR-002-v4-default-pipeline.md) | Accepted | v4 骨架流水线升级为默认生成路径（v3 仅回退） |
| [ADR-003-v4-workflow-staging-and-agents.md](architecture/ADR-003-v4-workflow-staging-and-agents.md) | Draft | v4 分阶段入口与 Agent 编排收敛 |
| [ADR-004-core-llm-refactor.md](architecture/ADR-004-core-llm-refactor.md) | Draft | 核心结构化 LLM 调用从 Crew 重构为 LLMClient |
| [ADR-005-langgraph-agent-orchestration.md](architecture/ADR-005-langgraph-agent-orchestration.md) | Draft | 用 LangGraph 收敛 Agent 编排（保留 LLMClient 与 v4） |
| [ADR-006-response-llmclient-and-guided-approx-merge-scope.md](architecture/ADR-006-response-llmclient-and-guided-approx-merge-scope.md) | Accepted | 响应默认走 LLMClient + guided 近似合并按 depth/beat 分桶 |
| [ADR-011-persona-inertia.md](architecture/ADR-011-persona-inertia.md) | Accepted | 人格惯性 ending_seen.last 协议(Pass 25)|

------|------|
| [ADR-001-plot-skeleton-pipeline.md](architecture/ADR-001-plot-skeleton-pipeline.md) | 采用「骨架优先」的新故事生成流水线的架构决策 |

---

### 📌 任务与 Roadmap

| 文档 | 说明 |
|------|------|
| [SPEC_TODO.md](specs/SPEC_TODO.md) | 待开发功能规格与里程碑 |
| [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md) | 命令行游戏开发路线图 |
| [TASK_STORY_STRUCTURE.md](tasks/TASK_STORY_STRUCTURE.md) | 新故事结构化流水线（骨架模式）的实施任务拆解 |
| [TASK_GAMETREE_V1.md](tasks/TASK_GAMETREE_V1.md) | GameTree v1 可玩闭环与 VN/沙盒契约收敛 |
| [TASK_SCRIPT_SANDBOX_PASS1.md](tasks/TASK_SCRIPT_SANDBOX_PASS1.md) | 正式剧本沙盒化深层迭代 Pass 1 |
| [TASK_SCRIPT_SANDBOX_PASS2.md](tasks/TASK_SCRIPT_SANDBOX_PASS2.md) | 正式剧本人物弧线深挖 Pass 2 |
| [TASK_SCRIPT_SANDBOX_PASS3.md](tasks/TASK_SCRIPT_SANDBOX_PASS3.md) | 正式剧本群像深挖 Pass 3 |
| [TASK_SCRIPT_PROTAGONIST_UX_PASS4.md](tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md) | 正式剧本主角体验与 VN 演出 Pass 4 |
| [TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md](tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md) | 正式剧本行为反馈与功能 NPC 人格化 Pass 5 |
| [TASK_SCRIPT_DEPTH_BREADTH_PASS9.md](tasks/TASK_SCRIPT_DEPTH_BREADTH_PASS9.md) | 正式剧本深度与广度补强 Pass 9 |
| [TASK_SCRIPT_ROOT_CAUSE_PASS17.md](tasks/TASK_SCRIPT_ROOT_CAUSE_PASS17.md) | 正式剧本病根深改 Pass 17 |
| [TASK_SCRIPT_THIN_NODES_PASS18.md](tasks/TASK_SCRIPT_THIN_NODES_PASS18.md) | 正式剧本薄节点压缩 Pass 18 |
| [TASK_SCRIPT_PROTAGONIST_LEAK_PASS19.md](tasks/TASK_SCRIPT_PROTAGONIST_LEAK_PASS19.md) | G-273 主角身份泄漏清扫 Pass 19 |
| [TASK_SCRIPT_REACTION_PROFILE_PASS20.md](tasks/TASK_SCRIPT_REACTION_PROFILE_PASS20.md) | 跨周目联动与行为画像反喂 variants Pass 20 |
| [TASK_LINMOU_SANDBOX_PASS21.md](tasks/TASK_LINMOU_SANDBOX_PASS21.md) | linmou Act 1 沙盒骨架补齐 Pass 21 |
| [TASK_AUDIT_SEMANTIC_PASS22.md](tasks/TASK_AUDIT_SEMANTIC_PASS22.md) | audit 语义化三件套 + 行为画像不变量 Pass 22 |
| [TASK_SCRIPT_CROSS_RUN_FINALE_PASS23.md](tasks/TASK_SCRIPT_CROSS_RUN_FINALE_PASS23.md) | 主结局跨周目反咬补完 Pass 23 |
| [TASK_LINMOU_FINALE_REACTIONS_PASS24.md](tasks/TASK_LINMOU_FINALE_REACTIONS_PASS24.md) | linmou ending 跨周目反咬补完 Pass 24 |
| [TASK_PERSONA_INERTIA_PASS25.md](tasks/TASK_PERSONA_INERTIA_PASS25.md) | 人格惯性 ending_seen.last 协议 Pass 25 |
| [TASK_VN_PRESENTATION_RUNTIME_PASS10.md](tasks/TASK_VN_PRESENTATION_RUNTIME_PASS10.md) | VN 演出契约进入运行时 Pass 10 |
| [TASK_CHOICE_AFFORDANCE_PASS11.md](tasks/TASK_CHOICE_AFFORDANCE_PASS11.md) | 选择意图与风险提示 Pass 11 |
| [TASK_VN_SANDBOX_IMPROVEMENT_PLAN_PASS12.md](tasks/TASK_VN_SANDBOX_IMPROVEMENT_PLAN_PASS12.md) | VN 沙盒体验改进总方案 Pass 12 |
| [TASK_BEHAVIOR_PROFILE_PASS13.md](tasks/TASK_BEHAVIOR_PROFILE_PASS13.md) | 选择后反馈闭环与本轮行为画像 Pass 13 |
| [TASK_TUI_EXPERIENCE_PASS14.md](tasks/TASK_TUI_EXPERIENCE_PASS14.md) | TUI 体验收束与停留选项去重 Pass 14 |
| [TASK_TUI_SCENE_VIEW_PASS15.md](tasks/TASK_TUI_SCENE_VIEW_PASS15.md) | TUI 当前场景视图与过门反馈 Pass 15 |
| [TASK_TUI_PRESENTER_BOUNDARY_PASS16.md](tasks/TASK_TUI_PRESENTER_BOUNDARY_PASS16.md) | TUI 表达层边界拆分 Pass 16 |
| [TASK_NEXT_VN_SANDBOX_GOALS.md](tasks/TASK_NEXT_VN_SANDBOX_GOALS.md) | 下一阶段目标：剧本深挖与 VN 沙盒可玩闭环 |
| [TASK_V4_GAMETREE_ALIGNMENT.md](tasks/TASK_V4_GAMETREE_ALIGNMENT.md) | v4 生成器对齐 GameTree v1 沙盒拓扑 |

---

## 🎭 示例故事 (Examples)

位于 `examples/`，包含已生成的城市故事：

### hangzhou/杭州（完整示例）⭐
位于 `examples/hangzhou/`
- ✅ 候选列表: `杭州_candidates.json`
- ✅ 故事结构: `杭州_struct.json`
- ✅ Lore v1: `杭州_lore.json`
- ✅ 主角分析: `杭州_protagonist.md`
- ✅ Lore v2: `杭州_lore_v2.md`
- ✅ GDD: `杭州_GDD.md`
- ✅ 主线故事: `杭州_main_thread.md`
- ✅ 简化版: `杭州_story.md`

**故事简介**: 北高峰缆车空厢 - 特检院工程师调查午夜缆车异响

---

### wuhan/武汉（部分示例）
位于 `examples/wuhan/`
- ✅ 候选列表: `武汉_candidates.json`
- ✅ Lore v1: `武汉_lore.json`
- ✅ 故事: `武汉_story.md`
- ✅ 主角分析: `武汉_role_夜跑者.json`
- ✅ 故事结构: `武汉_struct.json`

---

### guangzhou/广州（经典故事）
位于 `examples/guangzhou/`
- ✅ 经典故事: `广州_荔湾广场_第七块玻璃.md`

**故事简介**: 荔湾广场灵异传说 - 第七块玻璃与"借光"仪式

---

### test-city/测试城（测试数据）
位于 `examples/test-city/`
- ✅ Lore v1: `测试城_lore.json`
- ✅ 主角分析: `测试城_role_保安.json`

---

## 📝 模板库 (Templates)

位于 `templates/`，包含 35 个设计模板文件。

**重要文档**:
- [templates/README.md](../templates/README.md) - 模板库总览
- [templates/00-architecture.md](../templates/00-architecture.md) - 架构总览
- [templates/00-index.md](../templates/00-index.md) - 上下文管理策略

**详细模板**: 参见 [templates/00-index.md](../templates/00-index.md)

---

## 🔍 按角色查找文档

### 👨‍💻 开发者
1. 先读 [README.md](../README.md)
2. 了解架构 [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
3. 查看规格 [SPEC_TODO.md](specs/SPEC_TODO.md)
4. 开发游戏引擎参考 [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md)

### ✍️ 内容创作者
1. 先读 [README.md](../README.md)
2. 学习使用 [USAGE.md](guides/USAGE.md)
3. 了解流程 [WORKFLOW.md](guides/WORKFLOW.md)
4. 参考示例 `examples/杭州/`

### 🎮 游戏设计师
1. 阅读templates [templates/README.md](../templates/README.md)
2. 学习设计 [templates/00-architecture.md](../templates/00-architecture.md)
3. 参考 GDD [examples/杭州/杭州_GDD.md](../examples/杭州/杭州_GDD.md)
4. 研究引擎 [GAME_ENGINE.md](architecture/GAME_ENGINE.md)

### 📊 项目管理
1. 查看规格 [SPEC_TODO.md](specs/SPEC_TODO.md)
2. 跟踪路线图 [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md)
3. 审查架构 [ARCHITECTURE.md](architecture/ARCHITECTURE.md)

---

## 🆘 常见问题

### Q: 从哪里开始？
A: 阅读项目根目录的 [README.md](../README.md)

### Q: 如何生成第一个故事？
A: 按顺序阅读：
1. [USAGE.md](guides/USAGE.md)
2. [WORKFLOW.md](guides/WORKFLOW.md)
3. 参考 `examples/杭州/` 的完整示例

### Q: 如何开发游戏引擎？
A: 按顺序阅读：
1. [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md) ⭐
2. [GAME_ENGINE.md](architecture/GAME_ENGINE.md)
3. [SPEC_TODO.md](specs/SPEC_TODO.md)

### Q: templates太多，怎么高效使用？
A: 阅读 [templates/00-index.md](../templates/00-index.md)，了解分层加载策略

---

## 📞 获取帮助

- **GitHub Issues**: 提交 Bug 或功能请求
- **文档问题**: 检查 [USAGE.md](guides/USAGE.md) 的 FAQ 章节
- **技术问题**: 参考 [ARCHITECTURE.md](architecture/ARCHITECTURE.md)

---

**最后提醒**: 所有文档都使用相对路径链接，可以在 GitHub 或本地 Markdown 阅读器中正常浏览。
