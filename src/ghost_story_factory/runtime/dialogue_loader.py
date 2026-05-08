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
        """获取选择列表（过滤 hidden=true 的选项）"""
        if node_id is None:
            node_id = self.current_node_id

        node = self.get_node(node_id)
        if not node:
            return []
        choices = node.get("choices", []) or []
        return [c for c in choices if not c.get("hidden")]

    def can_traverse(self, choice_id: str, node_id: Optional[str] = None) -> bool:
        """检测某个选项从当前节点是否可到达下一个节点。"""
        if node_id is None:
            node_id = self.current_node_id
        node = self.get_node(node_id)
        if not node:
            return False
        for ch in (node.get("choices", []) or []):
            if ch.get("choice_id") == choice_id:
                next_id = ch.get("next_node_id")
                if next_id and next_id in self.tree:
                    return True
                # 通过 parent_choice_id 唯一映射判断
                candidates = []
                for nid, nd in self.tree.items():
                    try:
                        if nd.get("parent_id") == node_id and nd.get("parent_choice_id") == choice_id:
                            candidates.append(nid)
                    except Exception:
                        continue
                if len(candidates) == 1:
                    return True
                # 父节点仅一个 children 也可推进
                children = (node.get("children") or [])
                if len(children) == 1 and children[0] in self.tree:
                    return True
                return False
        return False

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
                # 回退路径：有些旧检查点的 choice 可能未写回 next_node_id，
                # 但子节点记录了 parent_id 与 parent_choice_id，可通过它们恢复跳转
                # 1) 通过 parent_id/current_node 与 parent_choice_id=choice_id 定位唯一子节点
                candidates = []
                for nid, node in self.tree.items():
                    try:
                        if node.get("parent_id") == self.current_node_id and node.get("parent_choice_id") == choice_id:
                            candidates.append(nid)
                    except Exception:
                        continue
                if len(candidates) == 1:
                    self.current_node_id = candidates[0]
                    print(f"ℹ️  回退修复：基于 parent_choice_id → {self.current_node_id}")
                    return self.current_node_id
                # 2) 若找不到，但当前节点仅有一个 children，则按唯一子节点前进
                node = self.get_node(self.current_node_id) or {}
                children = node.get("children", []) or []
                if len(children) == 1 and children[0] in self.tree:
                    self.current_node_id = children[0]
                    print(f"ℹ️  回退修复：按唯一子节点前进 → {self.current_node_id}")
                    return self.current_node_id
                # 3) 仍不可用：直接失败。
                # 坏树必须在生成/导入审计阶段修掉，运行时不能伪造剧情。
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
