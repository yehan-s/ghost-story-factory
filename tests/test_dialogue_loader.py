"""
DialogueTreeLoader 单元测试

测试对话树加载器的核心功能和性能。
"""

import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

from ghost_story_factory.runtime.dialogue_loader import DialogueTreeLoader


class MockDatabaseManager:
    """Mock 数据库管理器"""

    def __init__(self, tree_data: Dict[str, Any]):
        """
        Args:
            tree_data: 模拟的对话树数据
        """
        self.tree_data = tree_data

    def load_dialogue_tree(self, story_id: int, character_id: int) -> Dict[str, Any]:
        """模拟加载对话树"""
        return self.tree_data


@pytest.fixture
def simple_tree():
    """简单对话树（用于基础功能测试）"""
    return {
        "root": {
            "node_id": "root",
            "scene": "S1",
            "depth": 0,
            "narrative": "欢迎来到杭州灵异故事",
            "choices": [
                {
                    "choice_id": "C1",
                    "choice_text": "前往西湖断桥",
                    "next_node_id": "node_001",
                    "tags": ["exploration"],
                    "consequences": {"PR": 5}
                },
                {
                    "choice_id": "C2",
                    "choice_text": "返回旅馆",
                    "next_node_id": "node_002",
                    "tags": ["safe"],
                    "consequences": {"PR": -2}
                },
                {
                    "choice_id": "C3",
                    "choice_text": "隐藏选项",
                    "next_node_id": "node_003",
                    "hidden": True  # 应被过滤
                }
            ],
            "children": ["node_001", "node_002", "node_003"],
            "is_ending": False
        },
        "node_001": {
            "node_id": "node_001",
            "scene": "S2",
            "depth": 1,
            "narrative": "你来到西湖断桥，寒风中传来若有若无的呜咽声",
            "choices": [
                {
                    "choice_id": "C4",
                    "choice_text": "靠近声源",
                    "next_node_id": "node_004",
                    "tags": ["danger"],
                    "consequences": {"PR": 10}
                }
            ],
            "parent_id": "root",
            "parent_choice_id": "C1",
            "children": ["node_004"],
            "is_ending": False
        },
        "node_002": {
            "node_id": "node_002",
            "scene": "S1",
            "depth": 1,
            "narrative": "你回到旅馆，今晚平安无事",
            "choices": [],
            "parent_id": "root",
            "parent_choice_id": "C2",
            "children": [],
            "is_ending": True,
            "ending_type": "safe"
        },
        "node_003": {
            "node_id": "node_003",
            "scene": "S3",
            "depth": 1,
            "narrative": "隐藏分支",
            "choices": [],
            "parent_id": "root",
            "parent_choice_id": "C3",
            "children": [],
            "is_ending": True,
            "ending_type": "hidden"
        },
        "node_004": {
            "node_id": "node_004",
            "scene": "S3",
            "depth": 2,
            "narrative": "你触发了灵异事件",
            "choices": [],
            "parent_id": "node_001",
            "parent_choice_id": "C4",
            "children": [],
            "is_ending": True,
            "ending_type": "death"
        }
    }


@pytest.fixture
def fallback_tree():
    """回退机制测试树（缺少 next_node_id）"""
    return {
        "root": {
            "node_id": "root",
            "scene": "S1",
            "depth": 0,
            "narrative": "开始",
            "choices": [
                {
                    "choice_id": "C1",
                    "choice_text": "选择1",
                    # 缺少 next_node_id（触发回退路径1）
                    "tags": [],
                    "consequences": {}
                },
                {
                    "choice_id": "C2",
                    "choice_text": "选择2（唯一子节点）",
                    # 缺少 next_node_id（触发回退路径2）
                    "tags": [],
                    "consequences": {}
                }
            ],
            "children": ["node_001"],  # 只有一个子节点
            "is_ending": False
        },
        "node_001": {
            "node_id": "node_001",
            "scene": "S2",
            "depth": 1,
            "narrative": "通过 parent_id 推断",
            "choices": [],
            "parent_id": "root",
            "parent_choice_id": "C1",  # 可以通过这个推断
            "children": [],
            "is_ending": True,
            "ending_type": "inferred"
        }
    }


