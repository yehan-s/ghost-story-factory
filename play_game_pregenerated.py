"""
游戏启动入口（预生成模式）

启动游戏主菜单，支持：
1. 选择故事（从数据库）
2. 生成故事（AI预生成）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from ghost_story_factory.database import DatabaseManager
from ghost_story_factory.ui.menu import MenuSystem
from ghost_story_factory.runtime import DialogueTreeLoader
from ghost_story_factory.engine.game_loop import GameEngine
from rich.console import Console


def _safe_input(prompt: str = "") -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def main():
    """主函数"""
    console = Console()

    # 显示欢迎信息
    console.clear()
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════════╗", style="bold cyan")
    console.print("║          🎮 Ghost Story Factory                                 ║", style="bold cyan")
    console.print("║          恐怖故事工厂 - 预生成模式                              ║", style="bold cyan")
    console.print("╚══════════════════════════════════════════════════════════════════╝", style="bold cyan")
    console.print("\n")

    _safe_input("按 Enter 开始游戏...")

    # 初始化数据库
    db = DatabaseManager()

    # 初始化菜单系统
    menu = MenuSystem(db)

    # 主循环
    while True:
        choice = menu.show_main_menu()

        if choice == '1':
            # 选择故事
            result = menu.select_story_flow()
            if result:
                story, character = result
                console.print(f"\n✅ 已选择：{story.title} - {character.name}\n")

                # 加载对话树
                loader = DialogueTreeLoader(db, story.id, character.id)

                # 获取城市名
                cities = db.get_cities()
                city_name = "未知城市"
                for city in cities:
                    if city.id == story.city_id:
                        city_name = city.name
                        break

                # 🎮 启动游戏引擎（预生成模式）
                console.print("\n🎮 启动游戏引擎...\n")

                try:
                    engine = GameEngine(
                        city=city_name,
                        dialogue_loader=loader
                    )

                    # 运行游戏
                    result = engine.run()
                    console.print(f"\n游戏结束：{result}")

                except Exception as e:
                    console.print(f"\n[red]❌ 游戏运行错误：{e}[/red]")
                    import traceback
                    traceback.print_exc()

                _safe_input("\n按 Enter 返回主菜单...")

        elif choice == '2':
            # 生成故事
            story = menu.generate_story_flow()
            if story:
                console.print(f"\n✅ 故事「{story.title}」已生成！\n")
                console.print("现在可以返回主菜单选择「选择故事」开始游玩")
                _safe_input("\n按 Enter 继续...")

        elif choice == 'q':
            console.print("\n再见！👋\n")
            break
        else:
            console.print("\n[red]❌ 无效选择，请重新输入[/red]\n")
            _safe_input("按 Enter 继续...")

    # 关闭数据库
    db.close()


if __name__ == "__main__":
    main()

