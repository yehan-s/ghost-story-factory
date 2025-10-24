"""选择点生成器

根据当前场景和游戏状态生成3种类型的选择点：
- 微选择（MICRO）：日常互动，低风险
- 普通选择（NORMAL）：情节推进
- 关键选择（CRITICAL）：结局分支
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import json

from .state import GameState


class ChoiceType(str, Enum):
    """选择点类型"""
    MICRO = "micro"          # 微选择：日常互动
    NORMAL = "normal"        # 普通选择：情节推进
    CRITICAL = "critical"    # 关键选择：结局分支


class Choice(BaseModel):
    """选择点数据模型

    Attributes:
        choice_id: 唯一标识，如 "S3_C1"
        choice_text: 显示给玩家的选项文本
        choice_type: 选择类型（micro/normal/critical）
        preconditions: 前置条件（可选），如 {"PR": ">=40", "items": ["道具1"]}
        consequences: 后果（可选），如 {"PR": "+5", "items": ["道具2"]}
        tags: 标签列表，用于分类，如 ["保守", "遵守手册"]
        timeout: 超时时间（秒），仅用于 CRITICAL 类型
        can_skip: 是否可跳过
    """

    choice_id: str = Field(..., description="唯一标识，如 S3_C1")
    choice_text: str = Field(..., description="显示文本")
    choice_type: ChoiceType = Field(default=ChoiceType.NORMAL, description="选择类型")

    preconditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="前置条件，如 {'PR': '>=40', 'items': ['道具1']}"
    )
    consequences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="后果，如 {'PR': '+5', 'items': ['道具2'], 'flags': {'flag1': True}}"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="标签列表，如 ['保守', '遵守手册']"
    )

    timeout: Optional[int] = Field(
        default=None,
        description="超时时间（秒），仅用于 CRITICAL 类型"
    )
    can_skip: bool = Field(
        default=False,
        description="是否可跳过"
    )

    def is_available(self, game_state: GameState) -> bool:
        """检查选项是否可用

        Args:
            game_state: 当前游戏状态

        Returns:
            bool: 是否满足前置条件
        """
        if not self.preconditions:
            return True
        return game_state.check_preconditions(self.preconditions)

    def get_display_text(self, game_state: GameState) -> str:
        """生成显示文本（含可用性标记）

        Args:
            game_state: 当前游戏状态

        Returns:
            str: 格式化的显示文本
        """
        # 检查是否可用
        if not self.is_available(game_state):
            return f"🔒 {self.choice_text} (条件不满足)"

        # 根据类型添加图标
        icon_map = {
            ChoiceType.MICRO: "💬",
            ChoiceType.NORMAL: "💼",
            ChoiceType.CRITICAL: "⚠️"
        }
        icon = icon_map.get(self.choice_type, "•")

        # 添加标签提示
        tag_hint = ""
        if self.tags:
            tag_hint = f" [{', '.join(self.tags)}]"

        return f"{icon} {self.choice_text}{tag_hint}"

    def get_consequence_preview(self) -> str:
        """获取后果预览（用于UI提示）

        Returns:
            str: 后果预览文本
        """
        if not self.consequences:
            return ""

        previews = []

        # PR 变化
        if "PR" in self.consequences:
            pr_change = self.consequences["PR"]
            previews.append(f"PR {pr_change}")

        # 道具变化
        if "items" in self.consequences:
            items = self.consequences["items"]
            if items:
                previews.append(f"获得道具 x{len(items)}")

        # 时间消耗
        if "timestamp" in self.consequences:
            previews.append("消耗时间")

        return " | ".join(previews) if previews else ""


class ChoicePointsGenerator:
    """选择点生成器

    根据当前场景和游戏状态，调用 LLM 生成合适的选择点列表
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
        root_prompt = Path("choice-points.prompt.md")
        if root_prompt.exists():
            with open(root_prompt, 'r', encoding='utf-8') as f:
                return f.read()

        # 回退到 templates 目录
        template_prompt = Path("templates/choice-points.prompt.md")
        if template_prompt.exists():
            with open(template_prompt, 'r', encoding='utf-8') as f:
                return f.read()

        # 如果都不存在，返回内置的简化模板
        return self._get_builtin_template()

    def _get_builtin_template(self) -> str:
        """获取内置模板（当文件不存在时的回退）"""
        return """
你是一个专业的"选择点生成器"，负责在关键剧情节点生成合适的选项。

## 你的任务

基于当前场景和游戏状态，生成 2-4 个选择点。

## 选择点分类

- MICRO：微选择，日常互动
- NORMAL：普通选择，情节推进
- CRITICAL：关键选择，结局分支

## 输出格式（JSON）

```json
{
  "scene_id": "S3",
  "choices": [
    {
      "choice_id": "S3_C1",
      "choice_text": "选项文本",
      "choice_type": "normal",
      "preconditions": {"PR": ">=40"},
      "consequences": {
        "PR": "+5",
        "items": ["道具1"],
        "flags": {"flag1": true}
      },
      "tags": ["保守", "安全"],
      "timeout": null,
      "can_skip": false
    }
  ]
}
```

## 注意事项

1. 每个选项都应该是"可行的"
2. 至少 2 个选项是"合理的"
3. 后果应该"可预见"
4. 选项数量：2-4 个
5. 不给玩家"跳出框架"的选项
"""

    def generate_choices(
        self,
        current_scene: str,
        game_state: GameState,
        narrative_context: Optional[str] = None
    ) -> List[Choice]:
        """生成选择点

        Args:
            current_scene: 当前场景 ID，如 "S3"
            game_state: 当前游戏状态
            narrative_context: 当前叙事上下文（可选），由 RuntimeResponseGenerator 提供

        Returns:
            List[Choice]: 选择点列表
        """
        # 延迟导入 CrewAI（避免基础功能依赖）
        try:
            from crewai import Agent, Task, Crew
        except ImportError:
            print("⚠️  CrewAI 未安装，无法生成选择点，返回默认选择点")
            return self._get_default_choices(current_scene)

        # 构建 prompt
        prompt = self._build_prompt(current_scene, game_state, narrative_context)

        # 创建 Agent
        agent = Agent(
            role="选择点设计师",
            goal="生成符合场景的选择点，引导玩家在框架内做出选择",
            backstory=(
                "你精通叙事设计和玩家心理学。"
                "你擅长设计有意义的选择点，让玩家感觉'我在控制剧情'，"
                "但实际上所有选择都在设计好的框架内。"
            ),
            verbose=False,
            allow_delegation=False
        )

        # 创建任务
        task = Task(
            description=prompt,
            expected_output="JSON 格式的选择点列表",
            agent=agent
        )

        # 执行
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()

        # 解析结果
        try:
            choices_data = self._parse_result(str(result))
            return [Choice(**choice) for choice in choices_data['choices']]
        except Exception as e:
            print(f"⚠️  解析选择点失败: {e}")
            # 返回默认选择点
            return self._get_default_choices(current_scene)

    def _build_prompt(
        self,
        current_scene: str,
        game_state: GameState,
        narrative_context: Optional[str]
    ) -> str:
        """构建完整的 prompt"""
        context = narrative_context or "玩家刚进入该场景。"

        return f"""
{self.prompt_template}

---

## 当前游戏状态

**场景**: {current_scene}
**叙事上下文**: {context}

**游戏状态**:
- PR（个人共鸣度）: {game_state.PR}/100
- GR（全局共鸣度）: {game_state.GR}/100
- WF（世界疲劳值）: {game_state.WF}/10
- 时间: {game_state.timestamp}
- 道具: {', '.join(game_state.inventory) if game_state.inventory else '无'}
- 标志位: {list(game_state.flags.keys()) if game_state.flags else '无'}

---

## GDD（剧情框架）

```markdown
{self.gdd}
```

---

## Lore v2（世界观规则）

```markdown
{self.lore}
```

---

请基于以上信息生成选择点，**必须**输出标准 JSON 格式。
"""

    def _parse_result(self, result_text: str) -> Dict:
        """解析 LLM 返回结果

        Args:
            result_text: LLM 返回的文本

        Returns:
            Dict: 解析后的数据
        """
        # 清理文本
        result_text = result_text.strip()

        # 提取 JSON 代码块
        if "```json" in result_text:
            start = result_text.find("```json") + 7
            end = result_text.find("```", start)
            result_text = result_text[start:end].strip()
        elif "```" in result_text:
            start = result_text.find("```") + 3
            end = result_text.find("```", start)
            result_text = result_text[start:end].strip()

        # 解析 JSON
        return json.loads(result_text)

    def _get_default_choices(self, current_scene: str) -> List[Choice]:
        """获取默认选择点（当生成失败时的回退）

        Args:
            current_scene: 当前场景 ID

        Returns:
            List[Choice]: 默认选择点列表
        """
        return [
            Choice(
                choice_id=f"{current_scene}_C1",
                choice_text="继续探索",
                choice_type=ChoiceType.NORMAL,
                consequences={"timestamp": "+5min"}
            ),
            Choice(
                choice_id=f"{current_scene}_C2",
                choice_text="原地观察",
                choice_type=ChoiceType.NORMAL,
                consequences={"PR": "+5", "timestamp": "+2min"}
            ),
            Choice(
                choice_id=f"{current_scene}_C3",
                choice_text="返回中控室",
                choice_type=ChoiceType.NORMAL,
                consequences={"timestamp": "+3min"}
            )
        ]


# 工具函数

def load_choices_from_file(filepath: str) -> List[Choice]:
    """从文件加载预设选择点

    Args:
        filepath: JSON 文件路径

    Returns:
        List[Choice]: 选择点列表
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [Choice(**choice) for choice in data['choices']]


def save_choices_to_file(choices: List[Choice], filepath: str) -> None:
    """保存选择点到文件

    Args:
        choices: 选择点列表
        filepath: 保存路径
    """
    data = {
        "choices": [choice.model_dump() for choice in choices]
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

