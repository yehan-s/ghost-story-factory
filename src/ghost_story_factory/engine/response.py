"""运行时响应生成器

根据玩家选择生成动态叙事响应：
- 场景描述（第二人称，氛围营造）
- 后果反馈（PR/GR/WF 变化的叙事化表达）
- 下一步引导（暗示可用选择点）

v4 约束：
- 核心 LLM I/O 默认走 LLMClient（可观测、可控超时），CrewAI 仅作为回退路径。
- 失败时必须兜底返回文本，不能让整轮生成崩溃。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

import os

from .state import GameState

# Choice 兼容导入
try:
    from .choices import Choice
except Exception:
    class Choice:  # type: ignore
        def __init__(
            self,
            choice_id: str,
            choice_text: str,
            choice_type: str = "normal",
            consequences=None,
            preconditions=None,
            tags=None,
        ):
            self.choice_id = choice_id
            self.choice_text = choice_text
            self.choice_type = type("ChoiceType", (), {"value": choice_type})() if not hasattr(choice_type, "value") else choice_type
            self.consequences = consequences or {}
            self.preconditions = preconditions or {}
            self.tags = tags or []


# LLMClient（新路径）
try:
    from ..utils.llm_client import LLMClient, create_llm_client, LLMClientError
    _USE_LLM_CLIENT = True
except Exception:
    _USE_LLM_CLIENT = False


# CrewAI（回退路径）
try:
    from crewai import Agent, Task, Crew, LLM as CrewLLM
    _CREWAI_AVAILABLE = True
except Exception:
    _CREWAI_AVAILABLE = False


class RuntimeResponseGenerator:
    """运行时响应生成器

    目标：生成一段连贯、沉浸、可控长度的叙事文本。

    约束：
    - 默认使用 LLMClient（避免 CrewAI 黑盒错误，提升日志可观测性）。
    - LLM 不可用时回退（CrewAI -> 本地兜底），确保主流程不崩。
    """

    def __init__(self, gdd_content: str, lore_content: str, main_story: str = ""):
        self.gdd = gdd_content
        self.lore = lore_content
        self.main_story = main_story

        self.prompt_template = self._load_prompt_template()

        # 缓存与并发控制
        self._crew_llm = None
        self._llm_client: Optional[LLMClient] = None
        self._kimi_model_response = None
        self._scene_memory: Dict[str, str] = {}

        import threading

        self._concurrency = int(os.getenv("KIMI_CONCURRENCY", "4"))
        self._sem = threading.Semaphore(self._concurrency)

        # 默认：响应生成走 LLMClient。需要时可回退 CrewAI。
        self.use_llmclient_response = os.getenv("USE_LLMCLIENT_RESPONSE", "1") == "1"

        # 收紧输出 token，避免 180s×2 的“卡死式失败”
        try:
            self.response_max_tokens = int(os.getenv("RESPONSE_MAX_TOKENS", "900"))
        except Exception:
            self.response_max_tokens = 900

        # 温度参数（保持可控）
        try:
            self.response_temperature = float(os.getenv("RESPONSE_TEMPERATURE", "0.7"))
        except Exception:
            self.response_temperature = 0.7

        # 是否拼接主线故事摘录（质量 vs 性能）
        self.use_main_story_excerpt = os.getenv("RESPONSE_USE_MAIN_STORY", "1") == "1"
        try:
            self.main_story_excerpt_chars = int(os.getenv("RESPONSE_STORY_EXCERPT_CHARS", "2000"))
        except Exception:
            self.main_story_excerpt_chars = 2000

    def _load_prompt_template(self) -> str:
        root_prompt = Path("runtime-response.prompt.md")
        if root_prompt.exists():
            return root_prompt.read_text(encoding="utf-8")

        template_prompt = Path("templates/runtime-response.prompt.md")
        if template_prompt.exists():
            return template_prompt.read_text(encoding="utf-8")

        return self._get_builtin_template()

    def _get_builtin_template(self) -> str:
        return """
你是一个专业的"选项式灵异游戏 AI 导演"，负责为玩家的每一次选择生成恰当的、沉浸式的实时响应。

