# 项目转型计划 ── 从 AI 故事生成器 转为 VN 沙盒播放器

**状态**:📋 计划草案,尚未执行
**前置**:✅ 已完成 `legacy/llm-pipeline` 分支冻结(2026-05-14)
**对应分支安全网**:`legacy/llm-pipeline`(已推 origin,永不删除)

---

## 0. 背景与判断

本项目在 v3–v5 时期的核心是「AI 自动生成 VN 剧本」(SkeletonGenerator + CrewAI +
LangGraph + 动态/预生成模式)。但实际迭代到 v7 时,**剧本生产方式已彻底转向**:

- **当前剧本工作流**:手写 9 个 `_fragment_v7_*.json` → `tools/merge_fragments.py`
  (1246 行)→ `stories/hangzhou_yebanbaoan/tree.json`
- **当前运行时**:`play_tui.py` → `v7/tui_player` → `v5/player` + `runtime/contracts`
- **第三方依赖**:**只有 `textual`**。无 LLM、无 crewai、无 langgraph、无 pydantic
  在 play 链路被引用

这意味着项目结构里大量代码是**死代码**:占着 pyproject 重依赖、撑大 wheel、
拖累 `pipx install` / `pyinstaller` 的产物体积,但运行时零调用。

转型目标:**`main` 瘦身成「带剧本的 VN 沙盒播放器」**,
让朋友能用单文件 release(PyInstaller)或 `pipx install` 直接玩。
LLM 生成流水线进 `legacy/llm-pipeline` 分支冻结。

---

## 1. Step 1:`main` 做减法(下一个 PR)

### 1.1 删除清单(整目录 / 整文件)

```
src/ghost_story_factory/pregenerator/    # SkeletonGenerator / TreeBuilder / synopsis_generator
src/ghost_story_factory/engine/          # 动态模式 game_loop / choices / response
src/ghost_story_factory/database/        # SQLite 预生成存储
src/ghost_story_factory/main.py          # set-city / gen-* CLI 命令实现
src/ghost_story_factory/orchestration/   # LangGraph 编排(若存在)
play_game_full.py                        # 动态模式入口
play_game_pregenerated.py                # 预生成模式入口
generate_full_story.py                   # 一发完整生成
check_progress.sh                        # 生成 checkpoint 进度查询
database/                                # 项目根目录的 sqlite 文件 + .db.shm/.wal
checkpoints/                             # 生成中间产物
```

### 1.2 删除清单(pyproject `[project] dependencies` 重依赖)

```toml
"crewai>=0.30.0",         # ← 删
"langchain-community",     # ← 删
"langchain-openai",        # ← 删
"langgraph>=1.0.0",        # ← 删
```

保留的最小依赖集:
```toml
dependencies = [
    "textual>=8.0",           # TUI 唯一硬依赖
    "rich>=13.7.0",            # textual 间接需要但显式留更稳
    "python-dotenv",           # 若 main 不需要 .env,这条也可以删(待核查 v7 引用)
]
```

如果某些 audit 工具或 v5/player.py 内部隐式依赖 pydantic,**保留**;否则也删。

### 1.3 删除清单(pyproject `[project.scripts]`)

```toml
# 全删:
gen-complete / set-city / get-struct / get-lore / gen-protagonist /
gen-lore-v2 / gen-gdd / gen-main-thread / gen-branch / get-story

# 改:
ghost-story-play = "ghost_story_factory.engine.game_loop:main"   # ← 这条删,engine 没了

# 新增:
ghost-story-tui = "ghost_story_factory.v7.tui_player:main"       # ← 唯一入口
```

### 1.4 保留清单(核心运行时 + 剧本开发工具)

```
src/ghost_story_factory/v5/              # State / meets / effects / behavior_profile_axes
src/ghost_story_factory/v7/              # TUI 全屏播放器
src/ghost_story_factory/runtime/         # contracts:RequirementEvaluator / EffectApplier / EndingResolver
src/ghost_story_factory/utils/           # ⚠️ 只保留 play 链路用的(logging_utils 等);llm_client / json_utils 可能也删
stories/hangzhou_yebanbaoan/             # 剧本本体 + 所有 fragment + tree.json
tools/audit_*.py                         # 13 项剧本审计(剧本开发还要)
tools/merge_fragments.py                 # 剧本编译脚本
tools/run_all_tests.py                   # 测试聚合
tests/                                   # 单测 — 但要清掉所有 test_skeleton / test_tree_builder / test_choices_llm_wrapper
```

### 1.5 测试要清的(对应被删模块)

```
tests/test_skeleton_generator.py
tests/test_choices_llm_wrapper.py
tests/test_tree_builder.py
tests/test_synopsis_generator.py
# ... 任何 import pregenerator / engine / database / langgraph 的测试
```

**保留的测试主轴**(必须全绿才能合并 Step 1 PR):

- `test_audit_pass22.py`(13 项审计的 20+ 单测)
- `test_ending_seen.py`(ending_seen 协议,含 `.last`)
- `test_save_manager_query.py`(record_ending 末尾重排不变量)
- `test_audit_paths_linmou.py`(必死不变量 ADR-009)
- `test_audit_script_depth.py`(剧本厚度审计)
- `test_behavior_profile.py`(行为画像派生)
- 其余 v5/v7/runtime 相关单测

### 1.6 必须保证

- `bash tools/audit_all.sh` 仍 13/13 全绿
- `.venv/bin/python tools/run_all_tests.py` 仍 7/7 全绿(已删的测试不计入)
- `.venv/bin/python play_tui.py stories/hangzhou_yebanbaoan/tree.json` 能跑通主菜单 → 选 G-273 → 进 picker → 完成 1 个 ending
- `pip install -e . && ghost-story-tui` 在干净 venv 能跑

