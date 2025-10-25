#!/usr/bin/env python3
"""
快速生成MVP故事 - 用于测试多角色功能

使用方法：
  python3 generate_mvp.py

配置：
  - 角色数量：2个（可通过 MAX_CHARACTERS 调整）
  - 对话树深度：5层（可通过 MAX_DEPTH 调整）
  - 主线深度：3层（可通过 MIN_MAIN_PATH 调整）
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


# ==================== 配置参数 ====================
# 你可以根据需要调整这些参数

MAX_CHARACTERS = 2      # 生成的角色数量（杭州总共8个，这里只生成前2个）
MAX_DEPTH = 5           # 对话树最大深度（正常20，测试用5）
MIN_MAIN_PATH = 3       # 主线最小深度（正常15，测试用3）

# 测试城市和故事
CITY = "杭州"
STORY_TITLE = "断桥残血-MVP测试"

# ==================================================


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          🚀 快速生成 MVP 故事                                    ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print("配置参数：")
    print(f"  城市：{CITY}")
    print(f"  故事：{STORY_TITLE}")
    print(f"  角色数量：{MAX_CHARACTERS} 个")
    print(f"  对话树深度：{MAX_DEPTH} 层")
    print(f"  主线深度：{MIN_MAIN_PATH} 层")
    print()
    print("预计时间：5-10 分钟")
    print("用途：测试多角色选择功能")
    print()

    # 检查环境变量
    if not os.getenv("KIMI_API_KEY"):
        print("❌ 错误：未设置 KIMI_API_KEY 环境变量")
        print("请确保 .env 文件存在并包含 KIMI_API_KEY")
        sys.exit(1)

    # MVP 测试使用快速模型（如果用户没有覆盖的话）
    if not os.getenv("KIMI_MODEL_RESPONSE"):
        os.environ["KIMI_MODEL_RESPONSE"] = "moonshot-v1-32k"
        print("ℹ️  使用快速模型 moonshot-v1-32k（测试模式）")
        print()

    # 创建故事简介
    synopsis = StorySynopsis(
        title=STORY_TITLE,
        synopsis="午夜时分，西湖断桥上出现白衣女子的身影，外卖骑手被卷入了一场超自然事件...",
        protagonist="外卖骑手",
        location="西湖断桥",
        estimated_duration=5  # MVP测试版，短时长
    )

    # 创建生成器（启用测试模式）
    generator = StoryGeneratorWithRetry(
        city=CITY,
        synopsis=synopsis,
        test_mode=True  # 🔥 启用测试模式
    )

    # 使用现有的杭州文档
    examples_dir = Path("examples/hangzhou")
    gdd_path = examples_dir / "杭州_GDD.md"
    lore_path = examples_dir / "杭州_lore_v2.md"
    main_story_path = examples_dir / "杭州_story.md"

    # 检查文件是否存在
    for path, name in [(gdd_path, "GDD"), (lore_path, "Lore"), (main_story_path, "Story")]:
        if not path.exists():
            print(f"❌ 错误：找不到 {name} 文件: {path}")
            sys.exit(1)

    print("准备开始生成...")
    print()
    input("按 Enter 确认开始...")

    try:
        result = generator.generate_full_story(
            gdd_path=str(gdd_path),
            lore_path=str(lore_path),
            main_story_path=str(main_story_path)
        )

        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║          ✅ MVP 故事生成成功！                                   ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        print("📊 生成统计：")
        print(f"  故事 ID：{result['story_id']}")
        print(f"  角色数量：{len(result['characters'])} 个")
        for i, char in enumerate(result['characters'], 1):
            mark = "⭐" if char['is_protagonist'] else "  "
            print(f"    {mark} {i}. {char['name']}")
        print(f"  总节点数：{result['metadata']['total_nodes']} 个")
        print(f"  主线深度：{result['metadata']['max_depth']} 层")
        print(f"  预计时长：{result['metadata']['estimated_duration']} 分钟")
        print()
        print("🎮 下一步：开始游玩测试")
        print()
        print("运行以下命令启动游戏：")
        print("  ./start_pregenerated_game.sh")
        print()
        print("在游戏中：")
        print("  1. 选择「选择故事」")
        print("  2. 选择城市「杭州」")
        print("  3. 选择故事「断桥残血-MVP测试」")
        print(f"  4. 选择角色（应该能看到 {len(result['characters'])} 个角色可选）")
        print("  5. 开始游玩测试！")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  生成被用户中断")
        return 1

    except Exception as e:
        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║          ❌ 生成失败                                             ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        print(f"错误信息：{e}")
        print()
        print("详细错误：")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

