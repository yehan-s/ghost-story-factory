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

# 4) 运行
get-story --city "广州"
```

### 作为一次性工具运行（发布到 PyPI 后）

```bash
# 使用 uvx（需用户已安装 uv）
uvx ghost-story-factory get-story --city "东莞"

# 或使用 pipx
pipx run ghost-story-factory get-story --city "东莞"
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

