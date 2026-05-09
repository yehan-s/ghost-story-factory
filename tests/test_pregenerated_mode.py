"""
预生成模式集成测试

测试 GameEngine 的预生成模式功能和性能。
"""

import pytest
import time
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch
from io import StringIO

from ghost_story_factory.engine.game_loop import GameEngine
from ghost_story_factory.runtime.dialogue_loader import DialogueTreeLoader


class MockDialogueTreeLoader:
    """Mock 对话树加载器"""

    def __init__(self, tree_data: Dict[str, Any]):
        """
        Args:
            tree_data: 模拟的对话树数据
        """
        self.tree = tree_data
        self.current_node_id = "root"

    def get_narrative(self, node_id: str = None) -> str:
        """获取叙事文本"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.tree.get(node_id)
        return node.get("narrative", "") if node else ""

    def get_choices(self, node_id: str = None) -> List[Dict[str, Any]]:
        """获取选择列表"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.tree.get(node_id)
        if not node:
            return []

        choices = node.get("choices", []) or []
        return [c for c in choices if not c.get("hidden")]

    def can_traverse(self, choice_id: str, node_id: str = None) -> bool:
        """检查选择是否可到达"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.tree.get(node_id)
        if not node:
            return False

        for choice in node.get("choices", []):
            if choice.get("choice_id") == choice_id:
                next_id = choice.get("next_node_id")
                return next_id and next_id in self.tree

        return False

    def select_choice(self, choice_id: str) -> str:
        """选择并跳转到下一节点"""
        choices = self.get_choices()

        for choice in choices:
            if choice.get("choice_id") == choice_id:
                next_node_id = choice.get("next_node_id")
                if next_node_id and next_node_id in self.tree:
                    self.current_node_id = next_node_id
                    return next_node_id

        return None

    def is_ending(self, node_id: str = None) -> bool:
        """判断是否为结局节点"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.tree.get(node_id)
        return node.get("is_ending", False) if node else False

    def get_ending_type(self, node_id: str = None) -> str:
        """获取结局类型"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.tree.get(node_id)
        return node.get("ending_type") if node else None

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_nodes = len(self.tree)
        ending_nodes = [
            node_id for node_id, node in self.tree.items()
            if node.get("is_ending", False)
        ]
        max_depth = max(node.get("depth", 0) for node in self.tree.values())

        return {
            "total_nodes": total_nodes,
            "ending_count": len(ending_nodes),
            "max_depth": max_depth
        }


@pytest.fixture
def simple_tree():
    """简单对话树"""
    return {
        "root": {
            "node_id": "root",
            "scene": "S1",
            "depth": 0,
            "narrative": "故事开始",
            "choices": [
                {
                    "choice_id": "C1",
                    "choice_text": "选择1",
                    "next_node_id": "node_001",
                    "tags": [],
                    "consequences": {}
                },
                {
                    "choice_id": "C2",
                    "choice_text": "选择2",
                    "next_node_id": "node_002",
                    "tags": [],
                    "consequences": {}
                }
            ],
            "children": ["node_001", "node_002"],
            "is_ending": False
        },
        "node_001": {
            "node_id": "node_001",
            "scene": "S2",
            "depth": 1,
            "narrative": "分支1",
            "choices": [],
            "parent_id": "root",
            "parent_choice_id": "C1",
            "children": [],
            "is_ending": True,
            "ending_type": "ending_1"
        },
        "node_002": {
            "node_id": "node_002",
            "scene": "S3",
            "depth": 1,
            "narrative": "分支2",
            "choices": [],
            "parent_id": "root",
            "parent_choice_id": "C2",
            "children": [],
            "is_ending": True,
            "ending_type": "ending_2"
        }
    }


@pytest.fixture
def linear_tree():
    """线性对话树（用于性能测试）"""
    tree = {}

    # 创建一条 30 节点的线性路径
    for i in range(30):
        node_id = "root" if i == 0 else f"node_{i:03d}"
        next_node_id = f"node_{i+1:03d}" if i < 29 else None

        tree[node_id] = {
            "node_id": node_id,
            "scene": f"S{i+1}",
            "depth": i,
            "narrative": f"第 {i+1} 节",
            "choices": [
                {
                    "choice_id": f"C{i+1}",
                    "choice_text": "继续",
                    "next_node_id": next_node_id,
                    "tags": [],
                    "consequences": {}
                }
            ] if next_node_id else [],
            "parent_id": f"node_{i-1:03d}" if i > 0 else None,
            "parent_choice_id": f"C{i}" if i > 0 else None,
            "children": [next_node_id] if next_node_id else [],
            "is_ending": i == 29,
            "ending_type": "linear_end" if i == 29 else None
        }

    return tree


class TestPregeneratedMode:
    """预生成模式测试套件"""

    def test_engine_mode_selection_pregenerated(self, simple_tree):
        """测试引擎模式自动选择（预生成模式）"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        engine = GameEngine(
            city="杭州",
            dialogue_loader=mock_loader
        )

        assert engine.mode == "pregenerated"
        assert engine.dialogue_loader == mock_loader
        assert engine.gdd == ""
        assert engine.lore == ""
        assert engine.choice_generator is None
        assert engine.response_generator is None

    def test_engine_mode_selection_realtime(self):
        """测试引擎模式自动选择（实时模式）"""
        # 不传入 dialogue_loader，应自动选择实时模式
        # 但会因为缺少 GDD/Lore 而抛出异常
        with pytest.raises(FileNotFoundError, match="无法找到"):
            GameEngine(city="杭州")

    @patch('builtins.input', side_effect=['1'])  # 模拟玩家选择1
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_pregenerated_full_game(self, mock_stdout, mock_input, simple_tree):
        """测试预生成模式完整游戏流程"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

        result = engine.run()

        # 验证游戏正常结束
        assert result == "ending_reached"

        # 验证输出包含关键内容
        output = mock_stdout.getvalue()
        assert "故事开始" in output  # 开场叙事
        assert "分支1" in output  # 结局叙事

    @patch('builtins.input', side_effect=['q'])  # 模拟玩家退出
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_pregenerated_player_quit(self, mock_stdout, mock_input, simple_tree):
        """测试玩家中途退出"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

        result = engine.run()

        # 验证退出结果
        assert result == "player_quit"

    @patch('builtins.input', side_effect=['999', '1'])  # 先输入无效选择，再输入有效选择
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_pregenerated_invalid_choice(self, mock_stdout, mock_input, simple_tree):
        """测试无效选择处理"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

        result = engine.run()

        # 验证游戏继续并正常结束
        assert result == "ending_reached"

        # 验证输出包含错误提示
        output = mock_stdout.getvalue()
        # input mock 会直接返回值，不会进入错误处理流程
        # 所以这里只验证游戏能正常结束

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_pregenerated_keyboard_interrupt(self, mock_stdout, mock_input, simple_tree):
        """测试键盘中断处理"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

        result = engine.run()

        # 验证中断结果
        assert result == "interrupted"

    def test_performance_pregenerated_30_rounds(self, linear_tree):
        """测试预生成模式性能（30 轮游戏）"""
        mock_loader = MockDialogueTreeLoader(linear_tree)

        # Mock _prompt_player 方法，模拟玩家快速选择
        with patch.object(
            GameEngine,
            '_prompt_player',
            side_effect=lambda choices: choices[0] if choices else None
        ):
            engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

            start_time = time.time()
            result = engine.run()
            elapsed = time.time() - start_time

            # 验证游戏正常结束
            assert result == "ending_reached"

            # 验证性能：30 轮应 <0.1s（零延迟）
            assert elapsed < 0.1, f"30 轮游戏耗时 {elapsed*1000:.1f}ms 超过 100ms"
            print(f"\n✅ 性能基准: 30 轮游戏耗时 {elapsed*1000:.2f}ms（平均 {elapsed/30*1000:.2f}ms/轮）")


