# ADR-012: 项目转型为 VN 沙盒播放器,LLM 流水线归档

## Status
Accepted

## Date
2026-05-14

## Context

项目 v0.x–v1.x 时期(2025-10 到 2025-12)的核心是
**AI 自动生成 VN 剧本**:`SkeletonGenerator` 起骨架 → `TreeBuilder` 扩对话树 →
`ChoicePointsGenerator` 出选项 → `RuntimeResponseGenerator` 出回应,
全链路用 CrewAI / LangGraph / LLMClient(ADR-001 ~ ADR-006)。

但到 v7 阶段(2026-05),实际剧本生产方式已**彻底转向**:

- **当前剧本工作流**:手写 9 个 `_fragment_v7_*.json` → `tools/merge_fragments.py`(1246 行)
  → `stories/hangzhou_yebanbaoan/tree.json`(162 节点 / 12 种结局)
- **当前运行时**:`play_tui.py` → `v7/tui_player`(textual TUI)→ `v5/player` + `runtime/contracts`
- **play 链路第三方依赖**:**只有 `textual`**。无 LLM、无 crewai、无 langgraph、无 langchain、无 pydantic 调用
- **pregenerator / engine / database / orchestration / ui / utils 整套**:半年没人调用,但还占着 pyproject 重依赖

这意味着项目**对外形象与实际能力脱节**:
- 包描述还是「AI 灵异故事生成助手」
- `pip install` 装 100+ MB 的 LLM 重依赖,朋友玩游戏完全用不到
- ADR-001~006 描述的代码在 main 上仍占目录,但无人维护

转折点是 2026-05-14 与用户的对话:用户希望"朋友打开终端就玩",
但实际链路要装 crewai 才能装上整个包,这是"为不存在的需求设计"的最纯反例。

## Decision

