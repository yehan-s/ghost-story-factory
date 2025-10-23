import argparse
import os
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Any
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import GoogleSearchRun
from crewai.llm import LLM
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (如 OPENAI_API_KEY、Google 搜索相关密钥)
load_dotenv()


# ============================================================================
# 数据模型定义（基于实际 JSON 结构）
# ============================================================================

@dataclass
class Candidate:
    """候选故事结构（来自 set-city 命令）"""
    title: str
    blurb: str
    source: str


@dataclass
class StoryStructure:
    """故事结构化框架（来自 get-struct 命令）"""
    title: str
    city: str
    location_name: str
    core_legend: str
    key_elements: List[str]
    potential_roles: List[str]


@dataclass
class LoreRule:
    """世界观规则项"""
    name: str
    description: str
    trigger: str = ""
    signal: str = ""


@dataclass
class LoreMotif:
    """世界观意象"""
    name: str
    pattern: str
    symbolism: str


@dataclass
class LoreLocation:
    """世界观地点"""
    name: str
    traits: List[str]
    taboos: List[str]
    sensory: List[str]


@dataclass
class Lore:
    """世界观圣经（来自 get-lore 命令）"""
    world_truth: str
    rules: List[Dict[str, Any]]  # 实际可以是 LoreRule，但为兼容性保持灵活
    motifs: List[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    timeline_hints: List[str]
    allowed_roles: List[str]


# ============================================================================
# 工具函数（JSON 处理、文件操作、Prompt 加载）
# ============================================================================


def _load_prompt(name: str) -> str | None:
    """从当前工作目录加载自定义 Prompt 文件，不存在则返回 None。"""
    path = os.path.join(os.getcwd(), name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _try_parse_json_obj(text: str) -> dict | None:
    """从文本中提取并解析 JSON 对象。

    处理流程：
    1. 直接尝试解析整个文本
    2. 若失败，提取 {...} 块并修正中文引号
    3. 返回解析后的 dict 或 None
    """
    # 1) 直接解析
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else None
    except Exception:
        pass

    # 2) 提取 JSON 对象并修正引号
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        blob = m.group(0)
        # 去除 BOM 和修正中文引号
        blob = blob.replace("\ufeff", "")
        blob = blob.replace('"', '"').replace('"', '"')
        blob = blob.replace(''', "'").replace(''', "'")
        try:
            v = json.loads(blob)
            return v if isinstance(v, dict) else None
        except Exception:
            pass

    return None


def _write_json_file(path: str, data: object) -> None:
    """保存 JSON 到文件。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_json_file(path: str) -> object:
    """从文件读取 JSON。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json_or_fallback(data: dict | None, json_path: str, text_fallback: str) -> None:
    """保存 JSON 数据，失败则保存原始文本到 .txt 文件。"""
    if data is not None:
        _write_json_file(json_path, data)
    else:
        txt_path = json_path.replace(".json", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_fallback)


def _ensure_candidates_file(city: str) -> tuple[list | None, str]:
    """确保候选文件存在，返回 (candidates_data, candidates_path)。

    若文件不存在，自动生成；返回的 data 可能是 list 或 None。

    注意：_generate_candidates 函数需要在调用此函数前定义。
    """
    cand_path = f"{_sanitize_filename(city)}_candidates.json"
    cand_txt_path = cand_path.replace(".json", ".txt")

    if not os.path.exists(cand_path) and not os.path.exists(cand_txt_path):
        print(f"[AI 助手]: 未找到候选文件 ./{cand_path}，将先自动生成候选……")
        # 需要在后面定义 _generate_candidates
        # 这里使用前向引用，实际调用时函数已定义
        _generate_candidates(city)

    candidates = None
    if os.path.exists(cand_path):
        try:
            candidates = _read_json_file(cand_path)
        except Exception:
            candidates = None

    return candidates, cand_path


def _pick_candidate_from_list(
    candidates: list,
    title_query: str | None = None,
    index: int = 1
) -> tuple[str, str]:
    """从候选列表中选择一个，返回 (title, blurb)。

    Args:
        candidates: 候选列表
        title_query: 标题模糊匹配（优先）
        index: 序号（从1开始，默认1）

    Returns:
        (picked_title, picked_blurb)
    """
    picked_title = None
    picked_blurb = None

    if title_query:
        key = title_query.strip().lower()
        for item in candidates:
            t = (item.get("title") if isinstance(item, dict) else None) or ""
            if key in t.lower():
                picked_title = t
                picked_blurb = item.get("blurb") if isinstance(item, dict) else ""
                break
    else:
        idx = index - 1
        if 0 <= idx < len(candidates):
            item = candidates[idx]
            picked_title = (item.get("title") if isinstance(item, dict) else str(item)) or ""
            picked_blurb = item.get("blurb") if isinstance(item, dict) else ""

    return picked_title or "", picked_blurb or ""


def _sanitize_filename(name: str) -> str:
    """将城市名转换为安全文件名。"""
    s = name.strip()
    s = s.replace("/", "_").replace("\\", "_")
    # 允许常见文字、数字、破折号与空格，其余替换为下划线
    s = re.sub(r"[^\w\-\s\u4e00-\u9fff]", "_", s)
    s = re.sub(r"\s+", "_", s)
    return s or "city"


def _generate_story_from_json(json_path: str, writer: Agent) -> str:
    """从 JSON 框架文件生成故事（通用逻辑）。

    Args:
        json_path: JSON 框架文件路径
        writer: Writer Agent

    Returns:
        生成的故事内容
    """
    # 读取 JSON 框架
    try:
        struct_obj = _read_json_file(json_path)
        struct_json = json.dumps(struct_obj, ensure_ascii=False, indent=2)
    except Exception:
        with open(json_path, "r", encoding="utf-8") as f:
            struct_json = f.read()

    # 加载自定义 Prompt 或使用默认
    writer_prompt = _load_prompt("get-story.md")
    if writer_prompt is None:
        writer_prompt = (
            "[SYSTEM]\n你是恐怖故事 UP 主，按给定 JSON 框架扩写成 1500+ 字 Markdown。\n"
            "[严格指令]\n只返回 Markdown 文案。\n[USER]\n[故事框架]\n{json_skeleton_from_agent_b}\n[/故事框架]"
        )

    # 创建任务并执行
    writer_task = Task(
        description=writer_prompt,
        expected_output='Markdown 格式完整故事',
        agent=writer,
    )
    story_crew = Crew(
        agents=[writer],
        tasks=[writer_task],
        process=Process.sequential,
        verbose=True,
    )
    inputs = {"json_skeleton_from_agent_b": struct_json}
    return str(story_crew.kickoff(inputs=inputs))


def _gather_raw_materials(
    city: str,
    picked_title: str,
    picked_blurb: str,
    researcher: Agent
) -> str:
    """汇编原始素材（通用逻辑）。

    Args:
        city: 城市名
        picked_title: 选中的故事标题
        picked_blurb: 选中的故事简介
        researcher: Researcher Agent

    Returns:
        汇编的原始素材长文本
    """
    research_desc = (
        "围绕城市 {city} 的选中候选故事，汇编原始素材为长文本。\n"
        "若给定标题与简介，则以其为主题展开收集与整合。\n"
        "请合并来源梳理、传说变体、时间线、目击叙述与反驳观点，输出为 Markdown 长文。\n"
        "选中候选：\n标题：{picked_title}\n简介：{picked_blurb}\n城市：{city}\n"
        "(如标题为空，则请根据城市最具代表性的一个传说自动选择)"
    )
    research_task = Task(
        description=research_desc,
        expected_output="关于选中候选的长篇原始素材（Markdown 长文）",
        agent=researcher,
    )
    research_crew = Crew(
        agents=[researcher],
        tasks=[research_task],
        process=Process.sequential,
        verbose=True
    )
    research_inputs = {
        "city": city,
        "picked_title": picked_title,
        "picked_blurb": picked_blurb
    }
    return str(research_crew.kickoff(inputs=research_inputs))


def _normalize_struct(data: dict, city_name: str) -> dict:
    """规范化故事结构字段。

    Args:
        data: 原始 JSON 对象
        city_name: 城市名（用于兜底）

    Returns:
        规范化后的 StoryStructure 字典
    """
    out = {}
    out["title"] = str(data.get("title") or "").strip() or "未命名故事"
    out["city"] = str(data.get("city") or city_name)
    loc = data.get("location_name") or data.get("location") or ""
    out["location_name"] = str(loc)
    out["core_legend"] = str(data.get("core_legend") or data.get("legend") or "").strip()

    # key_elements
    ke = data.get("key_elements")
    if not isinstance(ke, list):
        ke = []
    out["key_elements"] = [str(x) for x in ke if isinstance(x, (str, int, float))]

    # potential_roles
    roles = data.get("potential_roles")
    if not isinstance(roles, list):
        # 简单兜底，避免空字段
        roles = ["目击者", "讲述者", "地方居民"]
    out["potential_roles"] = [str(x) for x in roles if isinstance(x, (str, int, float))]

    return out


def _build_llm():
    """根据环境变量选择并构建 LLM 客户端。

    优先级：KIMI_* > OPENAI_* > 默认OpenAI。
    支持的变量：
      - KIMI_API_KEY, KIMI_API_BASE(或KIMI_BASE_URL), KIMI_MODEL
      - OPENAI_API_KEY, OPENAI_BASE_URL(或OPENAI_API_BASE), OPENAI_MODEL
    """
    # Kimi (Moonshot) 优先
    kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
    if kimi_key:
        base = (
            os.getenv("KIMI_API_BASE")
            or os.getenv("KIMI_BASE_URL")
            or os.getenv("KIMI_API_URL")
            or os.getenv("MOONSHOT_API_URL")
            or "https://api.moonshot.cn/v1"
        )
        model = (
            os.getenv("KIMI_MODEL")
            or os.getenv("MOONSHOT_MODEL")
            or "kimi-k2-0905-preview"
        )
        # Moonshot/Kimi 是 OpenAI 兼容接口，但模型名不带提供商前缀，需显式指定 provider
        return LLM(
            model=model,
            api_key=kimi_key,
            api_base=base,
            custom_llm_provider="openai",
            max_tokens=16000,  # 支持长文本生成（约5000字故事需要足够token）
        )

    # OpenAI 或兼容代理
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        # LLM 支持 base_url=None，则走官方默认
        return LLM(
            model=model,
            api_key=openai_key,
            base_url=base,
            max_tokens=16000,  # 支持长文本生成（约5000字故事需要足够token）
        )

    # 无任何可用密钥
    raise RuntimeError(
        "未检测到可用的 LLM 凭证。请在 .env 或环境中配置 KIMI_API_KEY 或 OPENAI_API_KEY。"
    )


# --- Agent 定义工厂 ---

def _make_agents():
    llm_main = _build_llm()
    # 如果需要不同写作模型，可在此创建第二个 llm；目前保持一致以简化
    llm_writer = llm_main

    google_enabled = bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID"))

    researcher = Agent(
        role='资深灵异故事调查员',
        goal='在中文互联网上搜索关于城市 {city} 的所有灵异故事、都市传说和闹鬼地点。',
        backstory='你是一个对都市传说和民间鬼故事了如指掌的专家，擅长从海量信息中过滤出有价值的线索。',
        tools=[GoogleSearchRun()] if google_enabled else [],
        llm=llm_main,
        verbose=True,
        allow_delegation=False,
    )

    analyst = Agent(
        role='金牌编剧与故事分析师',
        goal='从非结构化的原始文本中，提炼出结构化的、用于撰写故事的核心框架。必须以 JSON 格式输出。',
        backstory='你拥有敏锐的故事嗅觉，能迅速识别出任何故事的核心要素（地点、角色、事件、冲突），并将其整理为结构化数据。',
        tools=[],
        llm=llm_main,
        verbose=True,
        allow_delegation=False,
    )

    writer = Agent(
        role='B 站百万粉丝的恐怖故事 UP 主',
        goal='将结构化的 JSON 框架，扩写成一篇引人入胜、氛围感十足的“讲述式”故事文案（Markdown 格式）。',
        backstory='你是讲故事的大师，擅长使用第一人称视角、强烈的心理描写和恰到好处的停顿来营造恐怖气氛。你的文案能让人不寒而栗。',
        tools=[],
        llm=llm_writer,
        verbose=True,
        allow_delegation=False,
    )

    return researcher, analyst, writer


# --- Task 定义 ---

def _make_tasks(researcher: Agent, analyst: Agent, writer: Agent):
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

    return task_search, task_analyze, task_write


# --- CLI 入口函数 (`run` 函数) ---

def run():
    """命令行入口：解析参数，编排 Crew 流程，保存产出。"""
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="AI 灵异故事助手 (MCP-CLI)")
    parser.add_argument("--city", type=str, required=True, help="要搜索的目标城市名称")
    parser.add_argument("--out", type=str, required=False, help="自定义输出文件路径（可含目录）")
    parser.add_argument("--role", type=str, required=False, help="优先按角色线写作（若存在 <city>_role_<role>.json）")
    args = parser.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    print(f"\n[AI 助手]: 正在启动 MCP 工作流，目标城市: {city} ...\n")

    # 2. 组建 Agents 与 Tasks
    researcher, analyst, writer = _make_agents()
    task_search, task_analyze, task_write = _make_tasks(researcher, analyst, writer)

    # 3. 决定生成策略：角色线 > 结构框架 > 全流程
    role = (args.role or "").strip()

    # 检查角色线文件
    role_story_candidates = []
    if role:
        role_story_candidates.append(f"{_sanitize_filename(city)}_role_{_sanitize_filename(role)}.json")
    role_story_candidates.append(f"{_sanitize_filename(city)}_role_story.json")

    picked_role_story = next((p for p in role_story_candidates if os.path.exists(p)), None)
    struct_path = f"{_sanitize_filename(city)}_struct.json"

    # 执行生成策略
    if picked_role_story:
        # 策略 1: 使用角色线 JSON
        final_story_content = _generate_story_from_json(picked_role_story, writer)
    elif os.path.exists(struct_path):
        # 策略 2: 使用结构框架 JSON
        final_story_content = _generate_story_from_json(struct_path, writer)
    else:
        # 策略 3: 全流程（搜索 → 分析 → 写作）
        story_crew = Crew(
            agents=[researcher, analyst, writer],
            tasks=[task_search, task_analyze, task_write],
            process=Process.sequential,
            verbose=True,
        )
        final_story_content = story_crew.kickoff(inputs={"city": city})

    # 5. 保存产出到本地文件
    output_basename = args.out.strip() if getattr(args, "out", None) else f"{_sanitize_filename(city)}_story.md"
    try:
        content = str(final_story_content)
        out_dir = os.path.dirname(output_basename)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
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


# ---------------- 1.3 命令实现：set-city / get-struct / get-story ----------------

def _escape_json_str(s: str) -> str:
    """将文本转换为 JSON 字符串内容（不含外层引号）。"""
    return json.dumps(s, ensure_ascii=False)[1:-1]


def _normalize_candidates_blob(blob: str) -> str:
    """尽力将近似 JSON 的候选列表修正为可解析的 JSON。

    处理要点：
    - 去除 BOM / 不可见字符
    - 修正常见字段值使用中文引号包裹的情况（仅限字段 title/blurb/source）
    """
    blob = blob.replace("\ufeff", "")

    import re as _re

    def fix_field(field: str, text: str) -> str:
        # 将 "field": “xxx” 修正为 "field": "xxx"
        pattern = rf'("{field}"\s*:\s*)[“](.*?)[”]'
        def repl(m: _re.Match):
            content = m.group(2)
            return f'{m.group(1)}"{_escape_json_str(content)}"'
        return _re.sub(pattern, repl, text, flags=_re.S)

    for fld in ("title", "blurb", "source"):
        blob = fix_field(fld, blob)
    return blob


def _generate_candidates(city: str) -> list | None:
    """生成候选故事列表，并写入 <city>_candidates.json 或 .txt；返回 JSON 列表或 None。"""
    researcher, _, _ = _make_agents()
    # 优先使用 set-city.md 自定义提示词
    description = _load_prompt("set-city.md")
    if description is None:
        description = (
            "请针对城市 {city} 汇总至少 5 条广为流传的灵异故事/都市传说候选，"
            "以 JSON 数组输出。每项包含: title(故事名), blurb(一句话简介), source(可选来源或线索)。"
            "仅输出 JSON，不要其它文字。"
        )
    task = Task(
        description=description,
        expected_output="JSON 数组，字段: title, blurb, source",
        agent=researcher,
    )
    crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential, verbose=True)
    raw = crew.kickoff(inputs={"city": city})

    text = str(raw)
    out_json = f"{_sanitize_filename(city)}_candidates.json"
    out_txt = out_json.replace(".json", ".txt")

    # 1) 直接尝试解析
    try:
        data = json.loads(text)
        if isinstance(data, list):
            _write_json_file(out_json, data)
            return data
    except Exception:
        pass

    # 2) 提取数组并修正
    import re as _re
    m = _re.search(r"\[[\s\S]*\]", text)
    if m:
        blob = m.group(0)
        fixed = _normalize_candidates_blob(blob)
        try:
            data = json.loads(fixed)
            if isinstance(data, list):
                _write_json_file(out_json, data)
                return data
        except Exception:
            pass

    # 3) 失败则落原始文本
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(text)
    return None


