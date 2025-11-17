# TASK: 对话树生成进度可视化（TreeBuilder Progress Viewer）

版本: v0.1  
状态: 草案（可迭代）  
关联 ADR: `docs/architecture/ADR-001-plot-skeleton-pipeline.md`  

---

## 0. 背景

- 目前 v4 骨架流水线在生成阶段（TreeBuilder guided 模式）已经接入：
  - `ProgressTracker`（Rich 进度条 + 简单统计）；
  - 角色级检查点（`checkpoints/<city>_characters.json`）；
  - 节点级检查点（`checkpoints/<city>_<char>_tree.json`，TreeBuilder 保存 full checkpoint）；
  - 增量 JSONL 日志（`INCREMENTAL_LOG_PATH`，默认 `checkpoints/tree_incremental.jsonl`，记录 `event=add_node`）。
- 问题：  
  - 这些机制对 TreeBuilder 自己有用，但对外表现仍然是“黑盒”：  
    - 生成时只能看滚动日志，不方便定位“卡死在某个节点/深度”；  
    - 生成中断后，只能手动打开 JSON 检查，很难快速看出结构整体进展。  
- 需求：  
  - 提供一个**面向人类的对话树生成进度可视化工具**，可以基于已有检查点/增量日志快速回答：
    - 目前树长到多深了？
    - 各层节点/结局大致分布如何？
    - 最后几个生成的节点是什么（场景/叙事片段）？

---

## 1. 目标 / 非目标

### 1.1 目标

- [ ] 提供一个命令行工具，基于以下输入之一生成可读的进度视图：  
  - TreeBuilder full checkpoint（`checkpoints/<city>_<char>_tree.json`）；  
  - 或增量 JSONL 日志（`INCREMENTAL_LOG_PATH`）。  
- [ ] 工具至少支持两种输出模式：
  - 终端模式：用 Rich 表格打印当前结构概览；  
  - HTML 模式：生成一个静态 HTML 报告文件，可在浏览器中查看（作为“可视化页面”）。  
- [ ] 视图中包含至少以下信息：
  - 总节点数 / 最大深度 / 结局数量；  
  - 各 depth 上的节点数 / 结局数；  
  - 按 depth 展示一条“主线路径”的 node 列表（基于 parent_id 回溯最长路径），含简要场景和叙事摘要；  
  - 最近若干个新增节点的列表（time / depth / scene / is_ending / narrative 片段）。  

### 1.2 非目标

- 不在本任务中实现“实时推送”或前端轮询，只做基于当前文件的快照视图；  
- 不在本任务中引入复杂前端框架（React/Vue 等），HTML 报告保持简单纯静态；  
- 不修改 TreeBuilder/ProgressTracker 行为，仅消费其已有产出（checkpoint + JSONL）。

---

## 2. 里程碑与任务拆分

### M1: 需求细化与数据源确认

- [x] M1-1 梳理现有可用数据源：
  - TreeBuilder full checkpoint 结构（`tree` / `queue` / `state_cache` 等字段）；  
  - 增量日志 JSONL 格式（`event: add_node` + `node: {...}` + `ts`）。  
- [x] M1-2 在 Task 中补充一个“典型视图草图”（文字描述即可），说明终端模式与 HTML 模式各展示哪些信息。

### M2: CLI 工具实现（终端模式 + HTML 报告）

- [x] M2-1 新增模块 `tools/view_tree_progress.py`：
  - 支持参数：
    - `--checkpoint`：TreeBuilder checkpoint JSON 路径；  
    - `--log-jsonl`：增量日志 JSONL 路径（可选）；  
    - `--output-html`：HTML 报告输出路径（可选）；  
    - 若既不传 checkpoint 也不传 log，给出友好错误提示。  
  - 内部逻辑：
    - 解析 checkpoint 的 `tree` 字段（或直接当作树）；  
    - 根据 node 的 `depth` / `is_ending` / `scene` / `narrative` 等字段计算结构统计；  
    - 如提供 JSONL，则从中抽出最近若干个 `add_node` 事件作为“最新节点”列表。  
- [x] M2-2 终端模式输出：
  - 用 Rich 打印：总体统计表 / depth 分布表 / 主线路径简要表 / 最近节点列表。  
- [x] M2-3 HTML 报告输出：
  - 生成一个静态 HTML 文件，包含上述统计表格；  
  - 不依赖外部 JS/CSS 框架，使用简单内联样式即可。

### M3: 测试 / 集成 / 文档

- [x] M3-1 单元测试：
  - 新增 `tests/test_view_tree_progress.py`：  
    - 用临时目录写一个小的 checkpoint/tree JSON 与 JSONL，验证 `view_tree_progress` 中的解析和汇总逻辑（例如 depth 统计 / 结局数 / 主线路径长度）。  
- [x] M3-2 集成到统一测试脚本：
  - 在 `tools/run_all_tests.py` 的 pytest 部分增加 `tests/test_view_tree_progress.py`。  
- [x] M3-3 文档更新：
  - 在 `docs/architecture/NEW_PIPELINE.md` 或 `STORY_PIPELINE_V4.md` 中简要提及该工具；  
  - 在 `AGENTS.md` 的“重要工具”或对应部分补一条：生成卡死/怀疑结构异常时，先用 `tools/view_tree_progress.py` 诊断。

---

## 3. 依赖与协作

- 依赖模块：
  - `src/ghost_story_factory/pregenerator/tree_builder.py`（checkpoint + JSONL 格式）  
  - `src/ghost_story_factory/pregenerator/progress_tracker.py`（背景信息）  
- 依赖工具：
  - `tools/run_all_tests.py`（需要集成新的 pytest 用例）  
- 不新增第三方依赖，终端可视化仍用 Rich。

---

## 4. Done 定义

当且仅当满足以下条件，本任务视为完成：

- 可以通过如下命令在本地快速查看任意一次生成的结构进度（至少支持 checkpoint 模式）：  
  - `venv/bin/python tools/view_tree_progress.py --checkpoint checkpoints/上海_深夜电台主播_tree.json`  
  - 输出包含总节点数 / 最大深度 / 结局数量 / 各 depth 分布 / 一条主线路径（含叙事摘要）。  
- 通过 `--output-html` 生成的 HTML 报告能在浏览器中打开并清晰展示上述信息；  
- 新增测试 `tests/test_view_tree_progress.py` 通过，且已纳入 `tools/run_all_tests.py`；  
- 相关架构/AGENT 文档已更新，明确该工具作为排查生成卡死/结构异常时的第一诊断手段。
