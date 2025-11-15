# Ghost Story Factory 项目规格说明 v3.0

**文档版本**: v3.0  
**创建日期**: 2025-10-25  
**项目状态**: 🚦 发布候选（RC） - 架构 v3 已完成，按下述“验收标准与 Gating”落地后可标记生产  
**注意**: 本文档描述的是 **v3 架构规格**。自 `TASK_V4_DEFAULT_PIPELINE` 完成 M1/M2 起，**实际故事生成主路径已切换为 v4 骨架模式**，v3 仅作为兼容回退路径存在（通过 `USE_PLOT_SKELETON=0` 或骨架失败回退）。  

---

## 📋 文档索引

本文档是 Ghost Story Factory v3.0 的完整规格说明。如需查看其他文档：

- **快速上手**: `docs/QUICK_START.md`
- **架构详解**: `docs/architecture/NEW_PIPELINE.md`
- **使用指南**: `docs/guides/USAGE.md`
- **并行生成**: `docs/PARALLEL_GENERATION.md`
- **待开发功能**: `docs/specs/SPEC_TODO.md`

---

## 1. 项目概览

### 1.1 这是什么？

Ghost Story Factory 是一个**交互式恐怖故事生成与游玩系统**，包含两个核心能力：

**能力 1：智能故事生成器（Pregenerator）**
- 输入：城市名 + 故事概要
- 处理：多阶段 AI 内容生成流水线
- 输出：完整对话树 + 世界观文档 + 多角色剧情

**能力 2：交互式游戏引擎（Runtime Engine）**
- 运行模式：
  - **预生成模式**：零等待、流畅游玩（推荐）
  - **动态模式**：实时 LLM 生成（体验完整 AI 能力）
- 游戏类型：选择驱动的文字冒险（CYOA）
- 游玩时长：15-30 分钟
- 特色：多结局、状态管理、沉浸式叙事

### 1.2 核心产物

预生成阶段产出：
```
deliverables/程序-<城市>/
├── <城市>_<故事>_raw_materials.md    # 原始素材
├── <城市>_<故事>_lore_v1.md          # 世界观 v1（基础）
├── <城市>_<故事>_protagonist.md      # 主角 + 角色分析
├── <城市>_<故事>_lore_v2.md          # 世界观 v2（游戏化）
├── <城市>_<故事>_gdd.md              # 游戏设计文档
├── <城市>_<故事>_story.md            # 主线故事
└── <城市>_<故事>_branch_*.md         # 支线故事（N条）
```

数据库存储：
```
database/ghost_stories.db
├── cities              # 城市表
├── stories             # 故事表
├── characters          # 角色表
├── dialogue_nodes      # 对话节点表
└── story_metadata      # 元数据表
```

### 1.3 技术栈

**核心框架**：
- CrewAI：AI Agent 编排
- LiteLLM：多模型适配
- SQLite：数据持久化
- Rich：命令行美化

**LLM 提供商**：
- **主力**：Kimi (Moonshot AI)
- **备用**：OpenAI（已禁用，可选恢复）

**开发工具**：
- Python 3.11+
- uv：包管理
- pytest：测试框架

---

## 2. 架构 v3.0 核心设计

> ⚠️ 后补说明：自 TASK_V4_DEFAULT_PIPELINE 完成 M1/M2 之后，实际代码中的 StoryGenerator 主路径已经升级为 **v4 骨架流水线默认模式**（文档 → PlotSkeleton → guided TreeBuilder → NodeTextFiller → story_report）。  
> 本节仍按 v3 设计描述原始架构，用于理解 legacy 行为与兼容路径。v4 具体流程参见：  
> - `docs/architecture/STORY_PIPELINE_V4.md`  
> - `docs/architecture/NEW_PIPELINE.md`  
> - `docs/architecture/ADR-001-plot-skeleton-pipeline.md`

### 2.1 端到端流程

