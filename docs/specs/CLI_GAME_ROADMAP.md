# 命令行游戏开发路线图

**目标**: 实现可在命令行中完整游玩的灵异故事互动游戏
**预计周期**: 3-5 周
**技术栈**: Python + Rich + Pydantic

---

## 🎯 最终效果预览

```bash
$ ghost-story play --city "杭州"

╔══════════════════════════════════════════════════════════════════╗
║                    🎭 北高峰·空厢夜行                            ║
║                  特检院工程师 - 顾栖迟                          ║
╚══════════════════════════════════════════════════════════════════╝

📊 个人共鸣度 [████████░░░░░░░░░░] 45/100
🌍 全局共鸣度 [████████████░░░░░░] 63/100
⏱️  世界疲劳值 [█░░░░░░░░░] 1/10

⏰ 时间: 02:30  |  📍 场景: S4 - B3 入口

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

我把频谱仪贴在锁孔，播放 65 Hz 音源。
QTE 跳出，节拍 1.6 s，容错 3 次。

第一次，我故意晚按半拍，锁芯发出"咔哒"空转，像笑。
第二次，我闭眼，跟着心跳敲——

"咔——嗒——"

锁开，铁板掀起，一股 18 ℃的冷气扑在脸上...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【抉择点】请选择你的行动：

  1. 💼 直接拼合残片（限时 5min）
     └─ 后果：成功 → 获得【残片密钥】(+15 PR)
              失败 → 触发失魂者 T2

  2. 🔍 先调查电缆迷宫（+30min）
     └─ 后果：每读一句 +5 PR（上限 +30）
              但会延长时间，可能错过最佳时机

  3. 💾 保存进度并退出
     └─ 存档：杭州_S4_02:30.save

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请输入选项编号 [1-3]: _
```

---

## 📅 Week 1: 核心数据结构

### Day 1-2: GameState 类 ✅
**文件**: `src/ghost_story_factory/engine/state.py`

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

@dataclass
class GameState:
    """游戏状态"""
    # 核心变量
    PR: int = 5          # 个人共鸣度 (0-100)
    GR: int = 0          # 全局共鸣度 (0-100)
    WF: int = 0          # 世界疲劳值 (0-10)

    # 游戏进度
    current_scene: str = "S1"
    timestamp: str = "00:00"  # 游戏内时间

    # 玩家资源
    inventory: List[str] = field(default_factory=list)
    flags: Dict[str, bool] = field(default_factory=dict)
    consequence_tree: List[str] = field(default_factory=list)

    def update(self, changes: Dict[str, Any]) -> None:
        """应用状态变化"""
        for key, value in changes.items():
            if key in ["PR", "GR", "WF"]:
                # 数值变化（支持 +5, -10 等）
                if isinstance(value, str) and value[0] in ['+', '-']:
                    setattr(self, key, max(0, min(100, getattr(self, key) + int(value))))
                else:
                    setattr(self, key, value)
            elif key == "inventory":
                self.inventory.extend(value)
            elif key == "flags":
                self.flags.update(value)
            # ... 其他字段

    def check_preconditions(self, conditions: Dict) -> bool:
        """检查前置条件"""
        for key, value in conditions.items():
            if key == "PR":
                if not self._check_comparison(self.PR, value):
                    return False
            elif key == "items":
                if not all(item in self.inventory for item in value):
                    return False
        return True

    def save(self, filepath: str) -> None:
        """保存状态"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'GameState':
        """加载状态"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        state = cls()
        state.__dict__.update(data)
        return state
```

**测试任务**:
```bash
pytest tests/test_state.py -v
```

---

### Day 3-4: Choice 数据模型 ✅
**文件**: `src/ghost_story_factory/engine/choices.py`

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

class ChoiceType(str, Enum):
    MICRO = "micro"
    NORMAL = "normal"
    CRITICAL = "critical"

class Choice(BaseModel):
    """选择点"""
    choice_id: str = Field(..., description="唯一标识，如 S3_C1")
    choice_text: str = Field(..., description="显示文本")
    choice_type: ChoiceType = Field(default=ChoiceType.NORMAL)

    preconditions: Optional[Dict[str, Any]] = Field(default=None, description="前置条件")
    consequences: Optional[Dict[str, Any]] = Field(default=None, description="后果")

    def is_available(self, game_state: 'GameState') -> bool:
        """检查选项是否可用"""
        if not self.preconditions:
            return True
        return game_state.check_preconditions(self.preconditions)

    def get_display_text(self, game_state: 'GameState') -> str:
        """生成显示文本（含可用性标记）"""
        if not self.is_available(game_state):
            return f"🔒 {self.choice_text} (条件不满足)"

        icon = {
            ChoiceType.MICRO: "💬",
            ChoiceType.NORMAL: "💼",
            ChoiceType.CRITICAL: "⚠️"
        }[self.choice_type]

        return f"{icon} {self.choice_text}"
```

