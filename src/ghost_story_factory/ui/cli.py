"""命令行界面 (CLI UI)

使用 Rich 库美化命令行输出：
- Markdown 渲染
- 彩色高亮（选择点、系统提示、危险警告）
- 进度条（PR/GR/WF 可视化）
- 表格显示（选择列表）
- 交互式选择菜单
"""

from typing import List, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    # 回退占位，避免类型注解在无 rich 环境下触发 NameError
    Console = Markdown = Panel = Table = Progress = BarColumn = TextColumn = Prompt = Confirm = Layout = object  # type: ignore
    Text = object  # type: ignore
    RICH_AVAILABLE = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ghost_story_factory.engine.state import GameState
from ghost_story_factory.engine.choices import Choice


class GameCLI:
    """命令行界面

    提供美化的游戏界面显示和交互功能
    """

    def __init__(self, use_rich: bool = True):
        """初始化 CLI

        Args:
            use_rich: 是否使用 Rich 库美化（如果可用）
        """
        self.use_rich = use_rich and RICH_AVAILABLE

        if self.use_rich:
            self.console = Console()
        else:
            self.console = None

    def display_title(self, city: str, protagonist: Optional[str] = None) -> None:
        """显示标题画面

        Args:
            city: 城市名称
            protagonist: 主角名称（可选）
        """
        title = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    🎭 {city}·灵异故事                            ║
