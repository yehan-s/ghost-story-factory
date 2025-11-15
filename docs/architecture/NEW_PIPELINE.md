# 新架构流程图谱（v3.0 / v4.0 演进）

> **版本**: v3.0（附 v4.0 演进说明）  
> **更新日期**: 2025-11-15  
> **状态**: ✅ v4 骨架流水线为当前默认故事生成路径；v3 保留为兼容回退层

---

## 📊 概览

预生成流程采用 **"完整生成器优先 + v4 骨架优先"** 策略：

1. **先产出高质量文档**：Lore v2 / GDD / 主线故事（v3/v4 共用）  
2. **v4 默认路径**：  
   - 生成 PlotSkeleton（故事骨架）；  
   - 使用 guided `DialogueTreeBuilder(plot_skeleton=...)` 按骨架生成对话树；  
   - 使用 `NodeTextFiller` 填充节拍元数据与占位叙事；  
   - 使用 `story_report` 做结构+时长+结局验收（至少打印主角报告摘要）。  
3. **v3 兼容路径（仅在需要时回退）**：  
   - 显式配置 `USE_PLOT_SKELETON=0`，或骨架生成失败；  
   - 直接驱动旧版 `DialogueTreeBuilder`（`plot_skeleton=None`），保留 legacy heuristics（env 降级等）；  
   - 不执行 NodeTextFiller / story_report。  
4. **最后入库**：持久化到数据库供游戏运行时使用。

### 核心改进

- ✅ **世界书预分析 + 早提醒**：生成前评估质量，提前发现问题
- ✅ **主线优先加深**：确保主线深度达标，避免烂尾
- ✅ **结局门槛检查**：确保至少有 1 个结局可达
- ✅ **单轮内扩展直至达标（v3）**：不整轮重启，在同一轮内持续扩展
- ✅ **骨架优先（v4）**：先设计结构化 PlotSkeleton，再按骨架生成对话树
- ✅ **硬闸防死循环**：多重安全机制防止无限生成
- ✅ **仅走 Kimi**：统一使用 Kimi 的 OpenAI 兼容接口

> v4 骨架模式的详细设计见：  
> - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`  
> - `docs/architecture/STORY_PIPELINE_V4.md`

---

## 🔄 端到端流程

### 1️⃣ 选择与输入

**入口**：用户通过 UI 或脚本指定

```python
StorySynopsis(
    title="故事标题",
    protagonist="主角身份",
    location="主要场景",
    estimated_duration=20  # 分钟
)
```

**可选**：已有高质量文档时可直接传入路径复用
- `gdd_path`: GDD 文件路径
- `lore_path`: Lore v2 文件路径
- `main_story_path`: 主线故事路径

---

### 2️⃣ 文档阶段（完整生成器优先）

**策略**：`USE_FULL_GENERATOR=1`（默认）

```
完整生成器 (generate_full_story.py)
    ↓
产出文档:
    • {city}_lore_v2.md    (世界书 2.0)
    • {city}_gdd.md        (AI 导演任务简报)
    • {city}_story.md      (主线故事)
    ↓
失败时 → 回退到内置简版生成（确保不中断）
```

**完整生成器流程**：
1. 收集原始素材（可选 Google 搜索）
2. 生成 Lore v1（高保真地基）
3. 生成角色分析（Protagonist）
4. 生成 Lore v2（游戏化规则）
5. 生成 GDD（AI 导演任务简报）
6. 生成主线故事（完整文案）

**回退机制**：
```python
try:
    # 尝试完整生成器
    gdd, lore, story = full_generator.generate_all()
except Exception:
    # 回退到简版
    gdd = _generate_gdd_simple()
    lore = _generate_lore_simple()
    story = _generate_story_simple()
```

---

### 3️⃣ 世界书预分析（早提醒）

**目的**：在生成对话树前评估文档质量

```python
预分析器.analyze(lore_v2, gdd, main_story)
    ↓
估算指标:
    • 主线可达深度
    • 结局数量
    • 关键节拍数量
    ↓
若低于阈值 → 打印警示（但不中断）
```

**默认阈值**：
- 主线深度 ≥ 30
- 结局数量 ≥ 1

**示例输出**：
```
⚠️  [预分析警告]
   主线深度估算: 25 (低于阈值 30)
   建议: 增强 GDD 中的场景设计

   结局数量: 0 (低于阈值 1)
   建议: 在 Lore v2 中添加结局触发条件
```

---

### 4️⃣ 角色确定

**策略**：主角 = 用户选择，配角 = 可选

```python
主角 = synopsis.protagonist  # 始终使用用户选择

