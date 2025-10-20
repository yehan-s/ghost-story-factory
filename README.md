# Ghost Story Factory

一个基于 CrewAI 的命令行工具，输入城市名，自动进行素材搜集、框架提炼与故事撰写，在当前目录生成 `[城市名]_story.md`。

- AI 做“体力活”——搜集与撰写草稿
- 人类做“创意活”——基于产出编写最终游戏脚本与角色卡

## 安装与运行

建议使用 `uv`（或 `pip`）。项目已提供 `pyproject.toml` 与脚本入口。

### 本地开发

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
