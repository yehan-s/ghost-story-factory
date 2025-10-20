import argparse
import os
import re
import json
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import GoogleSearchRun
from crewai.llm import LLM
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (如 OPENAI_API_KEY、Google 搜索相关密钥)
load_dotenv()


def _load_prompt(name: str) -> str | None:
    """从当前工作目录加载自定义 Prompt 文件，不存在则返回 None。"""
    path = os.path.join(os.getcwd(), name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

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
        )

    # OpenAI 或兼容代理
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        # LLM 支持 base_url=None，则走官方默认
        return LLM(model=model, api_key=openai_key, base_url=base)

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
    parser.add_argument("--out", type=str, required=False, help="自定义输出文件路径（可含目录）")
    args = parser.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    print(f"\n[AI 助手]: 正在启动 MCP 工作流，目标城市: {city} ...\n")

    # 2. 组建 Agents 与 Tasks
    researcher, analyst, writer = _make_agents()
    task_search, task_analyze, task_write = _make_tasks(researcher, analyst, writer)

    # 3. 若存在角色线或结构化框架文件，则直接按之生成故事；否则走 A->B->C 流程
    role = (getattr(args, "role", "") or "").strip()
    role_story_path_candidates = []
    if role:
        role_story_path_candidates.extend([
            f"{_sanitize_filename(city)}_role_{_sanitize_filename(role)}.json",
            f"{_sanitize_filename(city)}_role_story.json",
        ])
    else:
        role_story_path_candidates.append(f"{_sanitize_filename(city)}_role_story.json")

    picked_role_story = None
    for _p in role_story_path_candidates:
        if os.path.exists(_p):
            picked_role_story = _p
            break

    struct_path = f"{_sanitize_filename(city)}_struct.json"
    if picked_role_story:
        try:
            struct_obj = _read_json_file(picked_role_story)
            struct_json = json.dumps(struct_obj, ensure_ascii=False, indent=2)
        except Exception:
            with open(picked_role_story, "r", encoding="utf-8") as f:
                struct_json = f.read()

        # 尝试加载 get-story.md 作为写作 Prompt（若不存在则使用内置提示）
        writer_prompt = _load_prompt("get-story.md")
        if writer_prompt is None:
            writer_prompt = (
                "[SYSTEM]\\n你是恐怖故事 UP 主，按给定 JSON 框架扩写成 1500+ 字 Markdown。\\n"
                "[严格指令]\\n只返回 Markdown 文案。\\n[USER]\\n[故事框架]\\n{json_skeleton_from_agent_b}\\n[/故事框架]"
            )

        writer_only = Task(
            description=writer_prompt,
            expected_output='Markdown 格式完整故事',
            agent=writer,
        )
        story_crew = Crew(
            agents=[writer],
            tasks=[writer_only],
            process=Process.sequential,
            verbose=True,
        )
        inputs = {"json_skeleton_from_agent_b": struct_json}
        final_story_content = story_crew.kickoff(inputs=inputs)
    elif os.path.exists(struct_path):
        try:
            struct_obj = _read_json_file(struct_path)
            struct_json = json.dumps(struct_obj, ensure_ascii=False, indent=2)
        except Exception:
            with open(struct_path, "r", encoding="utf-8") as f:
                struct_json = f.read()

        # 尝试加载 get-story.md 作为写作 Prompt（若不存在则使用内置提示）
        writer_prompt = _load_prompt("get-story.md")
        if writer_prompt is None:
            writer_prompt = (
                "[SYSTEM]\n你是恐怖故事 UP 主，按给定 JSON 框架扩写成 1500+ 字 Markdown。\n"
                "[严格指令]\n只返回 Markdown 文案。\n[USER]\n[故事框架]\n{json_skeleton_from_agent_b}\n[/故事框架]"
            )

        writer_only = Task(
            description=writer_prompt,
            expected_output='Markdown 格式完整故事',
            agent=writer,
        )
        story_crew = Crew(
            agents=[writer],
            tasks=[writer_only],
            process=Process.sequential,
            verbose=True,
        )
        inputs = {"json_skeleton_from_agent_b": struct_json}
        final_story_content = story_crew.kickoff(inputs=inputs)
    elif True:
        story_crew = Crew(
            agents=[researcher, analyst, writer],
            tasks=[task_search, task_analyze, task_write],
            process=Process.sequential,  # A -> B -> C 顺序执行
            verbose=True,
        )
        inputs = {"city": city}
        final_story_content = story_crew.kickoff(inputs=inputs)

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

