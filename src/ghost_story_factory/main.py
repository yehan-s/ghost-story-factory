import argparse
import os
import re
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import GoogleSearchRun
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (如 OPENAI_API_KEY、Google 搜索相关密钥)
load_dotenv()

# --- Agent 定义 ---

# Agent A: 故事搜寻者
researcher = Agent(
    role='资深灵异故事调查员',
    goal='在中文互联网上搜索关于城市 {city} 的所有灵异故事、都市传说和闹鬼地点。',
    backstory='你是一个对都市传说和民间鬼故事了如指掌的专家，擅长从海量信息中过滤出有价值的线索。',
    tools=[GoogleSearchRun()],
    llm=ChatOpenAI(model="gpt-4o"),  # 或替换为您可用的模型
    verbose=True,
    allow_delegation=False,
)

# Agent B: 框架提炼师
analyst = Agent(
    role='金牌编剧与故事分析师',
    goal='从非结构化的原始文本中，提炼出结构化的、用于撰写故事的核心框架。必须以 JSON 格式输出。',
    backstory='你拥有敏锐的故事嗅觉，能迅速识别出任何故事的核心要素（地点、角色、事件、冲突），并将其整理为结构化数据。',
    tools=[],
    llm=ChatOpenAI(model="gpt-4o"),
    verbose=True,
    allow_delegation=False,
)

# Agent C: 叙事编剧
writer = Agent(
    role='B 站百万粉丝的恐怖故事 UP 主',
    goal='将结构化的 JSON 框架，扩写成一篇引人入胜、氛围感十足的“讲述式”故事文案（Markdown 格式）。',
    backstory='你是讲故事的大师，擅长使用第一人称视角、强烈的心理描写和恰到好处的停顿来营造恐怖气氛。你的文案能让人不寒而栗。',
    tools=[],
    llm=ChatOpenAI(model="gpt-4"),  # 可根据可用模型调整
    verbose=True,
    allow_delegation=False,
)


# --- Task 定义 ---

# 任务 1: 搜索
task_search = Task(
    description='执行对城市 {city} 的深度网络搜索。汇总至少 3 个不同的故事或传说，将所有找到的原始文本合并为一个文档。',
    expected_output='一个包含所有搜索结果的 Markdown 格式长文本。',
    agent=researcher,
)

# 任务 2: 提炼
task_analyze = Task(
    description='分析 [搜寻者] 提供的原始素材。识别出最有潜力的 1 个故事，并将其提炼为 JSON 框架，包含 "title", "location", "core_legend", "key_elements" 字段。',
    expected_output='一个包含故事核心框架的 JSON 字符串。',
    agent=analyst,
)

# 任务 3: 撰写
task_write = Task(
    description='使用 [框架师] 提供的 JSON 框架，撰写一篇至少 1500 字的详细故事文案。必须包含引人入胜的开头、丰富的细节和恐怖的氛围渲染。',
    expected_output='一篇完整的、高质量的 Markdown 格式的故事文案。',
    agent=writer,
)


# --- CLI 入口函数 (`run` 函数) ---

def _sanitize_filename(name: str) -> str:
    """将城市名转换为安全文件名。"""
    s = name.strip()
    s = s.replace("/", "_").replace("\\", "_")
    # 允许常见文字、数字、破折号与空格，其余替换为下划线
    s = re.sub(r"[^\w\-\s\u4e00-\u9fff]", "_", s)
    s = re.sub(r"\s+", "_", s)
    return s or "city"


def run():
    """命令行入口：解析参数，编排 Crew 流程，保存产出。"""
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="AI 灵异故事助手 (MCP-CLI)")
    parser.add_argument("--city", type=str, required=True, help="要搜索的目标城市名称")
    args = parser.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    print(f"\n[AI 助手]: 正在启动 MCP 工作流，目标城市: {city} ...\n")

    # 2. 组建 Crew (团队) 和 Process (工作流)
    story_crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[task_search, task_analyze, task_write],
        process=Process.sequential,  # A -> B -> C 顺序执行
        verbose=2,
    )

    # 3. 启动任务
    inputs = {"city": city}
    final_story_content = story_crew.kickoff(inputs=inputs)

    # 4. 保存产出到本地文件
    output_basename = f"{_sanitize_filename(city)}_story.md"
    try:
        content = str(final_story_content)
        with open(output_basename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n[AI 助手]: 任务完成！故事已保存到: ./{output_basename}\n")
    except Exception as e:
        print(f"\n[AI 助手]: 错误！保存文件失败: {e}\n")
        print("--- 故事内容 (请手动复制) ---")
        try:
            print(str(final_story_content))
        except Exception:
            print("<无可打印内容>")
        print("--------------------------")


if __name__ == "__main__":
    # 允许直接运行：python src/ghost_story_factory/main.py --city "广州"
    run()