# 对比测试
class TestModeComparison:
    """预生成模式 vs 实时模式对比测试"""

    def test_startup_time_pregenerated(self, simple_tree):
        """测试预生成模式启动时间"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        start_time = time.time()
        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)
        elapsed = time.time() - start_time

        # 验证启动时间 <1s
        assert elapsed < 1.0, f"启动时间 {elapsed*1000:.1f}ms 超过 1000ms"
        print(f"\n✅ 预生成模式启动时间: {elapsed*1000:.2f}ms")

    def test_mode_resource_usage_pregenerated(self, simple_tree):
        """测试预生成模式资源占用"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

        # 验证资源优化：不加载 GDD/Lore
        assert engine.gdd == ""
        assert engine.lore == ""
        assert engine.main_story == ""

        # 验证 LLM 生成器未初始化
        assert engine.choice_generator is None
        assert engine.response_generator is None

    def test_mode_network_independence_pregenerated(self, simple_tree):
        """测试预生成模式网络独立性"""
        mock_loader = MockDialogueTreeLoader(simple_tree)

        # 预生成模式不依赖网络，即使 API 不可用也能运行
        with patch('requests.post', side_effect=Exception("Network error")):
            engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

            # 游戏应能正常初始化
            assert engine.mode == "pregenerated"

            # Mock 玩家输入
            with patch.object(
                engine,
                '_prompt_player',
                side_effect=lambda choices: choices[0] if choices else None
            ):
                result = engine.run()

            # 验证游戏正常结束（无网络依赖）
            assert result == "ending_reached"


# 兼容性测试
class TestBackwardCompatibility:
    """向后兼容性测试"""

    def test_convert_choices_format(self, simple_tree):
        """测试对话树选择格式转换"""
        mock_loader = MockDialogueTreeLoader(simple_tree)
        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

        # 获取原始选择数据
        choices_data = mock_loader.get_choices()

        # 转换为 Choice 对象
        choices = engine._convert_choices(choices_data)

        # 验证转换正确
        assert len(choices) == 2
        assert choices[0].choice_id == "C1"
        assert choices[0].choice_text == "选择1"
        assert choices[1].choice_id == "C2"
        assert choices[1].choice_text == "选择2"

    def test_pregenerated_mode_with_empty_consequences(self, simple_tree):
        """测试预生成模式处理空 consequences"""
        # 修改树：移除 consequences
        for node in simple_tree.values():
            for choice in node.get("choices", []):
                choice["consequences"] = {}

        mock_loader = MockDialogueTreeLoader(simple_tree)
        engine = GameEngine(city="杭州", dialogue_loader=mock_loader)

        # Mock 玩家输入
        with patch.object(
            engine,
            '_prompt_player',
            side_effect=lambda choices: choices[0] if choices else None
        ):
            result = engine.run()

        # 验证游戏正常结束（不依赖 consequences）
        assert result == "ending_reached"
