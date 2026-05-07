# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔴 第一公理:这是沙盒,不是死剧本(ADR-010)

**`hangzhou_yebanbaoan` 周目实质拓扑 = 沙盒**,不是分支剧本树。下次写剧本 / 加角色 / 改场景前,先想这条:

**沙盒原语(必须复用,不许重造)**:
- `_is_map_picker: true` hub 节点 + `landmark_map` + `connections`(地标网,非辐射)
- `_is_tool: true` + `effects.stay: true`(可反复访问的工具节点)
- `narrative_variants[].if.{deduction_resolved | foreshadow_resolved | theme_resolved | ending_seen}` 反应切档
- `reaction_contracts`(per_run / cross_run trigger_type)
- `endings_seen[story_id]: list[ending_id]` 跨周目联动(0 新字段)

**"死剧本"反模式黑名单(评审一票否决)**:
- ❌ entry → 单链 → ending(没有 picker hub)
- ❌ 地标只能从 picker 进,不能横向跳(没有 connections,只是辐射)
- ❌ 工具节点 `next` 直接跳走(应该 `stay: true`)
- ❌ NPC 反复访问 narrative 不变(没有 variants + 反应 clause)
- ❌ 加 `flags` 镜像伏笔/推论解开(违反 ADR-007/008 单一真相源)
- ❌ 加 state 字段表达"玩家见过 X"(查 `endings_seen`/`foreshadows_seen`/`deductions_resolved` 即可)

**新可玩角色"沙盒最小骨架"**(少于这个直接打回):
1. ≥ 1 个 `_is_map_picker` hub
2. ≥ 4 地标,每个 ≥ 1 条 `connections` 邻边
3. ≥ 2 个 `_is_tool` 节点
4. ≥ 1 处 `stay: true` 工具自循环
5. ≥ 1 处反应 clause variants

**参考实现**:G-273 周目(`n_landmark_picker` 56 入边 + 7 地标 + 9 工具)
**契约 ADR**:`docs/architecture/ADR-010-sandbox-topology-contract.md`
**已知 sandbox debt**:linmou Act 1(27 节点 / 0 工具 / 单向辐射,见 ADR-009)

---

## 开发任务工作流(强制)

收到任何"开发任务"指令时,助手必须先调用 `script-review-team` skill,
等评审报告产出且用户放行后,才能进入实际编码或方案撰写。

**判定为"开发任务"的关键词**(任一即触发):
- 实现 / 添加 / 改造 / 重构 / 重写 / 扩展 / 集成 / 迁移
- 设计 / 规划 / 方案 / 架构
- 修 / 修复(影响 ≥ 10 行,或跨文件)

**例外(可直接动手,不调用 skill)**:
- 拼写修复 / 注释更新
- 单文件 < 10 行的 bug 修复
- 配置文件调整(.env / pyproject.toml 字段)
- 纯重命名 / 格式化
- 创建/修改本 skill 自身的文件(`.claude/skills/script-review-team/`)

用户输入"跳过团队"显式覆盖,助手必须确认一次再跳过。

Skill 定义:`.claude/skills/script-review-team/SKILL.md`
完整设计:`docs/superpowers/specs/2026-05-07-script-review-team-skill-design.md`
评审历史:`docs/team-reviews/INDEX.md`

---

## Project Overview

Ghost Story Factory is an AI-powered horror story generation system with two modes:
1. **Dynamic Mode**: Real-time LLM generation during gameplay
2. **Pregenerated Mode** (recommended): Offline dialogue tree generation, zero-latency gameplay

The project uses a **v4 Skeleton-First Pipeline** with structured LLM calls for story generation, featuring plot skeletons, branching dialogue trees, and choice-based gameplay.

## Development Commands

### Environment Setup

```bash
# Create and activate virtual environment
uv venv && source venv/bin/activate  # or: source .venv/bin/activate

# Install in editable mode
uv pip install -e .

# Required environment variables (.env file)
KIMI_API_KEY=your_key_here  # or OPENAI_API_KEY
```

### Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_skeleton_generator.py
pytest tests/test_choices_llm_wrapper.py

# Run with coverage
pytest --cov=src/ghost_story_factory --cov-report=html
```

### Story Generation (CLI Commands)

```bash
# Quick start: Auto-pipeline (recommended)
set-city --city "杭州"           # Generate story candidates
get-struct --city "杭州"         # Select structure
gen-complete --city "杭州"       # Auto-generate all content