if multi_character:
    # 优先：复用 struct.json
    if exists(f"{city}_struct.json"):
        配角 = struct.potential_roles
    else:
        # 回退：从主线文本启发式提取
        配角 = extract_from_story(main_story)
```

**提取策略**：
- 优先匹配 `{city}_struct.json` 的 `potential_roles`
- 标题必须完全匹配才使用
- 不匹配时从故事中提取常见角色职业

---

### 5️⃣ 对话树构建（v4 默认路径 + v3 基线）

**核心组件**：`DialogueTreeBuilder`

#### 生成策略（v4 guided）

当 `StoryGeneratorWithRetry` 成功生成 `PlotSkeleton` 且 `USE_PLOT_SKELETON!=0` 时：

- `DialogueTreeBuilder(plot_skeleton=skeleton)` 进入 guided 模式：
  - depth → beat 映射控制每层分支数（`branches.max_children` + `config.max_branches_per_node`）；
  - `leads_to_ending` 控制在哪些深度允许结局：
    - 即使 `_check_ending` 判为结局，如果该深度对应的 beat 不允许结局，会强制继续扩展；
  - 保留安全闸（`MAX_TOTAL_NODES` / plateau / Beam）；
  - 同轮扩展次数由 `EXTEND_ON_FAIL_ATTEMPTS` 控制，但在 guided 模式下被强制收紧为最多 1 次；
  - **不再**通过修改 env（`MIN_DURATION_MINUTES` / `EXTEND_ON_FAIL_ATTEMPTS` / `FORCE_CRITICAL_INTERVAL`）来“死磕”，这些 heuristics 仅在 v3 legacy 模式下生效。

#### 生成策略（v3 legacy 基线）

```
BFS 广度优先遍历
    ↓
每个节点:
    1. 生成选择 (choices.py)
       • 调用 Kimi API
       • 返回 JSON: [{"text": "...", "consequences": {...}}]
       • 超时/失败 → 本地默认选择兜底

    2. 生成响应 (response.py)
       • 基于选择生成叙事
       • 强调伏笔回收与走向结局
       • 超时/失败 → 本地默认响应

    3. 更新状态 (state_manager.py)
       • 应用后果（PR/GR/WF/flags/inventory）
       • 纳入时间推进（避免停滞）
       • 量化去重（PR/GR ±5 合并）
    ↓
优先策略: 始终从"当前主线叶子"加深
    • 主线深度未达标 → 只扩展主线
    • 主线达标后 → 扩展分支（每节点 ≤3 分支）
```

#### 分支控制

```python
MAX_CHOICES_PER_NODE = 3  # 每个节点最多 3 个选择

if current_depth < MIN_MAIN_PATH_DEPTH:
    # 主线优先：只扩展主线叶子
    expand_main_path_only()
else:
    # 主线达标：开始扩展分支
    expand_branches(max_per_node=3)
```

#### 稳健性保障

| 场景 | 处理策略 |
|------|----------|
| API 超时 | 本地默认选择（3个通用选项） |
| 空响应 | 本地默认叙事（"你继续前进..."） |
| JSON 解析失败 | 提取文本 + 默认后果 |
| 状态重复 | 量化去重（PR/GR ±5 合并） |
| 时间停滞 | 默认后果含 `time += 5min` |

---

### 6️⃣ 校验与"同轮扩展直至达标"（v3 基线）

**核心理念**：不整轮重启，在同一轮内持续扩展

#### 校验阈值

```python
MIN_MAIN_PATH_DEPTH = 30    # 主线最小深度
MAX_DEPTH = 50              # 对话树最大深度
MIN_DURATION_MINUTES = 12   # 最小游戏时长（分钟）
MIN_ENDINGS = 1             # 最少结局数量
```

#### 扩展策略

```python
while not meets_thresholds(tree):
    if reached_safety_limit():
        break  # 触发硬闸，退出

    # 在同一轮内继续扩展
    if main_path_depth < MIN_MAIN_PATH_DEPTH:
        extend_main_path()  # 优先加深主线
    elif endings < MIN_ENDINGS:
        add_ending_branches()  # 添加结局分支
    else:
        extend_side_branches()  # 扩展支线
```

**关键点**：
- ❌ **不会**整轮重启（避免浪费已生成内容）
- ✅ **会**在同一轮内持续扩展直至达标
- ✅ **会**在触发硬闸时安全退出

---

### 7️⃣ 安全闸与退出条件

**多重安全机制**防止无限生成

#### 单轮硬闸

```python
MAX_TOTAL_NODES = 300           # 单轮最大节点数
PROGRESS_PLATEAU_LIMIT = 2      # 平台期检测（连续 N 轮无进展）

