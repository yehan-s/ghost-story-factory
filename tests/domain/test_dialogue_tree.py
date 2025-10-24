"""
领域模型测试 - Dialogue Tree (对话树)

DDD 领域模型测试，验证对话树的核心领域规则
"""
import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum


# ==================== 领域模型定义 ====================

class NodeType(Enum):
    """节点类型"""
    SCENE = "scene"           # 场景节点
    CHOICE = "choice"         # 选择节点
    CONSEQUENCE = "consequence"  # 后果节点
    ENDING = "ending"         # 结局节点


@dataclass
class GameState:
    """游戏状态值对象"""
    personal_resonance: float  # 个人共鸣度 0-100
    group_resonance: float     # 群体共鸣度 0-100
    world_fatigue: float       # 世界疲劳度 0-100
    visited_scenes: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """验证状态值的有效性"""
        if not 0 <= self.personal_resonance <= 100:
            raise ValueError("个人共鸣度必须在0-100之间")
        if not 0 <= self.group_resonance <= 100:
            raise ValueError("群体共鸣度必须在0-100之间")
        if not 0 <= self.world_fatigue <= 100:
            raise ValueError("世界疲劳度必须在0-100之间")
    
    def is_similar_to(self, other: 'GameState', threshold: float = 5.0) -> bool:
        """检查两个状态是否相似（用于剪枝）"""
        if not isinstance(other, GameState):
            return False
        
        pr_diff = abs(self.personal_resonance - other.personal_resonance)
        gr_diff = abs(self.group_resonance - other.group_resonance)
        wf_diff = abs(self.world_fatigue - other.world_fatigue)
        
        return pr_diff <= threshold and gr_diff <= threshold and wf_diff <= threshold


@dataclass
class DialogueNode:
    """对话节点值对象
    
    领域规则：
    1. 每个节点必须有唯一ID
    2. 节点内容不能为空
    3. 选择节点必须有子节点
    4. 结局节点不能有子节点
    """
    id: str
    node_type: NodeType
    content: str
    state: GameState
    children: List['DialogueNode'] = field(default_factory=list)
    parent_id: Optional[str] = None
    
    def __post_init__(self):
        """验证节点规则"""
        if not self.id or not self.id.strip():
            raise ValueError("节点ID不能为空")
        if not self.content or not self.content.strip():
            raise ValueError("节点内容不能为空")
        if self.node_type == NodeType.ENDING and self.children:
            raise ValueError("结局节点不能有子节点")
    
    def add_child(self, child: 'DialogueNode') -> None:
        """添加子节点（领域操作）"""
        if self.node_type == NodeType.ENDING:
            raise ValueError("结局节点不能添加子节点")
        
        # 检查ID重复
        if any(c.id == child.id for c in self.children):
            raise ValueError(f"子节点ID重复: {child.id}")
        
        child.parent_id = self.id
        self.children.append(child)
    
    def is_leaf(self) -> bool:
        """是否为叶子节点"""
        return len(self.children) == 0
    
    def depth(self) -> int:
        """计算节点深度"""
        if self.is_leaf():
            return 0
        return 1 + max(child.depth() for child in self.children)


