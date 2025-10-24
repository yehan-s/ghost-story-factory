# Ghost Story Factory v3.1 🎯

**一个专业的灵异故事生成工厂** - 基于CrewAI和专业templates模板，自动生成完整的、高质量的灵异故事。

> 🎮 **不只是故事生成器，更是交互式游戏开发工具**
> 从世界观设计到AI导演系统，从静态故事到动态游戏，一站式解决方案。

---

## 📌 项目简介

Ghost Story Factory 是一个基于 **Top-Down 叙事设计** 的专业故事生成工具，采用 **世界观 → 角色 → 游戏设计 → 故事** 的分层架构，确保生成内容的一致性和可玩性。

**适用场景：**
- 📖 内容创作者：快速生成高质量灵异故事文案
- 🎮 游戏开发者：获得完整的游戏设计文档（GDD + 世界观）
- 🎬 UP主/播客：获得可直接配音的故事脚本
- 🔬 叙事研究者：学习专业的故事设计流程

---

## 📚 文档索引

| 类型 | 文档 | 说明 |
|------|------|------|
| 📖 **使用指南** | [USAGE.md](docs/guides/USAGE.md) | 详细使用说明 |
| 📖 **工作流程** | [WORKFLOW.md](docs/guides/WORKFLOW.md) | 完整工作流程 |
| 📖 **命令速查** | [QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md) | 常用命令速查 |
| 🏗️ **架构设计** | [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | 项目整体架构 |
| 🎮 **游戏引擎** | [GAME_ENGINE.md](docs/architecture/GAME_ENGINE.md) | 交互游戏引擎 |
| 📋 **开发规格** | [SPEC_TODO.md](docs/specs/SPEC_TODO.md) | 待开发功能规格 |
| 🚀 **开发路线** | [CLI_GAME_ROADMAP.md](docs/specs/CLI_GAME_ROADMAP.md) | 命令行游戏开发 |
| 📂 **完整索引** | [docs/INDEX.md](docs/INDEX.md) | **所有文档总览** ⭐ |

---

## 🌟 核心特性

- ✅ **自动化生成**：输入城市名，自动生成完整故事（≥5000字）
- ✅ **专业templates**：基于35个专业设计模式（[templates文件夹](./templates/)）
- ✅ **分层架构**：阶段1（世界书1.0）→ 阶段2（主角分析）→ 阶段3（GDD+故事）→ 阶段4（交互层）
- ✅ **选项交互式设计**：支持生成游戏化的选择点系统
- ✅ **共鸣度系统**：动态的玩家-世界互动机制
- ✅ **后果树（Consequence Tree）**：多分支结局设计
- ✅ **AI做体力活，人类做创意活**

---

## 🎯 核心优势

### 1. **专业的叙事设计流程**
不是简单的"输入提示词→输出故事"，而是遵循专业游戏叙事设计流程：
```
原始素材 → Lore v1（世界观基础） → 主角分析 → Lore v2（系统增强）
→ GDD（AI导演任务简报） → 主线故事（≥5000字）
```

### 2. **可复用的中间产物**
每个阶段的输出都是独立可用的：
- **Lore v1/v2**：可用于世界观设定
- **主角分析**：可用于角色设计
- **GDD**：可直接用于游戏开发
- **主线故事**：可直接配音/发布

### 3. **游戏化设计支持**
不仅生成静态故事，还支持：
- 🎮 选项式交互设计
- 📊 共鸣度系统（玩家状态追踪）
- 🌳 后果树（多分支结局）
- 🤖 AI导演系统（动态响应）

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Ghost Story Factory                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stage 1: 候选与结构                                         │
│  ├─ set-city      → 城市候选列表 (candidates.json)          │
│  └─ get-struct    → 故事结构框架 (struct.json)              │
│                                                             │
│  Stage 2: 世界观基础                                         │
│  ├─ get-lore         → Lore v1 (lore.json)                 │
│  └─ gen-protagonist  → 主角设计 (protagonist.md)           │
│                                                             │
│  Stage 3: 系统增强                                           │
│  ├─ gen-lore-v2   → Lore v2 (lore_v2.md) [含游戏系统]       │
│  └─ gen-gdd       → GDD (GDD.md) [AI导演任务简报]          │
│                                                             │
│  Stage 4: 故事生成                                           │
│  ├─ gen-main-thread → 主线故事 (main_thread.md)            │
│  └─ gen-branch      → 分支故事 (branch_X.md)               │
│                                                             │
│  ⚡ 自动流水线                                                │
│  └─ gen-complete  → 一键完成 Stage 2-4                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**详细架构**：查看 [ARCHITECTURE.md](./ARCHITECTURE.md)

## 📚 文档索引

- **🔥 完整工作流程指南**：[WORKFLOW.md](./WORKFLOW.md) ⭐ **推荐**
- **快速上手**：见下方"快速开始"
- **游戏引擎使用指南**：[GAME_ENGINE.md](./GAME_ENGINE.md) 🎮
- **使用指南（精简版）**：[USAGE.md](./USAGE.md)
- **项目规格说明（开发者/验收）**：[SPEC.md](./SPEC.md)
- **templates库说明**：[templates/README.md](./templates/README.md)
- **templates索引（AI优化）**：[templates/00-index.md](./templates/00-index.md)
- **架构设计**：[templates/00-architecture.md](./templates/00-architecture.md)

## ⚡ 快速开始（推荐）

### ⭐ 新推荐：自动流水线（3步完成！）

```bash
# 1. 获取候选故事
set-city --city "杭州"

# 2. 选择故事框架
get-struct --city "杭州" --index 1

# 3. 一键生成所有内容（自动执行 5 个步骤！）
gen-complete --city "杭州" --index 1
```

**🎯 自动完成：** Lore v1 → 主角设计 → Lore v2 → GDD → 主线故事（≥5000字）

---

### 一键生成完整故事（备选方案）

```bash
# 1. 安装依赖
uv venv && source .venv/bin/activate
uv pip install -e .

# 2. 配置环境变量（创建 .env 文件）
# KIMI_API_KEY=your_key_here  # 或 OPENAI_API_KEY

# 3. 生成故事（自动执行完整流程，包含主线 + 支线）
python generate_full_story.py --city 武汉

# 只生成主线，不生成支线
python generate_full_story.py --city 武汉 --no-branches

# 或使用shell脚本
chmod +x generate_full_story.sh
./generate_full_story.sh 武汉
```

**输出目录：** `deliverables/程序-武汉/`

**生成文件：**
- ✅ `武汉_lore_v1.md` - 世界书1.0（高保真地基）
- ✅ `武汉_protagonist.md` - 角色分析
- ✅ `武汉_lore_v2.md` - 世界书2.0（游戏化规则）🎮
- ✅ `武汉_gdd.md` - AI导演任务简报（主线）🎮
- ✅ `武汉_story.md` - **主线故事（⭐最终产物）**
- 🌿 `武汉_branch_1_gdd.md` - 支线1 GDD（店主线）🎮
- 🌿 `武汉_branch_1_story.md` - 支线1故事文案 ⭐
- 🌿 `武汉_branch_2_gdd.md` - 支线2 GDD（顾客线）🎮
- 🌿 `武汉_branch_2_story.md` - 支线2故事文案 ⭐
- ✅ `README.md` - 说明文档

**🎮 = 游戏引擎所需文件 | 🌿 = 支线内容（可选）**

---

### 运行交互式游戏（可选）

生成故事后，可以运行交互式游戏引擎：

```bash
# 启动游戏（基于生成的GDD和Lore v2）
python game_engine.py \
    --city 武汉 \
    --gdd deliverables/程序-武汉/武汉_gdd.md \
    --lore deliverables/程序-武汉/武汉_lore_v2.md
```

**游戏特性：**
- 🎯 选项式交互（A/B/C/D）
- 📝 AI实时生成响应
- 🔄 动态状态管理
- 🎮 多结局系统

**详细说明：** 查看 [GAME_ENGINE.md](./GAME_ENGINE.md)

---

## 📖 详细安装与运行

建议使用 `uv`（或 `pip`）。项目已提供 `pyproject.toml` 与脚本入口。

### 方式A：使用新生成器（推荐）🎯

```bash
# 完整流程，基于templates模板
python generate_full_story.py --city 广州 --output deliverables/程序-广州/
```

**优点：**
- ✅ 自动执行阶段1→2→3的完整流程
- ✅ 使用templates文件夹中的专业提示词
- ✅ 生成所有中间产物（lore、protagonist、GDD等）
- ✅ 最终输出完整故事

---

### 方式B：使用旧命令行工具（兼容模式）

#### 本地开发

```bash
# 1) 创建并激活虚拟环境
uv venv
source .venv/bin/activate

# 2) 安装到可编辑模式
uv pip install -e .

# 3) 配置环境变量（创建 .env）
# 必需：OPENAI_API_KEY=...
# 若使用 Google 搜索：
#   GOOGLE_API_KEY=...
#   GOOGLE_CSE_ID=...

# 4) 运行（两种方式，择一）
# A) 可编辑安装后的直接运行
set-city --city "广州"      # 列出候选（名称+简介），保存 广州_candidates.json
get-struct --city "广州"   # 选定候选并生成结构化框架，保存 广州_struct.json
get-story --city "广州"    # 若存在 广州_struct.json 则按框架写作，否则走全流程

# B) 本地临时环境运行（不污染环境）
uvx --from . set-city --city "广州"
uvx --from . get-struct --city "广州"
uvx --from . get-story --city "广州"

# 自定义输出文件名（例如导出到 deliverables 目录）
uvx --from . get-story --city "广州" --out "deliverables/程序-广州/广州_story.md"
```

### 作为一次性工具运行（发布到 PyPI 后）

```bash
# 使用 uvx（推荐写法）
uvx --from ghost-story-factory set-city --city "东莞"
uvx --from ghost-story-factory get-struct --city "东莞"
uvx --from ghost-story-factory get-story --city "东莞"

# 锁定版本（可选，保证可重复）
uvx --from ghost-story-factory==1.0.0 get-story --city "东莞"

# 或使用 pipx（等价）
pipx run --spec ghost-story-factory get-story --city "东莞"
```

## 依赖

- crewai>=0.30.0
- langchain-community
- langchain-google-community
- langchain-openai
- python-dotenv

## 工作流说明

顺序执行三步：
1) 搜索素材（GoogleSearchRun）
2) 提炼故事结构（JSON 框架）
3) 扩写成 Markdown 故事