# Pregenerated mode (zero-latency gameplay)
python play_game_pregenerated.py # Main menu: select or generate stories

# Dynamic mode (real-time LLM)
python game_engine.py --city 杭州 --gdd path/to/gdd.md --lore path/to/lore_v2.md
```

### Utility Scripts

```bash
# Check checkpoint progress
./check_progress.sh

# Generate complete story (one-shot)
python generate_full_story.py --city 武汉

# Story quality analysis
python -m ghost_story_factory.tools.story_report --city 杭州
```

## Architecture

### Core Pipeline (v4 Skeleton-First)

```
Story Generation Flow:
┌─────────────────────────────────────────────────────────────┐
│ 1. Synopsis Generation (LLMClient)                          │
│    → StorySynopsis dataclass                                │
├─────────────────────────────────────────────────────────────┤
│ 2. Skeleton Generation (SkeletonGenerator + LLMClient)      │
│    → PlotSkeleton JSON (acts, beats, endings)               │
│    → Validates structure (min beats, min endings)           │
├─────────────────────────────────────────────────────────────┤
│ 3. Dialogue Tree Generation (TreeBuilder + LLMClient)       │
│    ├─ Guided Mode: PlotSkeleton-constrained expansion      │
│    ├─ ChoicePointsGenerator: LLM-based choice generation   │
│    ├─ RuntimeResponseGenerator: Narrative responses        │
│    └─ Checkpoint/Resume: Auto-save progress every N nodes  │
├─────────────────────────────────────────────────────────────┤
│ 4. Database Storage (SQLite)                                │
│    → StoryDatabase: Stores dialogue trees for pregenerated │
│    → Enables zero-latency gameplay                          │
└─────────────────────────────────────────────────────────────┘
```

### LLM Integration (Critical: ADR-004/006 Refactoring)

**Two LLM Call Modes:**

1. **LLMClient Mode** (New, Recommended - ADR-004/006)
   - Direct HTTP calls to Kimi/OpenAI APIs
   - Full request/response logging for debugging
   - Used by: `SkeletonGenerator`, `ChoicePointsGenerator`, `RuntimeResponseGenerator`
   - Location: `src/ghost_story_factory/utils/llm_client.py`
   - Key benefit: Complete error diagnostics (captures original LLM output)
   - **✅ ADR-006 完成**: Response 生成已迁移到 LLMClient（2025-12-13）
     - 环境变量: `USE_LLMCLIENT_RESPONSE=1` (默认启用)
     - 优化超时: `RESPONSE_MAX_TOKENS=800-1200` (降低成本与超时)
     - 修复 guided 模式结构塌陷: 近似合并引入 depth/beat 分桶

2. **CrewAI Mode** (Legacy)
   - Used for document generation (GDD, Lore v2)
   - Black-box behavior, limited error diagnostics
   - Being phased out for structured generation
   - Response 生成可通过 `USE_LLMCLIENT_RESPONSE=0` 回退到此模式

**When to use which:**
- Structured JSON generation → LLMClient (skeleton, choices, response)
- Long-form document generation → CrewAI (stories, GDD, lore)

### Directory Structure

```
src/ghost_story_factory/
├── engine/              # Runtime gameplay components
│   ├── choices.py       # ChoicePointsGenerator (LLMClient mode)
│   ├── response.py      # RuntimeResponseGenerator
│   └── game_loop.py     # Main game loop
├── pregenerator/        # Offline generation pipeline
│   ├── skeleton_generator.py  # PlotSkeleton generation (LLMClient)
│   ├── tree_builder.py        # Dialogue tree construction
│   └── synopsis_generator.py  # Story synopsis
├── database/            # SQLite storage for pregenerated stories
│   └── story_database.py
├── utils/               # Shared utilities
│   ├── llm_client.py    # LLMClient (ADR-004 core component)
│   ├── logging_utils.py # Unified logging
│   └── json_utils.py    # JSON parsing/salvage
├── runtime/             # Runtime state management
│   └── save_load.py     # Checkpoint/resume logic
└── ui/                  # User interface components
    └── cli.py           # Interactive menus

tests/                   # Test suite
├── test_skeleton_generator.py
├── test_choices_llm_wrapper.py
└── test_tree_builder.py

docs/                    # Documentation
├── architecture/        # ADRs (Architecture Decision Records)
│   └── ADR-004-core-llm-refactor.md  # LLMClient migration
└── tasks/               # Implementation tasks
    └── TASK_CORE_LLM_REFACTOR.md     # M1-M3 milestones
