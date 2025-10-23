# AI 灵异地图 - 设计模式库 (Design Pattern Library)

> **核心理念：** 契约式开发管线 (Contract-Based Pipeline)
> **设计哲学：** Linus Torvalds 的"Good Taste" - 数据结构优先，向后兼容，实用主义

---

## ⚡ AI使用提示：避免上下文浪费

**⚠️ 本文件夹共35个文件，约8,520行代码，一次性加载会消耗15-20万tokens！**

**✅ 推荐做法（分层加载）：**
1. 🎯 **首次对话：** 只读 [`00-index.md`](./00-index.md) + [`00-architecture.md`](./00-architecture.md)（~4k tokens）
2. 📖 **任务执行：** 按需读取相关模块的 `.design.md` 和 `.prompt.md`
3. 💡 **参考示例：** 仅在需要时读取 `.example.md`（通常是最大的文件）

**📚 详细指南：** 请查看 [`00-index.md`](./00-index.md) - 包含完整的加载策略和常见任务示例

**Token节省：** 使用分层加载可节省 **80-95%** 的上下文消耗！

---

## 📐 架构全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                  00-architecture.md (元架构)                     │
│         定义：阶段0→1→2(A||B)→3(C||D||E) 的数据流与依赖关系        │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段1: 地基层 (Lore Foundation) - 回答 "Why & What"              │
├─────────────────────────────────────────────────────────────────┤
│  lore-v1.design.md   │ 高保真 | 百科全书式 | 钩子分离               │
│  lore-v1.example.md  │ 荔湾广场案例: 8事件+3地点+2实体+形而上学      │
│  lore-v1.prompt.md   │ 输入:原始素材 → 输出:世界书1.0              │
└─────────────────────────────────────────────────────────────────┘
                    ↓                              ↓
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ 阶段2A: 逻辑层 (Who)         │  │ 阶段2B: 系统层 (How)          │
├──────────────────────────────┤  ├──────────────────────────────┤
│ protagonist.design.md        │  │ lore-v2.design.md            │
│   三维评估模型               │  │   保留地基+构建系统           │
│                              │  │                              │
│ protagonist.example.md       │  │ lore-v2.example.md           │
│   保安/顾客/店主分析         │  │   共鸣度+后果树               │
│                              │  │                              │
│ protagonist.prompt.md        │  │ lore-v2.prompt.md            │
│   世界书1 → 主角推导         │  │   世界书1 → 世界书2           │
└──────────────────────────────┘  └──────────────────────────────┘
                    ↓                              ↓
                    └──────────────┬───────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段3: 故事生成层 (Story Generation) - 回答 "How to Tell"        │