产出文件：`[城市名]_story.md`

## 免责声明

- 需自行提供并合法使用 API Key（OpenAI/Google 等）。
- 网络检索结果可能包含不准确或有偏差的信息，使用前请审阅与二次创作。

## LLM 配置（OpenAI 或 Kimi）

本工具支持通过环境变量选择不同的兼容提供商（优先使用 Kimi，再回退到 OpenAI）。同时兼容 MoonLens 中使用的 MOONSHOT_* 命名。

- 使用 Kimi（Moonshot）：
  - `KIMI_API_KEY=...`
  - 可选：`KIMI_API_BASE=https://api.moonshot.cn/v1`（默认已是该值）
  - 可选：`KIMI_MODEL=kimi-k2-0905-preview`
  - 兼容：`MOONSHOT_API_KEY`、`MOONSHOT_API_URL`、`MOONSHOT_MODEL`

- 使用 OpenAI（或兼容代理）：
  - `OPENAI_API_KEY=...`
  - 可选：`OPENAI_BASE_URL=...`（或 `OPENAI_API_BASE=...`）
  - 可选：`OPENAI_MODEL=gpt-4o`

优先级：`KIMI_*` > `OPENAI_*`。未配置任一密钥将无法运行。

## 自定义 Prompt 文件

本项目支持用仓库根目录下的 Markdown 提示词文件，精确控制三条命令的行为与风格：

