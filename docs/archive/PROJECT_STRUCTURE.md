# Ghost Story Factory - 项目结构说明

**最后更新**: 2025-10-24
**结构版本**: v2.0（已重组）

---

## 📁 完整目录结构

```
ghost-story-factory/
├── README.md                    # 🏠 项目主文档（入口）
├── PROJECT_STRUCTURE.md         # 📋 本文件 - 项目结构说明
├── pyproject.toml               # 📦 Python 项目配置
├── .env                         # 🔑 环境变量配置
├── .gitignore                   # 🚫 Git 忽略文件
│
├── docs/                        # 📚 项目文档
│   ├── INDEX.md                 # 📂 文档总索引 ⭐
│   ├── specs/                   # 📋 规格说明
│   │   ├── SPEC.md              # 原始规格书
│   │   ├── SPEC_TODO.md         # 待开发功能完整规格
│   │   └── CLI_GAME_ROADMAP.md  # 命令行游戏开发路线图
│   ├── guides/                  # 📖 使用指南
│   │   ├── USAGE.md             # 详细使用说明
│   │   ├── WORKFLOW.md          # 完整工作流程
│   │   └── QUICK_REFERENCE.md   # 命令速查卡
│   ├── architecture/            # 🏗️ 架构设计
│   │   ├── ARCHITECTURE.md      # 项目整体架构
│   │   └── GAME_ENGINE.md       # 游戏引擎设计
│   └── legacy/                  # 📦 旧文档（已废弃）
│       ├── get-story.md
│       ├── get-struct.md
│       ├── lore.md
│       ├── role-beats.md
│       └── set-city.md
│
├── examples/                    # 🎭 生成的故事示例
│   ├── 杭州/                    # 完整示例（推荐参考）
│   │   ├── 杭州_candidates.json
│   │   ├── 杭州_struct.json
│   │   ├── 杭州_lore.json
│   │   ├── 杭州_protagonist.md
│   │   ├── 杭州_lore_v2.md
│   │   ├── 杭州_GDD.md
│   │   ├── 杭州_main_thread.md  # 完整主线故事（≥5000字）
│   │   └── 杭州_story.md        # 简化版故事
│   ├── 武汉/                    # 部分示例
│   ├── 广州/                    # 初始示例
│   └── 测试城/                  # 测试数据
│
├── templates/                        # 📝 模板库（35个专业模板）
│   ├── README.md                # 模板库总览
│   ├── 00-architecture.md       # 架构总览（v3.1）
│   ├── 00-index.md              # 上下文管理策略
│   ├── lore-v1.design.md        # Lore v1 设计
│   ├── lore-v1.example.md       # Lore v1 示例
│   ├── lore-v1.prompt.md        # Lore v1 提示词
│   ├── protagonist.design.md    # 主角设计
│   ├── lore-v2.design.md        # Lore v2 设计（含游戏系统）
│   ├── GDD.design.md            # AI导演任务简报设计
│   ├── main-thread.design.md    # 主线故事设计
│   ├── choice-points.design.md  # 选择点设计
│   ├── runtime-response.design.md  # 运行时响应设计
│   ├── intent-mapping.design.md    # 意图映射设计
│   ├── state-management.design.md  # 状态管理设计
│   └── ... (共35个文件)
│
├── src/                         # 💻 源代码
│   └── ghost_story_factory/
│       ├── __init__.py
│       ├── main.py              # CLI 命令入口（已完成）
│       └── engine/              # 游戏引擎（待开发）
│           ├── __init__.py
│           ├── state.py         # 状态管理
│           ├── choices.py       # 选择点生成
│           ├── response.py      # 运行时响应
│           ├── intent.py        # 意图映射
│           └── game_loop.py     # 游戏主循环
│
├── tests/                       # 🧪 测试文件
│   └── ...
│
├── deliverables/                # 📦 交付物（旧版）
│   └── 程序-武汉/
│       └── 武汉_story.md
│
├── scripts/                     # 🔧 脚本工具
│   └── dev-run.sh
│
└── build/                       # 🏗️ 构建输出（自动生成）
    └── ...
```