if total_nodes >= MAX_TOTAL_NODES:
    log.warning("达到节点上限，停止生成")
    break

if no_progress_for_N_rounds >= PROGRESS_PLATEAU_LIMIT:
    log.warning("检测到平台期，停止生成")
    break
```

#### 跨轮重试（默认禁用）

```python
MAX_RETRIES = 0                 # 默认不重试
AUTO_RESTART_ON_FAIL = 0        # 默认不自动重启

# 杜绝"失败→整轮重跑"循环
```

**退出条件优先级**：
1. ✅ 达标退出（所有阈值满足）
2. ⚠️ 硬闸退出（节点上限/平台期）
3. ❌ 异常退出（捕获并记录日志）

---

### 8️⃣ 持久化与游玩

#### 数据库存储

```sql
-- database/ghost_stories.db

stories
    • id, city_name, title, synopsis
    • metadata (JSON): duration, nodes, depth, endings

characters
    • id, story_id, name, is_protagonist, description

dialogue_trees
    • id, story_id, character_id
    • tree_data (JSON): 完整对话树
```

#### 游戏启动

```bash
./start_pregenerated_game.sh
    ↓
菜单:
    1. 选择城市
    2. 选择故事
    3. 选择角色（主角/支线角色）
    ↓
开局: 加载对应角色的对话树
    • 主角 → 完整主线 + 分支
    • 支线角色 → 独立视角树
```

---

## 🗂️ 模块映射

### 核心模块

| 模块 | 文件路径 | 职责 |
|------|----------|------|
| **入口与协调** | `pregenerator/story_generator.py` | `StoryGeneratorWithRetry` 类 |
| **完整生成器** | `generate_full_story.py` | 生成 Lore/GDD/Story |
| **预分析** | `pregenerator/story_generator.py` | 世界书质量评估 |
| **阈值校验** | `pregenerator/time_validator.py` | 深度/时长/结局校验 |
| **树生成** | `pregenerator/tree_builder.py` | 主线优先 + 检查点 |
| **选择生成** | `engine/choices.py` | 生成选择 JSON |
| **响应生成** | `engine/response.py` | 生成叙事响应 |
| **状态管理** | `pregenerator/state_manager.py` | 状态推进 + 去重 |
| **数据库** | `database/db_manager.py` | 持久化 |
| **日志系统** | `utils/logging_utils.py` | 错误记录 |

### 调用关系

```
story_generator.py (协调器)
    ↓
    ├─→ generate_full_story.py (文档生成)
    ├─→ tree_builder.py (对话树)
    │       ↓
    │       ├─→ choices.py (选择)
    │       ├─→ response.py (响应)
    │       └─→ state_manager.py (状态)
    ├─→ time_validator.py (校验)
    └─→ db_manager.py (持久化)
```

---

## ⚙️ 配置开关

### 环境变量（`.env` 文件）

#### 深度/时长/结局

```bash
MAX_DEPTH=50                    # 对话树最大深度
MIN_MAIN_PATH_DEPTH=30          # 主线最小深度
MIN_DURATION_MINUTES=12         # 最小游戏时长（分钟）
MIN_ENDINGS=1                   # 最少结局数量
```

#### 扩展安全

```bash
MAX_TOTAL_NODES=300             # 单轮最大节点数
PROGRESS_PLATEAU_LIMIT=2        # 平台期检测阈值
```

#### 重试策略

```bash
MAX_RETRIES=0                   # 跨轮重试次数（默认禁用）
AUTO_RESTART_ON_FAIL=0          # 失败自动重启（默认禁用）
```

#### 完整生成器

```bash
USE_FULL_GENERATOR=1            # 启用完整生成器
FULL_INCLUDE_BRANCHES=0         # 是否生成支线（默认否）
```

#### API 提供商（仅 Kimi）

```bash
# ✅ 使用 Kimi
KIMI_API_KEY=sk-xxx
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2-0905-preview

# ❌ 禁用 OpenAI 直连
# OPENAI_API_KEY=  # 留空或删除
# OPENAI_BASE_URL= # 留空或删除
```

#### 并发控制

```bash
KIMI_CONCURRENCY=1              # Kimi 并发数（推荐 1）
KIMI_CONCURRENCY_CHOICES=1      # 选择生成并发（推荐 1）
```

---

## 🆚 与旧流程的关键差异

### 旧流程（v2.x）

```
简版文档生成
    ↓