"""
        if protagonist:
            title += f"║                  主角：{protagonist}                              ║\n"

        title += "║                  交互式恐怖游戏体验                              ║\n"
        title += "╚══════════════════════════════════════════════════════════════════╝"

        if self.use_rich:
            self.console.print(title, style="bold cyan")
        else:
            print(title)

    def display_state(self, state: GameState) -> None:
        """显示游戏状态

        Args:
            state: 游戏状态
        """
        if self.use_rich:
            self._display_state_rich(state)
        else:
            self._display_state_plain(state)

    def _display_state_rich(self, state: GameState) -> None:
        """使用 Rich 显示状态"""
        # 创建状态表格
        table = Table(show_header=False, box=None, padding=(0, 1))

        # PR 进度条
        pr_bar = self._create_progress_bar(state.PR, 100, 20, "green", "red")
        table.add_row("📊 个人共鸣度", pr_bar, f"{state.PR}/100")

        # GR 进度条
        gr_bar = self._create_progress_bar(state.GR, 100, 20, "blue", "yellow")
        table.add_row("🌍 全局共鸣度", gr_bar, f"{state.GR}/100")

        # WF 进度条
        wf_bar = self._create_progress_bar(state.WF, 10, 10, "cyan", "magenta")
        table.add_row("⏱️  世界疲劳值", wf_bar, f"{state.WF}/10")

        self.console.print()
        self.console.print(table)

        # 时间和场景
        info_text = Text()
        info_text.append("⏰ 时间: ", style="bold")
        info_text.append(state.timestamp, style="cyan")
        info_text.append("  |  ", style="dim")
        info_text.append("📍 场景: ", style="bold")
        info_text.append(state.current_scene, style="green")

        self.console.print(info_text)

        # 道具
        if state.inventory:
            items_text = Text()
            items_text.append("🎒 道具: ", style="bold")
            items_text.append(", ".join(state.inventory), style="yellow")
            self.console.print(items_text)

        self.console.print()

    def _display_state_plain(self, state: GameState) -> None:
        """使用纯文本显示状态"""
        print("\n" + "━" * 70)

        # 状态条
        pr_bar = self._render_bar_plain(state.PR, 100, 20)
        gr_bar = self._render_bar_plain(state.GR, 100, 20)
        wf_bar = self._render_bar_plain(state.WF, 10, 10)

        print(f"📊 个人共鸣度 {pr_bar} {state.PR}/100")
        print(f"🌍 全局共鸣度 {gr_bar} {state.GR}/100")
        print(f"⏱️  世界疲劳值 {wf_bar} {state.WF}/10")

        print(f"\n⏰ 时间: {state.timestamp}  |  📍 场景: {state.current_scene}")

        if state.inventory:
            print(f"🎒 道具: {', '.join(state.inventory)}")

        print("━" * 70 + "\n")

    def _create_progress_bar(
        self,
        value: int,
        max_value: int,
        bar_length: int,
        color_low: str,
        color_high: str
    ) -> Text:
        """创建进度条（Rich 版本）

        Args:
            value: 当前值
            max_value: 最大值
            bar_length: 进度条长度
            color_low: 低值颜色
            color_high: 高值颜色

        Returns:
            Text: Rich Text 对象
        """
        filled = int(value / max_value * bar_length)

        # 根据值选择颜色
        ratio = value / max_value
        if ratio < 0.3:
            color = color_low
        elif ratio < 0.7:
            color = "yellow"
        else:
            color = color_high

        bar = Text()
        bar.append("[", style="dim")
        bar.append("█" * filled, style=color)
        bar.append("░" * (bar_length - filled), style="dim")
        bar.append("]", style="dim")

        return bar

    def _render_bar_plain(self, value: int, max_value: int, bar_length: int) -> str:
        """渲染进度条（纯文本版本）"""
        filled = int(value / max_value * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"[{bar}]"

    def display_narrative(self, text: str, style: str = "green") -> None:
        """显示叙事文本

        Args:
            text: 叙事文本（支持 Markdown）
            style: 样式（仅 Rich 模式）
        """
        if self.use_rich:
            # 尝试渲染为 Markdown
            try:
                md = Markdown(text)
                panel = Panel(
                    md,
                    border_style=style,
                    padding=(1, 2)
                )
                self.console.print(panel)
            except:
                # 如果 Markdown 解析失败，直接显示文本
                self.console.print(text, style=style)
        else:
            print("\n" + "━" * 70)
            print(text)
            print("━" * 70 + "\n")

    def display_choices(
        self,
        choices: List[Choice],
        game_state: GameState,
        show_consequences: bool = True
    ) -> None:
        """显示选择列表

        Args:
            choices: 选择列表
            game_state: 游戏状态
            show_consequences: 是否显示后果预览
        """
        if self.use_rich:
            self._display_choices_rich(choices, game_state, show_consequences)
        else:
            self._display_choices_plain(choices, game_state, show_consequences)

    def _display_choices_rich(
        self,
        choices: List[Choice],
        game_state: GameState,
        show_consequences: bool
    ) -> None:
        """使用 Rich 显示选择列表"""
        self.console.print("\n【抉择点】请选择你的行动：\n", style="bold yellow")

        for i, choice in enumerate(choices, 1):
            is_available = choice.is_available(game_state)

            # 构建选项文本
            text = Text()
            text.append(f"  {i}. ", style="bold")

            if is_available:
                # 添加图标
                icon = self._get_choice_icon(choice.choice_type.value)
                text.append(icon + " ", style="bold")
                text.append(choice.choice_text, style="white")

                # 添加标签
                if choice.tags:
                    text.append(f" [{', '.join(choice.tags)}]", style="dim cyan")
            else:
                text.append("🔒 ", style="red")
                text.append(choice.choice_text, style="dim")
                text.append(" (条件不满足)", style="red")

            self.console.print(text)

            # 显示后果预览
            if is_available and show_consequences:
                preview = choice.get_consequence_preview()
                if preview:
                    self.console.print(f"     └─ 后果：{preview}", style="dim yellow")

            self.console.print()

        # 系统选项
        self.console.print(f"  {len(choices) + 1}. 💾 保存进度", style="cyan")
        self.console.print(f"  {len(choices) + 2}. 🚪 退出游戏\n", style="red")

    def _display_choices_plain(
        self,
        choices: List[Choice],
        game_state: GameState,
        show_consequences: bool
    ) -> None:
        """使用纯文本显示选择列表"""
        print("\n【抉择点】请选择你的行动：\n")

        for i, choice in enumerate(choices, 1):
            is_available = choice.is_available(game_state)

            if is_available:
                icon = self._get_choice_icon(choice.choice_type.value)
                display = f"  {i}. {icon} {choice.choice_text}"

                if choice.tags:
                    display += f" [{', '.join(choice.tags)}]"

                print(display)

                # 显示后果预览
                if show_consequences:
                    preview = choice.get_consequence_preview()
                    if preview:
                        print(f"     └─ 后果：{preview}")
            else:
                print(f"  {i}. 🔒 {choice.choice_text} (条件不满足)")

            print()

        # 系统选项
        print(f"  {len(choices) + 1}. 💾 保存进度")
        print(f"  {len(choices) + 2}. 🚪 退出游戏\n")

    def _get_choice_icon(self, choice_type: str) -> str:
        """获取选择类型的图标"""
        icons = {
            "micro": "💬",
            "normal": "💼",
            "critical": "⚠️"
        }
        return icons.get(choice_type, "•")

    def prompt_choice(
        self,
        choices: List[Choice],
        allow_save: bool = True,
        allow_quit: bool = True
    ) -> Optional[int]:
        """提示玩家输入选择

        Args:
            choices: 选择列表
            allow_save: 是否允许保存
            allow_quit: 是否允许退出

        Returns:
            int: 选择的索引（0-based），特殊值：-1=保存，-2=退出，None=无效输入
        """
        max_num = len(choices)
        if allow_save:
            max_num += 1
        if allow_quit:
            max_num += 1

        print("━" * 70)

        while True:
            try:
                if self.use_rich:
                    user_input = Prompt.ask(
                        f"\n请输入选项编号",
                        choices=[str(i) for i in range(1, max_num + 1)]
                    )
                else:
                    user_input = input(f"\n请输入选项编号 [1-{max_num}]: ").strip()

                if not user_input:
                    continue

                choice_num = int(user_input)

                # 保存选项
                if allow_save and choice_num == len(choices) + 1:
                    return -1

                # 退出选项
                if allow_quit and choice_num == len(choices) + 2:
                    return -2

                # 普通选择
                if 1 <= choice_num <= len(choices):
                    return choice_num - 1
                else:
                    self._print_error(f"请输入 1-{max_num} 之间的数字")

            except ValueError:
                self._print_error("请输入有效的数字")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self._print_error(f"输入错误：{e}")

    def confirm(self, message: str, default: bool = False) -> bool:
        """显示确认对话框

        Args:
            message: 提示消息
            default: 默认值

        Returns:
            bool: 用户选择
        """
        if self.use_rich:
            return Confirm.ask(message, default=default)
        else:
            default_str = "y" if default else "n"
            response = input(f"{message} (y/n, 默认 {default_str}): ").strip().lower()
            if not response:
                return default
            return response == 'y'

    def display_message(
        self,
        message: str,
        style: str = "info"
    ) -> None:
        """显示消息

        Args:
            message: 消息内容
            style: 消息样式（info/success/warning/error）
        """
        if self.use_rich:
            style_map = {
                "info": "blue",
                "success": "green",
                "warning": "yellow",
                "error": "red"
            }
            self.console.print(message, style=style_map.get(style, "white"))
        else:
            icon_map = {
                "info": "ℹ️ ",
                "success": "✅",
                "warning": "⚠️ ",
                "error": "❌"
            }
            print(f"{icon_map.get(style, '')} {message}")

    def _print_error(self, message: str) -> None:
        """打印错误消息"""
        self.display_message(message, style="error")

    def display_separator(self, char: str = "━", length: int = 70) -> None:
        """显示分隔线"""
        if self.use_rich:
            self.console.print(char * length, style="dim")
        else:
            print(char * length)

    def clear_screen(self) -> None:
        """清屏"""
        if self.use_rich:
            self.console.clear()
        else:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')


# 工具函数

def create_cli(use_rich: bool = True) -> GameCLI:
    """创建 CLI 实例

    Args:
        use_rich: 是否使用 Rich 库（如果可用）

    Returns:
        GameCLI: CLI 实例
    """
    return GameCLI(use_rich=use_rich)


def check_rich_available() -> bool:
    """检查 Rich 库是否可用"""
    return RICH_AVAILABLE