class DialogueTree:
    """对话树聚合根（Aggregate Root）
    
    领域规则：
    1. 树必须有唯一的根节点
    2. 所有节点ID必须唯一
    3. 不能有环路
    4. 树的最大深度有限制
    """
    
    def __init__(self, root: DialogueNode, max_depth: int = 20):
        self.root = root
        self.max_depth = max_depth
        self._node_map: Dict[str, DialogueNode] = {}
        self._build_node_map(root)
    
    def _build_node_map(self, node: DialogueNode) -> None:
        """构建节点映射（检查ID唯一性）"""
        if node.id in self._node_map:
            raise ValueError(f"节点ID重复: {node.id}")
        self._node_map[node.id] = node
        for child in node.children:
            self._build_node_map(child)
    
    def get_node(self, node_id: str) -> Optional[DialogueNode]:
        """根据ID获取节点"""
        return self._node_map.get(node_id)
    
    def total_nodes(self) -> int:
        """计算总节点数"""
        return len(self._node_map)
    
    def max_depth_reached(self) -> int:
        """计算实际达到的最大深度"""
        return self.root.depth()
    
    def is_valid(self) -> bool:
        """验证树的有效性"""
        # 1. 检查最大深度
        if self.max_depth_reached() > self.max_depth:
            return False
        
        # 2. 检查是否有环路（通过父子关系验证）
        visited = set()
        return self._check_no_cycles(self.root, visited)
    
    def _check_no_cycles(self, node: DialogueNode, visited: Set[str]) -> bool:
        """检查是否有环路"""
        if node.id in visited:
            return False  # 发现环路
        visited.add(node.id)
        for child in node.children:
            if not self._check_no_cycles(child, visited):
                return False
        visited.remove(node.id)  # 回溯
        return True
    
    def prune_similar_branches(self, threshold: float = 5.0) -> int:
        """剪枝：合并状态相似的分支
        
        返回剪掉的节点数
        """
        pruned_count = 0
        
        def _prune_level(nodes: List[DialogueNode]) -> List[DialogueNode]:
            nonlocal pruned_count
            result = []
            seen_states = []
            
            for node in nodes:
                # 检查是否与已存在的节点状态相似
                similar_node = None
                for existing in seen_states:
                    if node.state.is_similar_to(existing.state, threshold):
                        similar_node = existing
                        break
                
                if similar_node is None:
                    # 新状态，保留
                    result.append(node)
                    seen_states.append(node)
                else:
                    # 状态相似，合并到existing节点
                    pruned_count += 1
                    # 将子节点合并到similar_node
                    for child in node.children:
                        try:
                            similar_node.add_child(child)
                        except ValueError:
                            pass  # ID重复，跳过
            
            # 递归处理子节点
            for node in result:
                if node.children:
                    node.children = _prune_level(node.children)
            
            return result
        
        self.root.children = _prune_level(self.root.children)
        return pruned_count


# ==================== 领域服务 ====================

class DialogueTreeBuilder:
    """对话树构建器（领域服务）
    
    职责：根据领域规则构建有效的对话树
    """
    
    @staticmethod
    def create_simple_tree(scene_count: int = 3, choices_per_scene: int = 2) -> DialogueTree:
        """创建简单的测试对话树"""
        root = DialogueNode(
            id="root",
            node_type=NodeType.SCENE,
            content="开场场景",
            state=GameState(
                personal_resonance=10.0,
                group_resonance=5.0,
                world_fatigue=0.0
            )
        )
        
        # 递归构建树
        def _build_level(parent: DialogueNode, level: int, max_level: int):
            if level >= max_level:
                # 添加结局节点
                ending = DialogueNode(
                    id=f"{parent.id}_ending",
                    node_type=NodeType.ENDING,
                    content="结局",
                    state=parent.state
                )
                parent.add_child(ending)
                return
            
            for i in range(choices_per_scene):
                choice = DialogueNode(
                    id=f"{parent.id}_choice_{i}",
                    node_type=NodeType.CHOICE,
                    content=f"选择 {i+1}",
                    state=GameState(
                        personal_resonance=parent.state.personal_resonance + 10,
                        group_resonance=parent.state.group_resonance + 5,
                        world_fatigue=parent.state.world_fatigue + 2
                    )
                )
                parent.add_child(choice)
                _build_level(choice, level + 1, max_level)
        
        _build_level(root, 0, scene_count)
        return DialogueTree(root, max_depth=scene_count * 2)


# ==================== 领域模型测试 ====================

