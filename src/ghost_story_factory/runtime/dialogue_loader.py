"""
对话树加载器

从数据库加载对话树并提供查询接口
"""

from typing import Dict, Any, List, Optional
from ..database import DatabaseManager


class DialogueTreeLoader:
    """对话树加载器"""

    def __init__(self, db: DatabaseManager, story_id: int, character_id: int):
        """
        初始化加载器

        Args:
            db: 数据库管理器
            story_id: 故事 ID
            character_id: 角色 ID
        """
        self.db = db
        self.story_id = story_id
        self.character_id = character_id
        self.tree = None
        self.current_node_id = "root"

        self.load()

    def load(self):
        """加载对话树"""
        print(f"📂 加载对话树：story_id={self.story_id}, character_id={self.character_id}")

        self.tree = self.db.load_dialogue_tree(self.story_id, self.character_id)

        if self.tree:
            print(f"✅ 对话树已加载：{len(self.tree)} 个节点")
        else:
            raise ValueError("对话树加载失败")

    def get_current_node(self) -> Dict[str, Any]:
        """获取当前节点"""
        if not self.tree or self.current_node_id not in self.tree:
            raise ValueError(f"节点不存在：{self.current_node_id}")

        return self.tree[self.current_node_id]

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取指定节点"""
        if not self.tree:
            return None

        return self.tree.get(node_id)

    def get_narrative(self, node_id: str = None) -> str:
        """获取叙事文本"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.get_node(node_id)
        return node.get("narrative", "") if node else ""

    def get_choices(self, node_id: str = None) -> List[Dict[str, Any]]:
        """获取选择列表"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.get_node(node_id)
        return node.get("choices", []) if node else []

    def select_choice(self, choice_id: str) -> Optional[str]:
        """
        选择一个选项

        Args:
            choice_id: 选择 ID

        Returns:
            下一个节点 ID（如果存在）
        """
        choices = self.get_choices()

        for choice in choices:
            if choice.get("choice_id") == choice_id:
                next_node_id = choice.get("next_node_id")
                if next_node_id and next_node_id in self.tree:
                    self.current_node_id = next_node_id
                    return next_node_id
                else:
                    print(f"⚠️  下一个节点不存在：{next_node_id}")
                    return None

        print(f"⚠️  选择不存在：{choice_id}")
        return None

    def is_ending(self, node_id: str = None) -> bool:
        """判断是否为结局节点"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.get_node(node_id)
        return node.get("is_ending", False) if node else False

    def get_ending_type(self, node_id: str = None) -> Optional[str]:
        """获取结局类型"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.get_node(node_id)
        return node.get("ending_type") if node else None

    def reset(self):
        """重置到根节点"""
        self.current_node_id = "root"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.tree:
            return {}

        total_nodes = len(self.tree)
        ending_nodes = [
            node_id for node_id, node in self.tree.items()
            if node.get("is_ending", False)
        ]

        max_depth = max(
            node.get("depth", 0) for node in self.tree.values()
        )

        return {
            "total_nodes": total_nodes,
            "ending_count": len(ending_nodes),
            "max_depth": max_depth
        }

