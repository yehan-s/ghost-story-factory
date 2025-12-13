"""
状态哈希计算器

用于对话树生成过程中的状态去重，识别重复的游戏状态并合并节点，
防止对话树爆炸性增长。

设计理念：
- 只哈希核心状态字段（影响后续选择的字段）
- 忽略无关字段（如时间戳）
- 使用 MD5（快速且冲突概率极低）
"""

import hashlib
import json
from typing import Dict, Any


class StateHasher:
    """
    游戏状态哈希计算器

    用法：
        hasher = StateHasher()
        hash1 = hasher.hash(state1)
        hash2 = hasher.hash(state2)

        if hash1 == hash2:
            print("状态相同，可以合并节点")
    """

    def __init__(self):
        """初始化哈希器"""
        pass

    def hash(self, game_state: Dict[str, Any]) -> str:
        """
        计算游戏状态的哈希值

        只考虑核心状态字段：
        - PR (个人共鸣度): 影响选择点生成
        - GR (全局共鸣度): 影响实体行为
        - WF (世界疲劳值): 影响结局判定
        - current_scene (当前场景): 决定可用选择
        - inventory (道具栏): 影响前置条件检查
        - flags (标志位): 记录事件触发状态

        忽略字段：
        - timestamp (时间戳): 不影响后续选择逻辑
        - consequence_tree (历史记录): 仅用于统计，不影响游戏

        Args:
            game_state: 游戏状态字典

        Returns:
            MD5 哈希字符串（32字符）

        Example:
            >>> state = {
            ...     "PR": 45,
            ...     "GR": 10,
            ...     "WF": 2,
            ...     "current_scene": "S3",
            ...     "inventory": ["暗号:36-3=33", "金属锤柄"],
            ...     "flags": {"失魂者_已拍照": True},
            ...     "timestamp": "02:30"  # 忽略
            ... }
            >>> hasher = StateHasher()
            >>> hash_value = hasher.hash(state)
            >>> len(hash_value)
            32
        """
        # 提取核心状态（确保字段存在）
        core_state = {
            "PR": game_state.get("PR", 5),
            "GR": game_state.get("GR", 0),
            "WF": game_state.get("WF", 0),
            "current_scene": game_state.get("current_scene", "S1"),
            "inventory": sorted(game_state.get("inventory", [])),  # 排序确保一致性
            "flags": {
                k: v for k, v in sorted(game_state.get("flags", {}).items())
            }  # 排序字典键
        }

        # 序列化为 JSON 字符串（sort_keys=True 确保顺序一致）
        state_json = json.dumps(core_state, sort_keys=True, ensure_ascii=False)

        # 计算 MD5 哈希
        hash_value = hashlib.md5(state_json.encode('utf-8')).hexdigest()

        return hash_value

    def is_duplicate(
        self,
        state1: Dict[str, Any],
        state2: Dict[str, Any]
    ) -> bool:
        """
        判断两个状态是否重复（辅助方法）

        Args:
            state1: 第一个状态
            state2: 第二个状态

        Returns:
            True 如果状态相同
        """
        return self.hash(state1) == self.hash(state2)


# 辅助函数：快速哈希（无需实例化）
def quick_hash(game_state: Dict[str, Any]) -> str:
    """
    快速计算状态哈希（无需实例化 StateHasher）

    Args:
        game_state: 游戏状态字典

    Returns:
        MD5 哈希字符串
    """
    hasher = StateHasher()
    return hasher.hash(game_state)