class TestGameStateDomain:
    """领域模型测试 - GameState 值对象"""
    
    def test_valid_game_state_creation(self):
        """测试：创建有效的游戏状态"""
        # Given & When
        state = GameState(
            personal_resonance=50.0,
            group_resonance=30.0,
            world_fatigue=20.0
        )
        
        # Then
        assert state.personal_resonance == 50.0
        assert state.group_resonance == 30.0
        assert state.world_fatigue == 20.0
    
    def test_personal_resonance_out_of_range_raises_error(self):
        """测试：个人共鸣度超出范围应抛出错误"""
        # Given & When & Then
        with pytest.raises(ValueError, match="个人共鸣度必须在0-100之间"):
            GameState(personal_resonance=150.0, group_resonance=50.0, world_fatigue=10.0)
    
    def test_negative_resonance_raises_error(self):
        """测试：负数共鸣度应抛出错误"""
        # Given & When & Then
        with pytest.raises(ValueError):
            GameState(personal_resonance=-10.0, group_resonance=50.0, world_fatigue=10.0)
    
    def test_similar_states_are_detected(self):
        """测试：检测相似状态（用于剪枝）"""
        # Given
        state1 = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        state2 = GameState(personal_resonance=52.0, group_resonance=31.0, world_fatigue=21.0)
        
        # When & Then
        assert state1.is_similar_to(state2, threshold=5.0) is True
    
    def test_dissimilar_states_are_not_similar(self):
        """测试：差异大的状态不相似"""
        # Given
        state1 = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        state2 = GameState(personal_resonance=70.0, group_resonance=30.0, world_fatigue=20.0)
        
        # When & Then
        assert state1.is_similar_to(state2, threshold=5.0) is False


class TestDialogueNodeDomain:
    """领域模型测试 - DialogueNode 值对象"""
    
    def test_valid_node_creation(self):
        """测试：创建有效的对话节点"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        
        # When
        node = DialogueNode(
            id="scene_1",
            node_type=NodeType.SCENE,
            content="你站在北高峰索道站台",
            state=state
        )
        
        # Then
        assert node.id == "scene_1"
        assert node.content == "你站在北高峰索道站台"
        assert node.is_leaf() is True
    
    def test_empty_id_raises_error(self):
        """测试：空ID应抛出错误"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        
        # When & Then
        with pytest.raises(ValueError, match="节点ID不能为空"):
            DialogueNode(id="", node_type=NodeType.SCENE, content="内容", state=state)
    
    def test_empty_content_raises_error(self):
        """测试：空内容应抛出错误"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        
        # When & Then
        with pytest.raises(ValueError, match="节点内容不能为空"):
            DialogueNode(id="scene_1", node_type=NodeType.SCENE, content="", state=state)
    
    def test_ending_node_cannot_have_children(self):
        """测试：结局节点不能有子节点"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        child_state = GameState(personal_resonance=60.0, group_resonance=30.0, world_fatigue=20.0)
        
        # When & Then
        with pytest.raises(ValueError, match="结局节点不能有子节点"):
            DialogueNode(
                id="ending_1",
                node_type=NodeType.ENDING,
                content="你幸存了下来",
                state=state,
                children=[DialogueNode(id="child", node_type=NodeType.SCENE, content="内容", state=child_state)]
            )
    
    def test_add_child_to_scene_node(self):
        """测试：向场景节点添加子节点"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        parent = DialogueNode(id="scene_1", node_type=NodeType.SCENE, content="场景", state=state)
        child = DialogueNode(id="choice_1", node_type=NodeType.CHOICE, content="选择", state=state)
        
        # When
        parent.add_child(child)
        
        # Then
        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent_id == "scene_1"
    
    def test_cannot_add_child_to_ending_node(self):
        """测试：不能向结局节点添加子节点"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        ending = DialogueNode(id="ending_1", node_type=NodeType.ENDING, content="结局", state=state)
        child = DialogueNode(id="choice_1", node_type=NodeType.CHOICE, content="选择", state=state)
        
        # When & Then
        with pytest.raises(ValueError, match="结局节点不能添加子节点"):
            ending.add_child(child)
    
    def test_duplicate_child_id_raises_error(self):
        """测试：重复的子节点ID应抛出错误"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        parent = DialogueNode(id="scene_1", node_type=NodeType.SCENE, content="场景", state=state)
        child1 = DialogueNode(id="choice_1", node_type=NodeType.CHOICE, content="选择1", state=state)
        child2 = DialogueNode(id="choice_1", node_type=NodeType.CHOICE, content="选择2", state=state)
        
        # When
        parent.add_child(child1)
        
        # Then
        with pytest.raises(ValueError, match="子节点ID重复"):
            parent.add_child(child2)
    
    def test_node_depth_calculation(self):
        """测试：计算节点深度"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        root = DialogueNode(id="root", node_type=NodeType.SCENE, content="根", state=state)
        child1 = DialogueNode(id="child1", node_type=NodeType.CHOICE, content="子1", state=state)
        child2 = DialogueNode(id="child2", node_type=NodeType.ENDING, content="结局", state=state)
        
        # When
        root.add_child(child1)
        child1.add_child(child2)
        
        # Then
        assert root.depth() == 2
        assert child1.depth() == 1
        assert child2.depth() == 0