```

## Critical Code Patterns

### 1. LLMClient Usage (Post-ADR-004)

```python
# Correct: Using LLMClient for structured generation
from ghost_story_factory.utils.llm_client import LLMClient

client = LLMClient(provider="kimi")
result = client.call(
    prompt=my_prompt,
    model="kimi-k2-0905-preview",
    max_tokens=16000,
    temperature=0.7
)
# Result: Raw LLM text output (always returns str, never raises)
# Logs: Automatic request/response logging to logging_utils
```

### 2. F-String JSON Templates (CRITICAL BUG PATTERN)

**❌ WRONG - Causes "Invalid format specifier" errors:**
```python
# JavaScript-style boolean literals in f-strings break Python
prompt = f"""
Example JSON:
{{"flag": true}}   # ❌ Python interprets 'true' as format spec
"""
```

**✅ CORRECT - Use string values:**
```python
# Use quoted strings or Python booleans
prompt = f"""
Example JSON:
{{"flag": "value"}}      # ✅ String value
{{"flag": "触发"}}        # ✅ Chinese string
{{"flag": {str(True).lower()}}}  # ✅ Python bool converted
"""
```

**Why:** In f-strings, `{{}}` escapes braces but Python still parses format specifiers inside. `{{"key": true}}` is interpreted as `{"key": <format spec ' true'>}`, which is invalid.

**Files to check when editing prompts:**
- `src/ghost_story_factory/engine/choices.py` (lines 270, 743, 757)
- Any file with `f"""..."""` containing JSON examples

### 3. Checkpoint/Resume Pattern

```python
# Save checkpoint
checkpoint_manager.save_characters_checkpoint(
    city="杭州",
    characters_data={
        "夜班保安": {"tree": dialogue_tree, "stats": {...}}
    }
)

# Resume from checkpoint
existing = checkpoint_manager.load_characters_checkpoint("杭州")
if existing:
    # Resume generation for remaining characters
    pass
```

**Checkpoint files:** `checkpoints/{city}_characters.json`

### 4. PlotSkeleton Structure

```python
# PlotSkeleton JSON schema (generated by SkeletonGenerator)
{
  "title": "故事标题",
  "config": {
    "target_duration_minutes": 20,
    "min_depth": 30,
    "branching_factor": 3-4
  },
  "acts": [
    {
      "id": "act_1",
      "name": "开端",
      "beats": [
        {
          "id": "S1",
          "name": "初入异境",
          "scene_type": "exploration",
          "is_critical": true,      # Main path beat
          "is_ending_beat": false
        }
      ]
    }
  ]
}
```

**Validation:** Skeleton must have ≥1 act, ≥1 ending_beat, all critical beats in sequence.

## Common Development Tasks

### Adding New LLM-Based Generator

1. **Use LLMClient (not CrewAI)** for structured outputs
2. Follow the pattern in `SkeletonGenerator`:
   - Load prompt template
   - Call `LLMClient.call()`
   - Parse JSON with `_try_parse_json()` + salvage fallback
   - Log errors with `logging_utils.get_logger()`

3. Add tests with mock LLMClient responses

### Debugging LLM Generation Issues

**Step 1:** Check logs for `[LLMClient]` entries
```bash
grep "\[LLMClient\]" logs/full_generation_*.log
```

**Step 2:** Inspect JSON metrics
```bash
grep "choice_json_metrics" logs/full_generation_*.log
```

**Step 3:** Look for salvage attempts
```bash
grep "salvaged" logs/full_generation_*.log
```

**Common Issues:**
- `'total_calls': X, 'failures': Y` → Check LLM API quota/rate limits
- `Invalid format specifier` → F-string JSON template bug (see §2 above)
- `JSON decode error` → LLM output truncated, check `max_tokens`

### Running Quality Analysis Tools

```bash
# Story structure report
python -m ghost_story_factory.tools.story_report --city 杭州

# BMAD choice quality evaluation
python -m ghost_story_factory.tools.bmad_eval --city 杭州
```

## Environment Variables

```bash
# LLM Provider (Kimi recommended)
KIMI_API_KEY=sk-...
KIMI_API_BASE=https://api.moonshot.cn/v1  # Optional
KIMI_MODEL=kimi-k2-0905-preview            # Optional

# OpenAI (fallback)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1 # Optional

