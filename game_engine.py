#!/usr/bin/env python3
"""
Ghost Story Factory - 交互式游戏引擎

基于生成的故事（GDD、Lore v2）运行一个选项式交互游戏。
使用阶段4的templates（choice-points, runtime-response, state-management, intent-mapping）。

使用方法：
    python game_engine.py --city 武汉 --gdd deliverables/程序-武汉/武汉_gdd.json
"""

import argparse
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from dotenv import load_dotenv

load_dotenv()

TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass
class GameState:
    """游戏状态"""
    location: str
    time: str
    resonance: int  # 0-100
    inventory: List[str]
    flags: Dict[str, bool]
    current_scene: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Choice:
    """选择选项"""
    id: str
    text: str
    preconditions: Optional[Dict[str, Any]] = None
    consequences: Optional[Dict[str, Any]] = None


class GameEngine:
    """交互式游戏引擎"""

    def __init__(self, city: str, gdd_path: str, lore_path: str):
        self.city = city
        self.gdd = self._load_json(gdd_path)
        self.lore = self._load_json(lore_path)

        # 初始化游戏状态
        self.state = GameState(
            location="初始位置",
            time="00:00 AM",
            resonance=20,
            inventory=["手电筒", "对讲机"],
            flags={},
            current_scene="场景1"
        )

        # 构建LLM和Agent
        self.llm = self._build_llm()
        self.choice_generator = self._create_choice_generator()
        self.response_generator = self._create_response_generator()
        self.state_manager = self._create_state_manager()

    def _build_llm(self) -> LLM:
        """构建LLM"""
        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        if kimi_key:
            return LLM(
                model=os.getenv("KIMI_MODEL", "kimi-k2-0905-preview"),
                api_key=kimi_key,
                api_base=os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1"),
                custom_llm_provider="openai",
                max_tokens=4000,
            )

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return LLM(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL"),
                max_tokens=4000,
            )

        raise RuntimeError("未检测到 KIMI_API_KEY 或 OPENAI_API_KEY")

    def _create_choice_generator(self) -> Agent:
        """创建选择点生成器Agent"""
        return Agent(
            role='选择点设计师',
            goal='在关键剧情节点生成2-4个合理的选项，限制玩家在框架内',
            backstory='你是专业的游戏设计师，擅长设计既给玩家选择感，又不会跳出剧情框架的选项。',
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _create_response_generator(self) -> Agent:
        """创建响应生成器Agent"""
        return Agent(
            role='AI导演',
            goal='基于玩家的选择生成沉浸式的响应，推进剧情',
            backstory='你是经验丰富的AI导演，擅长根据玩家选择生成引人入胜的剧情响应。',
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _create_state_manager(self) -> Agent:
        """创建状态管理器Agent"""
        return Agent(
            role='状态管理器',
            goal='管理游戏状态，确保所有变化符合世界规则',
            backstory='你是严谨的状态管理系统，确保游戏世界的一致性和规则遵守。',
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _load_json(self, path: str) -> dict:
        """加载JSON文件"""
        p = Path(path)
        if not p.exists():
            # 尝试 .md 文件
            md_path = p.with_suffix('.md')
            if md_path.exists():
                content = md_path.read_text(encoding='utf-8')
                # 尝试从markdown中提取JSON
                import re
                match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', content)
                if match:
                    return json.loads(match.group(1))
            return {}
        return json.loads(p.read_text(encoding='utf-8'))

    def _load_prompt(self, module_name: str) -> str:
        """加载templates提示词"""
        prompt_file = TEMPLATE_DIR / f"{module_name}.prompt.md"
        if not prompt_file.exists():
            return ""
        return prompt_file.read_text(encoding='utf-8')

    # ==================== 阶段4: 交互运行层 ====================

    def generate_choices(self, narrative_context: str) -> List[Choice]:
        """生成选择点（使用 choice-points.prompt.md）"""
        print("\n" + "="*60)
        print("🎯 AI正在生成选择点...")
        print("="*60)

        prompt = self._load_prompt("choice-points")
        if not prompt:
            # 简化版提示词
            prompt = """
基于当前剧情情境和游戏状态，生成2-4个合理的选择选项。

当前情境：
{narrative_context}

当前状态：
{state}

GDD场景信息：
{gdd_scene}

世界规则：
{lore_rules}

要求：
1. 每个选项都是可行的（不给陷阱选项）
2. 选项之间有明显区别（保守/激进/策略）
3. 所有选项都在剧情框架内（不能跳出）
4. 返回JSON数组格式

输出格式：
```json
[
  {{"id": "A", "text": "选项文本", "tags": ["保守"], "consequences": {{"resonance": "+10"}}}},
  {{"id": "B", "text": "选项文本", "tags": ["激进"], "consequences": {{"resonance": "+20"}}}}
]
```
"""

        task = Task(
            description=prompt,
            expected_output="JSON数组格式的选项列表",
            agent=self.choice_generator,
        )

        crew = Crew(
            agents=[self.choice_generator],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "narrative_context": narrative_context,
            "state": json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2),
            "gdd_scene": json.dumps(self.gdd.get("current_scene", {}), ensure_ascii=False),
            "lore_rules": json.dumps(self.lore.get("rules", []), ensure_ascii=False),
        }))

        # 解析选项
        choices = self._parse_choices(result)
        return choices

    def generate_response(self, player_choice: Choice) -> str:
        """生成响应（使用 runtime-response.prompt.md）"""
        print("\n" + "="*60)
        print("📝 AI正在生成响应...")
        print("="*60)

        prompt = self._load_prompt("runtime-response")
        if not prompt:
            prompt = """
基于玩家的选择，生成一个沉浸式的响应（200-500字）。

玩家选择：
{player_choice}

当前状态：
{state}

世界规则：
{lore_rules}

要求：
1. 确认玩家的选择
2. 描述世界的反馈（物理/感官/心理）
3. 更新状态（共鸣度、位置、旗标等）
4. 引导下一步（但不强制）

输出格式：Markdown文本（200-500字）
"""

        task = Task(
            description=prompt,
            expected_output="Markdown格式的响应文本",
            agent=self.response_generator,
        )

        crew = Crew(
            agents=[self.response_generator],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "player_choice": json.dumps({
                "id": player_choice.id,
                "text": player_choice.text,
                "consequences": player_choice.consequences or {}
            }, ensure_ascii=False),
            "state": json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2),
            "lore_rules": json.dumps(self.lore.get("rules", []), ensure_ascii=False),
        }))

        return result

    def update_state(self, player_choice: Choice, response: str):
        """更新游戏状态（使用 state-management.prompt.md）"""
        print("\n" + "="*60)
        print("🔄 AI正在更新游戏状态...")
        print("="*60)

        prompt = self._load_prompt("state-management")
        if not prompt:
            prompt = """
基于玩家选择和生成的响应，更新游戏状态。

玩家选择的后果：
{consequences}

当前状态：
{state}

世界规则：
{lore_rules}

要求：
1. 应用选项预定义的后果
2. 检查是否触发了世界规则的级联效果
3. 验证新状态是否符合规则
4. 返回更新后的完整状态

输出格式：JSON格式的新状态
```json
{{
  "location": "新位置",
  "resonance": 30,
  "flags": {{"某事件": true}},
  ...
}}
```
"""

        task = Task(
            description=prompt,
            expected_output="JSON格式的新状态",
            agent=self.state_manager,
        )

        crew = Crew(
            agents=[self.state_manager],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "consequences": json.dumps(player_choice.consequences or {}, ensure_ascii=False),
            "state": json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2),
            "lore_rules": json.dumps(self.lore.get("rules", []), ensure_ascii=False),
        }))

        # 解析并更新状态
        new_state = self._parse_state(result)
        if new_state:
            self.state.location = new_state.get("location", self.state.location)
            self.state.time = new_state.get("time", self.state.time)
            self.state.resonance = new_state.get("resonance", self.state.resonance)
            self.state.flags.update(new_state.get("flags", {}))

    def _parse_choices(self, text: str) -> List[Choice]:
        """从AI响应中解析选项"""
        import re

        # 尝试提取JSON数组
        match = re.search(r'```json\s*(\[[\s\S]*?\])\s*```', text)
        if match:
            try:
                data = json.loads(match.group(1))
                return [Choice(
                    id=c.get("id", ""),
                    text=c.get("text", ""),
                    preconditions=c.get("preconditions"),
                    consequences=c.get("consequences"),
                ) for c in data]
            except:
                pass

        # 备用：简单解析
        return [
            Choice(id="A", text="继续前进", consequences={"resonance": "+5"}),
            Choice(id="B", text="原地观察", consequences={"time": "+5分钟"}),
        ]

    def _parse_state(self, text: str) -> Optional[dict]:
        """从AI响应中解析状态"""
        import re

        match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass

        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass

        return None

    # ==================== 游戏主循环 ====================

    def run(self):
        """运行游戏主循环"""
        print("\n" + "="*60)
        print(f"🎮 {self.city} 灵异故事 - 交互式游戏")
        print("="*60)
        print("\n欢迎来到灵异世界...")
        print("你的每个选择都会影响故事的走向。\n")

        turn = 0
        max_turns = 10  # 最大回合数（demo限制）

        while turn < max_turns:
            turn += 1
            print(f"\n{'='*60}")
            print(f"回合 {turn} | 位置: {self.state.location} | 时间: {self.state.time} | 共鸣度: {self.state.resonance}%")
            print(f"{'='*60}\n")

            # 1. 生成叙事情境
            narrative = self._generate_narrative_context()
            print(narrative)
            print()

            # 2. 生成选择点
            choices = self.generate_choices(narrative)

            # 3. 显示选项
            print("\n你的选择：")
            for choice in choices:
                print(f"  [{choice.id}] {choice.text}")

            # 4. 玩家选择（demo：自动选择第一个）
            print("\n[Demo模式：自动选择第一个选项]")
            selected = choices[0] if choices else None

            if not selected:
                print("没有可用选项，游戏结束。")
                break

            print(f"\n>>> 你选择了: [{selected.id}] {selected.text}\n")

            # 5. 生成响应
            response = self.generate_response(selected)
            print("\n" + "="*60)
            print("AI响应：")
            print("="*60)
            print(response)

            # 6. 更新状态
            self.update_state(selected, response)

            # 7. 检查结束条件
            if self.state.resonance >= 100:
                print("\n" + "="*60)
                print("⚠️ 共鸣度达到100%，你已无法脱身...")
                print("【坏结局】")
                print("="*60)
                break

            if self.state.flags.get("逃出成功"):
                print("\n" + "="*60)
                print("✅ 你成功逃出了这个诡异的地方！")
                print("【好结局】")
                print("="*60)
                break

            # Demo：限制回合数
            if turn >= max_turns:
                print("\n[Demo限制：已达到最大回合数]")
                break

            input("\n按回车键继续...")

        print("\n游戏结束。感谢体验！")

    def _generate_narrative_context(self) -> str:
        """生成当前的叙事情境"""
        # 简化版：基于当前状态生成情境描述
        return f"你正在{self.state.location}，时间是{self.state.time}。空气中弥漫着诡异的气息..."


def main():
    parser = argparse.ArgumentParser(
        description="Ghost Story Factory - 交互式游戏引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 运行武汉的游戏
    python game_engine.py --city 武汉 \\
        --gdd deliverables/程序-武汉/武汉_gdd.json \\
        --lore deliverables/程序-武汉/武汉_lore_v2.json
        """
    )

    parser.add_argument("--city", type=str, required=True, help="城市名称")
    parser.add_argument("--gdd", type=str, required=True, help="GDD文件路径（JSON或MD）")
    parser.add_argument("--lore", type=str, required=True, help="Lore v2文件路径（JSON或MD）")

    args = parser.parse_args()

    # 运行游戏
    engine = GameEngine(
        city=args.city,
        gdd_path=args.gdd,
        lore_path=args.lore
    )
    engine.run()


if __name__ == "__main__":
    main()