```
用户输入
  ↓
【阶段 1】选择与输入
  ├─ 城市选择
  └─ 故事概要（title/protagonist/location/duration）
  ↓
【阶段 2】文档生成（完整生成器优先）
  ├─ USE_FULL_GENERATOR=1 → 完整生成器
  │   ├─ raw_materials.md
  │   ├─ lore_v1.md
  │   ├─ protagonist.md
  │   ├─ lore_v2.md
  │   ├─ gdd.md
  │   └─ story.md
  │
  └─ 失败时 → 回退到内置简版生成
  ↓
【阶段 3】世界书预分析（早提醒）
  ├─ 解析 lore_v2 的节拍与结局信号
  ├─ 估算主线可达深度 / 结局数量
  └─ 若低于阈值 → 警告（但不中断）
  ↓
【阶段 4】角色确定
  ├─ 主角 = protagonist.md
  └─ 支线角色 = struct.json 或从主线提取
  ↓
【阶段 5】对话树构建（主线优先 + BFS）
  ├─ 策略：优先加深主线直至达标
  ├─ 生成单元：
  │   ├─ engine/choices.py（选择 JSON）
  │   └─ engine/response.py（叙事响应）
  ├─ 稳健性：
  │   ├─ 空响应 → 本地兜底
  │   ├─ 超时 → 默认选择
  │   └─ 默认后果含时间推进
  └─ 校验：MIN_MAIN_PATH_DEPTH、MAX_DEPTH、MIN_ENDINGS
  ↓
【阶段 6】同轮扩展直至达标
  ├─ 未达标 → 继续沿主线叶子加深
  └─ 达标或触发安全闸 → 结束
  ↓
【阶段 7】持久化
  ├─ 写入 database/ghost_stories.db
  └─ 保存完整对话树 + 统计信息
  ↓
【阶段 8】游玩
  ├─ 预生成模式：./start_pregenerated_game.sh
  └─ 动态模式：./start_full_game.sh
```

### 2.4 故事标识与映射（Slug）

为消除“只指明城市导致歧义”的特殊情况，统一使用“城市+标题”的稳定标识：

- 基本规则（只包含 `[a-z0-9-]`）：
  - `city_slug = pinyin(city).lower().replace(' ', '-')`
  - `title_slug = safe_kebab(title)`（见下）
  - `story_slug = f"{city_slug}__{title_slug}"`
- `safe_kebab(title)` 规范（确定性算法）：
  1) Unicode 归一化：NFKC（全角→半角）
  2) 过滤：仅保留字母/数字/空格/下划线/连字符，移除 emoji 与其它符号
  3) 非拉丁文字转写：
     - 汉字→拼音（无声调，按字符分词），示例：`静安寺地下电梯` → `jing-an-si-di-xia-dian-ti`
     - 无法转写时保留原字符再做降噪
  4) 小写
  5) 空白与下划线替换为 `-`
  6) 折叠多重 `-`，首尾去 `-`
  7) 长度上限 80；为空则用 `story`
  8) 与现有冲突时追加 `-2/-3/...`（由调用方保证唯一）

示例：
- 城市：`上海` → `shanghai`
- 标题：`静安寺地下电梯` → `jing-an-si-di-xia-dian-ti`
- 标题：`测试😊版 v2` → `ceshi-ban-v2`
- story_slug：`shanghai__jing-an-si-di-xia-dian-ti`

参考实现（示意）：
```python
def safe_kebab(s: str) -> str:
    import unicodedata, re
    s = unicodedata.normalize("NFKC", s)
    s = "".join(ch for ch in s if (ch.isalnum() or ch in " -_"))  # 过滤 emoji/符号
    try:
        from pypinyin import lazy_pinyin
        if any('\u4e00' <= ch <= '\u9fff' for ch in s):
            s = "-".join(lazy_pinyin(s))
    except Exception:
        pass
    s = s.lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return (s or "story")[:80]
```