class TestDialogueTreeLoader:
    """DialogueTreeLoader 测试套件"""

    def test_initialization(self, simple_tree):
        """测试初始化"""
        mock_db = MockDatabaseManager(simple_tree)

        loader = DialogueTreeLoader(mock_db, story_id=1, character_id=1)

        assert loader.story_id == 1
        assert loader.character_id == 1
        assert loader.tree == simple_tree
        assert loader.current_node_id == "root"

    def test_load_empty_tree_raises_error(self):
        """测试加载空树抛出异常"""
        mock_db = MockDatabaseManager(None)

        with pytest.raises(ValueError, match="对话树加载失败"):
            DialogueTreeLoader(mock_db, story_id=1, character_id=1)

    def test_get_node_o1_lookup(self, simple_tree):
        """测试 O(1) 节点查询性能"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # 测试多次查询，验证 O(1) 性能
        times = []
        for _ in range(100):
            start_time = time.time()
            node = loader.get_node("node_001")
            elapsed = time.time() - start_time
            times.append(elapsed)

            assert node is not None
            assert node["node_id"] == "node_001"

        # 平均查询时间应 <0.001s (1ms)
        avg_time = sum(times) / len(times)
        assert avg_time < 0.001, f"平均查询时间 {avg_time*1000:.3f}ms 超过 1ms"

    def test_get_node_nonexistent(self, simple_tree):
        """测试获取不存在的节点"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        node = loader.get_node("nonexistent")

        assert node is None

    def test_get_current_node(self, simple_tree):
        """测试获取当前节点"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        node = loader.get_current_node()

        assert node["node_id"] == "root"
        assert node["depth"] == 0

    def test_get_narrative(self, simple_tree):
        """测试获取叙事文本"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        narrative = loader.get_narrative()

        assert "欢迎来到杭州灵异故事" in narrative

    def test_get_narrative_specific_node(self, simple_tree):
        """测试获取指定节点的叙事文本"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        narrative = loader.get_narrative("node_001")

        assert "西湖断桥" in narrative

    def test_get_choices_filters_hidden(self, simple_tree):
        """测试获取选择列表（过滤 hidden=true）"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        choices = loader.get_choices()

        assert len(choices) == 2  # C1, C2（C3 被过滤）
        choice_ids = [c["choice_id"] for c in choices]
        assert "C1" in choice_ids
        assert "C2" in choice_ids
        assert "C3" not in choice_ids

    def test_get_choices_empty_list(self, simple_tree):
        """测试获取空选择列表（结局节点）"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        choices = loader.get_choices("node_002")

        assert choices == []

    def test_select_choice_with_next_node_id(self, simple_tree):
        """测试选择跳转（主路径：使用 next_node_id）"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        next_node_id = loader.select_choice("C1")

        assert next_node_id == "node_001"
        assert loader.current_node_id == "node_001"

    def test_select_choice_fallback_parent_id(self, fallback_tree):
        """测试选择跳转（回退路径1：通过 parent_id 推断）"""
        mock_db = MockDatabaseManager(fallback_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        next_node_id = loader.select_choice("C1")

        assert next_node_id == "node_001"
        assert loader.current_node_id == "node_001"

    def test_select_choice_fallback_unique_child(self, fallback_tree):
        """测试选择跳转（回退路径2：唯一子节点前进）"""
        mock_db = MockDatabaseManager(fallback_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        next_node_id = loader.select_choice("C2")

        # 因为 root 只有一个子节点 node_001，应该前进到该节点
        assert next_node_id == "node_001"
        assert loader.current_node_id == "node_001"

    def test_select_choice_does_not_create_stub_node(self, simple_tree):
        """测试坏分支不会在运行时创建占位节点"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # 修改树结构：移除 node_001，但保留 C1 选择
        del loader.tree["node_001"]
        loader.tree["root"]["children"] = []

        next_node_id = loader.select_choice("C1")

        # 坏树必须在审计阶段失败，运行时不能伪造剧情。
        assert next_node_id is None
        assert loader.current_node_id == "root"
        assert all(
            node.get("ending_type") != "missing_branch"
            for node in loader.tree.values()
            if isinstance(node, dict)
        )

    def test_select_choice_invalid(self, simple_tree):
        """测试选择不存在的选项"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        next_node_id = loader.select_choice("invalid_choice")

        assert next_node_id is None
        assert loader.current_node_id == "root"  # 保持在当前节点

    def test_can_traverse(self, simple_tree):
        """测试选择可达性检查"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # C1 可达（有 next_node_id）
        assert loader.can_traverse("C1") is True

        # C2 可达
        assert loader.can_traverse("C2") is True

        # C3 可达（虽然 hidden，但节点存在）
        assert loader.can_traverse("C3") is True

        # invalid 不可达
        assert loader.can_traverse("invalid") is False

    def test_is_ending(self, simple_tree):
        """测试结局节点判断"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # root 不是结局
        assert loader.is_ending("root") is False

        # node_002 是结局
        assert loader.is_ending("node_002") is True

    def test_get_ending_type(self, simple_tree):
        """测试获取结局类型"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # node_002 是 safe 结局
        assert loader.get_ending_type("node_002") == "safe"

        # node_004 是 death 结局
        assert loader.get_ending_type("node_004") == "death"

        # root 不是结局
        assert loader.get_ending_type("root") is None

    def test_reset(self, simple_tree):
        """测试重置到根节点"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # 跳转到其他节点
        loader.select_choice("C1")
        assert loader.current_node_id == "node_001"

        # 重置
        loader.reset()

        assert loader.current_node_id == "root"

    def test_get_stats(self, simple_tree):
        """测试获取统计信息"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        stats = loader.get_stats()

        assert stats["total_nodes"] == 5
        assert stats["ending_count"] == 3  # node_002, node_003, node_004
        assert stats["max_depth"] == 2


# 集成测试
class TestDialogueTreeLoaderIntegration:
    """DialogueTreeLoader 集成测试"""

    def test_full_game_playthrough(self, simple_tree):
        """测试完整游戏流程"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # 1. 开始游戏（root 节点）
        narrative = loader.get_narrative()
        assert "欢迎来到杭州灵异故事" in narrative

        # 2. 获取选择
        choices = loader.get_choices()
        assert len(choices) == 2

        # 3. 选择前往西湖断桥
        next_node_id = loader.select_choice("C1")
        assert next_node_id == "node_001"

        # 4. 获取新叙事
        narrative = loader.get_narrative()
        assert "西湖断桥" in narrative

        # 5. 获取新选择
        choices = loader.get_choices()
        assert len(choices) == 1

        # 6. 选择靠近声源
        next_node_id = loader.select_choice("C4")
        assert next_node_id == "node_004"

        # 7. 检查结局
        assert loader.is_ending() is True
        assert loader.get_ending_type() == "death"

    def test_safe_ending_playthrough(self, simple_tree):
        """测试安全结局流程"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        # 1. 开始游戏
        assert loader.current_node_id == "root"

        # 2. 选择返回旅馆
        next_node_id = loader.select_choice("C2")
        assert next_node_id == "node_002"

        # 3. 验证安全结局
        assert loader.is_ending() is True
        assert loader.get_ending_type() == "safe"
        narrative = loader.get_narrative()
        assert "平安无事" in narrative

    def test_performance_benchmark(self, simple_tree):
        """测试性能基准（模拟 30 轮游戏）"""
        mock_db = MockDatabaseManager(simple_tree)
        loader = DialogueTreeLoader(mock_db, 1, 1)

        start_time = time.time()

        # 模拟 30 轮游戏操作
        for _ in range(30):
            loader.get_narrative()
            choices = loader.get_choices()
            if choices:
                loader.select_choice(choices[0]["choice_id"])
            loader.reset()  # 重置到根节点

        elapsed = time.time() - start_time

        # 30 轮应 <0.1s（每轮 <3.3ms）
        assert elapsed < 0.1, f"30 轮游戏耗时 {elapsed*1000:.1f}ms 超过 100ms"
        print(f"\n✅ 性能基准: 30 轮游戏耗时 {elapsed*1000:.2f}ms（平均 {elapsed/30*1000:.2f}ms/轮）")