### 1.7 估时

约 **2-3 小时**。主要时间在:
- 验证哪些 utils/llm_client.py / utils/json_utils.py 还有非 LLM 调用方
- 删除 `database/` 后清查测试副作用(test db 文件、check_progress.sh)
- pyproject 修完跑一次 `pip install -e .` 验证 import 不挂

---

## 2. Step 2:README 重写

### 2.1 当前 README 的问题

当前 `README.md` 围绕 v3-v5 "AI 故事生成器" 写,例子全是 `set-city`/`gen-complete`,
对一个想玩游戏的朋友完全无用。

### 2.2 新 README 主轴

```
# 杭州夜班保安 — VN 沙盒播放器

> 一个文字冒险游戏。你扮演夜班保安 G-273,
> 在一座有些不对劲的杭州物资仓库里,
> 用 6 小时拼出 8 张照片背后的真相。

## 玩(选一种)

### A. 下载 release(零依赖)
1. 到 Releases 页面下载对应你系统的 binary(mac / win / linux)
2. 终端跑 `./ghost-story-tui` 或双击

### B. 用 Python(开发者)
pipx install ghost-story-factory
ghost-story-tui

### C. 从源码跑
git clone ... && uv sync && uv run play_tui.py

## 控制
↑↓ 选项 / Enter 确认 / 1-9 快选 / s 状态 / q 退出

## 剧情结构
- 5 个主结局 + 多个支线结局
- 跨周目人格惯性:上一次通关影响下一次开场残影
- 7 个 NPC,每个有可反复访问的对话变体

## 写新剧本?
见 docs/SCRIPTING.md(沙盒拓扑 + reaction_contracts 写法)。

## 想看历史代码
LLM 生成流水线代码冻结在 `legacy/llm-pipeline` 分支。
```

### 2.3 配套文档

- **新建** `docs/SCRIPTING.md`:面向"我想自己写剧本"的人,讲 fragment 结构、
  picker hub、tool 节点、`narrative_variants` 协议、`reaction_contracts`、5 类
  `ending_seen` 写法。
- **保留** `docs/architecture/ADR-007` 至 `ADR-011`:这些 ADR 都是描述运行时契约,
  与 LLM 无关,主分支继续维护。
- **挪到 legacy 分支专属**:
  - `docs/architecture/ADR-001` ~ `ADR-006`(全是 LLM 流水线相关)
  - 实际操作:在 `main` 上**删除**这 6 个 ADR(legacy 分支永远保留),
    然后在 `docs/architecture/README.md` 里加一行"ADR-001~006 历史文档见 legacy 分支"

### 2.4 估时

约 **1-1.5 小时**。

---

## 3. Step 3(可选):出 PyInstaller release

`main` 瘦身后,依赖只剩 textual + rich,binary 体积应在 30-50MB(可接受)。

```bash
# GitHub Actions matrix 跑三平台
pyinstaller play_tui.py \
  --onefile \
  --name ghost-story-tui \
  --add-data "stories:stories" \
  --collect-all textual
```

要做:
- 写 `.github/workflows/release.yml`(tag 触发,三 OS 矩阵)
- 测试三个 binary 都能跑(尤其 Windows cmd 的 emoji 渲染)
- 第一个 release 打 `v2.0.0`(主版本 bump,因为 API 不兼容了)

估时:**1-2 小时**(主要在 CI 调试)。

---

## 4. 顺序与发车点

```
┌─ Step 0 [DONE 2026-05-14] ─ 建 legacy/llm-pipeline 安全网
│
├─ Step 1 [TODO]            ─ main 做减法(整目录删 + pyproject 瘦身)
│                              估时 2-3h,产出 1 个 PR
│
├─ Step 2 [TODO]            ─ README 重写 + docs/SCRIPTING.md
│                              估时 1-1.5h,产出 1 个 PR(或与 Step 1 合并)
│
└─ Step 3 [可选]            ─ PyInstaller release
                               估时 1-2h,产出 1 个 PR + GitHub Release
```

Step 1 和 Step 2 强烈建议**两个独立 PR**——Step 1 改动大、影响面广,先合并稳定;
Step 2 改文档不会破坏运行时,跟在后面更稳。

---

## 5. 风险与回退

### 风险 1:Step 1 删多了

某个 v5/v7 模块隐式 import 了 pregenerator/engine 里的东西,删完跑不起来。

**回退**:`git checkout legacy/llm-pipeline -- <路径>` 把单个文件捞回来。

### 风险 2:某 audit 工具其实在用 database

`tools/audit_*.py` 部分早期工具(audit_choices / audit_consistency)可能 import 了
database/。Step 1 实施时要逐个 grep 确认,不能盲删。

**回退**:同上,从 legacy 分支单独捞文件。

### 风险 3:朋友的终端不支持 textual 全屏 UI

Windows cmd / 老版 PowerShell / 某些 SSH 终端可能渲染问题。

**缓解**:Step 3 release 时加一个 fallback CLI 模式(纯 print + input),
作为 `--simple` flag。Step 1 不做此项。

---

## 6. 不做的事(明账剔除)

- ❌ **不**重写为 Node/TypeScript(用户没要 npm 化,只想要朋友能玩)
- ❌ **不**保留任何 LLM 接口在 main(legacy 分支已经存)
- ❌ **不**给 main 上加 web UI(超出范围)
- ❌ **不**清理 git 历史(`git filter-branch` 危险且没必要,legacy 分支已经够)

---

## 相关

- 安全网分支:`legacy/llm-pipeline`(GitHub: `origin/legacy/llm-pipeline`)
- 当前 main 末梢 commit:`7f64154`(ADR INDEX 补全合并后)
- 转型决策对话:本会话 2026-05-14
