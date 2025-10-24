#!/usr/bin/env python3
"""
超快速测试：只验证角色提取功能

预计时间：< 5 秒
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ghost_story_factory.pregenerator.synopsis_generator import StorySynopsis
from ghost_story_factory.pregenerator.story_generator import StoryGeneratorWithRetry


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          🔍 角色提取功能验证（秒级测试）                         ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # 测试杭州
    print("📍 测试城市：杭州")
    print()

    synopsis = StorySynopsis(
        title="断桥残血",
        synopsis="测试故事",
        protagonist="外卖骑手",
        location="西湖断桥",
        estimated_duration=20
    )

    generator = StoryGeneratorWithRetry(
        city="杭州",
        synopsis=synopsis,
        test_mode=True
    )

    # 只测试角色提取
    main_story = "测试故事内容"
    characters = generator._extract_characters(main_story)

    print("提取结果：")
    print(f"  ✅ 找到 {len(characters)} 个角色\n")

    for idx, char in enumerate(characters, 1):
        protagonist_mark = "⭐ [主角]" if char['is_protagonist'] else ""
        print(f"  {idx}. {char['name']} {protagonist_mark}")
        print(f"     描述: {char['description']}")
        print()

    # 验证预期
    print("验证：")
    if len(characters) >= 2:
        print(f"  ✅ 成功提取多个角色（{len(characters)} 个）")
    else:
        print(f"  ❌ 只提取到 {len(characters)} 个角色")
        sys.exit(1)

    if characters[0]['name'] in ['夜爬驴友', '索道检修工', '监控室值班员', '外卖夜归人']:
        print(f"  ✅ 角色名称正确（从 struct.json 读取）")
    else:
        print(f"  ⚠️  角色名称可能不对：{characters[0]['name']}")

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          ✅ 角色提取功能正常！                                   ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print("下一步：")
    print("  • 运行完整MVP测试：python3 test_multi_character.py")
    print("  • 或直接生成完整故事（10-20小时）")


if __name__ == "__main__":
    main()

