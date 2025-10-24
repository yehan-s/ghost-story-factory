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
from .choices import Choice


class RuntimeResponseGenerator:
    """运行时响应生成器

    基于玩家的选择，调用 LLM 生成沉浸式的叙事响应，
    并自动更新游戏状态
    """

    def __init__(self, gdd_content: str, lore_content: str):
        """初始化生成器

        Args:
            gdd_content: GDD（AI 导演任务简报）内容
            lore_content: Lore v2（世界观）内容
        """
        self.gdd = gdd_content
        self.lore = lore_content
        self.prompt_template = self._load_prompt_template()

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
        apply_consequences: bool = True
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
            from crewai import Agent, Task, Crew
        except ImportError:
            print("⚠️  CrewAI 未安装，无法生成响应，返回简单确认")
            # 应用后果
            if apply_consequences and choice.consequences:
                game_state.update(choice.consequences)
                game_state.consequence_tree.append(choice.choice_id)
            return f"你选择了：{choice.choice_text}\n\n（CrewAI 未安装，无法生成完整叙事响应）"

        # 保存原始状态（用于对比）
        state_before = game_state.to_dict()

        # 构建 prompt
        prompt = self._build_prompt(choice, game_state, state_before)

        # 创建 Agent
        agent = Agent(
            role="B站百万粉丝的恐怖故事 UP 主",
            goal="生成沉浸式的叙事响应，营造恐怖氛围",
            backstory=(
                "你精通恐怖氛围营造和细节描写。"
                "你的文笔风格是：第一人称视角，强节奏停顿，多感官细节，"
                "符号反复召回，像一个在深夜给观众讲恐怖故事的 UP 主。"
            ),
            verbose=False,
            allow_delegation=False
        )

        # 创建任务
        task = Task(
            description=prompt,
            expected_output="第一人称叙事文本（Markdown 格式，200-500字）",
            agent=agent
        )

        # 执行
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()

        # 应用后果到游戏状态
        if apply_consequences and choice.consequences:
            game_state.update(choice.consequences)
            # 记录后果树
            game_state.consequence_tree.append(choice.choice_id)

        # 返回响应文本
        response_text = str(result)

        # 添加系统提示（如果状态发生变化）
        response_text = self._add_system_hints(
            response_text,
            state_before,
            game_state.to_dict()
        )

        return response_text

    def _build_prompt(
        self,
        choice: Choice,
        game_state: GameState,
        state_before: Dict[str, Any]
    ) -> str:
        """构建完整的 prompt"""
        return f"""
{self.prompt_template}

---

## 玩家选择

**选项 ID**: {choice.choice_id}
**选项文本**: {choice.choice_text}
**选项类型**: {choice.choice_type.value}
**选项标签**: {', '.join(choice.tags) if choice.tags else '无'}

**预定义后果**:
```json
{json.dumps(choice.consequences, ensure_ascii=False, indent=2) if choice.consequences else '{}'}
```

---

## 当前游戏状态

**场景**: {game_state.current_scene}
**时间**: {game_state.timestamp}
**位置**: 场景 {game_state.current_scene}

**核心状态**:
- PR（个人共鸣度）: {game_state.PR}/100
- GR（全局共鸣度）: {game_state.GR}/100
- WF（世界疲劳值）: {game_state.WF}/10

**玩家资源**:
- 道具: {', '.join(game_state.inventory) if game_state.inventory else '无'}
- 标志位: {', '.join(f"{k}={v}" for k, v in game_state.flags.items()) if game_state.flags else '无'}

**后果树**（历史选择）:
{' → '.join(game_state.consequence_tree[-5:]) if game_state.consequence_tree else '这是第一个选择'}

---

## GDD（剧情框架）

```markdown
{self.gdd[:2000]}
... （完整 GDD 内容）
```

---

## Lore v2（世界观规则）

```markdown
{self.lore[:2000]}
... （完整 Lore 内容）
```

---

## 生成要求

请基于以上信息生成一段 200-500 字的沉浸式叙事响应。

**响应结构**:
1. **物理反馈**（~100字）：确认玩家行为，描述直接结果
2. **感官细节**（~150字）：视觉、听觉、嗅觉、触觉，至少3种
3. **心理暗示**（~100字）：反映共鸣度变化，生理反应
4. **引导暗示**（~50字）：环境暗示或下一步提示

**必须包含的元素**:
- [ ] 明确确认玩家的选择行为
- [ ] 至少 3 种感官描述
- [ ] 《世界书》标志性元素：土腥味/潮湿/冰冷（至少一个）
- [ ] 音效标记（如果有）：`[音效: 描述]`
- [ ] 至少 1 个下一步的环境暗示

**禁止**:
- 不要替玩家做决定（"你决定..." → "你看到..."）
- 不要杀死玩家
- 不要破坏世界观规则
- 不要使用现代网络梗

现在开始生成叙事响应（只输出Markdown文本，不要包含JSON或其他格式）：
"""

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
            allow_delegation=False
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
            allow_delegation=False
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

