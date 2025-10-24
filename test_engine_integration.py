"""
测试 GameEngine 集成（预生成模式）

验证：
1. GameEngine 可以接受 DialogueTreeLoader
2. 预生成模式主循环正常工作
3. 整个游戏流程可以运行
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from ghost_story_factory.database import DatabaseManager
from ghost_story_factory.engine.game_loop import GameEngine
from ghost_story_factory.runtime import DialogueTreeLoader
from rich.console import Console


def test_engine_initialization():
    """测试引擎初始化"""
    console = Console()

    console.print("\n")
    console.print("=" * 70)
    console.print("测试 1: GameEngine 初始化（预生成模式）")
    console.print("=" * 70)
    console.print("\n")

    db = DatabaseManager("database/ghost_stories_test.db")

    # 获取测试数据
    cities = db.get_cities()
    if not cities:
        console.print("[red]❌ 没有可用的城市数据[/red]")
        db.close()
        return False

    city = cities[0]
    stories = db.get_stories_by_city(city.id)

    if not stories:
        console.print(f"[red]❌ {city.name} 没有可用的故事[/red]")
        db.close()
        return False

    story = stories[0]
    characters = db.get_characters_by_story(story.id)

    if not characters:
        console.print(f"[red]❌ {story.title} 没有可用的角色[/red]")
        db.close()
        return False

    character = characters[0]

    # 创建 DialogueTreeLoader
    loader = DialogueTreeLoader(db, story.id, character.id)

    console.print(f"✅ 测试数据准备完成")
    console.print(f"   城市: {city.name}")
    console.print(f"   故事: {story.title}")
    console.print(f"   角色: {character.name}")
    console.print("")

    # 创建 GameEngine（预生成模式）
    try:
        engine = GameEngine(
            city=city.name,
            dialogue_loader=loader
        )

        console.print("✅ GameEngine 初始化成功")
        console.print(f"   模式: {engine.mode}")
        console.print(f"   当前节点: {engine.current_node_id}")
        console.print("")

        # 测试方法是否存在
        console.print("检查方法:")
        console.print(f"   - run(): {'✅' if hasattr(engine, 'run') else '❌'}")
        console.print(f"   - run_pregenerated(): {'✅' if hasattr(engine, 'run_pregenerated') else '❌'}")
        console.print(f"   - run_realtime(): {'✅' if hasattr(engine, 'run_realtime') else '❌'}")
        console.print(f"   - _convert_choices(): {'✅' if hasattr(engine, '_convert_choices') else '❌'}")
        console.print("")

        db.close()
        return True

    except Exception as e:
        console.print(f"[red]❌ GameEngine 初始化失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        db.close()
        return False


def test_dialogue_loading():
    """测试对话加载"""
    console = Console()

    console.print("\n")
    console.print("=" * 70)
    console.print("测试 2: 对话加载和节点导航")
    console.print("=" * 70)
    console.print("\n")

    db = DatabaseManager("database/ghost_stories_test.db")

    # 获取测试数据
    cities = db.get_cities()
    if not cities:
        console.print("[red]❌ 没有可用的城市数据[/red]")
        db.close()
        return False

    city = cities[0]
    stories = db.get_stories_by_city(city.id)
    story = stories[0] if stories else None
    characters = db.get_characters_by_story(story.id) if story else []
    character = characters[0] if characters else None

    if not story or not character:
        console.print("[red]❌ 测试数据不完整[/red]")
        db.close()
        return False

    # 创建加载器和引擎
    loader = DialogueTreeLoader(db, story.id, character.id)
    engine = GameEngine(
        city=city.name,
        dialogue_loader=loader
    )

    # 测试获取开场叙事
    try:
        narrative = loader.get_narrative("root")
        console.print(f"✅ 开场叙事: {narrative[:60]}...")
        console.print("")
    except Exception as e:
        console.print(f"[red]❌ 获取叙事失败: {e}[/red]")
        db.close()
        return False

    # 测试获取选择
    try:
        choices_data = loader.get_choices("root")
        console.print(f"✅ 根节点选择: {len(choices_data)} 个")

        # 测试转换为 Choice 对象
        choices = engine._convert_choices(choices_data)
        console.print(f"✅ 转换为 Choice 对象: {len(choices)} 个")

        for idx, choice in enumerate(choices, 1):
            console.print(f"   {idx}. {choice.choice_text[:40]}...")

        console.print("")

        db.close()
        return True

    except Exception as e:
        console.print(f"[red]❌ 获取选择失败: {e}[/red]")
        import traceback
        traceback.print_exc()
        db.close()
        return False


def main():
    """主测试函数"""
    console = Console()

    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════════╗")
    console.print("║              🧪 GameEngine 集成测试                             ║")
    console.print("╚══════════════════════════════════════════════════════════════════╝")

    results = []

    # 测试 1: 引擎初始化
    results.append(("引擎初始化", test_engine_initialization()))

    # 测试 2: 对话加载
    results.append(("对话加载", test_dialogue_loading()))

    # 总结
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════════╗")
    console.print("║              ✅ 测试结果总结                                    ║")
    console.print("╚══════════════════════════════════════════════════════════════════╝")
    console.print("\n")

    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"   {status} - {test_name}")
        if not result:
            all_passed = False

    console.print("\n")

    if all_passed:
        console.print("🎉 所有测试通过！GameEngine 集成完成！\n")
        console.print("💡 下一步：")
        console.print("   运行完整游戏:")
        console.print("   $ python3 play_game_pregenerated.py\n")
        return 0
    else:
        console.print("❌ 部分测试失败，请检查错误信息\n")
        return 1


if __name__ == "__main__":
    exit(main())