---

### Day 5-7: 选择点生成器（简化版）✅
**文件**: `src/ghost_story_factory/engine/choice_generator.py`

```python
from crewai import Agent, Task, Crew
from .choices import Choice, ChoiceType
from .state import GameState
from typing import List
import json

class ChoicePointsGenerator:
    """选择点生成器"""

    def __init__(self, gdd_content: str, lore_content: str):
        self.gdd = gdd_content
        self.lore = lore_content
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """加载 choice-points.prompt.md"""
        with open("templates/choice-points.prompt.md", 'r', encoding='utf-8') as f:
            return f.read()

    def generate_choices(
        self,
        current_scene: str,
        game_state: GameState
    ) -> List[Choice]:
        """生成选择点"""
        prompt = self.prompt_template.format(
            scene_id=current_scene,
            game_state=game_state.__dict__,
            gdd_content=self.gdd,
            lore_content=self.lore
        )

        # 调用 LLM
        agent = Agent(
            role="选择点设计师",
            goal="生成符合场景的选择点",
            backstory="你精通叙事设计和玩家心理"
        )

        task = Task(
            description=prompt,
            expected_output="JSON 格式的选择点列表",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task])
        result = crew.kickoff()

        # 解析结果
        choices_data = json.loads(result)
        return [Choice(**choice) for choice in choices_data['choices']]
```

**测试**:
```python
# 测试生成 S1 的选择点
generator = ChoicePointsGenerator(gdd, lore_v2)
state = GameState(current_scene="S1", PR=5)
choices = generator.generate_choices("S1", state)

assert len(choices) >= 3
assert all(isinstance(c, Choice) for c in choices)
```

---

## 📅 Week 2: 响应生成与意图映射

### Day 8-10: 运行时响应生成器 ✅
**文件**: `src/ghost_story_factory/engine/response_generator.py`

```python
class RuntimeResponseGenerator:
    """运行时响应生成器"""

    def __init__(self, gdd_content: str, lore_content: str):
        self.gdd = gdd_content
        self.lore = lore_content
        self.prompt_template = self._load_prompt()

    def generate_response(
        self,
        choice: Choice,
        game_state: GameState
    ) -> str:
        """生成玩家选择后的叙事响应"""
        prompt = self.prompt_template.format(
            choice_text=choice.choice_text,
            choice_consequences=choice.consequences,
            game_state_before=game_state.__dict__,
            gdd_content=self.gdd,
            lore_content=self.lore
        )

        # 调用 LLM 生成响应
        agent = Agent(
            role="B站百万粉丝的恐怖故事 UP 主",
            goal="生成沉浸式的叙事响应",
            backstory="你精通恐怖氛围营造和细节描写"
        )

        task = Task(
            description=prompt,
            expected_output="第一人称叙事文本（Markdown）",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task])
        response = crew.kickoff()

        # 应用后果到游戏状态
        if choice.consequences:
            game_state.update(choice.consequences)

        return str(response)
```

---

### Day 11-14: 意图映射引擎 ✅
**文件**: `src/ghost_story_factory/engine/intent_mapper.py`

```python
from dataclasses import dataclass
from .choices import Choice
from .state import GameState

@dataclass
class ValidationResult:
    is_valid: bool
    reason: Optional[str] = None

class IntentMappingEngine:
    """意图映射引擎"""

    def validate_choice(
        self,
        choice: Choice,
        game_state: GameState
    ) -> ValidationResult:
        """验证选项是否可用"""
        if not choice.is_available(game_state):
            return ValidationResult(
                is_valid=False,
                reason=f"前置条件不满足：{choice.preconditions}"
            )

        return ValidationResult(is_valid=True)
```

---

## 📅 Week 3: 游戏主循环与 CLI

### Day 15-18: 游戏主循环 ✅
**文件**: `src/ghost_story_factory/engine/game_loop.py`

```python
class GameEngine:
    """游戏引擎"""

    def __init__(self, city: str, gdd_path: str, lore_path: str):
        self.city = city
        self.gdd = self._load_file(gdd_path)
        self.lore = self._load_file(lore_path)

        # 初始化游戏状态
        self.state = GameState()

        # 初始化各个生成器
        self.choice_generator = ChoicePointsGenerator(self.gdd, self.lore)
        self.response_generator = RuntimeResponseGenerator(self.gdd, self.lore)
        self.intent_mapper = IntentMappingEngine()

    def run(self):
        """主游戏循环"""
        print(f"🎭 开始游戏：{self.city}")

        while not self._check_ending():
            # 1. 生成选择点
            choices = self.choice_generator.generate_choices(
                self.state.current_scene,
                self.state
            )

            # 2. 显示并获取玩家输入
            selected_choice = self._prompt_player(choices)

            # 3. 验证
            validation = self.intent_mapper.validate_choice(selected_choice, self.state)
            if not validation.is_valid:
                print(f"❌ {validation.reason}")
                continue

            # 4. 生成响应并更新状态
            response = self.response_generator.generate_response(
                selected_choice,
                self.state
            )

            # 5. 显示响应
            self._display_response(response)

            # 6. 检查是否需要切换场景
            self._check_scene_transition()

        # 7. 结局
        self._show_ending()

    def _check_ending(self) -> bool:
        """检查是否达成结局"""
        # 根据 GDD 定义的结局条件判断
        if self.state.current_scene == "S6":
            return True
        return False
```

