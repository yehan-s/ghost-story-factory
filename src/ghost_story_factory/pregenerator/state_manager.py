"""
状态管理器

负责游戏状态的哈希、去重和剪枝
"""

import hashlib
import json
from typing import Dict, Any, Optional
from copy import deepcopy


class StateManager:
    """游戏状态管理器"""

    def __init__(self):
        """初始化状态管理器"""
        self.state_cache = {}  # 状态哈希 -> 节点ID 的映射

    def get_state_hash(self, game_state: Dict[str, Any]) -> str:
        """
        计算游戏状态的哈希值

        用于判断两个状态是否相同（去重）

        Args:
            game_state: 游戏状态字典

        Returns:
            状态哈希字符串
        """
        # 提取关键状态
        key_state = {
            "scene": game_state.get("current_scene"),
            "PR": game_state.get("PR", 0),
            "GR": game_state.get("GR", 0),
            "flags": sorted(game_state.get("flags", {}).items()),
            "inventory": sorted(game_state.get("inventory", []))
        }

        # 转为 JSON 并计算哈希
        state_json = json.dumps(key_state, sort_keys=True)
        return hashlib.md5(state_json.encode()).hexdigest()

    def is_duplicate(self, state_hash: str) -> bool:
        """
        判断状态是否已存在

        Args:
            state_hash: 状态哈希

        Returns:
            是否已存在
        """
        return state_hash in self.state_cache

    def register_state(self, state_hash: str, node_id: str):
        """
        注册新状态

        Args:
            state_hash: 状态哈希
            node_id: 节点ID
        """
        self.state_cache[state_hash] = node_id

    def get_node_by_state(self, state_hash: str) -> Optional[str]:
        """
        根据状态哈希获取节点ID

        Args:
            state_hash: 状态哈希

        Returns:
            节点ID（如果存在）
        """
        return self.state_cache.get(state_hash)

    def should_merge_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> bool:
        """
        判断两个状态是否应该合并

        策略：PR/GR 差异 <= 5，场景相同，主要标志位相同

        Args:
            state1: 状态1
            state2: 状态2

        Returns:
            是否应该合并
        """
        # PR/GR 差异小于 5
        pr_diff = abs(state1.get("PR", 0) - state2.get("PR", 0))
        gr_diff = abs(state1.get("GR", 0) - state2.get("GR", 0))

        if pr_diff > 5 or gr_diff > 5:
            return False

        # 场景必须相同
        if state1.get("current_scene") != state2.get("current_scene"):
            return False

        # 关键标志位必须相同
        flags1 = state1.get("flags", {})
        flags2 = state2.get("flags", {})

        # 提取关键标志位（以 "关键_" 开头的标志）
        key_flags1 = {k: v for k, v in flags1.items() if k.startswith("关键_")}
        key_flags2 = {k: v for k, v in flags2.items() if k.startswith("关键_")}

        if key_flags1 != key_flags2:
            return False

        return True

    def should_prune(self, game_state: Dict[str, Any], depth: int, max_depth: int) -> bool:
        """
        判断是否应该剪枝（停止生成）

        Args:
            game_state: 游戏状态
            depth: 当前深度
            max_depth: 最大深度

        Returns:
            是否剪枝
        """
        # 1. 达到最大深度
        if depth >= max_depth:
            return True

        # 2. PR 过高（恐惧值爆表，游戏失败）
        if game_state.get("PR", 0) >= 100:
            return True

        # 3. 检查是否到达结局
        flags = game_state.get("flags", {})
        if any(k.startswith("结局_") for k in flags.keys()):
            return True

        return False

    def update_state(
        self,
        base_state: Dict[str, Any],
        consequences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据选择的后果更新游戏状态

        Args:
            base_state: 基础状态
            consequences: 后果字典

        Returns:
            更新后的状态
        """
        new_state = deepcopy(base_state)

        # 更新 PR
        if "PR" in consequences:
            new_state["PR"] = max(0, min(100, new_state["PR"] + consequences["PR"]))

        # 更新 GR
        if "GR" in consequences:
            new_state["GR"] = max(0, min(100, new_state["GR"] + consequences["GR"]))

        # 更新 WF
        if "WF" in consequences:
            new_state["WF"] = max(0, min(100, new_state["WF"] + consequences["WF"]))

        # 更新场景
        if "scene" in consequences:
            new_state["current_scene"] = consequences["scene"]

        # 更新标志位
        if "flags" in consequences:
            new_state.setdefault("flags", {})
            new_state["flags"].update(consequences["flags"])

        # 更新物品栏
        if "inventory" in consequences:
            new_state.setdefault("inventory", [])
            for item in consequences["inventory"]:
                if item not in new_state["inventory"]:
                    new_state["inventory"].append(item)

        # 更新时间
        if "time" in consequences:
            new_state["time"] = consequences["time"]

        return new_state

    def clear_cache(self):
        """清空状态缓存"""
        self.state_cache.clear()

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self.state_cache)