映射关系：
- 目录：`deliverables/程序-<城市>/<标题>/...`
- DB：`stories.slug`（新列）存储 `<city_slug>__<title_slug>`，`stories.city`,`stories.title` 与 `story_slug` 对应；菜单按 `title` 展示。
- 失败摘要：必须包含 `city`, `title`, `story_slug` 字段，便于故障归集。

数据库变更（迁移）：
- 新增列与索引：
  - `ALTER TABLE stories ADD COLUMN slug TEXT;`
  - `CREATE INDEX IF NOT EXISTS idx_stories_slug ON stories(slug);`
  - 当前实现会在新库创建上述列；旧库需手动执行一次迁移（或清库）。

### 2.2 关键模块映射

| 功能模块 | 实现文件 | 职责 |
|---------|---------|------|
| **入口与协调** | `pregenerator/story_generator.py` | 完整流程编排、重试控制 |
| **世界书生成** | 完整生成器 + 内置回退 | Lore v1/v2、GDD、主线 |
| **预分析与阈值** | `story_generator.py` + `time_validator.py` | 早期质量评估、阈值校验 |
| **对话树生成** | `pregenerator/tree_builder.py` | 主线优先 BFS、检查点保存 |
| **选择点生成** | `engine/choices.py` | 生成选择 JSON（含结局引导） |
| **响应生成** | `engine/response.py` | 叙事响应（强调伏笔回收） |
| **状态管理** | `pregenerator/state_manager.py` | 时间哈希、量化去重 |
| **数据库** | `database/db_manager.py` | 持久化、查询、统计 |

### 2.3 配置开关（环境变量）

**深度与质量阈值**：
```bash
MAX_DEPTH=50                 # 最大对话深度
MIN_MAIN_PATH_DEPTH=30       # 主线最小深度
MIN_DURATION_MINUTES=12      # 最小游玩时长
MIN_ENDINGS=1                # 最小结局数量
```

**扩展安全闸**：
```bash
MAX_TOTAL_NODES=300          # 单轮最大节点数（防爆炸）
PROGRESS_PLATEAU_LIMIT=2     # 平台期探测（连续 N 轮无进展停止）
```

**重试策略**（推荐关闭）：
```bash
MAX_RETRIES=0                # 禁用跨轮重试
AUTO_RESTART_ON_FAIL=0       # 禁用失败重启
```

**完整生成器**：
```bash
USE_FULL_GENERATOR=1         # 启用完整生成器（推荐）
FULL_INCLUDE_BRANCHES=0      # 跳过支线生成（提速）
```

**LLM 提供商**（仅 Kimi）：
```bash
KIMI_API_KEY=sk-***
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2-0905-preview

# 禁用 OpenAI（清空以下变量）
OPENAI_API_KEY=
OPENAI_BASE_URL=
```

**并发控制**（推荐串行）：
```bash
KIMI_CONCURRENCY=1           # 主流程并发数
KIMI_CONCURRENCY_CHOICES=1   # 选择点生成并发数
```

---

## 3. 核心设计原则

### 3.1 Linus 的"好品味"（Good Taste）

**原则**：消除特殊情况，让代码自然流动。

**案例 1：状态去重的量化合并**
```python
# 糟糕的设计（特殊情况太多）
if PR == 20: merge()
elif PR == 21: merge()
elif PR == 22: merge()
# ...

# 好品味的设计（消除特殊情况）
PR_rounded = int(round(PR / 5) * 5)  # ±5 合并
```

**案例 2：兜底策略的统一处理**
```python
# 糟糕的设计（到处都是 try-except）
try:
    choices = llm.generate()
except:
    choices = DEFAULT_CHOICES

# 好品味的设计（统一兜底层）
choices = llm.generate() or get_default_choices(state)
```

### 3.2 Never Break Userspace

**铁律**：向后兼容是神圣不可侵犯的。

