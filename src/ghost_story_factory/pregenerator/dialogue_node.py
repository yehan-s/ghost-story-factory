"""
对话节点数据结构

定义对话树的节点结构
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class DialogueNode:
    """对话树节点"""

    # 节点标识
    node_id: str
    scene: str
    depth: int  # 从根节点算起的深度

    # 游戏状态（完整快照）
    game_state: Dict[str, Any] = field(default_factory=dict)
    state_hash: Optional[str] = None  # 状态哈希（用于去重）

    # 内容
    narrative: Optional[str] = None  # 叙事文本（响应或开场）
    choices: List[Dict[str, Any]] = field(default_factory=list)  # 选择列表

    # 树结构
    parent_id: Optional[str] = None
    parent_choice_id: Optional[str] = None
    children: List[str] = field(default_factory=list)  # 子节点 ID 列表

    # 元数据
    is_ending: bool = False
    ending_type: Optional[str] = None
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于保存）"""
        return {
            "node_id": self.node_id,
            "scene": self.scene,
            "depth": self.depth,
            "game_state": self.game_state,
            "state_hash": self.state_hash,
            "narrative": self.narrative,
            "choices": self.choices,
            "parent_id": self.parent_id,
            "parent_choice_id": self.parent_choice_id,
            "children": self.children,
            "is_ending": self.is_ending,
            "ending_type": self.ending_type,
            "generated_at": self.generated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialogueNode':
        """从字典创建节点"""
        return cls(
            node_id=data.get("node_id", ""),
            scene=data.get("scene", ""),
            depth=data.get("depth", 0),
            game_state=data.get("game_state", {}),
            state_hash=data.get("state_hash"),
            narrative=data.get("narrative"),
            choices=data.get("choices", []),
            parent_id=data.get("parent_id"),
            parent_choice_id=data.get("parent_choice_id"),
            children=data.get("children", []),
            is_ending=data.get("is_ending", False),
            ending_type=data.get("ending_type"),
            generated_at=data.get("generated_at", "")
        )


def create_root_node(scene: str = "S1") -> DialogueNode:
    """
    创建根节点

    Args:
        scene: 初始场景

    Returns:
        根节点
    """
    return DialogueNode(
        node_id="root",
        scene=scene,
        depth=0,
        game_state={
            "PR": 5,  # 初始恐惧值
            "GR": 0,  # 初始获得真相值
            "WF": 0,  # 初始世界熟悉度
            "current_scene": scene,
            "inventory": [],
            "flags": {},
            "time": "00:00"
        },
        generated_at=datetime.now().isoformat()
    )

