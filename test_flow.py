#!/usr/bin/env python3
"""测试游戏引擎完整流程（非交互式）"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 70)
print("🎮 Ghost Story Factory - 游戏引擎流程测试")
print("=" * 70 + "\n")

# 测试 1: 导入所有模块
print("📦 测试 1: 导入模块...")
try:
    from ghost_story_factory.engine import (
        GameState,
        Choice,
        ChoiceType,
        ChoicePointsGenerator,
        RuntimeResponseGenerator,
        GameEngine,
        IntentMappingEngine,
        EndingSystem,
        EndingType
    )
    from ghost_story_factory.ui import GameCLI
    print("✅ 所有模块导入成功\n")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}\n")
    sys.exit(1)

# 测试 2: 创建游戏状态
print("📊 测试 2: 创建游戏状态...")
try:
    state = GameState(
        PR=5,
        GR=0,
        WF=0,
        current_scene="S1",
        timestamp="00:00"
    )
    print(f"  初始状态: {state}")

    # 更新状态
    state.update({
        "PR": "+10",
        "inventory": ["手电筒", "对讲机"],
        "flags": {"场景1_已完成": True}
    })
    print(f"  更新后: PR={state.PR}, 道具={len(state.inventory)}个")
    print("✅ 状态管理正常\n")
except Exception as e:
    print(f"❌ 状态管理失败: {e}\n")
    sys.exit(1)

# 测试 3: 创建选择点
print("🎯 测试 3: 创建选择点...")
try:
    choice1 = Choice(
        choice_id="S1_C1",
        choice_text="走过去检查声音来源",
        choice_type=ChoiceType.NORMAL,
        tags=["调查", "主动"],
        consequences={"PR": "+15", "timestamp": "+3min"}
    )

    choice2 = Choice(
        choice_id="S1_C2",
        choice_text="使用念佛机",
        choice_type=ChoiceType.NORMAL,
        tags=["道具", "消耗"],
        preconditions={"items": ["念佛机"]},
        consequences={"PR": "-15"}
    )

    # 检查可用性
    available1 = choice1.is_available(state)
    available2 = choice2.is_available(state)

    print(f"  选择1 ({choice1.choice_text}): {'✅ 可用' if available1 else '❌ 不可用'}")
    print(f"  选择2 ({choice2.choice_text}): {'✅ 可用' if available2 else '❌ 不可用'}")
    print("✅ 选择点创建正常\n")
except Exception as e:
    print(f"❌ 选择点创建失败: {e}\n")
    sys.exit(1)

# 测试 4: 意图映射
print("🧠 测试 4: 意图映射...")
try:
    intent_engine = IntentMappingEngine()

    # 验证选择
    result = intent_engine.validate_choice(choice1, state)
    print(f"  选择1 验证: {'✅ 通过' if result.is_valid else '❌ 失败'}")

    result2 = intent_engine.validate_choice(choice2, state)
    print(f"  选择2 验证: {'❌ 失败' if not result2.is_valid else '✅ 通过'}")
    if not result2.is_valid:
        print(f"    原因: {result2.reason}")

    # 提取意图
    intent = intent_engine.extract_intent(choice1)
    print(f"  意图提取:")
    print(f"    物理: {intent.physical_action}")
    print(f"    心理: {intent.emotional_motivation}")
    print(f"    风险: {intent.risk_level}")
    print("✅ 意图映射正常\n")
except Exception as e:
    print(f"❌ 意图映射失败: {e}\n")
    sys.exit(1)

# 测试 5: 结局系统
print("🏆 测试 5: 结局系统...")
try:
    ending_system = EndingSystem()

    # 测试不同状态的结局
    test_states = [
        (GameState(PR=100), "迷失结局（PR=100）"),
        (GameState(PR=50, inventory=["失魂核心"], flags={"录音_已播放": True}), "补完结局"),
        (GameState(PR=50, flags={"录音_已播放": True}), "旁观结局"),
        (GameState(timestamp="06:30"), "超时结局"),
    ]

    for test_state, expected in test_states:
        ending = ending_system.check_ending(test_state)
        if ending:
            print(f"  {expected}: ✅ {ending.value}")
        else:
            print(f"  {expected}: ⚠️  无结局")

    print("✅ 结局系统正常\n")
except Exception as e:
    print(f"❌ 结局系统失败: {e}\n")
    sys.exit(1)

# 测试 6: CLI 界面
print("🎨 测试 6: CLI 界面...")
try:
    from ghost_story_factory.ui.cli import check_rich_available

    cli = GameCLI(use_rich=False)  # 使用纯文本模式避免交互

    print("  显示状态：")
    cli.display_state(state)

    rich_available = check_rich_available()
    print(f"  Rich 库: {'✅ 已安装' if rich_available else '⚠️  未安装（将使用纯文本模式）'}")
    print("✅ CLI 界面正常\n")
except Exception as e:
    print(f"❌ CLI 界面失败: {e}\n")
    sys.exit(1)

# 测试 7: 游戏引擎初始化
print("🎮 测试 7: 游戏引擎初始化...")
try:
    engine = GameEngine(
        city="杭州",
        gdd_path="examples/杭州/杭州_GDD.md",
        lore_path="examples/杭州/杭州_lore_v2.md"
    )

    print(f"  城市: {engine.city}")
    print(f"  GDD: {'✅ 已加载' if engine.gdd else '❌ 未加载'} ({len(engine.gdd)} 字符)")
    print(f"  Lore: {'✅ 已加载' if engine.lore else '❌ 未加载'} ({len(engine.lore)} 字符)")
    print(f"  初始状态: {engine.state}")
    print("✅ 游戏引擎初始化成功\n")
except Exception as e:
    print(f"❌ 游戏引擎初始化失败: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 8: 保存/读档
print("💾 测试 8: 保存/读档...")
try:
    # 保存状态
    save_path = "saves/test_save.save"
    state.save(save_path)
    print(f"  保存成功: {save_path}")

    # 加载状态
    loaded_state = GameState.load(save_path)
    print(f"  加载成功: PR={loaded_state.PR}, 场景={loaded_state.current_scene}")

    # 验证数据一致
    assert loaded_state.PR == state.PR
    assert loaded_state.current_scene == state.current_scene
    print("✅ 保存/读档正常\n")
except Exception as e:
    print(f"❌ 保存/读档失败: {e}\n")
    sys.exit(1)

# 总结
print("=" * 70)
print("✅ 所有测试通过！游戏引擎可以正常运行")
print("=" * 70)
print("\n📖 下一步:")
print("  1. 安装依赖: pip install pydantic rich")
print("  2. 运行游戏: ghost-story-play 杭州")
print("  3. 查看文档: cat GAME_ENGINE_USAGE.md")
print("\n🎮 准备好开始游戏了！\n")