**案例 1：命令行工具**
```bash
# 旧命令必须继续工作
ghost-story-play --city 杭州

# 新功能用新参数
ghost-story-play --city 杭州 --pregenerated
```

**案例 2：数据库 Schema**
```sql
-- 新增列必须有默认值
ALTER TABLE stories ADD COLUMN version TEXT DEFAULT 'v3';

-- 禁止删除旧列（除非有迁移脚本）
-- ALTER TABLE stories DROP COLUMN old_field;  ❌
```

### 3.3 实用主义（Pragmatism）

**原则**：解决实际问题，不为理论完美而堆砌复杂度。

**案例 1：失败重试**
```python
# 理论完美：指数退避 + 抖动 + 熔断器
# 实际问题：用户等不了那么久

# 实用方案：简单重试 + 快速失败
MAX_RETRIES = 0  # 禁用重试，直接兜底
```

**案例 2：并行生成**
```python
# 理论完美：动态负载均衡 + 优先级队列
# 实际问题：Kimi API 限流很严格

# 实用方案：串行生成 + 检查点保存
KIMI_CONCURRENCY = 1
```

### 3.4 简洁执念（Simplicity）

**原则**：如果需要超过 3 层缩进，重新设计它。

**案例 1：对话树生成**
```python
# 糟糕的设计（5 层嵌套）
for node in nodes:
    if node.is_leaf:
        for choice in generate_choices(node):
            if choice.is_valid:
                for consequence in choice.consequences:
                    if consequence.type == "ending":
                        # ...

# 好设计（提取函数，1-2 层嵌套）
def expand_leaf_node(node):
    choices = generate_choices(node)
    valid_choices = filter_valid(choices, node.state)
    return [apply_consequence(c) for c in valid_choices]

for node in leaf_nodes:
    if node.is_leaf:
        expand_leaf_node(node)
```

---

## 4. 使用指南

### 4.1 快速开始

**一键生成完整故事**：
```bash
python tools/generate_mvp.py
```

**自定义生成**：
```bash
python generate_full_story.py \
  --city 上海 \
  --title "静安寺地铁站末班逆旅" \
  --output deliverables/程序-上海/
```

**并行生成（多角色对话树）**：
```bash
python generate_smart_parallel.py \
  --city 杭州 \
  --title "宝石山避雷针" \
  --max-concurrent 2
```

**游玩预生成故事**（推荐）：
```bash
./start_pregenerated_game.sh
```

**游玩动态生成故事**（实时 LLM）：
```bash
./start_full_game.sh
```

### 4.2 命令清单

**生成器命令**：
- `python tools/generate_mvp.py` - MVP 快速生成
- `python generate_full_story.py` - 完整故事生成
- `python generate_smart_parallel.py` - 并行角色生成

**游戏命令**：
- `./start_pregenerated_game.sh` - 启动预生成模式
- `./start_full_game.sh` - 启动动态模式
- `python play_game_pregenerated.py` - 直接运行预生成游戏

**工具命令**：
- `./scripts/check_progress.sh` - 检查生成进度
- `./scripts/db_inspect.sh` - 检查数据库内容
- `./scripts/clean.sh` - 清理临时文件

### 4.3 环境配置

**最小配置**（`.env`）：
```bash
# 必填：Kimi API
KIMI_API_KEY=sk-***

# 可选：自定义配置
KIMI_MODEL=kimi-k2-0905-preview
MAX_DEPTH=50
MIN_MAIN_PATH_DEPTH=30
```

**完整配置**：参见 `ENV_EXAMPLE.md`

---

## 5. 质量保障

### 5.1 自动化测试

**测试套件**：
```bash
python run_all_tests.py
```

**单元测试**：
```bash
pytest tests/ -v
```

**集成测试**：
```bash
pytest test_full_flow.py -v
```

### 5.2 日志系统

