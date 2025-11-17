"""运行时响应生成器

根据玩家选择生成动态叙事响应：
- 场景描述（第一人称，氛围营造）
- 实体交互（根据 PR 触发不同 Tier）
- 后果反馈（PR/GR/WF 变化的叙事化表达）
- 下一步引导（暗示可用选择点）
"""

from pathlib import Path
from typing import Optional, Dict, Any
import json

from .state import GameState
try:
    from .choices import Choice
except Exception:
    # 兼容：当 pydantic 不可用时，退化为简单对象
    class Choice:  # type: ignore
        def __init__(self, choice_id: str, choice_text: str, choice_type: str = "normal", consequences=None, preconditions=None, tags=None):
            self.choice_id = choice_id
            self.choice_text = choice_text
            self.choice_type = type("ChoiceType", (), {"value": choice_type})() if not hasattr(choice_type, "value") else choice_type
            self.consequences = consequences or {}
            self.preconditions = preconditions or {}
            self.tags = tags or []


class RuntimeResponseGenerator:
    """运行时响应生成器

    基于玩家的选择，调用 LLM 生成沉浸式的叙事响应，
    并自动更新游戏状态
    """

    def __init__(self, gdd_content: str, lore_content: str, main_story: str = ""):
        """初始化生成器

        Args:
            gdd_content: GDD（AI 导演任务简报）内容
            lore_content: Lore v2（世界观）内容
            main_story: 主线故事内容（可选，用于高质量叙事）
        """
        self.gdd = gdd_content
        self.lore = lore_content
        self.main_story = main_story
        self.prompt_template = self._load_prompt_template()
        # 缓存与并发控制
        self._llm = None
        self._kimi_model_response = None
        self._scene_memory = {}
        self._global_story_summary = None
        import os, threading
        self._concurrency = int(os.getenv("KIMI_CONCURRENCY", "4"))
        self._sem = threading.Semaphore(self._concurrency)

    def _load_prompt_template(self) -> str:
        """加载 prompt 模板

        优先从项目根目录加载，如果不存在则从 templates 目录加载

        Returns:
            str: Prompt 模板内容
        """
        # 尝试从项目根目录加载
        root_prompt = Path("runtime-response.prompt.md")
        if root_prompt.exists():
            with open(root_prompt, 'r', encoding='utf-8') as f:
                return f.read()

        # 回退到 templates 目录
        template_prompt = Path("templates/runtime-response.prompt.md")
        if template_prompt.exists():
            with open(template_prompt, 'r', encoding='utf-8') as f:
                return f.read()

        # 如果都不存在，返回内置的简化模板
        return self._get_builtin_template()

    def _build_backstory_with_story(self) -> str:
        """构建包含完整故事的 backstory（混合方案）

        Returns:
            包含故事背景的 backstory 文本
        """
        # 截取主线故事的前 5000 字符（约 6000 tokens）
        story_excerpt = self.main_story[:5000] if len(self.main_story) > 5000 else self.main_story

        return f"""你是一个专业的恐怖故事作家，已经阅读了完整的故事背景：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【故事背景】
{story_excerpt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你的任务：
基于上述故事背景，为玩家的选择生成沉浸式的叙事响应。

你的风格：
- 第二人称视角（使用"你"）
- 强节奏停顿，多感官细节
- 符合故事设定和世界观规则
- 营造恐怖氛围

重要：
- 必须遵循故事背景中的设定
- 不能编造与背景矛盾的内容
- 保持叙事的连贯性和一致性
"""

    def _get_builtin_template(self) -> str:
        """获取内置模板（当文件不存在时的回退）"""
        return """
你是一个专业的"选项式灵异游戏 AI 导演"，负责为玩家的每一次选择生成恰当的、沉浸式的实时响应。

## 你的核心职责

1. 读取玩家选择
2. 读取游戏状态
3. 生成分层响应（物理/感官/心理/引导）
4. 更新游戏状态

## 响应生成规则

### 第一层：物理反馈（~100字）
- 明确确认玩家的行为
- 描述直接的物理结果
- 使用具体的动作动词

### 第二层：感官细节（~150字）
- 包含至少3种感官（视觉/听觉/嗅觉/触觉）
- 使用音效标记：`[音效: 描述]`
- 包含《世界书》的标志性元素："土腥味" / "潮湿" / "冰冷"

### 第三层：心理暗示（~100字）
- 反映共鸣度的变化
- 使用生理反应暗示恐惧程度
- 包含系统提示：`[系统: 共鸣度 X% → Y%]`

### 第四层：引导暗示（~50字）
- 自由探索期：使用软引导（环境暗示）
- 关键节点：使用硬引导（明确选项）
- 提供至少1个可行的下一步

## 输出格式

输出 Markdown 格式的叙事文本（200-500字）。

## 禁止事项

- ❌ 替玩家做决定
- ❌ 破坏《世界书》的规则
- ❌ 跳过场景
- ❌ 无理由提升/降低共鸣度
- ❌ 杀死玩家（失败应转为新分支）
"""

    def generate_response(
        self,
        choice: Choice,
        game_state: GameState,
        apply_consequences: bool = True,
        director_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """生成玩家选择后的叙事响应

        Args:
            choice: 玩家选择的选项
            game_state: 当前游戏状态
            apply_consequences: 是否自动应用后果到游戏状态（默认 True）

        Returns:
            str: Markdown 格式的叙事响应文本
        """
        # 延迟导入 CrewAI（避免基础功能依赖）
        try:
            from crewai import Agent, Task, Crew, LLM
            import os
        except ImportError:
            # 离线叙事回退：基于当前状态与场景记忆生成简短沉浸文本
            if apply_consequences and choice.consequences:
                game_state.update(choice.consequences)
                game_state.consequence_tree.append(choice.choice_id)

            scene_context = self._get_scene_memory(game_state.current_scene)
            pr_hint = "你的神经更紧绷了一些。" if game_state.PR >= 50 else "你努力让呼吸平稳下来。"
            text = (
                f"你选择了：{choice.choice_text}\n\n"
                f"昏黄的灯光在潮湿的墙面上跳动，空气里混着土腥味与细微的霉意。\n"
                f"远处传来水滴声，[音效: 滴——答] 一下比一下清晰。{pr_hint}\n\n"
                f"场景要点：\n{scene_context}\n"
            )
            return text

        # 复用 LLM（响应生成）
        llm = self._get_llm()
        print(f"🤖 [响应] 使用模型: {self._kimi_model_response}")

        # 保存原始状态（用于对比）
        state_before = game_state.to_dict()

        # 构建 prompt（加入导演上下文以增强连续性）
        prompt = self._build_prompt(choice, game_state, state_before, director_context=director_context)
        # 增强：在响应提示中加入世界书与伏笔回收要求，引导走向规范化结局
        prompt += (
            "\n\n[世界书与收束]\n"
            "- 不得破坏既定世界观；回收前文伏笔；逐步逼近结局节点\n"
            "- 如果当前已接近真相/危险阈值，暗示关键抉择临近（不替玩家决定）\n"
        )

        # 🎯 混合方案：响应生成使用完整故事背景
        if self.main_story:
            backstory = self._build_backstory_with_story()
            print("📚 [响应] 使用完整故事背景（高质量模式）")
        else:
            backstory = (
                "你精通恐怖氛围营造和细节描写。"
                "你的文笔风格是：第一人称视角，强节奏停顿，多感官细节，"
                "符号反复召回，像一个在深夜给观众讲恐怖故事的 UP 主。"
            )
            print("💡 [响应] 使用精简模式")

        # 创建 Agent（使用 Kimi LLM）
        agent = Agent(
            role="B站百万粉丝的恐怖故事 UP 主",
            goal="生成沉浸式的叙事响应，营造恐怖氛围",
            backstory=backstory,
            verbose=False,
            allow_delegation=False,
            llm=llm  # 使用 Kimi LLM
        )

        # 创建任务
        task = Task(
            description=prompt,
            expected_output="第一人称叙事文本（Markdown 格式，200-500字）",
            agent=agent
        )

        # 执行（增加防护，避免单次 LLM 故障直接中断整轮生成）
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        # 受限并发执行
        try:
            with self._sem:
                result = crew.kickoff()
            raw_text = str(result)
        except Exception as e:
            # 退回到本地兜底响应，避免整个 TreeBuilder 跑崩
            print(f"⚠️  响应生成失败，使用默认叙事兜底：{e}")
            raw_text = f"你选择了「{choice.choice_text}」，故事继续在黑暗中推进……"

        # 应用后果到游戏状态
        if apply_consequences and choice.consequences:
            game_state.update(choice.consequences)
            # 记录后果树
            game_state.consequence_tree.append(choice.choice_id)

        # 返回响应文本（附带系统提示）
        response_text = self._add_system_hints(
            raw_text,
            state_before,
            game_state.to_dict()
        )

        return response_text

    def _get_llm(self):
        """获取（并复用）LLM 实例"""
        if self._llm is not None:
            return self._llm

        from crewai import LLM
        import os

        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
        self._kimi_model_response = os.getenv("KIMI_MODEL_RESPONSE") or os.getenv("KIMI_MODEL", "kimi-k2-0905-preview")

        self._llm = LLM(
            model=self._kimi_model_response,
            api_key=kimi_key,
            base_url=kimi_base
        )
        return self._llm

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
        """构建完整的 prompt（优化版）"""
        # 计算状态变化
        pr_change = game_state.PR - state_before.get('PR', 0)

        # 提取场景相关内容（使用场景记忆）
        scene_context = self._get_scene_memory(game_state.current_scene)
        # 导演上下文摘要：最近几步的选择 / 响应 / 节拍，用于保持节奏与避免重复。
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

        return f"""
你是一个专业的恐怖故事作家。根据玩家选择生成沉浸式叙事响应（200-400字）。

## 玩家选择
**选择**: {choice.choice_text}
**类型**: {choice.choice_type.value} | **标签**: {', '.join(choice.tags[:2]) if choice.tags else '无'}

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

重要：必须使用"你"而不是"我"，例如：
- ✅ "你打开手电筒..."
- ❌ "我打开手电筒..."

请生成叙事响应（Markdown 格式，200-400字）
- 不要破坏世界观规则
- 不要使用现代网络梗

现在开始生成叙事响应（只输出Markdown文本，不要包含JSON或其他格式）：
"""

    def _extract_scene_context(self, gdd: str, scene: str, max_chars: int = 400) -> str:
        """提取当前场景相关的 GDD 片段"""
        lines = gdd.split('\n')
        relevant_lines = []

        for i, line in enumerate(lines):
            if scene.lower() in line.lower() or f"场景{scene[1:]}" in line:
                relevant_lines.append(line)
                for j in range(i + 1, min(i + 15, len(lines))):
                    if lines[j].strip().startswith('#') and lines[j].strip() != line.strip():
                        break
                    relevant_lines.append(lines[j])
                break

        result = '\n'.join(relevant_lines)[:max_chars]
        return result if result else f"场景 {scene}"

    def _add_system_hints(
        self,
        response_text: str,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any]
    ) -> str:
        """在响应文本后添加系统提示

        Args:
            response_text: 原始响应文本
            state_before: 之前的状态
            state_after: 之后的状态

        Returns:
            str: 添加了系统提示的文本
        """
        hints = []

        # PR 变化
        if state_before['PR'] != state_after['PR']:
            pr_change = state_after['PR'] - state_before['PR']
            sign = '+' if pr_change > 0 else ''
            hints.append(f"PR {sign}{pr_change} → 当前 {state_after['PR']}")

        # GR 变化
        if state_before['GR'] != state_after['GR']:
            gr_change = state_after['GR'] - state_before['GR']
            sign = '+' if gr_change > 0 else ''
            hints.append(f"GR {sign}{gr_change} → 当前 {state_after['GR']}")

        # WF 变化
        if state_before['WF'] != state_after['WF']:
            wf_change = state_after['WF'] - state_before['WF']
            sign = '+' if wf_change > 0 else ''
            hints.append(f"WF {sign}{wf_change} → 当前 {state_after['WF']}")

        # 道具变化
        new_items = set(state_after['inventory']) - set(state_before['inventory'])
        if new_items:
            hints.append(f"获得道具：{'、'.join(new_items)}")

        # 场景变化
        if state_before['current_scene'] != state_after['current_scene']:
            hints.append(f"进入场景：{state_after['current_scene']}")

        # 如果有变化，添加系统提示
        if hints:
            system_hint = "\n\n**【系统提示】**\n"
            for hint in hints:
                system_hint += f"- {hint}\n"

            response_text += system_hint

        return response_text

    def generate_ambient_response(
        self,
        game_state: GameState,
        idle_duration: int = 30
    ) -> str:
        """生成环境循环描述（当玩家长时间无动作时）

        Args:
            game_state: 当前游戏状态
            idle_duration: 玩家已经空闲的秒数

        Returns:
            str: 环境描述文本
        """
        # 导入 CrewAI 和配置 Kimi LLM
        try:
            from crewai import Agent, Task, Crew, LLM
            import os
        except ImportError:
            return "周围很安静……"

        # 配置 Kimi LLM（环境响应专用模型）
        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
        # 环境响应：使用高质量模型
        kimi_model = os.getenv("KIMI_MODEL_RESPONSE") or os.getenv("KIMI_MODEL", "kimi-k2-0905-preview")

        llm = LLM(
            model=kimi_model,
            api_key=kimi_key,
            base_url=kimi_base
        )

        prompt = f"""
你是一个恐怖游戏的 AI 导演。玩家已经在当前场景停留了 {idle_duration} 秒，没有采取任何行动。

当前游戏状态：
- 场景：{game_state.current_scene}
- 时间：{game_state.timestamp}
- PR：{game_state.PR}/100
- 位置：场景 {game_state.current_scene}

请生成一段 50-100 字的环境循环描述，包含：
1. 时间流逝的提示
2. 环境压力的暗示（土腥味/荧光灯/滴水声等）
3. 催促玩家行动的暗示

不要替玩家做决定，只描述环境。
"""

        agent = Agent(
            role="环境描述专家",
            goal="生成营造紧张感的环境描述",
            backstory="你擅长通过细节描写营造时间压力和环境压迫感",
            verbose=False,
            allow_delegation=False,
            llm=llm  # 使用 Kimi LLM
        )

        task = Task(
            description=prompt,
            expected_output="简短的环境描述（50-100字）",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()

        return str(result)

    def generate_scene_transition(
        self,
        from_scene: str,
        to_scene: str,
        game_state: GameState
    ) -> str:
        """生成场景转换的过渡文本

        Args:
            from_scene: 离开的场景
            to_scene: 进入的场景
            game_state: 当前游戏状态

        Returns:
            str: 场景转换文本
        """
        # 导入 CrewAI 和配置 Kimi LLM
        try:
            from crewai import Agent, Task, Crew, LLM
            import os
        except ImportError:
            game_state.current_scene = to_scene
            return f"你从 {from_scene} 来到了 {to_scene}……"

        # 配置 Kimi LLM（场景转换专用模型）
        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
        # 场景转换：使用高质量模型
        kimi_model = os.getenv("KIMI_MODEL_RESPONSE") or os.getenv("KIMI_MODEL", "kimi-k2-0905-preview")

        llm = LLM(
            model=kimi_model,
            api_key=kimi_key,
            base_url=kimi_base
        )

        prompt = f"""
你是一个恐怖游戏的 AI 导演。玩家正在从 {from_scene} 进入 {to_scene}。

当前游戏状态：
- 时间：{game_state.timestamp}
- PR：{game_state.PR}/100

请生成一段 100-200 字的场景转换描述，包含：
1. 离开当前场景的动作
2. 移动过程中的感官细节
3. 进入新场景的第一印象
4. 符合《世界书》氛围：土腥味/潮湿/冰冷

使用第一人称视角，Markdown 格式。
"""

        agent = Agent(
            role="场景转换专家",
            goal="生成流畅的场景转换描述",
            backstory="你擅长营造场景间的连贯性和氛围延续性",
            verbose=False,
            allow_delegation=False,
            llm=llm  # 使用 Kimi LLM
        )

        task = Task(
            description=prompt,
            expected_output="场景转换描述（100-200字）",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()

        # 更新游戏状态的场景
        game_state.current_scene = to_scene

        return str(result)


# 工具函数

def format_response_with_state(
    response_text: str,
    game_state: GameState
) -> str:
    """格式化响应文本，添加状态显示

    Args:
        response_text: 响应文本
        game_state: 游戏状态

    Returns:
        str: 格式化后的文本
    """
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