def set_city():
    """命令 set-city：
    - 输入：--city
    - 输出：打印候选故事列表，并保存到 ./<city>_candidates.json
    """
    parser = argparse.ArgumentParser(description="列出城市的灵异故事候选（名称 + 简介）")
    parser.add_argument("--city", type=str, required=True, help="目标城市")
    args = parser.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    data = _generate_candidates(city)
    out_json = f"{_sanitize_filename(city)}_candidates.json"
    if data is not None:
        print(f"\n[AI 助手]: 候选故事列表已保存: ./{out_json}\n")
        for i, item in enumerate(data, 1):
            title = item.get("title") if isinstance(item, dict) else None
            blurb = item.get("blurb") if isinstance(item, dict) else None
            print(f"[{i}] {title} - {blurb}")
    else:
        print(f"\n[AI 助手]: 未能解析为 JSON，已保存原始文本到 ./{out_json.replace('.json','.txt')}\n")


def get_struct():
    """命令 get-struct：
    - 输入：--city 必填； --index 或 --title 选其一（默认 index=1）
    - 行为：读取 ./<city>_candidates.json，选择指定故事，产出详细结构化 JSON 到 ./<city>_struct.json
    """
    # 1. 参数解析
    p = argparse.ArgumentParser(description="从候选中选定故事并生成结构化框架")
    p.add_argument("--city", type=str, required=True, help="目标城市")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--index", type=int, help="候选序号（从1开始）")
    g.add_argument("--title", type=str, help="候选标题（模糊匹配）")
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    # 2. 确保候选文件存在并加载
    candidates, _ = _ensure_candidates_file(city)

    # 3. 从候选列表中选择
    picked_title, picked_blurb = "", ""
    if isinstance(candidates, list):
        picked_title, picked_blurb = _pick_candidate_from_list(
            candidates,
            title_query=args.title,
            index=args.index or 1
        )

    # 4. 汇编原始素材
    researcher, analyst, _ = _make_agents()
    raw_material = _gather_raw_materials(city, picked_title, picked_blurb, researcher)

    # 5. 生成结构化框架
    prompt = _load_prompt("get-struct.md")
    if prompt is None:
        prompt = (
            "[SYSTEM]\n你是一个金牌编剧与故事分析师。\n"
            "[严格指令]\n1. 只返回一个 JSON 代码块。2. 严禁任何额外说明。\n"
            "键：title, city, location_name, core_legend, key_elements(数组), potential_roles(数组)\n"
            "[USER]\n[原始故事素材]\n{raw_text_from_agent_a}\n[/原始故事素材]"
        )

    analyze_task = Task(
        description=prompt,
        expected_output="仅一个 JSON 代码块，字段按规范返回",
        agent=analyst,
    )
    analyze_crew = Crew(
        agents=[analyst],
        tasks=[analyze_task],
        process=Process.sequential,
        verbose=True
    )
    text = str(analyze_crew.kickoff(inputs={"raw_text_from_agent_a": raw_material, "city": city}))

    # 6. 解析、规范化并保存
    data = _try_parse_json_obj(text)
    out_path = f"{_sanitize_filename(city)}_struct.json"

    if data is not None:
        data = _normalize_struct(data, city)
        _write_json_file(out_path, data)
        print(f"\n[AI 助手]: 故事框架已保存: ./{out_path}\n")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        with open(out_path.replace(".json", ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
        raise SystemExit("未能解析为 JSON，请检查输出（已保存为 .txt）。")


def get_lore():
    """生成城市的世界观圣经（lore.json）。"""
    # 1. 参数解析
    p = argparse.ArgumentParser(description="生成世界观圣经（lore.json）")
    p.add_argument("--city", type=str, required=True)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--index", type=int)
    g.add_argument("--title", type=str)
    p.add_argument("--out", type=str)
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    # 2. 确保候选文件存在并加载
    candidates, _ = _ensure_candidates_file(city)

    # 3. 从候选列表中选择
    picked_title, picked_blurb = "", ""
    if isinstance(candidates, list):
        picked_title, picked_blurb = _pick_candidate_from_list(
            candidates,
            title_query=args.title,
            index=args.index or 1
        )

    # 4. 汇编原始素材
    researcher, analyst, _ = _make_agents()
    raw_material = _gather_raw_materials(city, picked_title, picked_blurb, researcher)

    # 5. 生成世界观圣经
    lore_prompt = _load_prompt("lore.md")
    if lore_prompt is None:
        lore_prompt = (
            "[SYSTEM]\n你是一名'世界观圣经'构建专家。只返回一个 JSON 代码块。\n"
            "要求：world_truth, rules[], motifs[], locations[], timeline_hints[], allowed_roles[]；全部使用 ASCII 双引号。\n"
            "[USER]\n[城市]\n{city}\n[/城市]\n[原始素材]\n{raw_material}\n[/原始素材]"
        )
    task = Task(description=lore_prompt, expected_output="仅一个 JSON 代码块", agent=analyst)
    lore_crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    text = str(lore_crew.kickoff(inputs={"city": city, "raw_material": raw_material}))

    # 6. 解析并保存
    data = _try_parse_json_obj(text)
    out_path = (args.out or f"{_sanitize_filename(city)}_lore.json").strip()
    _save_json_or_fallback(data, out_path, text)

    if data is not None:
        print(f"\n[AI 助手]: 世界观圣经已保存: ./{out_path}\n")
    else:
        raise SystemExit("未能解析为 JSON，请检查输出（已保存为 .txt）。")


def gen_role():
    """基于 lore.json 生成角色剧情拍点 role_story.json。"""
    # 1. 参数解析
    p = argparse.ArgumentParser(description="从 lore.json 生成角色剧情拍点（role_story.json）")
    p.add_argument("--city", type=str, required=True)
    p.add_argument("--role", type=str, required=True)
    p.add_argument("--pov", type=str, required=False)
    p.add_argument("--lore", type=str, required=False)
    p.add_argument("--out", type=str, required=False)
    args = p.parse_args()

    city = (args.city or "").strip()
    role = (args.role or "").strip()
    if not city or not role:
        raise SystemExit("--city 与 --role 均为必填")

    # 2. 加载 lore 文件
    lore_path = (args.lore or f"{_sanitize_filename(city)}_lore.json").strip()
    if not os.path.exists(lore_path):
        raise SystemExit(f"未找到 lore 文件: {lore_path}。请先运行 get-lore。")

    try:
        lore_obj = _read_json_file(lore_path)
        lore_json = json.dumps(lore_obj, ensure_ascii=False, indent=2)
    except Exception:
        with open(lore_path, "r", encoding="utf-8") as f:
            lore_json = f.read()

    # 3. 生成角色剧情拍点
    prompt = _load_prompt("role-beats.md")
    if prompt is None:
        prompt = (
            "[SYSTEM] 你是剧情设计师。只返回一个 JSON 代码块。\n"
            "字段：role, pov, goal, constraints_used{rules[],motifs[],locations[]}, beats{opening_hook,first_contact,investigation,mid_twist,confrontation,aftershock,cta}。\n"
            "[USER]\n[世界观]\n{lore_json}\n[/世界观]\n[角色]\n{role}\n[/角色]\n[视角]\n{pov}\n[/视角]"
        )

    analyst = _make_agents()[1]
    task = Task(description=prompt, expected_output="仅一个 JSON 代码块", agent=analyst)
    role_crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    text = str(role_crew.kickoff(inputs={
        "lore_json": lore_json,
        "role": role,
        "pov": (args.pov or "第二人称")
    }))

    # 4. 解析并保存
    data = _try_parse_json_obj(text)
    out_default = f"{_sanitize_filename(city)}_role_{_sanitize_filename(role)}.json"
    out_path = (args.out or out_default).strip()
    _save_json_or_fallback(data, out_path, text)

    if data is not None:
        print(f"\n[AI 助手]: 角色剧情拍点已保存: ./{out_path}\n")
    else:
        raise SystemExit("未能解析为 JSON，请检查输出（已保存为 .txt）。")


def validate_role():
    """对比 role_story.json 与 lore.json 的一致性（软校验）。"""
    p = argparse.ArgumentParser(description="校验角色拍点与世界观圣经的一致性")
    p.add_argument("--city", type=str, required=True)
    p.add_argument("--role", type=str, required=False)
    p.add_argument("--lore", type=str, required=False)
    p.add_argument("--role-file", type=str, required=False)
    args = p.parse_args()

    city = (args.city or "").strip()
    role = (args.role or "").strip()
    lore_path = (args.lore or f"{_sanitize_filename(city)}_lore.json").strip()
    role_path = (args.role_file or (f"{_sanitize_filename(city)}_role_{_sanitize_filename(role)}.json" if role else f"{_sanitize_filename(city)}_role_story.json")).strip()

    if not os.path.exists(lore_path):
        raise SystemExit(f"未找到 lore 文件: {lore_path}")
    if not os.path.exists(role_path):
        raise SystemExit(f"未找到角色文件: {role_path}")

    lore_text = json.dumps(_read_json_file(lore_path), ensure_ascii=False)
    role_obj = _read_json_file(role_path)

    issues = []
    for k in ("role", "beats"):
        if k not in role_obj:
            issues.append(f"缺少字段: {k}")
    beats = role_obj.get("beats", {})
    for k in ("opening_hook","first_contact","investigation","mid_twist","confrontation","aftershock","cta"):
        if k not in beats:
            issues.append(f"缺少拍点: beats.{k}")

    cu = role_obj.get("constraints_used", {}) or {}
    for group in ("rules","motifs","locations"):
        arr = cu.get(group) or []
        for s in arr:
            if s and (s not in lore_text):
                issues.append(f"未在 lore 中找到约束引用: {group}:{s}")

    if issues:
        print("[验证] 发现问题：")
        for it in issues:
            print(f"- {it}")
        raise SystemExit("验证未通过。")
    else:
        print("[验证] 通过：role_story 与 lore 在软约束下匹配。")


def gen_protagonist():
    """基于 Lore v1 生成主角设计文档 (Protagonist)。"""
    p = argparse.ArgumentParser(description="生成主角设计文档 (protagonist.md)")
    p.add_argument("--city", type=str, required=True)
    p.add_argument("--lore", type=str, required=False)
    p.add_argument("--out", type=str, required=False)
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    # 加载 Lore v1 文件
    lore_path = (args.lore or f"{_sanitize_filename(city)}_lore.json").strip()
    if not os.path.exists(lore_path):
        raise SystemExit(f"未找到 Lore v1 文件: {lore_path}。请先运行 get-lore。")

    try:
        lore_obj = _read_json_file(lore_path)
        lore_content = json.dumps(lore_obj, ensure_ascii=False, indent=2)
    except Exception:
        with open(lore_path, "r", encoding="utf-8") as f:
            lore_content = f.read()

    # 加载 protagonist prompt
    prompt_path = os.path.join("范文", "protagonist.prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = (
            "[SYSTEM]\n你是一位首席叙事设计师。\n"
            "你的任务：基于《世界书 V1.0》，分析潜在主角，并推荐最佳主线角色。\n"
            "[USER]\n[世界书 V1.0]\n{world_book_markdown_content}\n[/世界书 V1.0]"
        )

    # 生成主角分析
    analyst = _make_agents()[1]
    task = Task(
        description=prompt,
        expected_output="主角分析报告 (Markdown 格式)",
        agent=analyst
    )
    crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    result = str(crew.kickoff(inputs={"world_book_markdown_content": lore_content}))

    # 保存为 Markdown
    out_path = (args.out or f"{_sanitize_filename(city)}_protagonist.md").strip()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n[AI 助手]: 主角设计文档已保存: ./{out_path}\n")


def gen_lore_v2():
    """基于 Lore v1 + Protagonist 生成深化世界观 (Lore v2)。"""
    p = argparse.ArgumentParser(description="生成深化世界观 (lore_v2.md)")
    p.add_argument("--city", type=str, required=True)
    p.add_argument("--lore-v1", type=str, required=False)
    p.add_argument("--protagonist", type=str, required=False)
    p.add_argument("--out", type=str, required=False)
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    # 加载 Lore v1
    lore_v1_path = (args.lore_v1 or f"{_sanitize_filename(city)}_lore.json").strip()
    if not os.path.exists(lore_v1_path):
        raise SystemExit(f"未找到 Lore v1 文件: {lore_v1_path}。请先运行 get-lore。")

    try:
        lore_v1_obj = _read_json_file(lore_v1_path)
        lore_v1_content = json.dumps(lore_v1_obj, ensure_ascii=False, indent=2)
    except Exception:
        with open(lore_v1_path, "r", encoding="utf-8") as f:
            lore_v1_content = f.read()

    # 加载 lore-v2 prompt
    prompt_path = os.path.join("范文", "lore-v2.prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = (
            "[SYSTEM]\n你是一位首席游戏系统设计师。\n"
            "你的任务：将《世界书 1.0》升级为《世界书 2.0 (系统增强版)》。\n"
            "[USER]\n[世界书 V1.0]\n{world_book_1_0_markdown_content}\n[/世界书 V1.0]"
        )

    # 生成 Lore v2
    analyst = _make_agents()[1]
    task = Task(
        description=prompt,
        expected_output="世界书 2.0 (Markdown 格式，含游戏系统)",
        agent=analyst
    )
    crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    result = str(crew.kickoff(inputs={"world_book_1_0_markdown_content": lore_v1_content}))

    # 保存为 Markdown
    out_path = (args.out or f"{_sanitize_filename(city)}_lore_v2.md").strip()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n[AI 助手]: Lore v2 已保存: ./{out_path}\n")


def gen_gdd():
    """基于 Lore v2 + Protagonist 生成 AI 导演任务简报 (GDD)。"""
    p = argparse.ArgumentParser(description="生成 AI 导演任务简报 (GDD.md)")
    p.add_argument("--city", type=str, required=True)
    p.add_argument("--lore-v2", type=str, required=False)
    p.add_argument("--protagonist", type=str, required=False)
    p.add_argument("--out", type=str, required=False)
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    # 加载 Lore v2
    lore_v2_path = (args.lore_v2 or f"{_sanitize_filename(city)}_lore_v2.md").strip()
    if not os.path.exists(lore_v2_path):
        raise SystemExit(f"未找到 Lore v2 文件: {lore_v2_path}。请先运行 gen-lore-v2。")

    with open(lore_v2_path, "r", encoding="utf-8") as f:
        lore_v2_content = f.read()

    # 加载 Protagonist (可选)
    protagonist_path = (args.protagonist or f"{_sanitize_filename(city)}_protagonist.md").strip()
    protagonist_content = ""
    if os.path.exists(protagonist_path):
        with open(protagonist_path, "r", encoding="utf-8") as f:
            protagonist_content = f.read()

    # 加载 GDD prompt
    prompt_path = os.path.join("范文", "GDD.prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = (
            "[SYSTEM]\n你是一位首席游戏系统设计师。\n"
            "你的任务：为主角撰写 AI 导演任务简报 (GDD)。\n"
            "[USER]\n请使用世界书和角色分析开始撰写 GDD。"
        )

    # 替换占位符
    prompt = prompt.replace("{《荔湾广场世界书 2.0 (系统增强版)》的全部 Markdown 内容}", lore_v2_content)
    prompt = prompt.replace('{《角色分析报告》中关于"保安（主角线）"的全部 Markdown 内容}', protagonist_content)

    # 生成 GDD
    analyst = _make_agents()[1]
    task = Task(
        description=prompt,
        expected_output="AI 导演任务简报 (Markdown 格式)",
        agent=analyst
    )
    crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    result = str(crew.kickoff())

    # 保存为 Markdown
    out_path = (args.out or f"{_sanitize_filename(city)}_GDD.md").strip()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n[AI 助手]: GDD 已保存: ./{out_path}\n")


def gen_main_thread():
    """基于 GDD + Lore v2 生成主线完整故事。"""
    p = argparse.ArgumentParser(description="生成主线完整故事 (main_thread.md)")
    p.add_argument("--city", type=str, required=True)
    p.add_argument("--gdd", type=str, required=False)
    p.add_argument("--lore-v2", type=str, required=False)
    p.add_argument("--out", type=str, required=False)
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    # 加载 GDD
    gdd_path = (args.gdd or f"{_sanitize_filename(city)}_GDD.md").strip()
    if not os.path.exists(gdd_path):
        raise SystemExit(f"未找到 GDD 文件: {gdd_path}。请先运行 gen-gdd。")

    with open(gdd_path, "r", encoding="utf-8") as f:
        gdd_content = f.read()

    # 加载 Lore v2 (可选)
    lore_v2_path = (args.lore_v2 or f"{_sanitize_filename(city)}_lore_v2.md").strip()
    lore_v2_content = ""
    if os.path.exists(lore_v2_path):
        with open(lore_v2_path, "r", encoding="utf-8") as f:
            lore_v2_content = f.read()

    # 加载 main-thread prompt
    prompt_path = os.path.join("范文", "main-thread.prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = (
            "[SYSTEM]\n你是 B 站百万粉丝的恐怖故事 UP 主。\n"
            "基于 GDD 和世界书，生成完整的主线故事。\n"
            "[USER]\n[GDD]\n{gdd_content}\n[/GDD]\n[世界书]\n{lore_content}\n[/世界书]"
        )

    # 替换占位符
    prompt = prompt.replace("{gdd_content}", gdd_content)
    prompt = prompt.replace("{lore_content}", lore_v2_content)

    # 生成主线故事
    storyteller = _make_agents()[2]
    task = Task(
        description=prompt,
        expected_output="完整主线故事 (Markdown 格式，≥5000字)",
        agent=storyteller
    )
    crew = Crew(
        agents=[storyteller],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    result = str(crew.kickoff())

    # 保存为 Markdown
    out_path = (args.out or f"{_sanitize_filename(city)}_main_thread.md").strip()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n[AI 助手]: 主线故事已保存: ./{out_path}\n")


def gen_branch():
    """基于 GDD + Lore v2 生成分支故事。"""
    p = argparse.ArgumentParser(description="生成分支故事 (branch_X.md)")
    p.add_argument("--city", type=str, required=True)
    p.add_argument("--branch-name", type=str, required=True, help="分支名称，如：店主线")
    p.add_argument("--gdd", type=str, required=False)
    p.add_argument("--lore-v2", type=str, required=False)
    p.add_argument("--out", type=str, required=False)
    args = p.parse_args()

    city = (args.city or "").strip()
    branch_name = (args.branch_name or "").strip()
    if not city or not branch_name:
        raise SystemExit("--city 和 --branch-name 不能为空")

    # 加载 Lore v2
    lore_v2_path = (args.lore_v2 or f"{_sanitize_filename(city)}_lore_v2.md").strip()
    if not os.path.exists(lore_v2_path):
        raise SystemExit(f"未找到 Lore v2 文件: {lore_v2_path}。")

    with open(lore_v2_path, "r", encoding="utf-8") as f:
        lore_v2_content = f.read()

    # 加载 branch prompt
    prompt_path = os.path.join("范文", "branch-1.prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = (
            "[SYSTEM]\n你是分支剧情设计师。\n"
            "基于世界书，为【{branch_name}】生成完整分支故事。\n"
            "[USER]\n[世界书]\n{lore_content}\n[/世界书]\n[分支角色]\n{branch_name}\n[/分支角色]"
        )

    # 替换占位符
    prompt = prompt.replace("{branch_name}", branch_name)
    prompt = prompt.replace("{lore_content}", lore_v2_content)

    # 生成分支故事
    storyteller = _make_agents()[2]
    task = Task(
        description=prompt,
        expected_output=f"{branch_name}分支故事 (Markdown 格式)",
        agent=storyteller
    )
    crew = Crew(
        agents=[storyteller],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    result = str(crew.kickoff())

    # 保存为 Markdown
    out_path = (args.out or f"{_sanitize_filename(city)}_branch_{_sanitize_filename(branch_name)}.md").strip()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n[AI 助手]: 分支故事已保存: ./{out_path}\n")


def gen_complete():
    """自动执行完整流程：从 struct.json 开始，依次生成所有文件直到主线故事。

    前提：必须先运行 set-city 和 get-struct
    执行流程：get-lore → gen-protagonist → gen-lore-v2 → gen-gdd → gen-main-thread
    """
    p = argparse.ArgumentParser(
        description="自动执行完整生成流程（需要先运行 set-city 和 get-struct）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法：
  # 1. 先选择故事
  set-city --city "杭州"
  get-struct --city "杭州" --index 1

  # 2. 一键生成所有内容
  gen-complete --city "杭州"

  # 或指定索引（会自动调用 get-lore）
  gen-complete --city "杭州" --index 1
"""
    )
    p.add_argument("--city", type=str, required=True, help="城市名称")
    p.add_argument("--index", type=int, required=False, help="候选故事索引（可选，如未运行 get-lore）")
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    san_city = _sanitize_filename(city)

    print("\n" + "="*60)
    print(f"🎬 开始完整故事生成流程 - 城市：【{city}】")
    print("="*60 + "\n")

    # 检查 struct.json 是否存在
    struct_path = f"{san_city}_struct.json"
    if not os.path.exists(struct_path):
        print(f"⚠️  未找到 {struct_path}")
        print("请先运行：")
        print(f"  1. set-city --city \"{city}\"")
        print(f"  2. get-struct --city \"{city}\" --index <编号>")
        raise SystemExit("\n中止：缺少必要的 struct.json 文件")

    # Step 1: 生成 Lore v1
    lore_path = f"{san_city}_lore.json"
    if os.path.exists(lore_path):
        print(f"✅ 已存在 {lore_path}，跳过生成\n")
    else:
        print("📖 Step 1/5: 生成 Lore v1 (世界观基础)...")
        print("-" * 60)
        if args.index is None:
            raise SystemExit("缺少 lore.json 且未指定 --index，请先运行 get-lore 或提供 --index 参数")

        # 调用 get_lore 的逻辑
        candidates, _ = _ensure_candidates_file(city)
        picked_title, picked_blurb = _pick_candidate_from_list(candidates, index=args.index)
        researcher, analyst, _ = _make_agents()
        raw_material = _gather_raw_materials(city, picked_title, picked_blurb, researcher)

        lore_prompt = _load_prompt("lore.md")
        if lore_prompt is None:
            lore_prompt = (
                "[SYSTEM]\n你是一名'世界观圣经'构建专家。只返回一个 JSON 代码块。\n"
                "要求：world_truth, rules[], motifs[], locations[], timeline_hints[], allowed_roles[]；全部使用 ASCII 双引号。\n"
                "[USER]\n[城市]\n{city}\n[/城市]\n[原始素材]\n{raw_material}\n[/原始素材]"
            )
        task = Task(description=lore_prompt, expected_output="仅一个 JSON 代码块", agent=analyst)
        crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True)
        text = str(crew.kickoff(inputs={"city": city, "raw_material": raw_material}))

        data = _try_parse_json_obj(text)
        _save_json_or_fallback(data, lore_path, text)
        print(f"✅ Lore v1 已生成: {lore_path}\n")

    # Step 2: 生成主角设计
    protagonist_path = f"{san_city}_protagonist.md"
    if os.path.exists(protagonist_path):
        print(f"✅ 已存在 {protagonist_path}，跳过生成\n")
    else:
        print("👤 Step 2/5: 生成主角设计 (Protagonist)...")
        print("-" * 60)

        lore_obj = _read_json_file(lore_path)
        lore_content = json.dumps(lore_obj, ensure_ascii=False, indent=2)

        prompt_path = os.path.join("范文", "protagonist.prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
        else:
            prompt = (
                "[SYSTEM]\n你是一位首席叙事设计师。\n"
                "你的任务：基于《世界书 V1.0》，分析潜在主角，并推荐最佳主线角色。\n"
                "[USER]\n[世界书 V1.0]\n{world_book_markdown_content}\n[/世界书 V1.0]"
            )

        analyst = _make_agents()[1]
        task = Task(description=prompt, expected_output="主角分析报告 (Markdown 格式)", agent=analyst)
        crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True)
        result = str(crew.kickoff(inputs={"world_book_markdown_content": lore_content}))

        with open(protagonist_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ 主角设计已生成: {protagonist_path}\n")

    # Step 3: 生成 Lore v2
    lore_v2_path = f"{san_city}_lore_v2.md"
    if os.path.exists(lore_v2_path):
        print(f"✅ 已存在 {lore_v2_path}，跳过生成\n")
    else:
        print("🎮 Step 3/5: 生成 Lore v2 (系统增强版)...")
        print("-" * 60)

        lore_obj = _read_json_file(lore_path)
        lore_v1_content = json.dumps(lore_obj, ensure_ascii=False, indent=2)

        prompt_path = os.path.join("范文", "lore-v2.prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
        else:
            prompt = (
                "[SYSTEM]\n你是一位首席游戏系统设计师。\n"
                "你的任务：将《世界书 1.0》升级为《世界书 2.0 (系统增强版)》。\n"
                "[USER]\n[世界书 V1.0]\n{world_book_1_0_markdown_content}\n[/世界书 V1.0]"
            )

        analyst = _make_agents()[1]
        task = Task(description=prompt, expected_output="世界书 2.0 (Markdown 格式，含游戏系统)", agent=analyst)
        crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True)
        result = str(crew.kickoff(inputs={"world_book_1_0_markdown_content": lore_v1_content}))

        with open(lore_v2_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ Lore v2 已生成: {lore_v2_path}\n")

    # Step 4: 生成 GDD
    gdd_path = f"{san_city}_GDD.md"
    if os.path.exists(gdd_path):
        print(f"✅ 已存在 {gdd_path}，跳过生成\n")
    else:
        print("🎬 Step 4/5: 生成 GDD (AI导演任务简报)...")
        print("-" * 60)

        with open(lore_v2_path, "r", encoding="utf-8") as f:
            lore_v2_content = f.read()

        protagonist_content = ""
        if os.path.exists(protagonist_path):
            with open(protagonist_path, "r", encoding="utf-8") as f:
                protagonist_content = f.read()

        prompt_path = os.path.join("范文", "GDD.prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
        else:
            prompt = (
                "[SYSTEM]\n你是一位首席游戏系统设计师。\n"
                "你的任务：为主角撰写 AI 导演任务简报 (GDD)。\n"
                "[USER]\n请使用世界书和角色分析开始撰写 GDD。"
            )

        prompt = prompt.replace("{《荔湾广场世界书 2.0 (系统增强版)》的全部 Markdown 内容}", lore_v2_content)
        prompt = prompt.replace('{《角色分析报告》中关于"保安（主角线）"的全部 Markdown 内容}', protagonist_content)

        analyst = _make_agents()[1]
        task = Task(description=prompt, expected_output="AI 导演任务简报 (Markdown 格式)", agent=analyst)
        crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True)
        result = str(crew.kickoff())

        with open(gdd_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ GDD 已生成: {gdd_path}\n")

    # Step 5: 生成主线故事
    main_thread_path = f"{san_city}_main_thread.md"
    if os.path.exists(main_thread_path):
        print(f"✅ 已存在 {main_thread_path}，跳过生成\n")
    else:
        print("📝 Step 5/5: 生成主线完整故事...")
        print("-" * 60)

        with open(gdd_path, "r", encoding="utf-8") as f:
            gdd_content = f.read()

        with open(lore_v2_path, "r", encoding="utf-8") as f:
            lore_v2_content = f.read()

        prompt_path = os.path.join("范文", "main-thread.prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
        else:
            prompt = (
                "[SYSTEM]\n你是 B 站百万粉丝的恐怖故事 UP 主。\n"
                "基于 GDD 和世界书，生成完整的主线故事。\n"
                "[USER]\n[GDD]\n{gdd_content}\n[/GDD]\n[世界书]\n{lore_content}\n[/世界书]"
            )

        prompt = prompt.replace("{gdd_content}", gdd_content)
        prompt = prompt.replace("{lore_content}", lore_v2_content)

        storyteller = _make_agents()[2]
        task = Task(description=prompt, expected_output="完整主线故事 (Markdown 格式，≥5000字)", agent=storyteller)
        crew = Crew(agents=[storyteller], tasks=[task], process=Process.sequential, verbose=True)
        result = str(crew.kickoff())

        with open(main_thread_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ 主线故事已生成: {main_thread_path}\n")

    # 完成总结
    print("\n" + "="*60)
    print("🎉 完整流程执行成功！")
    print("="*60)
    print("\n生成的文件：")
    print(f"  1. {lore_path}")
    print(f"  2. {protagonist_path}")
    print(f"  3. {lore_v2_path}")
    print(f"  4. {gdd_path}")
    print(f"  5. {main_thread_path}")
    print(f"\n✨ 主线故事已保存至：{main_thread_path}\n")