直接构建对话树
    ↓
深度不达标 → 整轮重启（浪费已生成内容）
    ↓
可能烂尾/无结局
```

### 新流程（v3.0）

```
完整生成器（高质量文档）
    ↓
预分析 + 早提醒
    ↓
主线优先加深 + 结局门槛
    ↓
未达标 → 同轮扩展（不重启）
    ↓
硬闸防死循环
    ↓
仅走 Kimi + 兜底机制
```

### 核心改进对比

| 维度 | 旧流程 | 新流程 |
|------|--------|--------|
| **文档质量** | 简版生成 | 完整生成器优先 |
| **质量评估** | 无 | 预分析 + 早提醒 |
| **主线保障** | 无特殊处理 | 主线优先加深 |
| **结局保障** | 无检查 | 结局门槛检查 |
| **未达标处理** | 整轮重启 | 同轮扩展 |
| **死循环防护** | 弱 | 多重硬闸 |
| **API 提供商** | OpenAI/Kimi 混用 | 仅 Kimi |
| **稳健性** | 依赖 API | 兜底机制完善 |

---

## 📈 性能与质量指标

### 生成质量

| 指标 | 目标值 | 实际表现 |
|------|--------|----------|
| 主线深度 | ≥ 30 | 通常 30-40 |
| 总节点数 | 100-300 | 平均 150-200 |
| 结局数量 | ≥ 1 | 通常 2-4 |
| 游戏时长 | ≥ 12 分钟 | 平均 15-25 分钟 |

### 生成效率

| 场景 | 耗时 | 说明 |
|------|------|------|
| MVP 测试（2 角色） | 5-10 分钟 | `generate_mvp.py` |
| 单角色完整生成 | 30-60 分钟 | `story_generator.py` |
| 多角色并行（4 角色） | 1-2 小时 | `generate_smart_parallel.py` |

### 成功率

- ✅ **文档生成成功率**: ~95%（有回退机制）
- ✅ **对话树生成成功率**: ~90%（有兜底机制）
- ✅ **达标率**: ~85%（主线优先 + 扩展策略）

---

## 🔍 调试与监控

### 日志系统

所有生成过程自动记录到 `logs/` 目录：

```bash
logs/
├── generate_mvp_20251025_143000.log
├── generate_smart_parallel_20251025_150000.log
└── generate_full_story_20251025_160000.log
```

### 关键日志点

```python
# 1. 文档生成
logger.info("开始生成 Lore v2...")
logger.info("✅ Lore v2 生成完成")

# 2. 预分析
logger.warning("⚠️ 主线深度估算: 25 (低于阈值 30)")

# 3. 对话树生成
logger.info(f"生成节点 {node_id}: depth={depth}")
logger.warning(f"API 超时，使用默认选择")

# 4. 校验
logger.info(f"主线深度: {main_depth} / {MIN_MAIN_PATH_DEPTH}")
logger.info(f"结局数量: {endings} / {MIN_ENDINGS}")

# 5. 安全闸
logger.warning(f"达到节点上限 {MAX_TOTAL_NODES}，停止生成")
```

### 监控命令

```bash
# 实时查看日志
tail -f logs/generate_*.log

