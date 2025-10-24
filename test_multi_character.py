#!/usr/bin/env python3
"""
快速测试多角色功能

测试模式：
- 只生成前2个角色
- 对话树深度降到 5 层（正常是 20 层）
- 主线深度降到 3 层（正常是 15 层）

预计时间：5-10 分钟
"""

import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有 python-dotenv，手动加载 .env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()

from ghost_story_factory.pregenerator.synopsis_generator import StorySynopsis
from ghost_story_factory.pregenerator.story_generator import StoryGeneratorWithRetry


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          🧪 多角色功能快速测试 (MVP)                            ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print("测试配置：")
    print("  • 只生成前 2 个角色")
    print("  • 对话树深度：5 层（正常 20 层）")
    print("  • 主线深度：3 层（正常 15 层）")
    print("  • 预计时间：5-10 分钟")
    print()

    # 使用杭州作为测试城市
    city = "杭州"

    # 创建一个简单的故事简介
    synopsis = StorySynopsis(
        title="断桥残血",
        synopsis="午夜时分，西湖断桥上出现白衣女子的身影...",
        protagonist="外卖骑手",
        location="西湖断桥",
        estimated_duration=20
    )

    print(f"测试故事：{synopsis.title}")
    print(f"测试城市：{city}")
    print()

    # 创建生成器（启用测试模式）
    generator = StoryGeneratorWithRetry(
        city=city,
        synopsis=synopsis,
        test_mode=True  # 🔥 启用测试模式
    )

    # 使用现有的杭州文档
    gdd_path = "examples/hangzhou/杭州_GDD.md"
    lore_path = "examples/hangzhou/杭州_lore_v2.md"
    main_story_path = "examples/hangzhou/杭州_story.md"

    print("按 Enter 开始测试...")
    input()

    try:
        result = generator.generate_full_story(
            gdd_path=gdd_path,
            lore_path=lore_path,
            main_story_path=main_story_path
        )

        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║          ✅ 测试成功！                                           ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        print("验证结果：")
        print(f"  ✅ 成功提取多个角色：{len(result['characters'])} 个")
        for char in result['characters']:
            print(f"     - {char['name']}")
        print(f"  ✅ 成功生成对话树")
        print(f"  ✅ 成功保存到数据库（ID: {result['story_id']}）")
        print()
        print("现在可以运行游戏验证角色选择功能：")
        print("  ./start_pregenerated_game.sh")

    except Exception as e:
        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║          ❌ 测试失败                                             ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        print(f"错误信息：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

