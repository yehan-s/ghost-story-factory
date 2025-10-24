# Ghost Story Factory v3.1 - 完整架构

## 📐 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Ghost Story Factory v3.1                         │
│                                                                           │
│  专业的灵异故事生成工厂 - 从素材到可玩游戏的完整工作流                       │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
        ┌───────────────────┐       ┌───────────────────┐
        │  开发阶段（离线）  │       │  运行阶段（在线）  │
        │  Story Generator  │       │   Game Engine     │
        └───────────────────┘       └───────────────────┘
                  │                           │
        阶段1→2→3（生成）           阶段4（交互运行）

> 运行模式：
> - 动态模式（LLM 实时生成）→ `play_game_full.py`
> - 预生成模式（零等待）→ `play_game_pregenerated.py` / `start_pregenerated_game.sh`
```

---

## 🔄 完整数据流

### 阶段0：templates库（AI的"配方"）

```
templates/ (35个文件，8520行代码)
├── 00-index.md              ← AI使用指南（分层加载策略）
├── 00-architecture.md       ← 架构设计文档
├── README.md                ← templates库总览
│
├── [阶段1-3的templates]          ← 故事生成用
│   ├── lore-v1.{design,example,prompt}.md
│   ├── protagonist.{design,example,prompt}.md
│   ├── lore-v2.{design,example,prompt}.md
│   ├── GDD.{design,example,prompt}.md
│   ├── main-thread.{design,example,prompt}.md
│   └── branch-1/2.{design,example,prompt}.md
│
└── [阶段4的templates]            ← 游戏运行用 🎮
    ├── choice-points.{design,example,prompt}.md
    ├── runtime-response.{design,example,prompt}.md
    ├── intent-mapping.{design,example,prompt}.md
    └── state-management.{design,example,prompt}.md
```

---

### 开发阶段：Story Generator

```
┌──────────────────────────────────────────────────────────────┐
│  输入: 城市名（如"武汉"）                                       │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│  generate_full_story.py                                      │
│                                                               │
│  阶段1: 世界书1.0（高保真地基）                                │
│  ├─ 读取: templates/lore-v1.prompt.md                              │
│  ├─ AI生成: 传说事件、地点、实体、形而上学                       │
│  └─ 输出: 武汉_lore_v1.md                                     │
│                                                               │
│  阶段2A: 角色分析                                              │
│  ├─ 读取: templates/protagonist.prompt.md                          │
│  ├─ 输入: 武汉_lore_v1.md                                     │
│  ├─ AI生成: 角色身份、访问权、动机、限制                         │
│  └─ 输出: 武汉_protagonist.md                                 │
│                                                               │
│  阶段2B: 世界书2.0（游戏化规则）🎮                             │
│  ├─ 读取: templates/lore-v2.prompt.md                              │
│  ├─ 输入: 武汉_lore_v1.md                                     │
│  ├─ AI生成: 共鸣度系统、实体等级、场域规则、道具系统              │
│  └─ 输出: 武汉_lore_v2.md ✅ 游戏引擎需要                      │
│                                                               │
│  阶段3A: AI导演任务简报（GDD）🎮                               │
│  ├─ 读取: templates/GDD.prompt.md                                  │
│  ├─ 输入: 武汉_protagonist.md + 武汉_lore_v2.md               │
│  ├─ AI生成: 场景流程、关键节点、分支设计                        │
│  └─ 输出: 武汉_gdd.md ✅ 游戏引擎需要                          │
│                                                               │
│  阶段3B: 主线故事                                              │
│  ├─ 读取: templates/main-thread.prompt.md                          │
│  ├─ 输入: 武汉_gdd.md + 武汉_lore_v2.md                       │
│  ├─ AI生成: 1500-3000字的完整故事                             │
│  └─ 输出: 武汉_story.md ⭐ 最终产物                            │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│  输出目录: deliverables/程序-武汉/                             │
│                                                               │
│  ├── 武汉_lore_v1.md      (传说素材)                          │
│  ├── 武汉_protagonist.md  (角色设定)                          │
│  ├── 武汉_lore_v2.md      (游戏规则) 🎮                       │
│  ├── 武汉_gdd.md          (剧情流程) 🎮                       │
│  ├── 武汉_story.md        (完整故事) ⭐                        │
│  └── README.md            (说明文档)                          │
└──────────────────────────────────────────────────────────────┘
```

---

### 运行阶段：Game Engine

```
┌──────────────────────────────────────────────────────────────┐
│  输入: 武汉_gdd.md + 武汉_lore_v2.md                           │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│  game_engine.py                                              │
│                                                               │
│  初始化:                                                       │
│  ├─ 加载 GDD（剧情流程）                                       │
│  ├─ 加载 Lore v2（游戏规则）                                   │
│  └─ 初始化状态（位置、时间、共鸣度、道具）                       │
│                                                               │
│  游戏循环:                                                     │
│  ┌────────────────────────────────────────────────┐          │
│  │ 回合 N                                          │          │
│  │                                                 │          │
│  │ 1. 生成叙事情境                                 │          │
│  │    "你正在五楼中庭，听到拍皮球声..."           │          │
│  │                                                 │          │
│  │ 2. 🎯 Choice Points（生成选项）                │          │
│  │    ├─ 读取: templates/choice-points.prompt.md       │          │
│  │    ├─ 输入: 当前情境 + 游戏状态 + GDD + Lore   │          │
│  │    └─ AI生成: 2-4个选项                        │          │
│  │       [A] 走过去检查                            │          │
│  │       [B] 查看监控                              │          │
│  │       [C] 巡逻其他楼层                          │          │
│  │                                                 │          │
│  │ 3. 玩家选择: A                                  │          │
│  │                                                 │          │
│  │ 4. 📝 Runtime Response（生成响应）             │          │
│  │    ├─ 读取: templates/runtime-response.prompt.md    │          │
│  │    ├─ 输入: 玩家选择 + 状态 + Lore             │          │
│  │    └─ AI生成: 200-500字沉浸式响应              │          │
│  │       "你握紧手电筒，慢慢走向..."             │          │
│  │                                                 │          │
│  │ 5. 🔄 State Management（更新状态）             │          │
│  │    ├─ 读取: templates/state-management.prompt.md    │          │
│  │    ├─ 应用: 选项的后果                         │          │
│  │    ├─ 检查: Lore v2 规则                       │          │
│  │    └─ 更新: 位置、共鸣度、旗标                 │          │
│  │       位置: 五楼中庭 → 五楼深层走廊            │          │
│  │       共鸣度: 35% → 50%                         │          │
│  │                                                 │          │
│  │ 6. 检查结束条件                                 │          │
│  │    ├─ 共鸣度 >= 100% → 坏结局                  │          │
│  │    ├─ flags["逃出成功"] → 好结局               │          │
│  │    └─ 继续 → 下一回合                          │          │
│  └────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 两个核心工具