# 查找错误
grep -i error logs/*.log

# 查找警告
grep -i warning logs/*.log

# 统计生成进度
grep "生成节点" logs/*.log | wc -l
```

---

## 🧱 v4 骨架优先流水线（设计与当前进展）

> v4 不是一条全新重写的管线，而是在 v3 基线之上增加三个关键阶段：
> 1）PlotSkeleton 骨架生成；2）guided TreeBuilder；3）节点文本填充。

### 1. 共同阶段（v3 / v4 共用）

以下阶段在 v3 / v4 中完全相同：

- 城市 + synopsis 输入（StorySynopsis）
- 完整文档生成：
  - Lore v1 / Lore v2
  - Protagonist
  - GDD
  - main story
- 世界书预分析（lore_v2 + GDD + main story）
- 角色列表提取（主角 + 若干配角）

### 2. v4 Stage B：PlotSkeleton 骨架生成

- 入口模块：
  - `src/ghost_story_factory/pregenerator/skeleton_model.py`
  - `src/ghost_story_factory/pregenerator/skeleton_generator.py`
- 数据结构：`PlotSkeleton`
  - Story-level: `title / config / acts / metadata`
  - Act: `index / label / beats`
  - Beat: `id / act_index / beat_type / tension_level / is_critical_branch_point / leads_to_ending / branches`
  - BranchSpec: `branch_type / max_children / notes`
- 行为：
  - 使用 `templates/plot-skeleton.prompt.md` 调用 LLM，生成骨架 JSON；
  - 解析为 `PlotSkeleton`，并做轻量校验（至少一幕、若干节拍）；
  - 如果骨架生成失败，则回退到 v3 行为（TreeBuilder 不启用 guided 模式）。

### 3. v4 Stage C：guided TreeBuilder

- 入口模块：
  - `src/ghost_story_factory/pregenerator/tree_builder.py`
- 对比 v3：
  - v3：TreeBuilder 仅依赖 env 阈值（MAX_DEPTH / MIN_MAIN_PATH_DEPTH 等）和 heuristics 决定扩展路径；
  - v4：TreeBuilder 多了 `plot_skeleton: Optional[PlotSkeleton]` 参数：
    - 当提供骨架时：`guided_mode = True`；
    - 以 depth → beat 的映射控制：
      - 每层允许的最大分支数（`branches.max_children` / `config.max_branches_per_node`）；
      - 哪些深度允许结局出现（`beat.leads_to_ending`）；
      - 关键节拍处优先生成 critical 分支。
- heuristics 调整：
  - 保留安全闸（MAX_TOTAL_NODES / PROGRESS_PLATEAU_LIMIT / Beam）；
  - guided 模式下：
    - 同轮扩展最多 1 次（`EXTEND_ON_FAIL_ATTEMPTS` 被收紧）；
    - 不再通过修改 env（MIN_DURATION_MINUTES / EXTEND_ON_FAIL_ATTEMPTS / FORCE_CRITICAL_INTERVAL）来“死磕”；
    - `TimeValidator` 仍负责最终深度/时长/结局校验。

### 4. v4 Stage D：节点文本填充

- 入口模块：
  - `src/ghost_story_factory/pregenerator/text_filler.py`
- 目标：
  - 在对话树结构稳定后，为每个节点追加节拍元数据；
  - 对 narrative 为空或全空白的节点填充占位叙事，避免出现“完全空节点”。
- 当前实现（第一阶段）：
  - `NodeTextFiller(skeleton).fill(dialogue_tree)` 会：
    - 为每个节点写入 `metadata.beat_type / tension_level / act_index`（根据深度映射到骨架 beat）；
    - 若 `narrative` 为空，则填入一个简短的占位文本（不覆盖已有叙事）。
- 后续演进方向：
  - 在骨架 + NodeTextFiller 的基础上，引入专门的“节点文案生成器”：
    - 按 beat 类型控制叙事长度与节奏；
    - 在 CRITICAL 分支上保证选项语义差异明显；
    - 在 MICRO 分支上只做气氛微调。

### 5. v4 与 v3 的关系

- v3 仍为当前生产基线，保证所有已有故事生成流程可用；
- v4 模块旁路集成到 `StoryGeneratorWithRetry` 中：
  - 先尝试生成骨架 → 若成功则启用 guided TreeBuilder + NodeTextFiller；
  - 骨架生成失败时自动回退到 v3 TreeBuilder 行为；
- 目标状态：
  - 当 v4 在多个真实故事上验证稳定后，将逐步把 v3 的 heuristics 逻辑下沉为“legacy/兼容路径”，把 v4 骨架模式升级为默认路径。

---

## 🚀 快速开始

### 1. MVP 测试（推荐首次使用）

```bash
# 快速测试单角色生成
python3 generate_mvp.py

# 查看日志
tail -f logs/generate_mvp_*.log
```

### 2. 智能并行生成（多角色）

```bash
# 同时生成多个角色
python3 generate_smart_parallel.py

# 查看日志
tail -f logs/generate_smart_parallel_*.log
```

### 3. 完整故事生成（从零开始）

```bash
# 生成完整故事（包含文档）
python generate_full_story.py --city 武汉

# 查看日志
tail -f logs/generate_full_story_*.log
```

---

## 📚 相关文档

- [架构概览](ARCHITECTURE.md)
- [游戏引擎](GAME_ENGINE.md)
- [并行生成](../PARALLEL_GENERATION.md)
- [快速开始](../../QUICK_START.md)
- [命令手册](../COMMANDS.md)

---

## 📝 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v3.0 | 2025-10-25 | 完整生成器优先 + 主线优先 + 硬闸 |
| v2.x | 2025-10-20 | 基础预生成系统 |
| v1.x | 2025-10-15 | 动态生成模式 |

---

**最后更新**: 2025-10-25
**维护者**: Ghost Story Factory Team
**状态**: ✅ 生产就绪
