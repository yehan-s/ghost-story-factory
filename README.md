# Ghost Story Factory v3.1 🎯

**一个专业的灵异故事生成工厂** - 基于CrewAI和专业范文模板，自动生成完整的、高质量的灵异故事。

## 🌟 核心特性

- ✅ **自动化生成**：输入城市名，自动生成完整故事（1500-3000字）
- ✅ **专业范文**：基于35个专业设计模式（范文文件夹）
- ✅ **分层架构**：阶段1（世界书1.0）→ 阶段2（角色+规则）→ 阶段3（GDD+故事）
- ✅ **选项交互式设计**：支持生成游戏化的选择点系统
- ✅ **AI做体力活，人类做创意活**

## 📚 文档索引

- **🔥 完整工作流程指南**：[WORKFLOW.md](./WORKFLOW.md) ⭐ **推荐**
- **快速上手**：见下方"快速开始"
- **游戏引擎使用指南**：[GAME_ENGINE.md](./GAME_ENGINE.md) 🎮
- **使用指南（精简版）**：[USAGE.md](./USAGE.md)
- **项目规格说明（开发者/验收）**：[SPEC.md](./SPEC.md)
- **范文库说明**：[范文/README.md](./范文/README.md)
- **范文索引（AI优化）**：[范文/00-index.md](./范文/00-index.md)
- **架构设计**：[范文/00-architecture.md](./范文/00-architecture.md)

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

# 3. 生成故事（自动执行完整流程）
python generate_full_story.py --city 武汉

# 或使用shell脚本
chmod +x generate_full_story.sh
./generate_full_story.sh 武汉
```

**输出目录：** `deliverables/程序-武汉/`

**生成文件：**
- ✅ `武汉_lore_v1.md` - 世界书1.0（高保真地基）
- ✅ `武汉_protagonist.md` - 角色分析
- ✅ `武汉_lore_v2.md` - 世界书2.0（游戏化规则）🎮
- ✅ `武汉_gdd.md` - AI导演任务简报 🎮
- ✅ `武汉_story.md` - **完整故事（⭐最终产物）**
- ✅ `README.md` - 说明文档

**🎮 = 游戏引擎所需文件**

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
# 完整流程，基于范文模板
python generate_full_story.py --city 广州 --output deliverables/程序-广州/
```

**优点：**
- ✅ 自动执行阶段1→2→3的完整流程
- ✅ 使用范文文件夹中的专业提示词
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