---

## 📂 目录说明

### 1. **根目录文件**

| 文件 | 说明 | 重要性 |
|------|------|--------|
| `README.md` | 项目主文档，快速入门 | ⭐⭐⭐⭐⭐ |
| `PROJECT_STRUCTURE.md` | 项目结构说明（本文件） | ⭐⭐⭐⭐ |
| `pyproject.toml` | Python 项目配置，定义 CLI 命令 | ⭐⭐⭐⭐⭐ |
| `.env` | 环境变量（API Key 等） | ⭐⭐⭐⭐⭐ |

---

### 2. **docs/ - 项目文档**

所有文档的统一位置，按类型分类。

#### 📂 docs/INDEX.md
**文档总索引**，按角色提供阅读路径：
- 👨‍💻 开发者路径
- ✍️ 内容创作者路径
- 🎮 游戏设计师路径
- 📊 项目管理路径

#### 📋 docs/specs/ - 规格说明
| 文档 | 说明 | 适用人群 |
|------|------|----------|
| `SPEC.md` | 原始规格书 | 开发者、贡献者 |
| `SPEC_TODO.md` | **完整功能规格** | 开发者、项目管理 |
| `CLI_GAME_ROADMAP.md` | **命令行游戏路线图** | 游戏引擎开发者 |

#### 📖 docs/guides/ - 使用指南
| 文档 | 说明 | 适用人群 |
|------|------|----------|
| `USAGE.md` | 详细使用说明（命令、参数） | 所有用户 |
| `WORKFLOW.md` | 完整工作流程（3种模式） | 内容创作者 |
| `QUICK_REFERENCE.md` | 命令速查卡 | 经常使用者 |

#### 🏗️ docs/architecture/ - 架构设计
| 文档 | 说明 | 适用人群 |
|------|------|----------|
| `ARCHITECTURE.md` | 项目整体架构 | 开发者、架构师 |
| `GAME_ENGINE.md` | 游戏引擎设计 | 游戏引擎开发者 |

#### 📦 docs/legacy/ - 旧文档
已被新文档替代，仅作历史参考，**不建议阅读**。

---

### 3. **examples/ - 故事示例**

生成的城市故事示例，按城市分类。

#### 🎭 examples/杭州/ - **推荐参考的完整示例**
包含完整的生成流程输出：
```
杭州_candidates.json  → 候选列表
杭州_struct.json      → 故事结构
杭州_lore.json        → Lore v1
杭州_protagonist.md   → 主角分析
杭州_lore_v2.md       → Lore v2（含游戏系统）
杭州_GDD.md           → AI导演任务简报
杭州_main_thread.md   → 主线完整故事（≥5000字）⭐
杭州_story.md         → 简化版故事
```

**推荐阅读顺序**：
1. `杭州_protagonist.md` - 了解主角分析
2. `杭州_GDD.md` - 了解游戏设计
3. `杭州_main_thread.md` - 阅读完整故事

#### 🎭 其他城市
- `武汉/` - 部分示例
- `广州/` - 经典荔湾广场故事
- `测试城/` - 测试数据

---

### 4. **templates/ - 模板库**

35个专业设计模板，每个模块包含：
- `.design.md` - 设计理念和原则
- `.example.md` - 高质量示例
- `.prompt.md` - LLM 提示词模板

**核心文档**：
- `README.md` - 模板库总览（v3.1）
- `00-architecture.md` - 架构总览（4个阶段）
- `00-index.md` - 上下文管理策略（避免AI上下文溢出）

**模块分类**：
- **Stage 1**: 候选与结构
- **Stage 2**: Lore v1 + 主角分析
- **Stage 3**: Lore v2 + GDD + 主线/分支故事
- **Stage 4**: 交互运行层（Choice Points、Runtime Response、State Management、Intent Mapping）

---

### 5. **src/ - 源代码**