def _write_json_file(path: str, data: object) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_json_file(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    p = argparse.ArgumentParser(description="从候选中选定故事并生成结构化框架")
    p.add_argument("--city", type=str, required=True, help="目标城市")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--index", type=int, help="候选序号（从1开始）")
    g.add_argument("--title", type=str, help="候选标题（模糊匹配）")
    args = p.parse_args()

    city = (args.city or "").strip()
    if not city:
        raise SystemExit("--city 不能为空")

    cand_path = f"{_sanitize_filename(city)}_candidates.json"
    cand_txt_path = cand_path.replace(".json", ".txt")
    if not os.path.exists(cand_path) and not os.path.exists(cand_txt_path):
        print(f"[AI 助手]: 未找到候选文件 ./{cand_path}，将先自动生成候选……")
        _generate_candidates(city)

    candidates = None
    candidates_text = None
    if os.path.exists(cand_path):
        try:
            candidates = _read_json_file(cand_path)
        except Exception:
            candidates = None
    elif os.path.exists(cand_txt_path):
        with open(cand_txt_path, "r", encoding="utf-8") as f:
            candidates_text = f.read()

    picked_title = None
    picked_blurb = None
    picked_index = args.index or 1

    if isinstance(candidates, list):
        if args.title:
            key = args.title.strip().lower()
            for item in candidates:
                title = (item.get("title") if isinstance(item, dict) else None) or ""
                if key in title.lower():
                    picked_title = title
                    picked_blurb = item.get("blurb") if isinstance(item, dict) else ""
                    break
        else:
            idx = picked_index - 1
            if 0 <= idx < len(candidates):
                item = candidates[idx]
                picked_title = (item.get("title") if isinstance(item, dict) else str(item)) or ""
                picked_blurb = item.get("blurb") if isinstance(item, dict) else ""

    # 先用研究员对“选中的候选”进行素材汇编，得到原始长文本
    researcher, analyst, _ = _make_agents()
    research_desc = (
        "围绕城市 {city} 的选中候选故事，汇编原始素材为长文本。\n"
        "若给定标题与简介，则以其为主题展开收集与整合。\n"
        "请合并来源梳理、传说变体、时间线、目击叙述与反驳观点，输出为 Markdown 长文。\n"
        "选中候选：\n标题：{picked_title}\n简介：{picked_blurb}\n(如标题为空，则请根据城市最具代表性的一个传说自动选择)\n"
    )
    research_task = Task(
        description=research_desc,
        expected_output="关于选中候选的长篇原始素材（Markdown 长文）",
        agent=researcher,
    )
    research_crew = Crew(agents=[researcher], tasks=[research_task], process=Process.sequential, verbose=True)
    research_inputs = {"city": city, "picked_title": picked_title or "", "picked_blurb": picked_blurb or ""}
    raw_material = str(research_crew.kickoff(inputs=research_inputs))

    # 读取 get-struct.md 提示词，驱动分析师输出严格 JSON 代码块
    def _load_prompt(name: str) -> str | None:
        p = os.path.join(os.getcwd(), name)
        try:
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

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
    analyze_inputs = {"raw_text_from_agent_a": raw_material, "city": city}
    analyze_crew = Crew(agents=[analyst], tasks=[analyze_task], process=Process.sequential, verbose=True)
    text = str(analyze_crew.kickoff(inputs=analyze_inputs))

    # 提取 JSON 对象
    data = None
    def _try_parse_obj(s: str):
        try:
            v = json.loads(s)
            return v if isinstance(v, dict) else None
        except Exception:
            return None

    data = _try_parse_obj(text)
    if data is None:
        import re as _re
        m = _re.search(r"\{[\s\S]*\}", text)
        if m:
            blob = m.group(0)
            # 将中文引号替换为转义 ASCII 引号，避免破坏字符串
            blob = blob.replace("\ufeff", "")
            blob = blob.replace('“', '\\"').replace('”', '\\"')
            blob = blob.replace('’', "'").replace('‘', "'")
            data = _try_parse_obj(blob)

    def _normalize_struct(d: dict, city_name: str) -> dict:
        # 规范化键名与必填字段
        out = {}
        out["title"] = str(d.get("title") or "").strip() or "未命名故事"
        out["city"] = str(d.get("city") or city_name)
        loc = d.get("location_name") or d.get("location") or ""
        out["location_name"] = str(loc)
        out["core_legend"] = str(d.get("core_legend") or d.get("legend") or "").strip()
        # key_elements
        ke = d.get("key_elements")
        if not isinstance(ke, list):
            ke = []
        out["key_elements"] = [str(x) for x in ke if isinstance(x, (str,int,float))]
        # potential_roles
        roles = d.get("potential_roles")
        if not isinstance(roles, list):
            # 简单兜底，避免空字段
            roles = ["目击者", "讲述者", "地方居民"]
        out["potential_roles"] = [str(x) for x in roles if isinstance(x, (str,int,float))]
        return out

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

    # 确保候选存在
    cand_path = f"{_sanitize_filename(city)}_candidates.json"
    if not os.path.exists(cand_path):
        _generate_candidates(city)
    candidates = None
    try:
        if os.path.exists(cand_path):
            candidates = _read_json_file(cand_path)
    except Exception:
        candidates = None

    picked_title = None
    picked_blurb = None
    if isinstance(candidates, list):
        if args.title:
            key = args.title.strip().lower()
            for item in candidates:
                t = (item.get("title") if isinstance(item, dict) else None) or ""
                if key in t.lower():
                    picked_title = t
                    picked_blurb = item.get("blurb") if isinstance(item, dict) else ""
                    break
        else:
            idx = ((args.index or 1) - 1)
            if 0 <= idx < len(candidates):
                it = candidates[idx]
                picked_title = (it.get("title") if isinstance(it, dict) else str(it)) or ""
                picked_blurb = it.get("blurb") if isinstance(it, dict) else ""

    # 汇编原始素材
    researcher, analyst, _ = _make_agents()
    research_desc = (
        "围绕城市 {city} 的选中候选故事，汇编原始素材为长文本。\n"
        "合并来源、变体、时间线、目击叙述与反驳观点，输出为 Markdown 长文。\n"
        "选中候选：\n标题：{picked_title}\n简介：{picked_blurb}\n城市：{city}。"
    )
    research_task = Task(description=research_desc, expected_output="Markdown 长文", agent=researcher)
    raw_material = str(Crew(agents=[researcher], tasks=[research_task], process=Process.sequential, verbose=True).kickoff(inputs={
        "city": city, "picked_title": picked_title or "", "picked_blurb": picked_blurb or ""
    }))

    lore_prompt = _load_prompt("lore.md")
    if lore_prompt is None:
        lore_prompt = (
            "[SYSTEM]\n你是一名‘世界观圣经’构建专家。只返回一个 JSON 代码块。\n"
            "要求：world_truth, rules[], motifs[], locations[], timeline_hints[], allowed_roles[]；全部使用 ASCII 双引号。\n"
            "[USER]\n[城市]\n{city}\n[/城市]\n[原始素材]\n{raw_material}\n[/原始素材]"
        )
    task = Task(description=lore_prompt, expected_output="仅一个 JSON 代码块", agent=analyst)
    text = str(Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True).kickoff(inputs={
        "city": city, "raw_material": raw_material
    }))

    def _try_parse_obj(s: str):
        try:
            v = json.loads(s)
            return v if isinstance(v, dict) else None
        except Exception:
            return None
    data = _try_parse_obj(text)
    if data is None:
        import re as _re
        m = _re.search(r"\{[\s\S]*\}", text)
        if m:
            blob = m.group(0).replace("\ufeff", "").replace('“', '"').replace('”', '"')
            data = _try_parse_obj(blob)

    out_path = (args.out or f"{_sanitize_filename(city)}_lore.json").strip()
    if data is not None:
        _write_json_file(out_path, data)
        print(f"\n[AI 助手]: 世界观圣经已保存: ./{out_path}\n")
    else:
        with open(out_path.replace(".json", ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
        raise SystemExit("未能解析为 JSON，请检查输出（已保存为 .txt）。")


def gen_role():
    """基于 lore.json 生成角色剧情拍点 role_story.json。"""
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

    lore_path = (args.lore or f"{_sanitize_filename(city)}_lore.json").strip()
    if not os.path.exists(lore_path):
        raise SystemExit(f"未找到 lore 文件: {lore_path}。请先运行 get-lore。")

    try:
        lore_obj = _read_json_file(lore_path)
        lore_json = json.dumps(lore_obj, ensure_ascii=False, indent=2)
    except Exception:
        with open(lore_path, "r", encoding="utf-8") as f:
            lore_json = f.read()

    prompt = _load_prompt("role-beats.md")
    if prompt is None:
        prompt = (
            "[SYSTEM] 你是剧情设计师。只返回一个 JSON 代码块。\n"
            "字段：role, pov, goal, constraints_used{rules[],motifs[],locations[]}, beats{opening_hook,first_contact,investigation,mid_twist,confrontation,aftershock,cta}。\n"
            "[USER]\n[世界观]\n{lore_json}\n[/世界观]\n[角色]\n{role}\n[/角色]\n[视角]\n{pov}\n[/视角]"
        )
    analyst = _make_agents()[1]
    task = Task(description=prompt, expected_output="仅一个 JSON 代码块", agent=analyst)
    text = str(Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True).kickoff(inputs={
        "lore_json": lore_json, "role": role, "pov": (args.pov or "第二人称")
    }))

    def _try_parse_obj2(s: str):
        try:
            v = json.loads(s)
            return v if isinstance(v, dict) else None
        except Exception:
            return None
    data = _try_parse_obj2(text)
    if data is None:
        import re as _re
        m = _re.search(r"\{[\s\S]*\}", text)
        if m:
            blob = m.group(0).replace("\ufeff", "").replace('“', '"').replace('”', '"')
            data = _try_parse_obj2(blob)

    out_default = f"{_sanitize_filename(city)}_role_{_sanitize_filename(role)}.json"
    out_path = (args.out or out_default).strip()
    if data is not None:
        _write_json_file(out_path, data)
        print(f"\n[AI 助手]: 角色剧情拍点已保存: ./{out_path}\n")
    else:
        with open(out_path.replace(".json", ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
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
