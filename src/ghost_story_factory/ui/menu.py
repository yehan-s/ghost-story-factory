"""
主菜单系统

负责显示主菜单并处理用户选择
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional, Tuple

from ..database import DatabaseManager, City, Story, Character
from ..pregenerator import SynopsisGenerator, StorySynopsis
from ..pregenerator.story_generator import StoryGeneratorWithRetry


class MenuSystem:
    """主菜单系统"""

    def __init__(self, db: DatabaseManager):
        """
        初始化菜单系统

        Args:
            db: 数据库管理器
        """
        self.db = db
        self.console = Console()

    def show_main_menu(self) -> str:
        """
        显示主菜单

        Returns:
            用户选择（'1', '2', 'q'）
        """
        self.console.clear()
        self.console.print("\n")
        self.console.print("╔══════════════════════════════════════════════════════════════════╗", style="bold cyan")
        self.console.print("║          欢迎来到 Ghost Story Factory！                         ║", style="bold cyan")
        self.console.print("╚══════════════════════════════════════════════════════════════════╝", style="bold cyan")
        self.console.print("\n")

        self.console.print("请选择：")
        self.console.print("  [bold green]1.[/bold green] 📖 选择故事（从已生成的故事中游玩）")
        self.console.print("  [bold yellow]2.[/bold yellow] ✨ 生成故事（创建新的故事）")
        self.console.print("  [bold red]q.[/bold red] 🚪 退出")
        self.console.print("\n")

        choice = self.console.input("输入选项 [1/2/q]: ").strip().lower()
        return choice

    def select_story_flow(self) -> Optional[Tuple[Story, Character]]:
        """
        故事选择流程：城市 → 故事 → 角色

        Returns:
            (故事, 角色) 或 None
        """
        # 1. 选择城市
        city = self._select_city()
        if not city:
            return None

        # 2. 选择故事
        story = self._select_story(city)
        if not story:
            return None

        # 3. 选择角色
        character = self._select_character(story)
        if not character:
            return None

        return story, character

    def generate_story_flow(self) -> Optional[Story]:
        """
        故事生成流程：城市 → 简介 → 完整生成

        Returns:
            生成的故事 或 None
        """
        # 1. 输入城市
        city_name = self._input_city()
        if not city_name:
            return None

        # 2. 生成简介
        synopses = self._generate_synopses(city_name)
        if not synopses:
            return None

        # 3. 选择简介
        synopsis = self._select_synopsis(synopses)
        if not synopsis:
            return None

        # 4. 完整生成
        result = self._generate_full_story(city_name, synopsis)
        if not result:
            return None

        # 返回生成的故事
        return self.db.get_story_by_id(result['story_id'])

    def _select_city(self) -> Optional[City]:
        """选择城市"""
        self.console.clear()
        self.console.print("\n")
        self.console.print("═" * 70)
        self.console.print(" 📍 选择城市")
        self.console.print("═" * 70)
        self.console.print("\n")

        cities = self.db.get_cities()

        if not cities:
            self.console.print("[yellow]⚠️  数据库中还没有任何故事[/yellow]")
            self.console.print("[yellow]   请先选择「生成故事」创建新故事[/yellow]")
            self.console.print("\n")
            input("按 Enter 返回主菜单...")
            return None

        # 显示城市列表
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("编号", style="cyan", width=6)
        table.add_column("城市", style="green")
        table.add_column("故事数", style="yellow")

        for idx, city in enumerate(cities, 1):
            table.add_row(str(idx), city.name, f"{city.story_count} 个")

        self.console.print(table)
        self.console.print("\n")

        choice = self.console.input(f"输入城市编号 [1-{len(cities)}] 或 q 返回: ").strip()

        if choice.lower() == 'q':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(cities):
                return cities[idx]
        except ValueError:
            pass

        self.console.print("[red]❌ 无效选择[/red]")
        input("按 Enter 继续...")
        return self._select_city()

    def _select_story(self, city: City) -> Optional[Story]:
        """选择故事"""
        self.console.clear()
        self.console.print("\n")
        self.console.print("═" * 70)
        self.console.print(f" 📖 选择故事 - {city.name}")
        self.console.print("═" * 70)
        self.console.print("\n")

        stories = self.db.get_stories_by_city(city.id)

        if not stories:
            self.console.print(f"[yellow]⚠️  {city.name} 还没有故事[/yellow]")
            self.console.print("\n")
            input("按 Enter 返回...")
            return None

        # 显示故事列表
        for idx, story in enumerate(stories, 1):
            self.console.print(f"[bold cyan]{idx}.[/bold cyan] [bold]{story.title}[/bold]")
            self.console.print(f"   简介: {story.synopsis[:100]}...")
            self.console.print(f"   时长: {story.estimated_duration_minutes} 分钟 | 角色: {story.character_count} 个 | 节点: {story.total_nodes} 个")
            self.console.print("")

        choice = self.console.input(f"输入故事编号 [1-{len(stories)}] 或 q 返回: ").strip()

        if choice.lower() == 'q':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(stories):
                return stories[idx]
        except ValueError:
            pass

        self.console.print("[red]❌ 无效选择[/red]")
        input("按 Enter 继续...")
        return self._select_story(city)

    def _select_character(self, story: Story) -> Optional[Character]:
        """选择角色"""
        self.console.clear()
        self.console.print("\n")
        self.console.print("═" * 70)
        self.console.print(f" 👤 选择角色 - {story.title}")
        self.console.print("═" * 70)
        self.console.print("\n")

        characters = self.db.get_characters_by_story(story.id)

        # 显示角色列表
        for idx, char in enumerate(characters, 1):
            mark = "⭐ [主角线]" if char.is_protagonist else ""
            self.console.print(f"[bold cyan]{idx}.[/bold cyan] [bold]{char.name}[/bold] {mark}")
            if char.description:
                self.console.print(f"   {char.description}")
            self.console.print("")

        choice = self.console.input(f"输入角色编号 [1-{len(characters)}] 或 q 返回: ").strip()

        if choice.lower() == 'q':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(characters):
                return characters[idx]
        except ValueError:
            pass

        self.console.print("[red]❌ 无效选择[/red]")
        input("按 Enter 继续...")
        return self._select_character(story)

    def _input_city(self) -> Optional[str]:
        """输入城市名称"""
        self.console.clear()
        self.console.print("\n")
        self.console.print("═" * 70)
        self.console.print(" ✨ 生成新故事")
        self.console.print("═" * 70)
        self.console.print("\n")

        self.console.print("请输入城市名称（如：杭州、北京、上海）")
        self.console.print("\n")

        city_name = self.console.input("城市名称（或 q 返回）: ").strip()

        if city_name.lower() == 'q':
            return None

        if not city_name:
            self.console.print("[red]❌ 城市名称不能为空[/red]")
            input("按 Enter 继续...")
            return self._input_city()

        return city_name

    def _generate_synopses(self, city: str) -> Optional[list]:
        """生成故事简介"""
        self.console.print("\n")
        self.console.print(f"🤖 正在为「{city}」生成故事简介...")
        self.console.print("\n")

        generator = SynopsisGenerator(city)
        synopses = generator.generate_synopses(count=3)

        if not synopses:
            self.console.print("[red]❌ 简介生成失败[/red]")
            input("按 Enter 返回...")
            return None

        return synopses

    def _select_synopsis(self, synopses: list) -> Optional[StorySynopsis]:
        """选择故事简介"""
        self.console.print("\n")
        self.console.print("═" * 70)
        self.console.print(" AI 为你生成了以下故事简介：")
        self.console.print("═" * 70)
        self.console.print("\n")

        for idx, synopsis in enumerate(synopses, 1):
            panel = Panel(
                f"[bold]{synopsis.title}[/bold]\n\n{synopsis.synopsis}\n\n"
                f"主角：{synopsis.protagonist} | 场景：{synopsis.location} | 时长：{synopsis.estimated_duration}分钟",
                title=f"故事 {idx}",
                border_style="cyan"
            )
            self.console.print(panel)
            self.console.print("")

        choice = self.console.input(f"选择一个故事 [1-{len(synopses)}] 或 q 返回: ").strip()

        if choice.lower() == 'q':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(synopses):
                return synopses[idx]
        except ValueError:
            pass

        self.console.print("[red]❌ 无效选择[/red]")
        input("按 Enter 继续...")
        return self._select_synopsis(synopses)

    def _generate_full_story(self, city: str, synopsis: StorySynopsis) -> Optional[dict]:
        """完整生成故事"""
        generator = StoryGeneratorWithRetry(city, synopsis)

        try:
            result = generator.generate_full_story()
            return result
        except Exception as e:
            self.console.print(f"\n[red]❌ 生成失败：{e}[/red]\n")
            input("按 Enter 返回...")
            return None