# LLM Timeout & Retry Config (Optional)
# Progressive timeout schedule (default: [60, 120, 180])
LLM_TIMEOUTS=60,120,180    # Comma-separated timeout steps (seconds)
LLM_MAX_RETRIES=2          # Max retries (default: len(timeouts)-1)
LLM_RETRY_DELAY=2.0        # Initial retry delay (exponential backoff base, seconds)
LLM_RETRY_MAX_DELAY=60.0   # Max retry delay cap (seconds)

# ⚠️ Legacy: Single fixed timeout (backward compatible, but NOT recommended)
# LLM_TIMEOUT=180          # Fixed timeout (disables progressive timeout)

# Story Generation Config
USE_PLOT_SKELETON=1      # Enable v4 skeleton pipeline
MAX_DEPTH=50             # Max dialogue tree depth
MIN_MAIN_PATH_DEPTH=30   # Min main path depth (overridden by skeleton)
MIN_DURATION_MINUTES=12  # Min story duration
MIN_ENDINGS=3            # Min number of endings
```

## Key Files for Understanding

1. **ADR-004**: `docs/architecture/ADR-004-core-llm-refactor.md`
   - Why we migrated from CrewAI to LLMClient
   - Request/response logging design
   - Status: Accepted (M1-M4 completed)

2. **ADR-006**: `docs/architecture/ADR-006-response-llmclient-and-guided-approx-merge-scope.md`
   - Response generation LLMClient migration (ADR-004 M4 implementation)
   - Fixes guided mode structure collapse (depth/beat scoping)
   - Timeout optimization (RESPONSE_MAX_TOKENS)

3. **ADR-005**: `docs/architecture/ADR-005-langgraph-agent-orchestration.md`
   - ✅ Status: Accepted (M1-M2 completed, 2025-12-13)
   - LangGraph orchestration layer with node-level telemetry
   - JSON stability metrics tracking (100% success rate)
   - Environment variable: `USE_LANGGRAPH_PIPELINE=1` (experimental)
   - Key achievements:
     - Node-level telemetry collection
     - Guided mode structure validation
     - 10 LLM calls: 9 first-time success, 1 salvage success, 0 failures

4. **Task Document**: `docs/tasks/TASK_CORE_LLM_REFACTOR.md`
   - M1: LLMClient implementation ✅
   - M2: SkeletonGenerator refactoring ✅
   - M3: ChoicePointsGenerator refactoring ✅
   - M4: RuntimeResponseGenerator refactoring ✅ (see ADR-006)

4. **Main Entry Points**:
   - `src/ghost_story_factory/main.py` - CLI commands
   - `play_game_pregenerated.py` - Pregenerated mode entry
   - `game_engine.py` - Dynamic mode entry

5. **Core Components**:
   - `src/ghost_story_factory/utils/llm_client.py` - LLM wrapper
   - `src/ghost_story_factory/pregenerator/skeleton_generator.py` - Story structure
   - `src/ghost_story_factory/engine/choices.py` - Choice generation

## Testing Philosophy

- **Unit tests**: Mock LLMClient with fixed responses
- **Integration tests**: Use real API keys (slow, optional)
- **Validation tests**: Check PlotSkeleton structure, choice JSON format
- **Regression tests**: Ensure bug fixes (like f-string format specifier) don't return

Run tests before committing refactorings to LLM-facing code.

---

## Project Management & Development Workflow

**📋 Golden Workflow Reference:** `/Users/yehan/CLAUDE.md` (项目开发黄金流程 v3.4)

This section provides essential project management guidelines for maintaining high-quality development practices. For the complete workflow, consult the golden workflow document.

### Task & Version Management (GitHub-Based)

**🔴 CRITICAL: All development work MUST be tracked via GitHub Issues + Milestones**

#### Creating Milestones (Versions)
```bash
# Create a version milestone (gh CLI doesn't support milestone commands, use API)
gh api repos/:owner/:repo/milestones -X POST \
  -f title="v0.2.0" \
  -f description="Core objectives:
  1. Complete ADR-004 implementation
  2. Add story quality metrics

  Completion criteria:
  - All P0 bugs fixed
  - CI pass rate >95%
  - Core API docs complete" \
  -f due_on="2025-02-15T23:59:59Z"
```

#### Creating Issues (Tasks)
```bash
# Create issue with milestone and labels
gh issue create \
  --title "Implement story quality analyzer" \
  --body "Add BMAD metric calculator for choice quality evaluation" \
  --milestone "v0.2.0" \
  --label "p1,enhancement"

