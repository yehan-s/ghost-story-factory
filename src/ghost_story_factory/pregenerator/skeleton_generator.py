"""
故事骨架生成器（SkeletonGenerator）

职责：
- 基于城市、故事简介、Lore v2 与主线故事，从 LLM 生成 PlotSkeleton JSON；
- 解析为内部的 PlotSkeleton 对象，供后续 TreeBuilder guided 模式使用。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

from crewai import Agent, Task, Crew
from crewai.llm import LLM

from .skeleton_model import PlotSkeleton

# templates 目录：项目根目录下的 templates/
TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"


def _build_default_llm() -> LLM:
    """构建默认 LLM（优先 Kimi，回退 OpenAI）"""
    kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
    if kimi_key:
        base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
        model = os.getenv("KIMI_MODEL", "kimi-k2-0905-preview")
        return LLM(
            model=model,
            api_key=kimi_key,
            base_url=base,
            max_tokens=16000,
        )

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        base = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return LLM(
            model=model,
            api_key=openai_key,
            base_url=base,
            max_tokens=16000,
        )

    raise RuntimeError("未检测到 KIMI_API_KEY / MOONSHOT_API_KEY 或 OPENAI_API_KEY")


def _load_prompt() -> str:
    """加载 plot-skeleton.prompt.md 提示词"""
    prompt_file = TEMPLATE_DIR / "plot-skeleton.prompt.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"未找到骨架提示词文件: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


def _shorten(text: str, max_chars: int = 4000) -> str:
    """对长文本做截断，避免上下文爆炸"""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars] + "\n\n...[内容已截断]..."


def _try_parse_json(text: str) -> Dict[str, Any]:
    """尽力从 LLM 返回文本中提取一个 JSON 对象"""
    # 1) 直接解析
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 2) ```json``` 代码块
    m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        blob = m.group(1)
        try:
            obj = json.loads(blob)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # 3) 第一个大括号块（粗暴但实用）
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        blob = m.group(0)
        try:
            obj = json.loads(blob)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    raise ValueError("无法从骨架生成结果中解析出合法 JSON")


def _validate_skeleton(skeleton: PlotSkeleton) -> None:
    """
    对生成的 PlotSkeleton 做基础结构校验。

    目的：
    - 确保骨架与自身 config 至少在几个关键指标上自洽；
    - 避免明显“过浅 / 无结局 / 只有一幕”的骨架直接进入 v4 主路径。

    说明：
    - 真正“打回”的情况只保留在不可用骨架（例如完全无结局）的极端场景；
    - 大多数自相矛盾的配置（如 min_main_depth 远大于实际 beats）在这里被自动收敛，
      以骨架自身结构为准，不再轻易回退到 v3。
    """
    errors = []

    # 1) 幕数至少 3 幕（与 prompt 约定一致）
    if skeleton.num_acts < 3:
        errors.append(f"幕数过少: num_acts={skeleton.num_acts} < 3")

    cfg = skeleton.config

    # 2) 节拍总数不应明显低于配置的主线最小深度
    try:
        min_depth = int(cfg.min_main_depth)
    except Exception:
        min_depth = 0
    if min_depth > 0 and skeleton.num_beats < min_depth:
        # 与其直接判错，不如让配置向骨架实际节拍数收敛，
        # 避免“纸面 18 层、实际 12 层”的虚高要求。
        new_min_depth = max(4, skeleton.num_beats)
        cfg.min_main_depth = new_min_depth
        # target_main_depth 至少不小于 min_main_depth
        try:
            if cfg.target_main_depth < cfg.min_main_depth:
                cfg.target_main_depth = cfg.min_main_depth
        except Exception:
            pass

    # 3) 允许落到结局的节拍数量应不少于 target_endings
    try:
        target_endings = int(cfg.target_endings)
    except Exception:
        target_endings = 0
    if target_endings > 0 and skeleton.num_ending_beats < target_endings:
        if skeleton.num_ending_beats <= 0:
            # 完全没有结局节拍，这种骨架对引擎来说不可用
            errors.append(
                f"结局节拍数量为 0，target_endings={target_endings}"
            )
        else:
            # 否则让 target_endings 向实际结局节拍收敛，
            # 保证“至少每个结局节拍能支撑一个结局”。
            cfg.target_endings = skeleton.num_ending_beats

    # 4) 结局节拍的分布建议（暂不作为硬错误）：
    #    - Act I 不宜大量结局落点；
    #    - 最后一幕最好包含至少一个结局节拍。
    # 这些更适合作为 story_report / 诊断工具中的 warning，这里先不做 gating。

    if errors:
        # 统一抛出异常，由上层打印并回退 v3
        raise ValueError("PlotSkeleton 不满足基础结构约束: " + "; ".join(errors))


class SkeletonGenerator:
    """故事骨架生成器"""

    def __init__(self, city: str, llm: Optional[LLM] = None) -> None:
        """
        初始化骨架生成器

        Args:
            city: 城市名称
            llm: 可选，自定义 LLM 实例；不传则使用默认构建
        """
        self.city = city
        self.llm = llm or _build_default_llm()

    def generate(
        self,
        title: str,
        synopsis: str,
        lore_v2_text: str,
        main_story_text: str,
    ) -> PlotSkeleton:
        """
        生成 PlotSkeleton。

        Args:
            title: 故事标题
            synopsis: 故事简介 / 剧情概要
            lore_v2_text: 世界书 v2 文本
            main_story_text: 主线故事文本

        Returns:
            PlotSkeleton 对象
        """
        raw_prompt = _load_prompt()

        prompt = (
            raw_prompt.replace("{{CITY}}", self.city)
            .replace("{{TITLE}}", title.strip() or "未命名故事")
            .replace("{{SYNOPSIS}}", synopsis.strip())
            .replace("{{LORE_V2}}", _shorten(lore_v2_text))
            .replace("{{MAIN_STORY}}", _shorten(main_story_text))
        )

        agent = Agent(
            role="故事结构设计师",
            goal=f"为城市「{self.city}」的恐怖故事设计一个结构清晰、节奏合理的剧情骨架",
            backstory="你是一名资深叙事设计师，专长于分幕结构、节拍设计和多结局分支控制。",
            tools=[],
            llm=self.llm,
            verbose=False,
            allow_delegation=False,
        )

        task = Task(
            description=prompt,
            expected_output="一个符合说明的 PlotSkeleton JSON 对象",
            agent=agent,
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = str(crew.kickoff())

        data = _try_parse_json(result)
        skeleton = PlotSkeleton.from_dict(data)
        _validate_skeleton(skeleton)
        return skeleton