└─────────────────────────────────────────────────────────────────┘
         ↓                         ↓                        ↓
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
│ 3C: 导演设计     │  │ 3D: 主线执行          │  │ 3E: 支线并行      │
├──────────────────┤  ├──────────────────────┤  ├──────────────────┤
│ GDD.design.md    │  │ main-thread.design   │  │ branch-1.design  │
│  角色驱动        │  │  场景化流程          │  │  店主线          │
│  系统为核        │  │  沉浸式文笔          │  │                  │
│                  │  │                      │  │ branch-2.design  │
│ GDD.example.md   │  │ main-thread.example  │  │  顾客线          │
│  AI导演简报      │  │  保安线完整故事      │  │                  │
│  (保安线)        │  │  (≥1800字)          │  │ branch-1.example │
│                  │  │                      │  │ branch-2.example │
│ GDD.prompt.md    │  │ main-thread.prompt   │  │  关联点设计      │
│  规则→流程       │  │  简报→故事           │  │                  │
│                  │  │                      │  │ branch-1.prompt  │
│                  │  │                      │  │ branch-2.prompt  │
└──────────────────┘  └──────────────────────┘  └──────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段4: 交互运行层 (Runtime) - 回答 "How to Play"                 │
└─────────────────────────────────────────────────────────────────┘
         ↓                         ↓                        ↓
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
│ 4F: 实时响应     │  │ 4G: 意图识别          │  │ 4H: 状态管理      │
├──────────────────┤  ├──────────────────────┤  ├──────────────────┤
│ runtime-response │  │ intent-mapping       │  │ state-management │
│  .design.md      │  │  .design.md          │  │  .design.md      │
│  单次交互        │  │  自然语言→意图       │  │  游戏状态        │
│  分层响应        │  │  后果树绑定          │  │  规则验证        │
│                  │  │                      │  │                  │
│ .example.md      │  │ .example.md          │  │ .example.md      │
│  玩家输入→响应   │  │  意图分类示例        │  │  状态更新示例    │
│  场景1-5示例     │  │  歧义处理            │  │  级联更新        │
│                  │  │                      │  │                  │
│ .prompt.md       │  │ .prompt.md           │  │ .prompt.md       │
│  输入+状态→响应  │  │  文本→意图+目标      │  │  状态验证+更新   │
└──────────────────┘  └──────────────────────┘  └──────────────────┘
```

---

## 🔄 数据流与依赖关系

```
┌──────────────┐
│ 原始素材      │ (互联网传说、民间故事)
└──────┬───────┘
       ↓ [lore-v1.prompt.md]
┌──────────────┐
│ 世界书 1.0    │ (单一事实来源 - Single Source of Truth)
│              │
│ - 历史年表    │ (不可变事实)
│ - 地理志      │ (3个核心地点)
│ - 实体        │ (2个关键实体)
│ - 形而上学    │ (诅咒规则)
│ - [钩子]      │ (可扩展接口)
└──────┬───────┘
       ├─────────────────┬─────────────────┐
       ↓                 ↓                 ↓
       │ [protagonist    │ [lore-v2        │
       │  .prompt.md]    │  .prompt.md]    │
       ↓                 ↓                 │
┌─────────────┐   ┌─────────────┐         │
│ 角色分析     │   │ 世界书 2.0   │         │
│             │   │             │         │
│ - 保安 ✅    │   │ - 1.0内容   │ (100%保留)│
│ - 顾客 ❌    │   │ - 共鸣系统  │ (新增)   │
│ - 店主 ❌    │   │ - 后果树    │ (新增)   │
└──────┬──────┘   └──────┬──────┘         │
       │                  │                │
       └──────────┬───────┘                │
                  ↓                        │
           ┌─────────────┐                 │
           │ AI导演简报   │ [GDD.prompt.md]│
           │             │ ←───────────────┘
           │ - 场景流程  │
           │ - 共鸣追踪  │
           │ - 分支点    │
           └──────┬──────┘
                  ↓
          ┌───────┴────────┐
          ↓                ↓
   ┌─────────────┐  ┌─────────────┐
   │ 主线故事     │  │ 支线故事     │
   │             │  │             │
   │ - 保安线    │  │ - 店主线    │ [branch-1]
   │   (主角)    │  │   (关联)    │
   │             │  │             │
   │ ≥1800字     │  │ - 顾客线    │ [branch-2]
   │ 沉浸式      │  │   (呼应)    │
   │ UP主风格    │  │             │
   └─────────────┘  └─────────────┘
          ↓                ↓
          └────────┬───────┘
                   ↓
         [完整的互联世界]
       (主线+支线通过关联点形成统一时空)