# Label system:
# Priority: p0 (critical) > p1 (high) > p2 (medium) > p3 (low)
# Type: bug | enhancement | docs | refactor | test | chore
```

### Git Workflow Best Practices

#### Standard Development Cycle
1. **Create Issue** with clear acceptance criteria
2. **Create branch**: `git checkout -b feature/42-quality-analyzer`
3. **Develop**: Make frequent commits following Conventional Commits
4. **Prepare PR**: `git pull --rebase origin main` (resolve conflicts)
5. **Create PR**: Link to Issue, wait for CI green
6. **Merge**: Use "Create a merge commit" (preserves history)
7. **Cleanup**: Delete feature branch

#### Conventional Commits Format
```bash
# Format: <type>(<scope>): <subject>
feat(analyzer): add BMAD quality metrics
fix(choices): resolve f-string format specifier bug
docs(readme): update installation instructions
refactor(skeleton): simplify JSON parsing logic
test(choices): add unit tests for LLMClient mode
chore(deps): upgrade pytest to 7.4.0

# Link to Issue (auto-close on merge)
git commit -m "feat: add story analyzer (Closes #42)"

# Breaking changes (triggers MAJOR version bump)
feat!: redesign PlotSkeleton JSON schema

BREAKING CHANGE: changed 'beats' field to 'scenes'
```

#### Hotfix Workflow
When production has a critical bug:
1. Create hotfix branch from release tag: `git checkout -b hotfix/1.2.1 v1.2.0`
2. Fix bug, add regression test
3. Release patch version: `v1.2.1`
4. Merge back to main (use `git merge --no-ff` if no conflicts, else `git cherry-pick`)

### Code Quality Automation

**Enforce quality gates automatically (not manually)**

#### Pre-commit Hooks (Recommended)
```bash
# Install pre-commit framework
brew install pre-commit  # or: pipx install pre-commit

# Activate hooks (one-time setup)
pre-commit install

# Hooks auto-run on: git commit
# - Code formatting (black, ruff-format)
# - Linting (ruff)
# - Trailing whitespace removal
# - YAML/JSON validation
```

#### CI/CD Quality Gates
- **Formatter check**: Ruff/Black
- **Linter**: Ruff (with --fix disabled in CI)
- **Type checker**: mypy
- **Tests**: pytest with coverage ≥70%
- **Security**: Dependency vulnerability scan

### ADR (Architecture Decision Records)

**Why we made this choice, and what we rejected**

Every major technical decision MUST be documented in `docs/architecture/ADR-XXX-title.md` using this template:

```markdown
# ADR-XXX: [Decision Title]

## Status
Accepted | Proposed | Deprecated | Superseded by ADR-YYY

## Date
YYYY-MM-DD

## Context
What problem are we solving? What constraints exist?

## Decision
We will use [solution], because [core reason].

## Alternatives Considered
### Option A: [Name]
- **Pros**: [advantages]
- **Why rejected**: [specific reasons]

### Option B: [Name]
- **Pros**: [advantages]
- **Why rejected**: [specific reasons]

## Consequences
### Positive
- [Impact 1]
- [Impact 2]

### Negative & Mitigation
- [Impact] → **Mitigation**: [how we'll handle it]
```

**Example:** See `docs/architecture/ADR-004-core-llm-refactor.md` for how we documented the CrewAI → LLMClient migration.

### Development Environment Setup

#### Tool Version Management (asdf)
```bash
# Install asdf (one-time)
brew install asdf

# Install project tools (reads .tool-versions)
asdf install

# All team members get same Python/Node/etc versions automatically
```

### Documentation Standards

**Tier 1 (Code)**: Self-documenting code with "why" comments
**Tier 2 (API)**: Auto-generated from docstrings (Sphinx/TypeDoc)
**Tier 3 (User)**: README.md, quick start guides
**Tier 4 (Architecture)**: ADRs, dependency diagrams

**Rule**: Code changes MUST include doc updates in the same PR.

### Core Philosophy

> **"Bad programmers worry about the code. Good programmers worry about data structures and their relationships."** - Linus Torvalds

**Applied to this project:**
- Simplicity > Complexity: Always seek the simplest solution
- Automation > Manual process: Quality enforced by tools, not docs
- Code is truth: Tests verify behavior, not assumptions
- JIT Documentation: Generate project-specific docs from interviews, not generic templates

**For the complete workflow including:**
- Five-dimension technical decision interviews
- Milestone/Issue/Commit linkage diagrams
- Git conflict resolution strategies
- Pre-commit framework configuration examples

**→ Refer to:** `/Users/yehan/CLAUDE.md` (Golden Workflow v3.4)
