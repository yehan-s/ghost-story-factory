"""游戏主循环

整合所有引擎组件，实现完整的游戏循环：
1. 生成当前场景的选择点
2. 显示给玩家并等待输入
3. 验证选择合法性
4. 应用后果并更新状态
5. 生成运行时响应
6. 检查结局条件
7. 重复或结束
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import time

from .state import GameState
from .choices import Choice, ChoiceType, ChoicePointsGenerator
from .response import RuntimeResponseGenerator


class GameEngine:
    """游戏引擎

    管理游戏的主循环，协调所有子系统
    """

    def __init__(
        self,
        city: str,
        gdd_path: Optional[str] = None,
        lore_path: Optional[str] = None,
        save_dir: str = "saves"
    ):
        """初始化游戏引擎

        Args:
            city: 城市名称
            gdd_path: GDD 文件路径（可选）
            lore_path: Lore v2 文件路径（可选）
            save_dir: 存档目录
        """
        self.city = city
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

        # 加载故事资源
        self.gdd = self._load_gdd(gdd_path)
        self.lore = self._load_lore(lore_path)

        # 初始化游戏状态
        self.state = GameState()

        # 初始化生成器
        self.choice_generator = ChoicePointsGenerator(self.gdd, self.lore)
        self.response_generator = RuntimeResponseGenerator(self.gdd, self.lore)

        # 运行时变量
        self.is_running = False
        self.last_action_time = time.time()
        self.current_choices: List[Choice] = []

    def _load_gdd(self, gdd_path: Optional[str]) -> str:
        """加载 GDD 文件

        Args:
            gdd_path: GDD 文件路径，如果为 None 则自动查找

        Returns:
            str: GDD 内容
        """
        if gdd_path and Path(gdd_path).exists():
            with open(gdd_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 自动查找：examples/{city}/{city}_GDD.md
        auto_path = Path(f"examples/{self.city}/{self.city}_GDD.md")
        if auto_path.exists():
            with open(auto_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 查找 deliverables
        deliverable_path = Path(f"deliverables/程序-{self.city}/{self.city}_GDD.md")
        if deliverable_path.exists():
            with open(deliverable_path, 'r', encoding='utf-8') as f:
                return f.read()

        raise FileNotFoundError(
            f"无法找到 {self.city} 的 GDD 文件。\n"
            f"请提供 gdd_path 参数，或确保文件位于 examples/{self.city}/ 或 deliverables/程序-{self.city}/ 目录下。"
        )

    def _load_lore(self, lore_path: Optional[str]) -> str:
        """加载 Lore v2 文件

        Args:
            lore_path: Lore 文件路径，如果为 None 则自动查找

        Returns:
            str: Lore 内容
        """
        if lore_path and Path(lore_path).exists():
            with open(lore_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 自动查找：examples/{city}/{city}_lore_v2.md
        auto_path = Path(f"examples/{self.city}/{self.city}_lore_v2.md")
        if auto_path.exists():
            with open(auto_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 查找 JSON 格式
        json_path = Path(f"examples/{self.city}/{self.city}_lore.json")
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                lore_data = json.load(f)
                # 转换为文本格式
                return json.dumps(lore_data, ensure_ascii=False, indent=2)

        raise FileNotFoundError(
            f"无法找到 {self.city} 的 Lore 文件。\n"
            f"请提供 lore_path 参数，或确保文件位于 examples/{self.city}/ 目录下。"
        )

    def run(self) -> str:
        """主游戏循环

        Returns:
            str: 游戏结束原因（结局类型或退出原因）
        """
        self.is_running = True

        print(f"\n🎭 开始游戏：{self.city}\n")
        print(self._get_title_screen())

        # 显示初始状态
        self._display_state()

        # 显示开场叙事
        opening_narrative = self._get_opening_narrative()
        print(f"\n{opening_narrative}\n")

        # 主循环
        while self.is_running and not self._check_ending():
            try:
                # 1. 生成当前场景的选择点
                self.current_choices = self.choice_generator.generate_choices(
                    self.state.current_scene,
                    self.state
                )

                # 2. 显示选择点并获取玩家输入
                selected_choice = self._prompt_player(self.current_choices)

                if selected_choice is None:
                    # 玩家选择退出
                    self.is_running = False
                    return "player_quit"

                # 3. 生成响应并更新状态
                response = self.response_generator.generate_response(
                    selected_choice,
                    self.state,
                    apply_consequences=True
                )

                # 4. 显示响应
                self._display_response(response)

                # 5. 显示当前状态
                self._display_state()

                # 6. 检查是否需要切换场景
                self._check_scene_transition()

                # 更新最后行动时间
                self.last_action_time = time.time()

            except KeyboardInterrupt:
                print("\n\n⚠️  游戏中断")
                self._offer_save()
                self.is_running = False
                return "interrupted"

            except Exception as e:
                print(f"\n❌ 发生错误：{e}")
                self._offer_save()
                self.is_running = False
                return "error"

        # 7. 显示结局
        ending_type = self._show_ending()
        return ending_type

    def _get_title_screen(self) -> str:
        """获取标题画面"""
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║                    🎭 {self.city}·灵异故事                        ║
║                  交互式恐怖游戏体验                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

    def _get_opening_narrative(self) -> str:
        """获取开场叙事"""
        # 从 GDD 中提取开场描述，或生成默认开场
        return f"""