**日志位置**：
```
logs/
├── generate_mvp_20251025_194855.log
├── generate_full_story_20251025_203020.log
└── generate_smart_parallel_20251025_210133.log
```

**日志内容**：
- 完整的生成流程记录
- 错误堆栈跟踪
- API 调用统计
- 性能指标

### 5.3 错误处理

**分级兜底策略**：
```python
try:
    # 尝试 LLM 生成
    choices = llm.generate_choices(state)
except TimeoutError:
    # 超时兜底
    choices = get_default_choices_for_scene(state.scene)
except JSONDecodeError:
    # JSON 解析失败兜底
    choices = parse_with_regex(raw_response)
except Exception:
    # 最终兜底（保证游戏不中断）
    choices = EMERGENCY_FALLBACK_CHOICES
```

### 5.4 验收标准与 Gating（RC → 生产）

一次“预生成→入库→可游玩”的合格故事必须满足：
- 质量阈值：
  - `MIN_MAIN_PATH_DEPTH ≥ 30`
  - `MIN_DURATION_MINUTES ≥ 12`
  - `MIN_ENDINGS ≥ 1`
  - `MAX_DEPTH ≤ 50`
- 扩展策略：
  - `EXTEND_ON_FAIL_ATTEMPTS ≥ 4`
  - `PROGRESS_PLATEAU_LIMIT ∈ {2,3}`
  - `SECONDS_PER_CHOICE ≥ 90`（预生成模式建议值）
  - `FORCE_CRITICAL_INTERVAL ∈ {2,3}`（每 N 场景强制注入 critical 选项以推进/收束）
- 提供商与并发：
  - 仅 Kimi（`OPENAI_*` 为空）
  - `KIMI_CONCURRENCY = 1`，`KIMI_CONCURRENCY_CHOICES = 1`
- 可追溯性：
  - 运行日志：`logs/full_generation_*.log`
  - 失败摘要：`logs/failures/*.json`（见 5.5）

#### 自动降级策略（可选）
当未达标时，允许按以下顺序自动降级一次（记录在失败摘要 `suggested_fixes` 与日志中）：
1) 降低 `MIN_DURATION_MINUTES`（12→10）若 `estimated_duration ∈ [9,12)`
2) 保持时长，增加 `EXTEND_ON_FAIL_ATTEMPTS`（+2）若 `plateau_rounds < PROGRESS_PLATEAU_LIMIT`
3) 将 `FORCE_CRITICAL_INTERVAL` 降至 2，强制注入 critical 以触发结局路径
4) 若仍无法达标，则失败，不再继续降级（避免破坏叙事质量）

实现说明：当前实现通过设置环境变量触发降级，需在同一轮结束后重跑一次以生效；后续可升级为同轮自动复评。

### 5.5 失败摘要 JSON 规范

路径：`logs/failures/<city>_<title>_<timestamp>.json`

必填字段：
```json
{
  "city": "上海",
  "title": "静安寺地下电梯",
  "story_slug": "shanghai__jing-an-si-di-xia-dian-ti",
  "attempt": 1,
  "failure_reason": "时长不足 est=8.8 < min=12",
  "quality_state": "rejected",
  "validator_report": {
    "estimated_duration_minutes": 8.8,
    "main_path_depth": 7,
    "endings_count": 0,
    "thresholds": {"min_duration": 12, "min_depth": 30, "min_endings": 1}
  },
  "builder_metrics": {
    "total_nodes": 22,
    "max_depth": 7,
    "plateau_rounds": 3
  },
  "runtime_config": {
    "MAX_DEPTH": 50,
    "EXTEND_ON_FAIL_ATTEMPTS": 4,
    "PROGRESS_PLATEAU_LIMIT": 3,
    "SECONDS_PER_CHOICE": 90,
    "FORCE_CRITICAL_INTERVAL": 2
  },
  "timestamps": {"start": "...", "end": "..."},
  "log_path": "logs/full_generation_20251025_203020.log"
}
```
说明：字段名称与类型为兼容稳定接口；新增字段需向后兼容。