```

---

## 📁 文件结构说明

### 📋 三文件模式 (Design-Example-Prompt)

每个模块都遵循统一的三文件结构：

| 文件类型 | 命名模式 | 作用 | 受众 |
|---------|---------|------|------|
| **设计文档** | `*.design.md` | 定义设计哲学、架构原则、核心机制 | 架构师、未来维护者 |
| **范文示例** | `*.example.md` | 提供高质量的实现案例（如荔湾广场） | 内容创作者、AI参考 |
| **生成提示** | `*.prompt.md` | 定义 AI 生成器的系统提示与约束 | LLM、自动化工具 |

---

### 🗂️ 模块详解

#### 00-architecture.md
- **类型：** 元架构文档
- **作用：** 定义整个开发管线的阶段划分与数据流
- **关键内容：** 阶段0(原始素材) → 阶段1(地基) → 阶段2(并行派生)

---

#### Lore v1 (地基层)
- **设计哲学：** 高保真 (High Fidelity) - 严禁凭空创造
- **核心机制：** 钩子分离 (Hook-Fact Separation)
- **数据结构：** 4部分（历史年表 + 地理志 + 实体 + 形而上学）
- **作用：** 建立"客观的、不可变的"世界观合约

**文件：**
- `lore-v1.design.md` - 百科全书式架构原则
- `lore-v1.example.md` - 荔湾广场完整案例 (7.5K)
- `lore-v1.prompt.md` - 原始素材 → 世界书1.0 生成器

---

#### Lore v2 (系统层)
- **设计哲学：** 保留地基，构建系统 (Lore Intact, Systems Added)
- **核心机制：** 统一共鸣度系统 + 可交互后果树
- **数据结构：** 继承v1全部内容 + 新增第五部分（核心游戏系统）
- **作用：** 将"线性博物馆"升级为"动态游戏蓝图"

**文件：**
- `lore-v2.design.md` - 系统化与动态化原则
- `lore-v2.example.md` - 共鸣度+后果树+行为等级 (8.8K)
- `lore-v2.prompt.md` - 世界书1.0 → 世界书2.0 升级器

---

#### Protagonist (逻辑层)
- **设计哲学：** 逻辑优先 (Logic-First) - 主角选择是推导，非创意
- **核心机制：** 三维评估模型（访问权 + 交集点 + 动机）
- **数据结构：** 角色分析报告（对比评估 + 最终推荐）
- **作用：** 在写故事前通过逻辑确定唯一正确的主角

**文件：**
- `protagonist.design.md` - 多维评估模型架构
- `protagonist.example.md` - 保安/顾客/店主对比分析 (4.2K)
- `protagonist.prompt.md` - 世界书1.0 → 主角推导器

---

#### GDD (导演设计层)
- **设计哲学：** 角色驱动 + 系统为核 (Role-Driven & Systems-First)
- **核心机制：** 场景化流程（关键场景 + 共鸣度追踪 + 后果树分支）
- **数据结构：** AI 导演任务简报（角色目标 + 场景流程 + 系统规则）
- **作用：** 将《世界书 2.0》的规则转译为可执行的剧情流程

**文件：**
- `GDD.design.md` - 五大核心原则（角色驱动/系统为核/场景化/动态分支/关联保真）
- `GDD.example.md` - 保安线 AI 导演任务简报（场景1-6）
- `GDD.prompt.md` - 世界书2.0 + 角色分析 → AI 导演简报生成器

---

#### Main Thread (主线执行层)
- **设计哲学：** Show, Don't Tell - 沉浸式叙事优先
- **核心机制：** UP 主风格（第二人称 + 音效 + 停顿 + 多感官细节）
- **数据结构：** 长篇 Markdown 文案（≥1800 字，分章节，强节奏）
- **作用：** 将 AI 导演简报演绎为完整的主线故事范文

**文件：**
- `main-thread.design.md` - 沉浸式文笔设计原则
- `main-thread.example.md` - 保安线完整故事范文《荔湾尸场：4:44 的巡更》
- `main-thread.prompt.md` - AI 导演简报 → 主线故事生成器

---

#### Branch 1 & 2 (支线并行层)
- **设计哲学：** Interconnected World - 通过关联点构建统一时空
- **核心机制：** 支线与主线在同一时间发生，通过"关联点"形成呼应
- **数据结构：** 支线故事文案（店主线/顾客线，各自独立但与保安线关联）
- **作用：** 让世界感觉"活"了起来，不同角色的故事在同一世界中交织

**文件：**
- `branch-1.design.md` - 店主线设计（四楼 + 破财 + 4:44 目击）
- `branch-1.example.md` - 店主线完整故事《荔湾尸场：第四层的算盘》
- `branch-1.prompt.md` - 世界书2.0 → 店主线生成器
- `branch-2.design.md` - 顾客线设计（被困 + B3 + 白衣女子警告）
- `branch-2.example.md` - 顾客线完整故事
- `branch-2.propmt.md` - 世界书2.0 → 顾客线生成器

---

#### Choice Points (选择点设计层) 🎯 **核心**
- **设计哲学：** 结构化自由 - 给玩家选择感，但在框架内运行
- **核心机制：** 三级选择点（微选择/普通选择/关键选择）+ 后果树绑定
- **数据结构：** 选项列表（2-4个选项，每个选项对应不同后果和分支）
- **作用：** 在关键剧情节点设置明确选项，引导剧情分支，限制玩家在框架内

**文件：**
- `choice-points.design.md` - 六大核心原则（分层选择/4W原则/笼子设计/后果映射/必经点/2-4法则）
- `choice-points.example.md` - 场景1-5的选择点实战示例（微选择/普通选择/关键选择/限制跳出）
- `choice-points.prompt.md` - 情境+状态 → 选项生成器

---

#### Runtime Response (实时响应生成层)
- **设计哲学：** 单次交互的原子性 + 状态驱动叙事
- **核心机制：** 四层响应结构（物理反馈/感官细节/心理暗示/引导提示）
- **数据结构：** 单次交互响应（200-500字，包含状态更新和事件触发）
- **作用：** 基于玩家选择生成沉浸式的AI响应，推进剧情

**文件：**
- `runtime-response.design.md` - 六大核心原则（原子性/状态驱动/分层结构/软硬引导/失败即内容/氛围连续）
- `runtime-response.example.md` - 场景1-5的完整交互示例（探索/干预/逃跑/错误处理）
- `runtime-response.prompt.md` - 玩家选择+状态 → 实时响应生成器

---

#### Intent Mapping (意图识别与映射层)
- **设计哲学：** 选项→意图→后果的清晰映射
- **核心机制：** 验证Choice Points生成的选项映射 + 前置条件检查 + 后果树绑定
- **数据结构：** 选项映射表（choice_id → intent → consequence）
- **作用：** 确保玩家选择能准确映射到游戏逻辑和后果分支（在选项式游戏中，不处理自由文本解析）

**主要职责：**
1. 验证选项映射（确认选项ID对应的意图）
2. 检查前置条件（验证玩家是否满足条件）
3. 绑定后果树（确认选项对应的GDD分支）
4. 处理特殊情况（极少数的自由文本补充，如输入NPC名字）

**文件：**
- `intent-mapping.design.md` - 在选项式游戏中的新角色 + 可选的自由输入式扩展
- `intent-mapping.example.md` - 选项映射示例（包含特殊情况处理）
- `intent-mapping.prompt.md` - 选项选择 → 意图验证 + 后果绑定

---

#### State Management (状态管理层)
- **设计哲学：** 状态即契约 + 不可变历史
- **核心机制：** 四层状态（玩家/世界/叙事/元数据）+ 原子性更新 + 级联更新
- **数据结构：** 完整游戏状态（位置/共鸣度/道具/实体/时间/旗标/选择历史）
- **作用：** 维护世界的"记忆"，确保100%符合《世界书》规则，支持快照和回滚

**文件：**
- `state-management.design.md` - 六大核心原则（分层架构/不可变历史/状态契约/事件驱动/查询接口/快照恢复）
- `state-management.example.md` - 状态初始化/查询/更新/验证/级联/回滚完整示例
- `state-management.prompt.md` - 状态验证+更新规则+级联逻辑

---

## 🎯 使用指南

### 对于内容创作者

```bash
# 1. 阅读设计文档，理解设计哲学
cat lore-v1.design.md          # 地基层：高保真世界观
cat protagonist.design.md      # 逻辑层：主角推导
cat lore-v2.design.md          # 系统层：游戏化机制
cat GDD.design.md              # 导演层：剧情流程
cat main-thread.design.md      # 执行层：沉浸式文笔