**场景 1：开始**

今夜，你将作为 {self.city} 的一名夜班人员，
经历一段无法忘记的经历...

时间：00:00
地点：{self.state.current_scene}
"""

    def _display_state(self) -> None:
        """显示当前游戏状态"""
        print("\n" + "━" * 70)

        # 状态条
        pr_bar = self._render_bar(self.state.PR, 100, 20)
        gr_bar = self._render_bar(self.state.GR, 100, 20)
        wf_bar = self._render_bar(self.state.WF, 10, 10)

        print(f"📊 个人共鸣度 {pr_bar} {self.state.PR}/100")
        print(f"🌍 全局共鸣度 {gr_bar} {self.state.GR}/100")
        print(f"⏱️  世界疲劳值 {wf_bar} {self.state.WF}/10")

        print(f"\n⏰ 时间: {self.state.timestamp}  |  📍 场景: {self.state.current_scene}")

        if self.state.inventory:
            print(f"🎒 道具: {', '.join(self.state.inventory)}")

        print("━" * 70 + "\n")

    def _render_bar(self, value: int, max_value: int, bar_length: int) -> str:
        """渲染进度条"""
        filled = int(value / max_value * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"[{bar}]"

    def _prompt_player(self, choices: List[Choice]) -> Optional[Choice]:
        """显示选择列表并获取玩家输入

        Args:
            choices: 选择点列表

        Returns:
            Choice: 玩家选择的选项，如果选择退出则返回 None
        """
        print("\n【抉择点】请选择你的行动：\n")

        # 显示选项
        available_choices = []
        for i, choice in enumerate(choices, 1):
            if choice.is_available(self.state):
                available_choices.append(choice)
                display_text = choice.get_display_text(self.state)

                # 添加后果预览
                consequence_preview = choice.get_consequence_preview()
                if consequence_preview:
                    display_text += f"\n     └─ 后果：{consequence_preview}"

                print(f"  {i}. {display_text}\n")
            else:
                # 显示不可用的选项（灰色）
                print(f"  {i}. 🔒 {choice.choice_text} (条件不满足)\n")

        # 添加系统选项
        print(f"  {len(choices) + 1}. 💾 保存进度")
        print(f"  {len(choices) + 2}. 🚪 退出游戏\n")

        print("━" * 70)

        # 获取输入
        while True:
            try:
                user_input = input(f"\n请输入选项编号 [1-{len(choices) + 2}]: ").strip()

                if not user_input:
                    continue

                choice_num = int(user_input)

                # 系统选项
                if choice_num == len(choices) + 1:
                    # 保存进度
                    self.save_game()
                    print("✅ 进度已保存\n")
                    continue

                elif choice_num == len(choices) + 2:
                    # 退出游戏
                    confirm = input("确定要退出吗？(y/n): ").strip().lower()
                    if confirm == 'y':
                        return None
                    continue

                # 选择点
                if 1 <= choice_num <= len(choices):
                    selected = choices[choice_num - 1]

                    # 检查是否可用
                    if selected.is_available(self.state):
                        return selected
                    else:
                        print("❌ 该选项当前不可用（条件不满足）")
                        continue
                else:
                    print(f"❌ 请输入 1-{len(choices) + 2} 之间的数字")

            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ 输入错误：{e}")

    def _display_response(self, response: str) -> None:
        """显示叙事响应

        Args:
            response: 响应文本
        """
        print("\n" + "━" * 70 + "\n")
        print(response)
        print("\n" + "━" * 70)

    def _check_scene_transition(self) -> None:
        """检查是否需要切换场景"""
        # TODO: 根据 GDD 定义的场景转换规则判断
        # 目前简化版：由选择点的后果直接控制场景切换
        pass

    def _check_ending(self) -> bool:
        """检查是否达成结局

        Returns:
            bool: 是否已达成结局条件
        """
        # TODO: 根据 GDD 定义的结局条件判断
        # 简化版实现

        # 条件 1: 达到最终场景
        if self.state.current_scene == "S6" or self.state.current_scene.startswith("结局"):
            return True

        # 条件 2: 超时（游戏内时间超过 06:00）
        if self._parse_time(self.state.timestamp) >= self._parse_time("06:00"):
            return True

        # 条件 3: 共鸣度达到 100（失衡状态）
        if self.state.PR >= 100:
            return True

        return False

    def _parse_time(self, time_str: str) -> int:
        """解析时间字符串为分钟数

        Args:
            time_str: 时间字符串，如 "03:45"

        Returns:
            int: 总分钟数
        """
        try:
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        except:
            return 0

    def _show_ending(self) -> str:
        """显示结局

        Returns:
            str: 结局类型
        """
        print("\n\n" + "=" * 70)
        print("                          【 结 局 】")
        print("=" * 70 + "\n")

        # 判断结局类型
        ending_type = self._determine_ending_type()

        # 显示结局文本
        ending_text = self._get_ending_text(ending_type)
        print(ending_text)

        # 显示统计信息
        self._show_statistics()

        print("\n" + "=" * 70)
        print("                      感谢游玩！")
        print("=" * 70 + "\n")

        return ending_type

    def _determine_ending_type(self) -> str:
        """判断结局类型

        Returns:
            str: 结局类型标识
        """
        # TODO: 根据 GDD 定义的结局条件判断
        # 简化版实现

        # 检查后果树中的关键选择
        has_core = "失魂核心" in self.state.inventory
        has_played_audio = "录音_已播放" in self.state.flags

        if has_core and has_played_audio:
            return "ending_completion"  # 补完结局
        elif not has_core and has_played_audio:
            return "ending_observer"    # 旁观结局
        elif self.state.PR >= 100:
            return "ending_lost"        # 迷失结局
        elif self._parse_time(self.state.timestamp) >= self._parse_time("06:00"):
            return "ending_timeout"     # 超时结局
        else:
            return "ending_unknown"     # 未知结局

    def _get_ending_text(self, ending_type: str) -> str:
        """获取结局文本

        Args:
            ending_type: 结局类型

        Returns:
            str: 结局文本
        """
        endings = {
            "ending_completion": """