推荐字段（可选）：
```json
"suggested_fixes": [
  {"action": "increase", "param": "EXTEND_ON_FAIL_ATTEMPTS", "to": 6},
  {"action": "set", "param": "FORCE_CRITICAL_INTERVAL", "to": 2},
  {"action": "decrease", "param": "MIN_DURATION_MINUTES", "to": 10}
]
```

---

## 6. 与 v2 的关键差异

| 维度 | v2（旧架构） | v3（新架构） |
|-----|-----------|-----------|
| **世界观生成** | 简版文档 → 直接生成树 | 完整生成器 → 高质量文档 → 生成树 |
| **质量门槛** | 无预分析 | 世界书预分析 + 早提醒 |
| **生成策略** | 随机扩展 | 主线优先 + 结局门槛 |
| **失败处理** | 整轮重跑（死循环风险） | 同轮扩展 + 硬闸保护 |
| **LLM 提供商** | Kimi + OpenAI | 仅 Kimi（清晰性） |
| **稳健性** | JSON 失败中断 | 多级兜底策略 |
| **日志系统** | 分散打印 | 集中式日志 + 时间戳文件 |
| **并行生成** | 无 | 智能并行 + 检查点保存 |

---

## 7. 已知限制与风险

### 7.1 当前限制

1. **单提供商依赖**：仅支持 Kimi，若 API 不可用则无法生成
2. **无自动质量评估**：依赖人工测试发现内容质量问题
3. **缺少回归测试**：改进后不知道质量是提升还是下降
4. **性能监控不完善**：缺少详细的成本追踪和性能分析

### 7.2 风险缓解

**风险 1：文档质量不确定**
- **缓解**：完整生成器优先 + 失败回退简版
- **建议**：增加质量评分器（见潜在改进）

**风险 2：生成时间长**
- **缓解**：检查点保存 + 断点续传
- **建议**：优化 Prompt 减少 Token 消耗

**风险 3：LLM 限流**
- **缓解**：串行生成 + 重试退避
- **建议**：增加提供商抽象层

---

## 8. 潜在改进方向

详见 `docs/specs/SPEC_TODO.md` 第 13 节：

**高优先级**：
1. 文档质量门槛检查（评分 0-100）
2. 自动化质量评估（叙事连贯性、氛围）
3. 性能监控和成本追踪
4. 缓存机制（节省 30-50% 成本）

**中优先级**：
5. 预分析改用静态分析（提高准确性）
6. 配置管理集中化（便于维护）
7. 混合生成策略（平衡主线和分支）
8. 提供商抽象层（降低风险）

**低优先级**：
9. 状态去重优化（自适应策略）
10. A/B 测试框架（科学决策）
11. 回归测试（质量保障）

---

## 9. 文档索引

### 9.1 用户文档

- **快速开始**: `docs/QUICK_START.md`
- **使用指南**: `docs/guides/USAGE.md`
- **工作流程**: `docs/guides/WORKFLOW.md`
- **快速参考**: `docs/guides/QUICK_REFERENCE.md`

### 9.2 技术文档

- **架构总览**: `docs/architecture/ARCHITECTURE.md`
- **新流程详解**: `docs/architecture/NEW_PIPELINE.md`
- **游戏引擎**: `docs/architecture/GAME_ENGINE.md`
- **并行生成**: `docs/PARALLEL_GENERATION.md`
- **骨架模式 v4 草案**: `docs/architecture/STORY_PIPELINE_V4.md`

### 9.3 规格文档

- **本文档**: `docs/specs/SPEC_V3.md`（你在这里）
- **待开发功能**: `docs/specs/SPEC_TODO.md`

### 9.4 其他文档

