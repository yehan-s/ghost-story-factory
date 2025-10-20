
好的，这是一份专门为您的 AI 开发助手（"CLI Agent"）准备的开发说明文档。

这份文档的目标是构建一个**本地命令行工具 (CLI)**，它将作为您的“AI 故事助手”。它严格遵循您的要求：AI 负责素材搜集和故事撰写，您（人类）负责最终的游戏脚本和角色卡设计。

该工具将被打包并发布到 PyPI，以便您可以使用 `uvx`（或 `pipx`）在任何地方“在线”运行它。

-----

### AI 灵异故事助手 (MCP-CLI) 开发规格文档

**版本：** 1.0 (CLI-Edition)
**项目代号：** Ghost Story Factory

### 1\. 项目目标与哲学

**1.1. 目标 (Goal)**
构建一个 Python 命令行工具。该工具接收一个“城市”名称作为参数，然后自动搜集、分析并撰写一篇关于该城市的、高质量的“UP 主风格”灵异故事文案。

**1.2. 核心哲学 (Philosophy): “人类在环” (Human-in-the-Loop)**
本项目**不是**一个全自动的游戏内容工厂。它是“总设计师”（用户）的**辅助工具**。

  * **AI 的职责（本项目）：** 负责繁琐的“体力活”——即搜集海量素材、提炼核心框架、并将其扩写成一篇细节丰富的灵异故事。
  * **人类的职责（项目外）：** 负责核心的“创意活”——即阅读 AI 产出的故事文案，并基于此灵感，**手动**创作最终的游戏脚本（`.xml`）和角色卡（`.json`）。

**1.3. 命令列表 (Command List)**

  * `set-city`：接收一个城市作为参数，列出这个城市的灵异故事，只把名字和一段简介列表
  * `get-struct`：选取刚刚其中一个故事的，列出这个故事框架，补充所有细节
  * `get-story`：以讲述者的角度，完善这个故事所有细节，逻辑要得到闭环，可以进行一定量的改

**1.4. 最终产出 (Final Deliverable)**

  * 一个 `[城市名]_story.md` 格式的 Markdown 文件，保存在当前运行目录下。

-----

### 2\. 核心技术栈

| 类别 | 技术 | 用途 |
| :--- | :--- | :--- |
| **MCP 框架** | `CrewAI` | 编排和管理多智能体（Agents）的工作流。 |
| **工具集** | `LangChain` | 为 `CrewAI` 的 Agent 提供现成的工具，尤其是 `GoogleSearchRun`。 |
| **打包与依赖** | `pyproject.toml` | Python 项目的“身份证”，定义依赖和脚本入口。 |
| **包管理器** | `uv` / `pip` | 用于管理本地开发环境。 |
| **执行器 (用户端)** | `uvx` (或 `pipx`) | 目标：实现 `npx` 风格的“在线”执行。 |
| **CLI 接口** | `argparse` (Python 内置) | 用于解析命令行参数（如 `--city`）。 |

-----

### 3\. 项目文件结构

这是标准的 Python 包结构，对于发布到 PyPI 至关重要。

```
ghost-story-factory/
├── pyproject.toml       <-- [核心] 包定义、依赖和脚本入口
├── src/
│   └── ghost_story_factory/
│       ├── __init__.py
│       └── main.py          <-- 所有的 CrewAI 逻辑和 CLI 入口
└── README.md
```

-----

### 4\. `pyproject.toml` 规格 (关键文件)

这是项目的“灵魂”。它告诉 `uvx` 该如何运行您的代码。

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "ghost-story-factory" # 确保这个名字在 PyPI 上是唯一的
version = "1.0.0"
description = "一个 AI 灵异故事素材收集助手 (MCP-CLI)"
readme = "README.md"
authors = [
    { name = "Your Name", email = "your@email.com" },
]
license = { file = "LICENSE" } # (可选, 但推荐)
requires-python = ">=3.10"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Topic :: Utilities",
]

# [重要] 核心依赖
dependencies = [
    "crewai>=0.30.0",          # CrewAI 框架
    "langchain-community",   # LangChain 社区版 (提供工具)
    "langchain-google-community", # Google 搜索工具
    "python-dotenv",         # 用于加载 .env 文件 (如 API Keys)
    "langchain-openai",      # (或其他 LLM 提供商, 如 langchain-anthropic)
]

# [核心中的核心] 命令行脚本入口
# 这行代码的意思是：
# 当用户在终端运行 "get-story" 命令时,
# 系统应执行 "src/ghost_story_factory/main.py" 文件中的 "run" 函数。
[project.scripts]
get-story = "ghost_story_factory.main:run"

[project.urls]
"Homepage" = "https://github.com/your-username/ghost-story-factory"
"Bug Tracker" = "https://github.com/your-username/ghost-story-factory/issues"
```

-----

### 5\. `src/ghost_story_factory/main.py` 实施指南

这是您唯一的 Python 逻辑文件。

```python
import argparse
import os
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import GoogleSearchRun
from langchain_openai import ChatOpenAI # (或您选择的任何 LLM)
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (如 OPENAI_API_KEY)
load_dotenv()

# --- Agent 定义 ---

# Agent A: 故事搜寻者
researcher = Agent(
    role='资深灵异故事调查员',
    goal='在中文互联网上搜索关于城市 {city} 的所有灵异故事、都市传说和闹鬼地点。',
    backstory='你是一个对都市传说和民间鬼故事了如指掌的专家，擅长从海量信息中过滤出有价值的线索。',
    tools=[GoogleSearchRun()],
    llm=ChatOpenAI(model="gpt-4o"), # (或您选择的 LLM)
    verbose=True,
    allow_delegation=False
)