# 2. 学习范文示例，理解质量标准
cat lore-v1.example.md         # 学习如何整理传说
cat protagonist.example.md     # 学习如何分析角色
cat lore-v2.example.md         # 学习如何设计系统
cat GDD.example.md             # 学习如何设计场景流程
cat main-thread.example.md     # 学习如何写完整故事（保安线）
cat branch-1.example.md        # 学习如何写支线（店主线）
cat branch-2.example.md        # 学习如何写支线（顾客线）
cat runtime-response.example.md  # 学习如何处理玩家输入（实时交互）
cat intent-mapping.example.md    # 学习如何识别玩家意图
cat state-management.example.md  # 学习如何管理游戏状态

# 3. 参考 prompt 文件，了解生成约束
cat lore-v1.prompt.md          # 了解世界书的生成规则
cat GDD.prompt.md              # 了解 AI 导演简报的生成规则
cat main-thread.prompt.md      # 了解故事文案的生成规则
cat runtime-response.prompt.md # 了解实时响应的生成规则
cat intent-mapping.prompt.md   # 了解意图识别的规则
cat state-management.prompt.md # 了解状态管理的规则
```

---

### 对于 AI 集成开发者

```python
# 示例：构建完整的故事生成管线

def generate_lore_v1(raw_text: str) -> str:
    """阶段1: 原始素材 → 世界书 1.0"""
    with open('范文/lore-v1.prompt.md') as f:
        system_prompt = f.read()
    return llm.complete(system_prompt + raw_text)