- set-city.md
  - 作用：生成城市候选列表
  - 变量：`{city}`
  - 输出：严格的 JSON 数组（每项仅含 `title`,`blurb`,`source`）
  - 约束：只返回一个 ```json 代码块；强制 ASCII 双引号，不得使用中文引号/书名号

- get-struct.md
  - 作用：从原始素材中提炼结构化框架
  - 变量：`{raw_text_from_agent_a}`（由命令内部先让研究员汇编长文素材后注入）
  - 输出：仅一个 JSON 代码块；必须包含键：
    - `title` (string)
    - `city` (string)
    - `location_name` (string)
    - `core_legend` (string)
    - `key_elements` (string[])
    - `potential_roles` (string[])

- get-story.md
  - 作用：将结构化 JSON 扩写为 UP 主讲述风格的 Markdown 文案
  - 变量：`{json_skeleton_from_agent_b}`（即 `*_struct.json` 的完整 JSON 字符串）
  - 输出：仅 Markdown 文案，≥1500 字，强氛围、第二人称倾向、可直接配音

放置/修改以上文件后，命令会优先读取这些 md；若缺失，则使用内置默认提示词。

## 顶层设计（Top-Down Design）工作流

推荐以"世界观 → 角色拍点 → **完整故事**"的顺序产出，保证一致性与可复用。

### ⚡ 方式 A：一键生成（推荐）

```bash
# 自动完成 3 步：lore → role → story
./generate_full_story.sh 武汉 夜跑者