# Agent B: 框架提炼师
analyst = Agent(
    role='金牌编剧与故事分析师',
    goal='从非结构化的原始文本中，提炼出结构化的、用于撰写故事的核心框架。必须以 JSON 格式输出。',
    backstory='你拥有敏锐的故事嗅觉，能迅速识别出任何故事的核心要素（地点、角色、事件、冲突），并将其整理为结构化数据。',
    tools=[],
    llm=ChatOpenAI(model="gpt-4o"),
    verbose=True,
    allow_delegation=False
)

# Agent C: 叙事编剧
writer = Agent(
    role='B 站百万粉丝的恐怖故事 UP 主',
    goal='将结构化的 JSON 框架，扩写成一篇引人入胜、氛围感十足的“讲述式”故事文案（Markdown 格式）。',
    backstory='你是讲故事的大师，擅长使用第一人称视角、强烈的心理描写和恰到好处的停顿来营造恐怖气氛。你的文案（如‘荔湾广场’版）能让人不寒而栗。',
    tools=[],
    llm=ChatOpenAI(model="gpt-4"), # (使用文笔更强的模型)
    verbose=True,
    allow_delegation=False
)

# --- Task 定义 ---

# 任务 1: 搜索
task_search = Task(
    description='执行对城市 {city} 的深度网络搜索。汇总至少 3 个不同的故事或传说，将所有找到的原始文本合并为一个文档。',
    expected_output='一个包含所有搜索结果的 Markdown 格式长文本。',
    agent=researcher
)

# 任务 2: 提炼
task_analyze = Task(
    description='分析 [搜寻者] 提供的原始素材。识别出最有潜力的 1 个故事，并将其提炼为 JSON 框架，包含 "title", "location", "core_legend", "key_elements" 字段。',
    expected_output='一个包含故事核心框架的 JSON 字符串。',
    agent=analyst
)

# 任务 3: 撰写
task_write = Task(
    description='使用 [框架师] 提供的 JSON 框架，撰写一篇至少 1500 字的详细故事文案。必须包含引人入胜的开头、丰富的细节和恐怖的氛围渲染。',
    expected_output='一篇完整的、高质量的 Markdown 格式的故事文案。',
    agent=writer
)

# --- CLI 入口函数 (`run` 函数) ---

def run():
    # 1. 设置命令行参数解析
    parser = argparse.ArgumentParser(description="AI 灵异故事助手 (MCP-CLI)")
    parser.add_argument("--city", type=str, required=True, help="要搜索的目标城市名称")
    args = parser.parse_args()

    city = args.city
    print(f"\n[AI 助手]: 正在启动 MCP 工作流，目标城市: {city} ...\n")

    # 2. 组建 Crew (团队) 和 Process (工作流)
    story_crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[task_search, task_analyze, task_write],
        process=Process.sequential, # 关键：A -> B -> C 顺序执行
        verbose=2
    )

    # 3. 启动任务
    inputs = {'city': city}
    final_story_content = story_crew.kickoff(inputs=inputs)

    # 4. 保存产出到本地文件
    output_filename = f"{city}_story.md"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(final_story_content)
        print(f"\n[AI 助手]: 任务完成！故事已保存到: ./{output_filename}\n")
    except Exception as e:
        print(f"\n[AI 助手]: 错误！保存文件失败: {e}\n")
        print("--- 故事内容 (请手动复制) ---")
        print(final_story_content)
        print("--------------------------")

# (这是为了在本地开发时也能直接运行 `python src/ghost_story_factory/main.py --city "广州"`)
if __name__ == "__main__":
    run()
```

-----

### 6\. 开发、发布与执行流程

#### 6.1. 本地开发

1.  确保安装了 Python 和 `uv` (或 `pip`)。
2.  创建虚拟环境：`uv venv`
3.  激活环境：`source .venv/bin/activate`
4.  安装依赖（进入可编辑模式）：`uv pip install -e .`
5.  创建 `.env` 文件并填入 `OPENAI_API_KEY=...`
6.  运行测试：`get-story --city "广州"` (因为已安装到可编辑模式)

#### 6.2. 发布到 PyPI

1.  安装 `build` 和 `twine`：`uv pip install build twine`
2.  打包：`python -m build`
3.  上传 (需要 PyPI 账号)：`twine upload dist/*`

#### 6.3. 最终用户执行 (使用 `uvx`)

这是您最关心的部分。一旦发布到 PyPI，您（或任何用户）就可以在**任何电脑上**执行以下命令，无需手动下载或安装：

```bash
# 确保用户安装了 uv (例如: pip install uv)
# `uvx` 会自动处理：
# 1. 临时下载您的 "ghost-story-factory" 包
# 2. 自动安装其所有依赖 (crewai, langchain...)
# 3. 运行您在 [project.scripts] 中定义的 "get-story" 入口
# 4. 执行您的 main:run() 函数
# 5. 在当前目录下生成 "[城市名]_story.md" 文件

uvx ghost-story-factory get-story --city "东莞"
```

**(备选：使用 `pipx`)**

```bash
# 确保用户安装了 pipx (例如: pip install pipx)
pipx run ghost-story-factory get-story --city "东莞"
```