def analyze_protagonist(lore_v1: str) -> str:
    """阶段2A: 世界书 1.0 → 角色分析"""
    with open('范文/protagonist.prompt.md') as f:
        system_prompt = f.read()
    return llm.complete(system_prompt.replace(
        '{world_book_markdown_content}', lore_v1
    ))

def upgrade_to_v2(lore_v1: str) -> str:
    """阶段2B: 世界书 1.0 → 世界书 2.0"""
    with open('范文/lore-v2.prompt.md') as f:
        system_prompt = f.read()
    return llm.complete(system_prompt.replace(
        '{world_book_1_0_markdown_content}', lore_v1
    ))

def generate_gdd(lore_v2: str, protagonist_analysis: str) -> str:
    """阶段3C: 世界书 2.0 + 角色分析 → AI 导演简报"""
    with open('范文/GDD.prompt.md') as f:
        system_prompt = f.read()
    return llm.complete(
        system_prompt
        .replace('{lore_v2_content}', lore_v2)
        .replace('{protagonist_analysis}', protagonist_analysis)
    )

def generate_main_story(gdd: str, lore_v2: str) -> str:
    """阶段3D: AI 导演简报 + 世界书 2.0 → 主线故事"""
    with open('范文/main-thread.prompt.md') as f:
        system_prompt = f.read()
    return llm.complete(
        system_prompt
        .replace('{gdd_content}', gdd)
        .replace('{lore_v2_content}', lore_v2)
    )

def generate_branch_story(lore_v2: str, main_story: str, branch_type: str) -> str:
    """阶段3E: 世界书 2.0 + 主线故事 → 支线故事"""
    prompt_file = f'范文/branch-{branch_type}.prompt.md'
    with open(prompt_file) as f:
        system_prompt = f.read()
    return llm.complete(
        system_prompt
        .replace('{lore_v2_content}', lore_v2)
        .replace('{main_story}', main_story)
    )