class TestDialogueTreeDomain:
    """领域模型测试 - DialogueTree 聚合根"""
    
    def test_valid_tree_creation(self):
        """测试：创建有效的对话树"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        root = DialogueNode(id="root", node_type=NodeType.SCENE, content="开场", state=state)
        
        # When
        tree = DialogueTree(root, max_depth=20)
        
        # Then
        assert tree.root == root
        assert tree.total_nodes() == 1
        assert tree.is_valid() is True
    
    def test_duplicate_node_id_raises_error(self):
        """测试：重复的节点ID应抛出错误"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        root = DialogueNode(id="node1", node_type=NodeType.SCENE, content="根", state=state)
        # 手动创建重复ID（绕过add_child的检查）
        child1 = DialogueNode(id="node1", node_type=NodeType.CHOICE, content="子1", state=state)
        root.children.append(child1)
        
        # When & Then
        with pytest.raises(ValueError, match="节点ID重复"):
            DialogueTree(root)
    
    def test_get_node_by_id(self):
        """测试：根据ID获取节点"""
        # Given
        state = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        root = DialogueNode(id="root", node_type=NodeType.SCENE, content="根", state=state)
        child = DialogueNode(id="child1", node_type=NodeType.CHOICE, content="子", state=state)
        root.add_child(child)
        tree = DialogueTree(root)
        
        # When
        node = tree.get_node("child1")
        
        # Then
        assert node == child
    
    def test_total_nodes_count(self):
        """测试：计算总节点数"""
        # Given & When
        tree = DialogueTreeBuilder.create_simple_tree(scene_count=2, choices_per_scene=2)
        
        # Then
        # 结构：root + (2 choices * 2 endings) = 1 + 2 + 4 = 7
        assert tree.total_nodes() == 7
    
    def test_max_depth_validation(self):
        """测试：最大深度验证"""
        # Given
        tree = DialogueTreeBuilder.create_simple_tree(scene_count=3, choices_per_scene=2)
        
        # When & Then
        assert tree.max_depth_reached() <= tree.max_depth
        assert tree.is_valid() is True
    
    def test_prune_similar_branches(self):
        """测试：剪枝相似分支"""
        # Given
        state1 = GameState(personal_resonance=50.0, group_resonance=30.0, world_fatigue=20.0)
        state2 = GameState(personal_resonance=51.0, group_resonance=31.0, world_fatigue=21.0)  # 相似
        
        root = DialogueNode(id="root", node_type=NodeType.SCENE, content="根", state=state1)
        child1 = DialogueNode(id="child1", node_type=NodeType.CHOICE, content="子1", state=state1)
        child2 = DialogueNode(id="child2", node_type=NodeType.CHOICE, content="子2", state=state2)
        root.add_child(child1)
        root.add_child(child2)
        
        tree = DialogueTree(root)
        
        # When
        pruned_count = tree.prune_similar_branches(threshold=5.0)
        
        # Then
        assert pruned_count >= 1  # 至少剪掉了1个相似分支


class TestDialogueTreeBuilderService:
    """领域服务测试 - DialogueTreeBuilder"""
    
    def test_create_simple_tree(self):
        """测试：创建简单的测试树"""
        # Given & When
        tree = DialogueTreeBuilder.create_simple_tree(scene_count=2, choices_per_scene=2)
        
        # Then
        assert tree.root.id == "root"
        assert len(tree.root.children) == 2
        assert tree.is_valid() is True
    
    def test_tree_structure_is_valid(self):
        """测试：生成的树结构是有效的"""
        # Given & When
        tree = DialogueTreeBuilder.create_simple_tree(scene_count=3, choices_per_scene=3)
        
        # Then
        assert tree.is_valid() is True
        assert tree.total_nodes() > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