- **安装指南**: `docs/INSTALLATION.md`
- **命令清单**: `docs/COMMANDS.md`
- **环境配置**: `ENV_EXAMPLE.md`
- **总览索引**: `docs/INDEX.md`
- **架构决策 ADR**: `docs/architecture/ADR-001-plot-skeleton-pipeline.md`

---

## 10. 原则与文化

### 10.1 Good Taste

> "能重构就不加分支；把'特殊情况'变成'正常情况'。"
> —— Linus Torvalds

**示例**：
- 量化去重（PR ±5 合并）
- 统一兜底层（而非到处 try-except）

### 10.2 Never Break Userspace

> "我们不破坏用户空间！任何导致现有程序崩溃的改动都是 bug。"
> —— Linus Torvalds

**示例**：
- 命令名保持稳定
- 数据库 Schema 向后兼容
- 新功能用新参数

### 10.3 Pragmatism

> "我是个该死的实用主义者。解决实际问题，而不是假想的威胁。"
> —— Linus Torvalds

**示例**：
- 禁用重试（用户等不了）
- 串行生成（避免限流）

### 10.4 Simplicity

> "如果需要超过 3 层缩进，你就完蛋了。"
> —— Linus Torvalds

**示例**：
- 提取函数（而非深度嵌套）
- 早返回（而非 if-else 地狱）

---

## 11. 常见问题（FAQ）

### Q1：为什么禁用 OpenAI？

**A**：架构 v3 为了清晰性和稳定性，专注于单一提供商（Kimi）。如需恢复 OpenAI：
```bash
OPENAI_API_KEY=sk-***
OPENAI_BASE_URL=https://api.openai.com/v1
```

### Q2：如何提高生成质量？

**A**：
1. 使用 `USE_FULL_GENERATOR=1`（完整生成器）
2. 提高阈值：`MIN_MAIN_PATH_DEPTH=40`、`MIN_ENDINGS=2`
3. 手动审核 `lore_v2.md` 和 `gdd.md`

### Q3：生成失败怎么办？

**A**：
1. 检查日志文件（`logs/` 目录）
2. 查看错误堆栈跟踪
3. 降低阈值或跳过支线（`FULL_INCLUDE_BRANCHES=0`）
4. 使用检查点恢复（`checkpoint.json`）

### Q4：如何节省成本？

**A**：
1. 启用缓存（待实现）
2. 减少最大深度：`MAX_DEPTH=30`
3. 跳过支线生成：`FULL_INCLUDE_BRANCHES=0`
4. 使用 MVP 模式（`tools/generate_mvp.py`）

### Q5：如何贡献代码？