# 完整管线示例
def full_pipeline(raw_text: str):
    """完整的故事生成管线：原始素材 → 完整故事"""
    # 阶段1: 地基
    lore_v1 = generate_lore_v1(raw_text)

    # 阶段2: 并行派生
    protagonist = analyze_protagonist(lore_v1)
    lore_v2 = upgrade_to_v2(lore_v1)

    # 阶段3: 故事生成
    gdd = generate_gdd(lore_v2, protagonist)
    main_story = generate_main_story(gdd, lore_v2)

    # 支线故事（可选）
    branch_1 = generate_branch_story(lore_v2, main_story, '1')  # 店主线
    branch_2 = generate_branch_story(lore_v2, main_story, '2')  # 顾客线

    return {
        'lore_v1': lore_v1,
        'lore_v2': lore_v2,
        'protagonist': protagonist,
        'gdd': gdd,
        'main_story': main_story,
        'branches': {'shopkeeper': branch_1, 'customer': branch_2}
    }
```

---

### 对于架构师/维护者

```bash
# 检查架构完整性
./scripts/validate_architecture.sh

# 验证文件命名规范
find . -name "*.md" | grep -v -E "(design|example|prompt)\.md$"

# 检查依赖关系
./scripts/check_dependencies.sh
```

---

## 🏛️ 设计哲学 (Linus 原则)

### 1. Good Taste - 数据结构优先
> "Bad programmers worry about code. Good programmers worry about data structures."

- ✅ 核心是"世界书 1.0"这个数据结构
- ✅ 所有功能都是对这个结构的"转换"或"派生"
- ✅ 消除特殊情况：共鸣度系统统一所有实体的触发逻辑

---

### 2. Never Break Userspace - 向后兼容
> "We do not break userspace!"

- ✅ 世界书 2.0 完整保留 1.0 的所有内容
- ✅ 范文文件夹本身就是"API 文档"，可长期依赖
- ✅ 明确标注 `(同 1.0)` 确保透明性

---

### 3. 实用主义 - 解决真实问题
> "I'm a huge proponent of designing your code around the data."

- ✅ 每个模块都解决明确的问题（Lore/Logic/System）
- ✅ 世界书 2.0 明确针对 1.0 的三个真实缺陷
- ✅ 没有引入任何"理论完美但实际复杂"的抽象

---

### 4. 简洁执念 - 三层架构
> "If you need more than 3 levels of indentation, you're screwed."

- ✅ 设计 → 范文 → Prompt 三个文件，职责清晰
- ✅ 阶段0 → 阶段1 → 阶段2，流程简单
- ✅ 没有过度工程化

---

## 📊 架构质量评估

| 评估维度 | 得分 | 证据 |
|---------|------|------|
| **完整性** | 🟢 100% | 每个模块都有 design/example/prompt 三文件 |
| **一致性** | 🟢 100% | 设计文档、范文、Prompt 三者完全对应 |
| **可扩展性** | 🟢 高 | 并行派生设计支持无限扩展新模块 |
| **可维护性** | 🟢 高 | 清晰的依赖关系，无循环依赖 |
| **向后兼容** | 🟢 完美 | v2 完整保留 v1，契约式升级 |
| **文档质量** | 🟢 A+ | 设计哲学+实现案例+生成约束 全覆盖 |

---

## 🚀 下一步扩展

基于当前架构，可轻松扩展以下模块：

```
范文/
├── 00-architecture.md
├── lore-v1.{design,example,prompt}.md         ✅ 已完成
├── lore-v2.{design,example,prompt}.md         ✅ 已完成
├── protagonist.{design,example,prompt}.md     ✅ 已完成
├── GDD.{design,example,prompt}.md             ✅ 已完成
├── main-thread.{design,example,prompt}.md     ✅ 已完成
├── branch-1.{design,example,prompt}.md        ✅ 已完成（店主线）
├── branch-2.{design,example,prompt}.md        ✅ 已完成（顾客线）
├── runtime-response.{design,example,prompt}.md ✅ 已完成
├── intent-mapping.{design,example,prompt}.md   ✅ 已完成
├── state-management.{design,example,prompt}.md ✅ 已完成
├── choice-points.{design,example,prompt}.md    ✅ 已完成 🎯
│
└── [未来扩展模块]
    ├── branch-3.{design,example,prompt}.md    # 其他支线角色
    ├── dialogue.{design,example,prompt}.md    # NPC对话系统
    ├── validation.{design,example,prompt}.md  # 质量验证器
    ├── error-handling.{design,example,prompt}.md   # 错误处理系统
    ├── tutorial.{design,example,prompt}.md    # 新手引导设计
    └── ending.{design,example,prompt}.md      # 结局分支生成器
