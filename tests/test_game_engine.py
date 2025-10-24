"""游戏引擎测试

简单的集成测试，验证核心功能
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_game_state():
    """测试游戏状态管理"""
    from ghost_story_factory.engine import GameState

    print("测试 GameState...")

    # 创建状态
    state = GameState(PR=5, current_scene="S1")
    assert state.PR == 5
    assert state.current_scene == "S1"

    # 更新状态
    state.update({
        "PR": "+10",
        "inventory": ["道具1"],
        "flags": {"test_flag": True}
    })
    assert state.PR == 15
    assert "道具1" in state.inventory
    assert state.flags["test_flag"] is True

    # 检查前置条件
    result = state.check_preconditions({
        "PR": ">=10",
        "items": ["道具1"]
    })
    assert result is True

    result = state.check_preconditions({
        "PR": ">=20"
    })
    assert result is False

    print("✅ GameState 测试通过")


def test_choice():
    """测试选择点"""
    from ghost_story_factory.engine import Choice, ChoiceType, GameState

    print("\n测试 Choice...")

    # 创建选择
    choice = Choice(
        choice_id="S1_C1",
        choice_text="测试选项",
        choice_type=ChoiceType.NORMAL,
        preconditions={"PR": ">=10"},
        consequences={"PR": "+5"}
    )

    # 测试可用性
    state = GameState(PR=5)
    assert choice.is_available(state) is False

    state = GameState(PR=15)
    assert choice.is_available(state) is True

    # 测试显示文本
    display = choice.get_display_text(state)
    assert "💼" in display or "测试选项" in display

    print("✅ Choice 测试通过")


def test_intent_mapping():
    """测试意图映射"""
    from ghost_story_factory.engine import IntentMappingEngine, Choice, ChoiceType, GameState

    print("\n测试 IntentMappingEngine...")

    engine = IntentMappingEngine()

    # 创建测试选择
    choice = Choice(
        choice_id="S1_C1",
        choice_text="走过去检查",
        choice_type=ChoiceType.NORMAL,
        tags=["调查", "主动"],
        preconditions={"PR": ">=10"}
    )

    # 验证选择
    state = GameState(PR=5)
    result = engine.validate_choice(choice, state)
    assert result.is_valid is False
    assert result.reason is not None

    state = GameState(PR=15)
    result = engine.validate_choice(choice, state)
    assert result.is_valid is True

    # 提取意图
    intent = engine.extract_intent(choice)
    assert intent.physical_action == "走过去检查"
    assert intent.risk_level in ["low", "medium", "high"]

    print("✅ IntentMappingEngine 测试通过")


def test_ending_system():
    """测试结局系统"""
    from ghost_story_factory.engine import EndingSystem, EndingType, GameState

    print("\n测试 EndingSystem...")

    system = EndingSystem()

    # 测试迷失结局（PR = 100）
    state = GameState(PR=100)
    ending_type = system.check_ending(state)
    assert ending_type == EndingType.LOST

    # 测试补完结局
    state = GameState(
        PR=50,
        inventory=["失魂核心"],
        flags={"录音_已播放": True},
        timestamp="05:00"
    )
    ending_type = system.check_ending(state)
    assert ending_type == EndingType.COMPLETION

    # 测试旁观结局
    state = GameState(
        PR=50,
        inventory=[],  # 没有核心
        flags={"录音_已播放": True},
        timestamp="05:00"
    )
    ending_type = system.check_ending(state)
    assert ending_type == EndingType.OBSERVER

    # 渲染结局
    ending_text = system.render_ending(EndingType.COMPLETION, state)
    assert "补完" in ending_text
    assert "统计数据" in ending_text

    print("✅ EndingSystem 测试通过")


def test_cli():
    """测试 CLI 界面"""
    from ghost_story_factory.ui import GameCLI, check_rich_available
    from ghost_story_factory.engine import GameState, Choice, ChoiceType

    print("\n测试 GameCLI...")

    # 测试创建（不依赖 rich）
    cli = GameCLI(use_rich=False)

    # 测试显示状态
    state = GameState(PR=45, GR=63, WF=1)
    cli.display_state(state)

    # 测试显示选择
    choices = [
        Choice(
            choice_id="S1_C1",
            choice_text="选项 1",
            choice_type=ChoiceType.NORMAL
        ),
        Choice(
            choice_id="S1_C2",
            choice_text="选项 2",
            choice_type=ChoiceType.CRITICAL
        )
    ]
    cli.display_choices(choices, state, show_consequences=False)

    # 检查 Rich 是否可用
    rich_available = check_rich_available()
    print(f"  Rich 库: {'✅ 已安装' if rich_available else '⚠️  未安装（将使用纯文本模式）'}")

    print("✅ GameCLI 测试通过")


def main():
    """运行所有测试"""
    print("=" * 70)
    print("开始测试 Ghost Story Factory 游戏引擎")
    print("=" * 70 + "\n")

    try:
        test_game_state()
        test_choice()
        test_intent_mapping()
        test_ending_system()
        test_cli()

        print("\n" + "=" * 70)
        print("✅ 所有测试通过！")
        print("=" * 70)
        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

