#!/usr/bin/env python3
"""
Ghost Story Factory - 完整游戏引擎（LLM 驱动版本）

使用 Kimi LLM 动态生成完整的游戏内容
- 完整的 S1-S6 主线场景
- 20-30+ 个动态生成的场景
- 15-30 分钟游玩时长
- 基于 GDD 和 Lore v2 的自适应叙事

使用方法：
    python3 play_game_full.py

需要的环境变量：
    KIMI_API_KEY 或 MOONSHOT_API_KEY
"""

import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ghost_story_factory.engine import (
    GameState,
    Choice,
    ChoiceType,
    ChoicePointsGenerator,
    RuntimeResponseGenerator,
    IntentMappingEngine,
    EndingSystem,
    GameEngine,
)
from ghost_story_factory.ui import GameCLI

from dotenv import load_dotenv

load_dotenv()

# 检查 API Key
kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
if not kimi_key:
    print("=" * 70)
    print("⚠️  错误：未找到 Kimi API Key")
    print("=" * 70)
    print("\n请设置环境变量：")
    print("  export KIMI_API_KEY=your_key_here")
    print("\n或创建 .env 文件：")
    print("  KIMI_API_KEY=your_key_here")
    print("\n" + "=" * 70)
    sys.exit(1)

# 初始化
cli = GameCLI(use_rich=True)

# 显示欢迎
cli.display_title("杭州·北高峰", "特检院工程师 - 顾栖迟")

print("""
╔══════════════════════════════════════════════════════════════════╗
║     北高峰·空厢夜行 | 完整版 | Ghost Story Factory            ║
║                                                                  ║
║  📋 身份：浙江省特检院 索道与游乐设施事业部 一级检验师         ║
║  🎯 任务：完成停运索道安全复核，夜间空载运行试验               ║
║  ⏱️  时长：15-30 分钟完整体验                                   ║
║                                                                  ║
║  ✨ 特性：                                                       ║
║    - LLM 动态生成所有场景和对话                                 ║
║    - 完整的 S1-S6 主线（20-30+ 场景）                           ║
║    - 根据你的选择自适应生成剧情                                 ║
║    - 多结局分支系统                                             ║
║                                                                  ║
║  💡 提示：每个场景由 Kimi AI 实时生成，请耐心等待               ║
║  🎮 操作：输入选项编号 | /save 保存 | /quit 退出               ║
╚══════════════════════════════════════════════════════════════════╝
""")

print("⏳ 正在加载游戏资源...")

# 检查资源文件
gdd_path = Path("examples/hangzhou/杭州_GDD.md")
lore_path = Path("examples/hangzhou/杭州_lore_v2.md")

if not gdd_path.exists():
    print(f"\n❌ 错误：找不到 GDD 文件: {gdd_path}")
    print("\n💡 提示：请先生成杭州故事：")
    print("   gen-complete --city 杭州 --index 1")
    sys.exit(1)

if not lore_path.exists():
    print(f"\n❌ 错误：找不到 Lore 文件: {lore_path}")
    print("\n💡 提示：请先生成杭州故事：")
    print("   gen-complete --city 杭州 --index 1")
    sys.exit(1)

print("✅ 资源文件已找到")
print("⏳ 初始化游戏引擎...")

# 创建完整游戏引擎
try:
    engine = GameEngine(
        city="杭州",
        gdd_path=str(gdd_path),
        lore_path=str(lore_path),
        save_dir="saves"
    )
    print("✅ 游戏引擎初始化成功")
except Exception as e:
    print(f"\n❌ 引擎初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("🎮 准备开始游戏...")
print("=" * 70)

input("\n按 Enter 开始你的检验任务...\n")

# 运行游戏
try:
    engine.run()
except KeyboardInterrupt:
    print("\n\n" + "=" * 70)
    print("👋 游戏已中断")
    print("=" * 70)
    print("\n💾 提示：使用 /save 命令保存进度")
except Exception as e:
    print(f"\n\n❌ 游戏运行出错: {e}")
    import traceback
    traceback.print_exc()

print("""
╔══════════════════════════════════════════════════════════════════╗
║                       感谢游玩！                                 ║
║                                                                  ║
║  🎮 北高峰·空厢夜行 | 完整版                                    ║
║  💡 这是由 Kimi AI 动态生成的完整游戏体验                       ║
║  📖 主角：顾栖迟 - 特检院工程师                                 ║
║  🎯 核心：索道检验 + 65Hz异常 + 第三节车厢                      ║
║                                                                  ║
║  ⭐ 如果你喜欢这个故事，可以尝试：                              ║
║     - 重新游玩，做出不同选择                                    ║
║     - 探索其他城市的故事                                        ║
║     - 查看 GDD 了解完整世界观                                   ║
╚══════════════════════════════════════════════════════════════════╝
""")