```

---

## 📜 版本历史

- **v3.1** (2025-10-23) - **核心调整：选项交互式设计** 🎯
  - 🎯 新增 **Choice Points 模块**（选择点设计系统）
    - 三级选择点架构（微选择/普通选择/关键选择）
    - 四重笼子设计（限制玩家在框架内）
    - 2-4 法则与选项质量保证
  - 📝 **重新定位现有模块**：
    - Runtime Response：从"处理自由输入"改为"基于选项生成响应"
    - Intent Mapping：从"解析自由文本"改为"验证选项映射"
    - GDD：明确为"选项式交互游戏"设计
  - 📊 **更新架构图**：新增 Choice Points 为阶段4核心模块
  - 🔄 **更新数据流**：剧情推进→生成选项→玩家选择→验证→响应→状态更新
  - 游戏模式：从"酒馆式自由输入"明确为"选项交互式"

- **v3.0** (2025-10-23) - 新增阶段4：交互运行层（初始版本）
  - 新增 Runtime Response 模块（实时响应生成器）
  - 新增 Intent Mapping 模块（意图识别与映射）
  - 新增 State Management 模块（游戏状态管理）
  - 完善数据流：阶段0→1→2→3→4 完整运行时循环
  - 更新架构图：展示四阶段十模块完整架构
  - 初版为"酒馆式自由输入"设计（v3.1已调整为"选项式"）

- **v2.0** (2025-10-23) - 新增阶段3：故事生成层
  - 新增 GDD 模块（AI 导演任务简报）
  - 新增 Main Thread 模块（主线故事生成）
  - 新增 Branch 1 & 2 模块（支线故事：店主线、顾客线）
  - 完善数据流：阶段0→1→2→3 完整管线
  - 更新架构图：展示完整的三阶段七模块架构
  - 更新 README 和 00-architecture.md

- **v1.0** (2025-10-21) - 初始架构：地基层 + 逻辑层 + 系统层
  - 建立 lore-v1（世界书 1.0）
  - 建立 lore-v2（世界书 2.0）
  - 建立 protagonist（角色分析）
  - 文件重命名：中文 → 英文 kebab-case
  - 完善三文件模式（design/example/prompt）

---

## 🤝 贡献指南

### 新增模块时，必须遵循：

1. **三文件原则：** 创建 `module-name.{design,example,prompt}.md`
2. **依赖声明：** 在 `00-architecture.md` 中声明数据流
3. **契约式设计：** 明确定义输入/输出的数据格式
4. **向后兼容：** 不得修改现有模块的输出格式

### 修改现有模块时，必须检查：

1. **三维一致性：** design/example/prompt 必须同步更新
2. **下游影响：** 检查依赖此模块的其他模块
3. **版本策略：** 破坏性变更必须创建新版本（如 v3）

---

**📧 联系方式：** 如有疑问，请查阅 `00-architecture.md` 或提交 Issue

**🔗 相关文档：**
- [项目主 README](../README.md)
- [开发管线架构](./00-architecture.md)

---

*Last Updated: 2025-10-23*
*Architecture Version: 3.1* 🎯 **选项交互式**