**A**：
1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/xxx`
3. 遵循代码规范（PEP 8、类型注解、中文注释）
4. 编写测试（覆盖率 ≥ 80%）
5. 提交 PR 并说明改动理由

---

## 12. 联系方式

**项目维护者**：@yehan
**GitHub**：https://github.com/your-repo/ghost-story-factory
**问题反馈**：提交 Issue 或 PR

---

**文档版本**: v3.0
**最后更新**: 2025-10-25
**下次审核**: 2025-11-25

---

## 附录 A：术语表

| 术语 | 英文 | 定义 |
|-----|-----|------|
| **世界观** | Lore | 定义故事世界规则、实体、地点的文档 |
| **GDD** | Game Design Document | 游戏设计文档，定义场景、选择点、结局 |
| **主线** | Main Thread | 从开场到结局的主要故事路径 |
| **支线** | Branch | 其他角色视角的独立故事线 |
| **对话树** | Dialogue Tree | 选择驱动的分支故事结构 |
| **节点** | Node | 对话树中的一个状态点 |
| **选择点** | Choice Point | 玩家可以做出选择的节点 |
| **后果** | Consequence | 选择导致的状态变化 |
| **PR** | Personal Resonance | 个人共鸣度（0-100） |
| **GR** | Global Resonance | 全局共鸣度（多人共享） |
| **WF** | World Fatigue | 世界疲劳值（0-10） |
| **兜底** | Fallback | 错误时的默认处理逻辑 |
| **检查点** | Checkpoint | 生成进度的保存点 |

---

## 附录 B：配置速查表（含使用场景）

| 配置项 | 默认值 | 说明 | 建议值 | 使用场景 |
|-------|-------|------|--------|----------|
| `MAX_DEPTH` | 50 | 最大对话深度 | 30-50 | 复杂主线或高叙事密度时取高值 |
| `MIN_MAIN_PATH_DEPTH` | 30 | 主线最小深度 | 30-40 | 确保可玩性与探索感 |
| `MIN_DURATION_MINUTES` | 12 | 最小游玩时长（分钟） | 12-20 | 城市题材长篇；短篇可按降级策略到 10 |
| `MIN_ENDINGS` | 1 | 最小结局数量 | 1-3 | 需要强收束时取 2-3 |
| `MAX_TOTAL_NODES` | 300 | 单轮最大节点数 | 200-300 | 限制成本/避免爆炸 |
| `PROGRESS_PLATEAU_LIMIT` | 2 | 平台期限制 | 2-3 | 模型难推进时取 3 |
| `EXTEND_ON_FAIL_ATTEMPTS` | 4 | 未达标时同轮扩展次数 | 4-6 | 平台化明显时取 6 |
| `SECONDS_PER_CHOICE` | 90 | 每步时间估计（秒） | 90-120 | 文本更厚重时取 120 |
| `FORCE_CRITICAL_INTERVAL` | 2 | 每 N 场景必含 critical 选项 | 2-3 | 快速达成结局/线索回收 |
| `MAX_RETRIES` | 0 | 最大重试次数 | 0（禁用） | 快速失败、便于诊断 |
| `AUTO_RESTART_ON_FAIL` | 0 | 失败自动重启 | 0（禁用） | 避免无谓消耗 |
| `USE_FULL_GENERATOR` | 1 | 使用完整生成器 | 1（启用） | 高质量生成必开 |
| `FULL_INCLUDE_BRANCHES` | 0 | 包含支线生成 | 0（跳过） | 追求速度时关闭 |
| `KIMI_CONCURRENCY` | 1 | Kimi 并发数 | 1（串行） | 限流环境/提升稳定性 |

---

## 附录 C：文件结构速查

```
ghost-story-factory/
├── docs/                           # 文档目录
│   ├── specs/                      # 规格文档
│   │   ├── SPEC_V3.md             # 本文档
│   │   └── SPEC_TODO.md           # 待开发功能
│   ├── architecture/               # 架构文档
│   │   ├── NEW_PIPELINE.md        # 新流程详解
│   │   ├── GAME_ENGINE.md         # 游戏引擎
│   │   └── ARCHITECTURE.md        # 总览
│   ├── guides/                     # 使用指南
│   │   ├── USAGE.md
│   │   ├── WORKFLOW.md
│   │   ├── QUICK_REFERENCE.md
│   │   └── BRANCH_GENERATION.md
│   └── INDEX.md                    # 文档索引
├── src/                            # 源代码
│   └── ghost_story_factory/
│       ├── pregenerator/           # 预生成器
│       ├── engine/                 # 游戏引擎
│       ├── database/               # 数据库
│       ├── runtime/                # 运行时
│       ├── ui/                     # 用户界面
│       └── utils/                  # 工具库
├── tools/                          # 工具脚本
│   ├── generate_mvp.py
│   └── run_all_tests.py
├── scripts/                        # Shell 脚本
│   ├── check_progress.sh
│   ├── db_inspect.sh
│   └── clean.sh
├── templates/                      # Prompt 模板
├── database/                       # 数据库文件
├── deliverables/                   # 生成产物
├── logs/                           # 日志文件
└── saves/                          # 游戏存档
```

---

**结束 - 感谢阅读！**