**【补完结局】**

你持有失魂核心，播放了录音。
那些失魂者...终于找到了归宿。

这座城市的裂缝，被你修补了。
至少，暂时如此。
""",
            "ending_observer": """
**【旁观结局】**

你播放了录音，但没有核心。
你只是一个见证者。

那些失魂者仍在游荡，
而你...活了下来。
""",
            "ending_lost": """
**【迷失结局】**

共鸣度达到 100%。
你的意识...溶解了。

你成为了第九个失魂者。
""",
            "ending_timeout": """
**【超时结局】**

天亮了。
早班员工到来，你离开了这里。

但你知道，今晚发生的一切，
都是真的。
""",
            "ending_unknown": """
**【未知结局】**

你的故事，以一种意想不到的方式结束了。
"""
        }

        return endings.get(ending_type, endings["ending_unknown"])

    def _show_statistics(self) -> None:
        """显示统计信息"""
        print("\n**【统计数据】**\n")
        print(f"- 最终 PR：{self.state.PR}/100")
        print(f"- 最终 GR：{self.state.GR}/100")
        print(f"- 最终 WF：{self.state.WF}/10")
        print(f"- 游戏时长：{self.state.timestamp}")
        print(f"- 做出选择：{len(self.state.consequence_tree)} 次")
        print(f"- 获得道具：{len(self.state.inventory)} 个")

    def save_game(self, filename: Optional[str] = None) -> str:
        """保存游戏进度

        Args:
            filename: 存档文件名（可选）

        Returns:
            str: 存档文件路径
        """
        if filename is None:
            # 自动生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.city}_{self.state.current_scene}_{timestamp}.save"

        filepath = self.save_dir / filename
        self.state.save(str(filepath))

        return str(filepath)

    def load_game(self, filepath: str) -> None:
        """加载游戏进度

        Args:
            filepath: 存档文件路径
        """
        self.state = GameState.load(filepath)
        print(f"✅ 已加载存档：{filepath}")

    def _offer_save(self) -> None:
        """提示玩家是否保存进度"""
        try:
            save = input("\n是否保存当前进度？(y/n): ").strip().lower()
            if save == 'y':
                filepath = self.save_game()
                print(f"✅ 进度已保存至：{filepath}")
        except:
            pass


def main():
    """命令行入口（用于测试）"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m ghost_story_factory.engine.game_loop <城市名>")
        print("示例: python -m ghost_story_factory.engine.game_loop 杭州")
        sys.exit(1)

    city = sys.argv[1]

    try:
        engine = GameEngine(city)
        engine.run()
    except FileNotFoundError as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n游戏已中断")
        sys.exit(0)


if __name__ == "__main__":
    main()