---

### Day 19-21: CLI UI（Rich 美化）✅
**文件**: `src/ghost_story_factory/ui/cli.py`

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress
from rich.table import Table
from rich.prompt import Prompt

class GameCLI:
    """命令行界面"""

    def __init__(self):
        self.console = Console()

    def display_title(self, city: str, protagonist: str):
        """显示标题"""
        title = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    🎭 {city} 灵异故事                            ║
║                  {protagonist}                                   ║
╚══════════════════════════════════════════════════════════════════╝
        """
        self.console.print(title, style="bold cyan")

    def display_state(self, state: GameState):
        """显示游戏状态"""
        self.console.print(f"\n📊 个人共鸣度 {self._render_bar(state.PR, 100)}")
        self.console.print(f"🌍 全局共鸣度 {self._render_bar(state.GR, 100)}")
        self.console.print(f"⏱️  世界疲劳值 {self._render_bar(state.WF, 10)}")
        self.console.print(f"\n⏰ 时间: {state.timestamp}  |  📍 场景: {state.current_scene}\n")

    def display_narrative(self, text: str):
        """显示叙事文本"""
        panel = Panel(
            Markdown(text),
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(panel)

    def display_choices(self, choices: List[Choice]) -> Choice:
        """显示选择列表"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("编号", style="cyan", width=6)
        table.add_column("选项", style="white")

        for i, choice in enumerate(choices, 1):
            table.add_row(str(i), choice.get_display_text())

        self.console.print(table)

        # 获取输入
        while True:
            choice_num = Prompt.ask(
                "请输入选项编号",
                choices=[str(i) for i in range(1, len(choices) + 1)]
            )
            return choices[int(choice_num) - 1]

    def _render_bar(self, value: int, max_value: int) -> str:
        """渲染进度条"""
        filled = int(value / max_value * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return f"[{bar}] {value}/{max_value}"
```

---

## 📅 Week 4-5: 完善体验

### 功能清单
- [x] 保存/读档系统
- [x] 多结局判定
- [x] 成就系统（可选）
- [x] 历史记录查看
- [x] 快捷命令（/save, /load, /quit）

---

## 🚀 新增 CLI 命令

在 `pyproject.toml` 中注册：

```toml
[project.scripts]
# ... 已有命令 ...

# 新增：游戏命令
"ghost-story-play" = "ghost_story_factory.engine.game_loop:main"
```

使用方式：

```bash
# 1. 生成故事（已有）
gen-complete --city "杭州" --index 1

# 2. 开始游戏（新增）
ghost-story-play --city "杭州"

# 3. 读档继续（新增）
ghost-story-play --load saves/杭州_S4_02:30.save
```

---

## ✅ 验收标准

### Milestone 1 交付（Week 3）
- [ ] 可以完整玩完一个故事（杭州）
- [ ] 至少 3 个场景的选择点生成正常
- [ ] 状态变化正确（PR/GR/WF）
- [ ] 基础 CLI 显示清晰

### Milestone 2 交付（Week 5）
- [ ] Rich 美化完成，界面美观
- [ ] 保存/读档功能正常
- [ ] 多结局系统正常
- [ ] 性能良好（每次响应 <10s）

---

## 📝 开发注意事项

1. **优先使用已有的 prompt 模板**
   - `templates/choice-points.prompt.md`
   - `templates/runtime-response.prompt.md`
   - 不要重复造轮子

2. **复用现有代码**
   - `src/ghost_story_factory/main.py` 中的 LLM 配置
   - Agent 创建逻辑

3. **测试驱动开发**
   - 先写测试，再写实现
   - 用杭州故事作为测试数据

4. **性能优化**
   - 缓存已生成的选择点
   - 异步生成响应（可选）

---

## 🎯 下一步行动

1. 创建 `src/ghost_story_factory/engine/` 目录
2. 复制 `game_engine.py` 到 `engine/game_loop.py` 作为起点
3. 从 Week 1 Day 1 开始逐步实现

准备好开始了吗？ 🚀