**main 分支转型为「VN 沙盒播放器,自带《杭州夜班保安》剧本」**。
LLM 生成流水线整套(代码 + ADR + 依赖)从 main 移除,
冻结到 [`legacy/llm-pipeline`](https://github.com/yehan-s/ghost-story-factory/tree/legacy/llm-pipeline) 分支永久存档。

### 具体动作(已完成)

| 阶段 | 内容 | 产出 |
|---|---|---|
| **Step 0** | 建 `legacy/llm-pipeline` 分支冻结存档,含 `LEGACY.md` | commit `d7ff176` |
| **Step 1** | main 删 21036 行死代码 + pyproject 重依赖瘦身 + version 2.0.0 | PR #64(`+205 / -21036`) |
| **Step 2** | README 从 739 行收敛到 139 行 + 新增 `docs/SCRIPTING.md`(356 行) | PR #65(`+434 / -678`) |
| **Step 3** | **本 ADR + ADR-001~006 标 Superseded** | 本 PR |
| **Step 4** | PyInstaller release 出三平台 binary | 可选,未启动 |

### main 上保留的 src 目录

```text
src/ghost_story_factory/
├── v5/         玩家状态 + 派生量(meets / effects / behavior_profile)
├── v7/         全屏 TUI 播放器(textual)
└── runtime/    GameTree 契约(RequirementEvaluator / EffectApplier / EndingResolver)
```

### main 上保留的依赖

```toml
dependencies = [
    "textual>=8.0",
    "rich>=13.7.0",
]
```

### main 上保留的入口

```toml
[project.scripts]
ghost-story-tui = "ghost_story_factory.v7.tui_player:main"
```

### legacy 分支上保留的(冻结、不再维护)

- `src/ghost_story_factory/{pregenerator,engine,database,orchestration,ui,utils}/`
- 重依赖:`crewai / langchain-* / langgraph / pydantic-heavy`
- 13 个废 `[project.scripts]`(set-city / gen-* / ghost-story-play)
- 顶层 `play_game_full.py / play_game_pregenerated.py / generate_full_story.py`
- LLM 时代的测试与工具(`tests/test_skeleton_*.py` 等 17 个 + `tools/generate_mvp.py` 等 6 个)
- ADR-001 ~ ADR-006(本 PR 标 Superseded)

## Alternatives Considered

### Option A:保留 LLM 流水线作为可选 extras
```toml
[project.optional-dependencies]
generate = ["crewai", "langchain-*", "langgraph"]
```

- **Pros**:朋友 `pip install` 默认轻量,需要生成的人 `pip install .[generate]`
- **Why rejected**:
  1. LLM 流水线半年没人调用,本身是死代码,不是"可选功能"
  2. 留着会引诱未来维护(导入 broken / 测试挂)
  3. pyproject 复杂度上升,新人接手要先解释"这套你不要用"
  4. 是"为不存在的需求设计"——典型 over-engineering

### Option B:完全删除,不要 legacy 分支
- **Pros**:仓库最干净,git 历史就够了
- **Why rejected**:
  1. git 历史不够显式,翻起来要 git log + grep
  2. 长期分支是"我知道这里有,但不在主线"的明确信号
  3. 万一未来想做"半自动剧本工具链",legacy 分支是现成脚手架
  4. 安全网成本是 0(GitHub 不收钱 + 不污染 main)

### Option C:重写为 Node/TypeScript(走 npm 路径)
- **Pros**:`npx ghost-story` 朋友最方便,前端开发者基本都有 Node
- **Why rejected**:
  1. 需要重写 `player.py`(1000+ 行)+ `tui_player.py`(900+ 行)成 TypeScript + Ink
  2. 工作量 1-2 周,且需要重新通过 13 项 audit
  3. 用户没要 npm 化,只要"朋友能玩"——PyInstaller 单文件 release 同样能做到零环境
  4. 不解决根本问题(项目主线还该不该带 LLM 流水线)

### Option D:不转型,保持现状
- **Pros**:不动现有结构
- **Why rejected**:
  1. 死代码继续腐烂,新人 onboard 看到 pregenerator/ 会以为还在用
  2. wheel 体积大、装包慢、对不写 LLM 的用户(99%)是纯成本
  3. README / pyproject description 与实际能力脱节,对外不诚实

## Consequences

### Positive

- **包体积**:pyproject 依赖从 8 个(含 crewai/langchain-*/langgraph)瘦到 2 个(textual/rich)
- **wheel 大小**:LLM 流水线代码移除后预估减少 80%+
- **对外形象一致**:README + package description 真实反映"VN 播放器自带剧本",不再吹 AI
- **新人 onboard 路径清晰**:`docs/SCRIPTING.md`(356 行 + 11 项 checklist + 13 项 audit 速查)直接告诉作者怎么写剧本
- **legacy 分支无成本永久保留**:历史代码 / 方法论 / git blame 都还在,可随时复活
- **Step 3 可行**:PyInstaller 单文件 release 在依赖瘦身后才合理(否则 300MB+ binary 无人下载)

### Negative & Mitigation

| Negative | Mitigation |
|---|---|
| ADR-001~006 描述的代码不在 main → 新人读 ADR 找不到对应代码 | 本 PR 给 6 个 ADR 顶部加统一 "Superseded by ADR-012" 警告,指向 legacy 分支 |
| 现有玩家从源码运行时,装包路径处理未完成 → `pipx install` 后必须 cd 仓库才能跑 | README 明确说明已知限制,Step 4 PyInstaller release 解决 |
| 失去 LLM 流水线意味着新剧本必须人工写 | 这本来就是 v7 阶段已经发生的事实(9 个 fragment 都是手写),ADR 只是承认现状 |
| 3 个测试在 main 上 pre-existing 失败(测试与剧本不同步) | 与本 ADR 无关,留作后续修复;PR #64 已在描述里明确标注 |

## Migration / Rollout

```text
2026-05-14 12:00  Step 0 ── legacy/llm-pipeline 分支冻结(commit d7ff176)
2026-05-14 13:00  Step 1 ── PR #64 合并(main 瘦身 -21036 / +205)
2026-05-14 14:00  Step 2 ── PR #65 合并(README + SCRIPTING)
2026-05-14 15:00  Step 3 ── 本 PR(ADR-012 + ADR-001~006 标 Superseded)← 当前节点
后续(可选) Step 4 ── PyInstaller release 三平台 binary
```

## References

- 转型计划:[docs/tasks/TASK_PROJECT_PIVOT_TO_PLAYER.md](../tasks/TASK_PROJECT_PIVOT_TO_PLAYER.md)
- 安全网分支:[`legacy/llm-pipeline`](https://github.com/yehan-s/ghost-story-factory/tree/legacy/llm-pipeline)
- legacy 分支根的 [`LEGACY.md`](https://github.com/yehan-s/ghost-story-factory/blob/legacy/llm-pipeline/LEGACY.md)
- PR #63(转型计划文档):https://github.com/yehan-s/ghost-story-factory/pull/63
- PR #64(Step 1 瘦身):https://github.com/yehan-s/ghost-story-factory/pull/64
- PR #65(Step 2 文档):https://github.com/yehan-s/ghost-story-factory/pull/65

## 与其他 ADR 的关系

| ADR | 关系 |
|---|---|
| ADR-001 ~ ADR-006 | **本 ADR Supersedes 它们**(描述的代码在 legacy 分支) |
| ADR-007(状态契约) | 仍在 main 上有效 — `v5/player` 实现 State + meets/effects |
| ADR-008(反应机制) | 仍在 main 上有效 — `runtime/contracts` 实现 |
| ADR-009(linmou 周目) | 仍在 main 上有效 — `_fragment_v7_linmou_1985.json` 实现,审计 `tools/audit_paths_linmou.py` |
| ADR-010(沙盒第一公理) | 仍在 main 上有效 — 这是 v7 的拓扑契约,跟本 ADR 互补 |
| ADR-011(人格惯性) | 仍在 main 上有效 — `runtime/contracts._meets_ending_seen` 实现 |
