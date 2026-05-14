# 杭州夜班保安

[![Version](https://img.shields.io/badge/version-v2.0.0-blue.svg)](https://github.com/yehan-s/ghost-story-factory/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

> 一个文字冒险游戏。
> 你扮演夜班保安 G-273,
> 在一座有些不对劲的杭州物资仓库里,
> 用一晚上拼出 8 张照片背后的真相。

终端里跑的全屏 TUI,沙盒拓扑、跨周目人格惯性、可反复访问的 NPC 对话变体。
**12 种结局,162 个节点**,主角线 5 个主要 ending + 4 个 BAD/NEUTRAL ending +
4 个 1985 年前传线 ending。

---

## 玩(选一种)

### A. 从源码跑(推荐,最稳)

```bash
git clone https://github.com/yehan-s/ghost-story-factory
cd ghost-story-factory
uv venv && source .venv/bin/activate
uv pip install -e .
python play_tui.py
```

### B. `pipx` 安装(纯命令使用)

```bash
pipx install git+https://github.com/yehan-s/ghost-story-factory
ghost-story-tui
```

> **当前已知限制**:剧本路径目前从 repo 根读取,装包模式下需要 `cd` 到本仓库目录跑。
> 单文件 release(零环境依赖)在 Step 3 路线图上。

---

## 控制

**菜单**:↑↓ 移动 / Enter 选择 / b 或 Esc 返回 / q 退出

**游戏**:↑↓ 选项 / Enter 确认 / 1–9 快选 / s 状态面板 / q 退出

---

## 剧情结构

| 维度 | 数量 |
|---|---|
| 节点总数 | 162 |
| 主线主结局 | 5(E_TRUE / E_TRUTH / E_BROADCAST / E_DATA / E_HIDDEN) |
| 中性 / BAD 结局 | 3(E_NEUTRAL / E_BAD_1987 / E_BAD_DROWN) |
| 1985 前传线结局 | 4(RELEASE / EXPOSED / GRIEVANCE / REGRET) |
| 可反复访问 NPC | 7 |
| 沙盒地标 | 6(picker 中枢 + 横向 connections) |

**跨周目人格惯性**:上一次通关结局会影响下一次开场的"残影"——
通关 E_TRUE,开局你会**下意识把手伸进衣袋**找一封不存在的信;
通关 E_DATA,对讲机里前任会**先报字段名问你确认 schema**。

**反应式 NPC**:看过某条伏笔后,下次访问对话会**自动切换变体**,
不是单链回放。

---

## 项目结构

```
src/ghost_story_factory/
├── v5/         玩家状态 + 派生量(meets / effects / behavior_profile)
├── v7/         全屏 TUI 播放器(textual)
└── runtime/    GameTree 契约(RequirementEvaluator / EffectApplier / EndingResolver)

stories/hangzhou_yebanbaoan/
├── tree.json                # 合并产物,真正被引擎读
└── _fragment_v7_*.json      # 9 个手写片段,merge_fragments.py 编译成 tree.json

tools/
├── merge_fragments.py       # 编译剧本
├── audit_*.py(13 项)        # 剧本质检
└── run_all_tests.py         # 跑测试套件

docs/
├── architecture/            # ADR-007 ~ ADR-011(运行时契约)
└── SCRIPTING.md             # 想自己写剧本?看这个
```

---

## 想自己写剧本?

看 [docs/SCRIPTING.md](docs/SCRIPTING.md)。

核心套路:
- **沙盒不是死剧本**:picker hub + landmark connections + tool 节点 + 反应 variants
- **0 新真相源**:`endings_seen` / `foreshadows_seen` / `deductions_resolved` 是单一真相,不许加镜像 flag
- **跨周目联动**:`ending_seen.ending_id`(曾经)+ `ending_seen.last`(最近)

ADR 索引在 [docs/INDEX.md](docs/INDEX.md)。

---

## 历史代码 / LLM 生成流水线

本项目早期(v0.x–v1.x)是 LLM 自动生成 VN 剧本的工具,
基于 CrewAI + LangGraph + LLMClient 流水线。

**v2.0.0 起转型为 VN 沙盒播放器**,
LLM 流水线整套代码冻结在 [`legacy/llm-pipeline`](https://github.com/yehan-s/ghost-story-factory/tree/legacy/llm-pipeline) 分支,永不删除。

如需复活:`git checkout legacy/llm-pipeline`,见该分支的 `LEGACY.md`。

---

## 开发

```bash
# 编辑剧本片段
$EDITOR stories/hangzhou_yebanbaoan/_fragment_v7_shared.json

# 编译
python tools/merge_fragments.py

# 跑 13 项审计(沙盒拓扑 / 反应契约 / 跨周目联动 / 人格惯性...)
bash tools/audit_all.sh

# 跑测试套件
python tools/run_all_tests.py
```

---

## License

MIT