### 1. generate_full_story.py（故事生成器）

**用途：** 开发阶段，生成故事素材

**输入：**
- 城市名

**输出：**
- 所有中间产物（lore、protagonist、GDD等）
- 最终故事（story.md）

**templates依赖：** 阶段1-3的所有templates

**使用场景：**
- 为新城市创建故事
- 快速原型设计
- 内容生产

---

### 2. game_engine.py（游戏引擎）

**用途：** 运行阶段，玩家实际玩游戏

**输入：**
- GDD文件（剧情流程）
- Lore v2文件（游戏规则）

**输出：**
- 实时交互体验
- 动态剧情响应

**templates依赖：** 阶段4的所有templates

**使用场景：**
- 玩家体验游戏
- 测试剧情分支
- Demo演示

---

## 📊 templates使用对比

| templates模块 | 故事生成器 | 游戏引擎 |
|---------|-----------|---------|
| lore-v1 | ✅ 阶段1 | ❌ |
| protagonist | ✅ 阶段2A | ❌ |
| lore-v2 | ✅ 阶段2B | ✅ 输入 |
| GDD | ✅ 阶段3A | ✅ 输入 |
| main-thread | ✅ 阶段3B | ❌ |
| branch-1/2 | ⭕ 可选 | ❌ |
| choice-points | ❌ | ✅ 运行时 |
| runtime-response | ❌ | ✅ 运行时 |
| intent-mapping | ❌ | ✅ 运行时 |
| state-management | ❌ | ✅ 运行时 |

---

## 🔧 技术栈

### 核心依赖
- **CrewAI** - Multi-Agent编排框架
- **LangChain** - LLM工具链
- **Python 3.10+** - 主要语言

### LLM支持
- **Kimi (Moonshot)** - 优先使用
- **OpenAI GPT-4** - Fallback
- 兼容所有OpenAI API格式的服务

### 数据格式
- **Markdown** - 故事和文档
- **JSON** - 结构化数据（可选）

---

## 💡 设计哲学

### 1. 契约式开发（Contract-Based）
- 每个模块有明确的输入/输出定义
- 阶段之间通过文件契约连接
- 向后兼容

### 2. templates驱动（Template-Driven）
- AI读取templates作为"配方"
- 三文件模式：design + example + prompt
- 可扩展、可维护

### 3. 分层架构（Layered）
- 阶段1：地基（Lore v1）
- 阶段2：逻辑（Protagonist + Lore v2）
- 阶段3：生成（GDD + Story）
- 阶段4：交互（Choice + Response + State）

### 4. AI + 人类协作
- AI做"体力活"（搜集、生成、扩写）
- 人类做"创意活"（审核、调整、二次创作）

### 5. Good Taste（Linus Torvalds）
- 数据结构优先
- 实用主义
- 简单胜于复杂

---

## 📈 扩展路线

### 已完成 ✅
- [x] 阶段1-3：完整故事生成
- [x] 阶段4：交互运行层templates
- [x] 游戏引擎Demo
- [x] 分层加载优化（节省80-95% tokens）

### 规划中 📋
- [ ] Web界面（Flask/FastAPI）
- [ ] 多结局系统
- [ ] 存档/读档功能
- [ ] 支线任务系统
- [ ] 成就系统
- [ ] 音效/配乐集成

### 未来愿景 🚀
- [ ] 可视化剧情编辑器
- [ ] 多人协作模式
- [ ] 社区分享平台
- [ ] 移动端适配

---

## 📖 相关文档

- **快速开始**: [README.md](./README.md)
- **游戏引擎**: [GAME_ENGINE.md](./GAME_ENGINE.md)
- **使用指南**: [USAGE.md](./USAGE.md)
- **项目规格**: [SPEC.md](./SPEC.md)
- **templates库**: [templates/README.md](./templates/README.md)
- **templates索引**: [templates/00-index.md](./templates/00-index.md)

---

**版本：** v3.1
**更新日期：** 2025-10-23
**架构模式：** 选项交互式 🎯

