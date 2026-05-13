# Legacy Archive — LLM Pipeline Snapshot

**冻结时间**:2026-05-14
**冻结点 commit**:见本分支 `HEAD~1`(本 LEGACY.md commit 之前的最后一个 main commit)
**主分支去向**:`main` 已转型为「VN 沙盒播放器(自带《杭州夜班保安》剧本)」,
不再维护 LLM 生成流水线。

---

## 这个分支是什么

`legacy/llm-pipeline` 是项目 v3–v5 时期的**完整代码快照**,
保留以下当时仍在用、但 `main` 已经/即将删除的能力:

- **LLM 故事生成流水线**(SkeletonGenerator / TreeBuilder / ChoicePointsGenerator)
- **CrewAI + LangGraph 编排层**(ADR-003 / ADR-005)
- **动态模式游戏循环**(`engine/game_loop.py`,边玩边生成)
- **预生成模式 + SQLite 存储**(`database/`)
- **大量 CLI 命令**:`set-city` / `get-struct` / `gen-complete` / `gen-skeleton` / ...
- 重依赖:`crewai` / `langchain-*` / `langgraph` / 完整 `pydantic` 用法

对应文档(在本分支内仍有效):
- `docs/architecture/ADR-001` ~ `ADR-006`(骨架流水线 / v4 默认 / LLMClient / LangGraph)
- `docs/architecture/STORY_PIPELINE_V4.md`
- `docs/tasks/TASK_CORE_LLM_REFACTOR.md`

---

## 为什么留它

1. **历史价值**:LLM 自动生成 VN 剧本的整套尝试,从骨架到选项到回应。
   即便不再继续走,也是有方法论价值的失败/转向案例。
2. **可能回头**:未来若要做"半自动剧本工具链",这里有现成的脚手架。
3. **不污染 main**:`main` 要做激进减法、出 release 给非开发者朋友玩,
   不能背 100MB+ 重依赖。两条线分开,各得其所。

---

## 这个分支的运维规则

- **冻结**:不再接收新 PR、不再合 main。
- **不删**:永久保留。
- **如要复活**:`git checkout legacy/llm-pipeline && git checkout -b feat/revive-pipeline`,
  从这里继续。不要试图把它合回 `main`(`main` 的形态已经不兼容)。
- **安全网**:如果某天 `main` 删多了想找回某段代码,直接 `git log legacy/llm-pipeline -- 路径` 或 cherry-pick。

---

## main 的瘦身计划

具体清单见 `docs/tasks/TASK_PROJECT_PIVOT_TO_PLAYER.md`(在 `main` 分支上,
本分支不维护该文档)。
