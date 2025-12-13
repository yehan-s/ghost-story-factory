"""
StateHasher 单元测试

测试状态哈希计算器的正确性和一致性。
"""

import pytest
from ghost_story_factory.pregenerator.state_hasher import StateHasher, quick_hash


class TestStateHasher:
    """StateHasher 测试套件"""

    def test_hash_consistency(self):
        """测试相同状态产生相同哈希"""
        hasher = StateHasher()

        state = {
            "PR": 45,
            "GR": 10,
            "WF": 2,
            "current_scene": "S3",
            "inventory": ["暗号:36-3=33", "金属锤柄"],
            "flags": {"失魂者_已拍照": True}
        }

        hash1 = hasher.hash(state)
        hash2 = hasher.hash(state)

        assert hash1 == hash2, "相同状态应产生相同哈希"
        assert len(hash1) == 32, "MD5哈希应为32字符"

    def test_hash_ignores_timestamp(self):
        """测试哈希忽略时间戳字段"""
        hasher = StateHasher()

        state1 = {
            "PR": 45,
            "current_scene": "S3",
            "timestamp": "02:30",
            "inventory": [],
            "flags": {}
        }

        state2 = {
            "PR": 45,
            "current_scene": "S3",
            "timestamp": "03:45",  # 不同时间戳
            "inventory": [],
            "flags": {}
        }

        hash1 = hasher.hash(state1)
        hash2 = hasher.hash(state2)

        assert hash1 == hash2, "时间戳不同不应影响哈希"

    def test_hash_sensitive_to_core_fields(self):
        """测试哈希对核心字段敏感"""
        hasher = StateHasher()

        base_state = {
            "PR": 45,
            "GR": 10,
            "WF": 2,
            "current_scene": "S3",
            "inventory": [],
            "flags": {}
        }

        # 测试 PR 变化
        state_pr_diff = {**base_state, "PR": 50}
        assert hasher.hash(base_state) != hasher.hash(state_pr_diff)

        # 测试 scene 变化
        state_scene_diff = {**base_state, "current_scene": "S4"}
        assert hasher.hash(base_state) != hasher.hash(state_scene_diff)

        # 测试 inventory 变化
        state_inv_diff = {**base_state, "inventory": ["道具A"]}
        assert hasher.hash(base_state) != hasher.hash(state_inv_diff)

        # 测试 flags 变化
        state_flag_diff = {**base_state, "flags": {"事件A": True}}
        assert hasher.hash(base_state) != hasher.hash(state_flag_diff)

    def test_inventory_order_irrelevant(self):
        """测试道具栏顺序不影响哈希（内部会排序）"""
        hasher = StateHasher()

        state1 = {
            "PR": 45,
            "current_scene": "S3",
            "inventory": ["道具A", "道具B", "道具C"],
            "flags": {}
        }

        state2 = {
            "PR": 45,
            "current_scene": "S3",
            "inventory": ["道具C", "道具A", "道具B"],  # 不同顺序
            "flags": {}
        }

        hash1 = hasher.hash(state1)
        hash2 = hasher.hash(state2)

        assert hash1 == hash2, "道具栏顺序不应影响哈希"

    def test_is_duplicate_helper(self):
        """测试 is_duplicate 辅助方法"""
        hasher = StateHasher()

        state1 = {
            "PR": 45,
            "current_scene": "S3",
            "inventory": [],
            "flags": {}
        }

        state2 = {
            "PR": 45,
            "current_scene": "S3",
            "inventory": [],
            "flags": {},
            "timestamp": "different"  # 额外字段应被忽略
        }

        state3 = {
            "PR": 50,  # 不同PR
            "current_scene": "S3",
            "inventory": [],
            "flags": {}
        }

        assert hasher.is_duplicate(state1, state2), "应识别为重复"
        assert not hasher.is_duplicate(state1, state3), "应识别为不同"

    def test_quick_hash_function(self):
        """测试 quick_hash 辅助函数"""
        state = {
            "PR": 45,
            "current_scene": "S3",
            "inventory": [],
            "flags": {}
        }

        hash_value = quick_hash(state)

        assert len(hash_value) == 32, "应返回32字符MD5哈希"
        assert isinstance(hash_value, str), "应返回字符串"

    def test_missing_fields_use_defaults(self):
        """测试缺失字段使用默认值"""
        hasher = StateHasher()

        # 空状态（所有字段缺失）
        empty_state = {}

        # 完整默认状态
        default_state = {
            "PR": 5,
            "GR": 0,
            "WF": 0,
            "current_scene": "S1",
            "inventory": [],
            "flags": {}
        }

        hash_empty = hasher.hash(empty_state)
        hash_default = hasher.hash(default_state)

        assert hash_empty == hash_default, "空状态应使用默认值"

    def test_hash_deterministic(self):
        """测试哈希的确定性（多次调用结果一致）"""
        hasher = StateHasher()

        state = {
            "PR": 45,
            "GR": 10,
            "current_scene": "S3",
            "inventory": ["道具A", "道具B"],
            "flags": {"事件A": True, "事件B": False}
        }

        hashes = [hasher.hash(state) for _ in range(10)]

        assert len(set(hashes)) == 1, "多次计算应产生相同哈希"

    def test_chinese_characters_support(self):
        """测试中文字符支持"""
        hasher = StateHasher()

        state = {
            "PR": 45,
            "current_scene": "西湖断桥",
            "inventory": ["暗号:36-3=33", "金属锤柄"],
            "flags": {"失魂者_已拍照": True}
        }

        hash_value = hasher.hash(state)

        assert len(hash_value) == 32, "中文字符不应影响哈希长度"
        assert hash_value.isalnum(), "哈希应为字母数字组合"


# 集成测试
class TestStateHasherIntegration:
    """StateHasher 集成测试"""

    def test_deduplication_scenario(self):
        """测试对话树去重场景"""
        hasher = StateHasher()

        # 模拟对话树生成过程
        visited_states = set()
        nodes = []

        # 节点1: 初始状态
        state1 = {"PR": 5, "current_scene": "S1", "inventory": [], "flags": {}}
        hash1 = hasher.hash(state1)

        if hash1 not in visited_states:
            visited_states.add(hash1)
            nodes.append(("node_001", state1))

        # 节点2: 选择后状态（PR+5）
        state2 = {"PR": 10, "current_scene": "S2", "inventory": ["道具A"], "flags": {}}
        hash2 = hasher.hash(state2)

        if hash2 not in visited_states:
            visited_states.add(hash2)
            nodes.append(("node_002", state2))

        # 节点3: 另一路径到达相同状态（应被去重）
        state3 = {"PR": 10, "current_scene": "S2", "inventory": ["道具A"], "flags": {}, "timestamp": "01:00"}
        hash3 = hasher.hash(state3)

        if hash3 not in visited_states:
            visited_states.add(hash3)
            nodes.append(("node_003", state3))

        # 断言
        assert len(nodes) == 2, "重复状态应被去重（只添加2个节点）"
        assert hash2 == hash3, "状态2和状态3应产生相同哈希"