# 自定义输出路径
./generate_full_story.sh 广州 保安 deliverables/广州_story.md
```

**⚠️ 重要**：这个脚本会自动生成 **完整的 Markdown 故事**，而不仅仅是 JSON！

### 📋 方式 B：手动分步执行

**第 1 步**：生成世界观圣经（lore）

```bash
uvx --from . get-lore --city "广州" --title "荔湾"
# 输出：广州_lore.json
```

**第 2 步**：生成角色剧情拍点（beats）

```bash
uvx --from . gen-role --city "广州" --role "保安" --pov "第二人称"
# 输出：广州_role_保安.json
```

**第 3 步**：生成完整故事 ← **必须执行，否则只有 JSON！**

```bash
uvx --from . get-story --city "广州" --role "保安" --out "deliverables/广州_story.md"
# 输出：广州_story.md ✅ 这才是完整的故事！
```

**第 4 步**：一致性校验（可选）

```bash
uvx --from . validate-role --city "广州" --role "保安"
```

### 📁 产出文件说明

| 文件类型 | 示例 | 说明 |
|---------|------|------|
| `*_lore.json` | `武汉_lore.json` | 世界观圣经（中间文件） |
| `*_role_*.json` | `武汉_role_夜跑者.json` | 角色剧情拍点（中间文件） |
| `*_story.md` | `武汉_story.md` | **✅ 完整故事（最终产物）** |

**💡 提示**：JSON 文件是中间产物，用于保证一致性。最终的故事在 `.md` 文件中！

---

所有新增命令均不破坏现有 set-city / get-struct / get-story 契约，仅作为增强。

---

## 📊 示例输出

### 杭州 - 北高峰午夜缆车空厢

**生成的文件：**
```
杭州_candidates.json      # 6个候选故事
杭州_struct.json          # 故事结构框架
杭州_lore.json            # 世界观基础（JSON）
杭州_protagonist.md       # 主角分析报告
杭州_lore_v2.md           # 世界观系统增强版（含共鸣度）
杭州_GDD.md               # AI导演任务简报
杭州_main_thread.md       # 完整主线故事（5000+字）
```

**故事特色：**
- 🎭 低频象征物："000号车厢"、"00:44时间"
- 🎬 多感官细节：机油味、钢缆震颤、冰露触感
- 📖 完整叙事弧：建置→异象→深挖→反转→高潮→余波
- 🎯 B站UP主风格：第二人称代入、强节奏停顿、可配音

**查看完整示例：** [杭州_story.md](./杭州_story.md)

---

## 🤝 贡献指南

欢迎贡献！您可以：

1. **添加新的templates模板**
   - 在 `templates/` 文件夹中添加新的 `.design.md`, `.example.md`, `.prompt.md`
   - 遵循三文件模式（设计-示例-提示词）

2. **改进提示词**
   - 优化现有的 prompt 模板
   - 提高生成质量

3. **报告问题**
   - 在 [Issues](https://github.com/your-username/ghost-story-factory/issues) 提交bug报告
   - 提供详细的复现步骤

4. **提交新功能**
   - Fork 本仓库
   - 创建功能分支
   - 提交 Pull Request

**代码风格：**
- 遵循 PEP 8
- 使用有意义的变量名
- 添加必要的注释和文档字符串

---

## ❓ 常见问题（FAQ）

### 1. 为什么需要先运行 `set-city` 和 `get-struct`？

这是为了让用户有**选择权**。`set-city` 生成多个候选故事，用户可以选择最感兴趣的一个，而不是由AI随机决定。

### 2. `gen-complete` 和 `generate_full_story.py` 有什么区别？

- **`gen-complete`**：命令行工具，适合分步调试和精细控制
- **`generate_full_story.py`**：Python脚本，适合一键自动化，会生成到指定输出目录

### 3. 生成的故事质量如何保证？

通过**多层验证**：
1. Lore v1 提供世界观一致性
2. 主角分析确保角色合理性
3. Lore v2 添加游戏系统约束
4. GDD 提供叙事结构指导
5. templates模板提供质量标准

### 4. 可以用于商业项目吗？

**可以**，但请注意：
- 本项目代码遵循 MIT 许可证
- AI生成的内容版权归使用者
- 需自行确保API使用合规（OpenAI/Kimi ToS）

### 5. 支持哪些LLM？

目前支持：
- ✅ Kimi (Moonshot) - 推荐，长文本支持好
- ✅ OpenAI (GPT-4o/GPT-4) - 备选
- ✅ 任何 OpenAI 兼容 API

### 6. 为什么有些命令超时？

**常见原因：**
- Kimi API 限流（504 Gateway Timeout）
- 生成内容过长（使用 `gen-complete` 分步生成）

**解决方案：**
1. 使用 `gen-complete --city "城市名" --index 1`（会自动跳过已生成文件）
2. 检查 `.env` 中的 API Key 是否有效
3. 尝试切换到 OpenAI API

### 7. 如何自定义故事风格？

修改 `templates/` 文件夹中的 `.prompt.md` 文件，或在项目根目录创建自定义 prompt：
- `set-city.md`
- `get-struct.md`
- `get-story.md`

---

## 🛠️ 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| **AI 框架** | [CrewAI](https://github.com/joaomdmoura/crewAI) | 多Agent协作 |
| **LLM** | Kimi/OpenAI | 内容生成 |
| **包管理** | [uv](https://github.com/astral-sh/uv) | 快速依赖管理 |
| **环境配置** | python-dotenv | 环境变量管理 |
| **语言链** | LangChain | LLM工具链 |

---

## 📜 许可证

本项目采用 **MIT License** 开源。

详见 [LICENSE](./LICENSE) 文件。

---

## 🙏 致谢

- **设计灵感**：Linus Torvalds 的"Good Taste"设计哲学
- **叙事理论**：《Save the Cat!》、《The Anatomy of Story》
- **技术支持**：CrewAI 团队、LangChain 社区
- **templates贡献者**：感谢所有提供专业设计模式的贡献者

---

## 📈 版本历史

### v3.1 (2025-10-24) - 当前版本 🎯

- ✨ 添加自动流水线命令 `gen-complete`
- ✨ 新增 6 个核心命令（gen-protagonist, gen-lore-v2, gen-gdd等）
- 📚 完善文档体系（WORKFLOW.md, QUICK_REFERENCE.md等）
- 🎮 添加交互式游戏引擎（game_engine.py）
- 📦 完整的templates模板库（35个文件）

### v3.0 (2025-10-23)

- ✨ 添加 Stage 4 交互层设计
- ✨ 选项交互式游戏支持
- 📚 templates库初版

### v2.0

- ✨ Top-Down 设计工作流
- ✨ Lore + Role Beats 系统

### v1.0

- 🎉 初始版本
- ✅ 基础故事生成功能

**完整更新日志**：查看 [Git Commits](https://github.com/your-username/ghost-story-factory/commits/main)

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-username/ghost-story-factory/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ghost-story-factory/discussions)
- **Email**: your@email.com

---

## ⭐ Star History

如果这个项目对您有帮助，请给一个 Star ⭐！

---

<p align="center">
  <strong>用 AI 讲好中国的都市传说故事 🎭👻</strong>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/your-username">Your Name</a>
</p>