#### 已完成功能
`src/ghost_story_factory/main.py` 包含所有 CLI 命令：
- ✅ `set-city` - 生成候选列表
- ✅ `get-struct` - 选择故事
- ✅ `get-lore` - 生成 Lore v1
- ✅ `gen-protagonist` - 生成主角分析
- ✅ `gen-lore-v2` - 生成 Lore v2
- ✅ `gen-gdd` - 生成 GDD
- ✅ `gen-main-thread` - 生成主线故事
- ✅ `gen-branch` - 生成分支故事
- ✅ `gen-complete` - **自动化完整流程** ⭐

#### 待开发功能
`src/ghost_story_factory/engine/` 游戏引擎目录（待创建）：
- ⏳ `state.py` - 游戏状态管理
- ⏳ `choices.py` - 选择点生成器
- ⏳ `response.py` - 运行时响应生成器
- ⏳ `intent.py` - 意图映射引擎
- ⏳ `game_loop.py` - 游戏主循环

参考：[docs/specs/CLI_GAME_ROADMAP.md](docs/specs/CLI_GAME_ROADMAP.md)

---

## 🚀 快速导航

### 我想...

#### 📖 **快速上手**
1. 阅读 [README.md](README.md)
2. 安装依赖：`pip install -e .`
3. 生成第一个故事：`gen-complete --city "城市名" --index 1`

#### ✍️ **创作故事**
1. 阅读 [docs/guides/USAGE.md](docs/guides/USAGE.md)
2. 参考 [docs/guides/WORKFLOW.md](docs/guides/WORKFLOW.md)
3. 查看示例 [examples/杭州/](examples/杭州/)

#### 🎮 **开发游戏引擎**
1. 阅读 [docs/specs/CLI_GAME_ROADMAP.md](docs/specs/CLI_GAME_ROADMAP.md)
2. 参考 [docs/architecture/GAME_ENGINE.md](docs/architecture/GAME_ENGINE.md)
3. 查看 [docs/specs/SPEC_TODO.md](docs/specs/SPEC_TODO.md)

#### 🏗️ **理解架构**
1. 阅读 [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
2. 查看 [templates/00-architecture.md](templates/00-architecture.md)
3. 参考 [templates/README.md](templates/README.md)

#### 📚 **查找文档**
直接访问 [docs/INDEX.md](docs/INDEX.md)

---

## 📝 文件命名规范

### 生成的故事文件
格式：`{城市}_{模块}.{扩展名}`

示例：
- `杭州_candidates.json` - 候选列表
- `杭州_lore.json` - Lore v1
- `杭州_protagonist.md` - 主角分析
- `杭州_GDD.md` - AI导演任务简报
- `杭州_main_thread.md` - 主线故事

### templates模板文件
格式：`{模块}-{类型}.md`

示例：
- `lore-v1.design.md` - 设计文档
- `lore-v1.example.md` - 示例文档
- `lore-v1.prompt.md` - 提示词模板

---

## 🔄 版本历史

### v2.0 (2025-10-24) - **文档重组**
- ✅ 创建 `docs/` 统一文档目录
- ✅ 创建 `examples/` 统一示例目录
- ✅ 文档按类型分类（specs/guides/architecture/legacy）
- ✅ 故事按城市分类
- ✅ 创建 `docs/INDEX.md` 文档索引
- ✅ 更新 `README.md` 添加文档索引

### v1.0 - **初始版本**
- 所有文档和示例混在根目录

---

## 💡 维护建议

### 添加新文档
1. 确定文档类型（规格/指南/架构/示例）
2. 放入对应的 `docs/` 子目录
3. 更新 `docs/INDEX.md`
4. 更新 `README.md` 的文档索引表

### 添加新示例
1. 在 `examples/` 创建城市文件夹
2. 生成的文件统一放入该文件夹
3. 更新 `docs/INDEX.md` 的示例章节

### 废弃旧文档
1. 移动到 `docs/legacy/`
2. 在 `docs/INDEX.md` 标注替代文档
3. 不要删除（保留历史追溯）

---

**最后更新**: 2025-10-24
**维护者**: @yehan