## 输出要求
- Markdown 格式，200-400字
- 第二人称视角（使用"你"）
- 至少 2 种感官描写（视觉/听觉/嗅觉/触觉）
- 不替玩家做决定
- 不破坏世界观规则
"""

    def _get_llm_client(self) -> Optional[LLMClient]:
        """获取（并复用）LLMClient。

        注意：LLMClient 初始化可能因缺少 API Key 失败；此处必须吞掉错误并回退。
        """
        if not self.use_llmclient_response or not _USE_LLM_CLIENT:
            return None
        if self._llm_client is not None:
            return self._llm_client

        try:
            self._llm_client = create_llm_client()
            self._kimi_model_response = getattr(self._llm_client, "default_model", None)
            return self._llm_client
        except Exception:
            self._llm_client = None
            return None

    def _get_crew_llm(self):
        """获取（并复用）CrewAI LLM（仅回退路径使用）。"""
        if self._crew_llm is not None:
            return self._crew_llm

        if not _CREWAI_AVAILABLE:
            return None

        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
        self._kimi_model_response = os.getenv("KIMI_MODEL_RESPONSE") or os.getenv("KIMI_MODEL", "kimi-k2-0905-preview")

        self._crew_llm = CrewLLM(
            model=self._kimi_model_response,
            api_key=kimi_key,
            base_url=kimi_base,
        )
        return self._crew_llm

    def _build_backstory_excerpt(self) -> str:
        """构建主线故事摘录（用于提升连贯性，但要控制长度）。"""
        if not self.main_story or not self.use_main_story_excerpt:
            return ""
        excerpt = self.main_story[: self.main_story_excerpt_chars]
        return (
            "\n\n[故事背景摘录]\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{excerpt}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    def _call_llmclient(self, prompt: str) -> str:
        client = self._get_llm_client()
        if client is None:
            raise RuntimeError("LLMClient 不可用")

        with self._sem:
            return client.call(
                prompt=prompt,
                model=None,
                max_tokens=self.response_max_tokens,
                temperature=self.response_temperature,
            )

    def generate_response(
        self,
        choice: Choice,
        game_state: GameState,
        apply_consequences: bool = True,
        director_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """生成玩家选择后的叙事响应。

        返回值必须始终是字符串，任何失败都要兜底。
        """
        # 保存原始状态（用于系统提示）
        state_before = game_state.to_dict()
        # 本地兜底响应（最坏情况）
        def _offline_fallback() -> str:
            scene_context = self._get_scene_memory(game_state.current_scene)
            pr_hint = "你的神经更紧绷了一些。" if game_state.PR >= 50 else "你努力让呼吸平稳下来。"
            text = (
                f"你选择了：{choice.choice_text}\n\n"
                f"昏黄的灯光在潮湿的墙面上跳动，空气里混着土腥味与细微的霉意。\n"
                f"远处传来水滴声，[音效: 滴——答] 一下比一下清晰。{pr_hint}\n\n"
                f"场景要点：\n{scene_context}\n"
            )
            return text

        # 构建 prompt（加入导演上下文以增强连续性）
        prompt = self._build_prompt(choice, game_state, state_before, director_context=director_context)
        prompt += (
            "\n\n[世界书与收束]\n"
            "- 不得破坏既定世界观；回收前文伏笔；逐步逼近结局节点\n"
            "- 如果当前已接近真相/危险阈值，暗示关键抉择临近（不替玩家决定）\n"
        )

        # LLMClient 默认路径
        full_prompt = self.prompt_template + self._build_backstory_excerpt() + "\n\n" + prompt
        raw_text: str = ""
        if self.use_llmclient_response and _USE_LLM_CLIENT:
            try:
                raw_text = self._call_llmclient(full_prompt)
            except (LLMClientError, Exception):
                raw_text = ""

        # CrewAI 回退路径
        if not raw_text.strip() and _CREWAI_AVAILABLE:
            try:
                llm = self._get_crew_llm()
                if llm is not None:
                    agent = Agent(
                        role="B站百万粉丝的恐怖故事 UP 主",
                        goal="生成沉浸式的叙事响应，营造恐怖氛围",
                        backstory="你精通恐怖氛围营造和细节描写。",
                        verbose=False,
                        allow_delegation=False,
                        llm=llm,
                    )
                    task = Task(
                        description=full_prompt,
                        expected_output="第二人称叙事文本（Markdown 格式，200-400字）",
                        agent=agent,
                    )
                    crew = Crew(agents=[agent], tasks=[task], verbose=False)
                    with self._sem:
                        result = crew.kickoff()
                    raw_text = str(result)
            except Exception:
                raw_text = ""

        # 最终兜底
        if not raw_text.strip():
            raw_text = _offline_fallback()

        # 应用后果到游戏状态（由调用方控制）
        if apply_consequences and getattr(choice, "consequences", None):
            try:
                game_state.update(choice.consequences)
                game_state.consequence_tree.append(choice.choice_id)
            except Exception:
                pass

        return self._add_system_hints(raw_text, state_before, game_state.to_dict())

    def _get_scene_memory(self, scene: str) -> str:
        """获取场景锚点与规则（缓存）"""
        if scene in self._scene_memory:
            return self._scene_memory[scene]

        scene_ctx = self._extract_scene_context(self.gdd, scene, max_chars=400)
        core_lore = self._extract_scene_context(self.lore, scene, max_chars=200)
        memory = f"{scene_ctx}\n\n[规则与约束]\n{core_lore}"
        memory = memory[:900]
        self._scene_memory[scene] = memory
        return memory

    def _build_prompt(
        self,
        choice: Choice,
        game_state: GameState,
        state_before: Dict[str, Any],
        director_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建完整 prompt（沿用现有结构，便于保持行为稳定）。"""
        pr_change = game_state.PR - state_before.get("PR", 0)
        scene_context = self._get_scene_memory(game_state.current_scene)

        ctx_lines = []
        if director_context:
            recent_choices = director_context.get("recent_choices") or []
            recent_responses = director_context.get("recent_responses") or []
            recent_beats = director_context.get("recent_beats") or []
            if recent_choices:
                ctx_lines.append("最近几个关键选择：")
                for t in recent_choices[-3:]:
                    ctx_lines.append(f"- {t}")
            if recent_beats:
                ctx_lines.append("\n最近几个节拍：")
                for b in recent_beats[-3:]:
                    bt = b.get("beat_type")
                    tl = b.get("tension_level")
                    ctx_lines.append(f"- depth={b.get('depth')}, type={bt}, tension={tl}")
            if recent_responses:
                ctx_lines.append("\n最近一段响应摘要（供你保持语气与节奏一致，不要照抄原文）：")
                last_resp = str(recent_responses[-1])[:180]
                ctx_lines.append(last_resp + ("..." if len(last_resp) == 180 else ""))
        ctx_block = "\n".join(ctx_lines) if ctx_lines else "（暂无历史上下文，可按常规节奏书写。）"

        # choice_type 兼容（pydantic enum 或 str）
        try:
            choice_type_val = choice.choice_type.value  # type: ignore[attr-defined]
        except Exception:
            choice_type_val = str(getattr(choice, "choice_type", "normal"))

        tags = getattr(choice, "tags", None) or []
        tag_text = ", ".join(tags[:2]) if tags else "无"

        return f"""
你是一个专业的恐怖故事作家。根据玩家选择生成沉浸式叙事响应（200-400字）。

## 玩家选择
**选择**: {choice.choice_text}
**类型**: {choice_type_val} | **标签**: {tag_text}

## 当前状态
**场景**: {game_state.current_scene} | **时间**: {game_state.timestamp}
**PR**: {state_before.get('PR', 0)} → {game_state.PR} ({'+' if pr_change >= 0 else ''}{pr_change})
**道具**: {', '.join(game_state.inventory[:2]) if game_state.inventory else '无'}

## 场景信息
{scene_context}

## 最近几步的叙事上下文（请用于保持连贯性，避免简单重复）
{ctx_block}

---

## 写作要求
1. **第二人称视角**（使用"你"），营造恐怖氛围
2. **包含细节**：至少 2 种感官描写（视觉/听觉/嗅觉）
3. **体现后果**：反映选择的影响和状态变化
4. **暗示下一步**：环境提示，但不替玩家决定

请生成叙事响应（Markdown 格式，200-400字），只输出 Markdown 文本：
"""

    def _extract_scene_context(self, gdd: str, scene: str, max_chars: int = 400) -> str:
        lines = gdd.split("\n")
        relevant_lines = []

        for i, line in enumerate(lines):
            if scene.lower() in line.lower() or f"场景{scene[1:]}" in line:
                relevant_lines.append(line)
                for j in range(i + 1, min(i + 15, len(lines))):
                    if lines[j].strip().startswith("#") and lines[j].strip() != line.strip():
                        break
                    relevant_lines.append(lines[j])
                break

        result = "\n".join(relevant_lines)[:max_chars]
        return result if result else f"场景 {scene}"

    def _add_system_hints(self, response_text: str, state_before: Dict[str, Any], state_after: Dict[str, Any]) -> str:
        hints = []

        if state_before.get("PR") != state_after.get("PR"):
            pr_change = state_after.get("PR", 0) - state_before.get("PR", 0)
            sign = "+" if pr_change > 0 else ""
            hints.append(f"PR {sign}{pr_change} → 当前 {state_after.get('PR')}")

        if state_before.get("GR") != state_after.get("GR"):
            gr_change = state_after.get("GR", 0) - state_before.get("GR", 0)
            sign = "+" if gr_change > 0 else ""
            hints.append(f"GR {sign}{gr_change} → 当前 {state_after.get('GR')}")

        if state_before.get("WF") != state_after.get("WF"):
            wf_change = state_after.get("WF", 0) - state_before.get("WF", 0)
            sign = "+" if wf_change > 0 else ""
            hints.append(f"WF {sign}{wf_change} → 当前 {state_after.get('WF')}")

        # 道具变化
        before_inv = set(state_before.get("inventory", []) or [])
        after_inv = set(state_after.get("inventory", []) or [])
        new_items = list(after_inv - before_inv)
        if new_items:
            hints.append(f"获得道具：{'、'.join(new_items)}")

        if state_before.get("current_scene") != state_after.get("current_scene"):
            hints.append(f"进入场景：{state_after.get('current_scene')}")

        if not hints:
            return response_text

        system_hint = "\n\n**【系统提示】**\n" + "\n".join(f"- {h}" for h in hints) + "\n"
        return response_text + system_hint

    def generate_ambient_response(self, game_state: GameState, idle_duration: int = 30) -> str:
        """生成环境循环描述（尽量复用 LLMClient，失败时兜底）。"""
        prompt = (
            f"玩家已经在当前场景停留了 {idle_duration} 秒，没有采取任何行动。\n\n"
            f"当前游戏状态：\n- 场景：{game_state.current_scene}\n- 时间：{game_state.timestamp}\n- PR：{game_state.PR}/100\n\n"
            "请生成一段 50-100 字的环境循环描述，包含时间压力与环境压迫感。\n"
            "只输出文本。"
        )

        full_prompt = self.prompt_template + "\n\n" + prompt

        if self.use_llmclient_response and _USE_LLM_CLIENT:
            try:
                return self._call_llmclient(full_prompt)
            except Exception:
                pass

        if _CREWAI_AVAILABLE:
            try:
                llm = self._get_crew_llm()
                if llm is None:
                    raise RuntimeError("CrewAI LLM 不可用")
                agent = Agent(
                    role="环境描述专家",
                    goal="生成营造紧张感的环境描述",
                    backstory="你擅长通过细节描写营造时间压力和环境压迫感",
                    verbose=False,
                    allow_delegation=False,
                    llm=llm,
                )
                task = Task(
                    description=prompt,
                    expected_output="简短的环境描述（50-100字）",
                    agent=agent,
                )
                crew = Crew(agents=[agent], tasks=[task], verbose=False)
                with self._sem:
                    return str(crew.kickoff())
            except Exception:
                pass

        return "周围很安静……"

    def generate_scene_transition(self, from_scene: str, to_scene: str, game_state: GameState) -> str:
        """生成场景转换文本（尽量复用 LLMClient，失败时兜底）。"""
        prompt = (
            f"玩家正在从 {from_scene} 进入 {to_scene}。\n\n"
            f"当前游戏状态：\n- 时间：{game_state.timestamp}\n- PR：{game_state.PR}/100\n\n"
            "请生成一段 100-200 字的场景转换描述，包含感官细节与氛围延续。\n"
            "只输出 Markdown 文本。"
        )

        full_prompt = self.prompt_template + "\n\n" + prompt

        text = ""
        if self.use_llmclient_response and _USE_LLM_CLIENT:
            try:
                text = self._call_llmclient(full_prompt)
            except Exception:
                text = ""

        if not text.strip() and _CREWAI_AVAILABLE:
            try:
                llm = self._get_crew_llm()
                if llm is None:
                    raise RuntimeError("CrewAI LLM 不可用")
                agent = Agent(
                    role="场景转换专家",
                    goal="生成流畅的场景转换描述",
                    backstory="你擅长营造场景间的连贯性和氛围延续性",
                    verbose=False,
                    allow_delegation=False,
                    llm=llm,
                )
                task = Task(
                    description=prompt,
                    expected_output="场景转换描述（100-200字）",
                    agent=agent,
                )
                crew = Crew(agents=[agent], tasks=[task], verbose=False)
                with self._sem:
                    text = str(crew.kickoff())
            except Exception:
                text = ""

        if not text.strip():
            text = f"你从 {from_scene} 来到了 {to_scene}……"

        game_state.current_scene = to_scene
        return text


def format_response_with_state(response_text: str, game_state: GameState) -> str:
    """格式化响应文本，添加状态显示"""
    formatted = f"""
{response_text}

---

**当前状态**:
- 📊 PR: {game_state.PR}/100
- 🌍 GR: {game_state.GR}/100
- ⏱️  WF: {game_state.WF}/10
- 🕐 时间: {game_state.timestamp}
- 📍 场景: {game_state.current_scene}
"""

    if game_state.inventory:
        formatted += f"\n- 🎒 道具: {', '.join(game_state.inventory)}"

    return formatted
