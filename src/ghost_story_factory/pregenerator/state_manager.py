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
        # 近似状态合并索引：scene -> 列表[(state_hash, key_state)]
        self.scene_index = {}

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
            "time": game_state.get("time", "00:00"),
            "flags": sorted(game_state.get("flags", {}).items()),
            "inventory": sorted(game_state.get("inventory", []))
        }

        # 转为 JSON 并计算哈希
        state_json = json.dumps(key_state, sort_keys=True)
        return hashlib.md5(state_json.encode()).hexdigest()

    def _quantize_key_state(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """对关键状态做量化，便于近似匹配"""
        return {
            "scene": game_state.get("current_scene"),
            "PR": int(round(game_state.get("PR", 0) / 5) * 5),
            "GR": int(round(game_state.get("GR", 0) / 5) * 5),
            "time_bin": self._quantize_time(game_state.get("time", "00:00")),
            "flags": tuple(sorted([(k, v) for k, v in game_state.get("flags", {}).items() if k.startswith("关键_")])),
            "inventory_core": tuple(sorted(game_state.get("inventory", [])[:3]))
        }

    def _quantize_time(self, time_str: str) -> str:
        """将时间量化到 10 分钟粒度，减少状态爆炸"""
        try:
            if not isinstance(time_str, str) or ":" not in time_str:
                return "00:00"
            h, m = time_str.split(":", 1)
            total = int(h) * 60 + int(m)
            bucket = (total // 10) * 10
            return f"{bucket // 60:02d}:{bucket % 60:02d}"
        except Exception:
            return "00:00"

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

    def register_scene_index(self, game_state: Dict[str, Any], state_hash: str):
        """注册到场景近似索引，用于后续近似合并"""
        scene = game_state.get("current_scene")
        if not scene:
            return
        key = self._quantize_key_state(game_state)
        self.scene_index.setdefault(scene, []).append((state_hash, key))

    def find_approximate(self, game_state: Dict[str, Any]) -> Optional[str]:
        """在同场景内查找近似状态对应的节点ID（若已注册）"""
        scene = game_state.get("current_scene")
        if not scene:
            return None
        candidates = self.scene_index.get(scene, [])
        target = self._quantize_key_state(game_state)
        for state_hash, key in candidates:
            if key == target and state_hash in self.state_cache:
                return self.state_cache[state_hash]
        return None

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

        # 统一/规范化后果字段名
        normalized = dict(consequences or {})
        # 时间字段别名：timestamp -> time
        if "timestamp" in normalized and "time" not in normalized:
            normalized["time"] = normalized.pop("timestamp")
        # 场景字段别名：current_scene -> scene
        if "current_scene" in normalized and "scene" not in normalized:
            normalized["scene"] = normalized.pop("current_scene")
        # 共鸣/真相度别名：resonance -> GR
        if "resonance" in normalized and "GR" not in normalized:
            normalized["GR"] = normalized.pop("resonance")

        # 更新 PR
        if "PR" in normalized:
            try:
                delta = int(normalized["PR"]) if not isinstance(normalized["PR"], bool) else 0
            except Exception:
                delta = 0
            new_state["PR"] = max(0, min(100, int(new_state.get("PR", 0)) + delta))

        # 更新 GR
        if "GR" in normalized:
            try:
                delta = int(normalized["GR"]) if not isinstance(normalized["GR"], bool) else 0
            except Exception:
                delta = 0
            new_state["GR"] = max(0, min(100, int(new_state.get("GR", 0)) + delta))

        # 更新 WF
        if "WF" in normalized:
            try:
                delta = int(normalized["WF"]) if not isinstance(normalized["WF"], bool) else 0
            except Exception:
                delta = 0
            new_state["WF"] = max(0, min(100, int(new_state.get("WF", 0)) + delta))

        # 更新场景
        if "scene" in normalized:
            new_state["current_scene"] = normalized["scene"]

        # 更新标志位
        if "flags" in normalized:
            new_state.setdefault("flags", {})
            new_state["flags"].update(normalized["flags"])

        # 更新物品栏
        if "inventory" in normalized:
            new_state.setdefault("inventory", [])
            for item in normalized["inventory"]:
                if item not in new_state["inventory"]:
                    new_state["inventory"].append(item)

        # 更新时间：支持绝对时间 (HH:MM) 与相对时间 (+5min / -3min / +5m / +5)
        if "time" in normalized:
            value = str(normalized["time"]).strip()
            try:
                if value.startswith(("+", "-")):
                    # 解析相对分钟
                    import re
                    m = re.match(r"([+-])(\d+)(?:\s*(?:min|m|分钟)?)?", value)
                    if m:
                        sign, mins = m.groups()
                        delta = int(mins) * (1 if sign == "+" else -1)
                        base = new_state.get("time", "00:00")
                        h, mm = base.split(":", 1)
                        total = int(h) * 60 + int(mm) + delta
                        total = max(0, min(4 * 60, total))  # 限制在 00:00-04:00 区间
                        new_state["time"] = f"{total // 60:02d}:{total % 60:02d}"
                elif ":" in value:
                    # 绝对时间
                    hh, mm = value.split(":", 1)
                    _ = int(hh); _ = int(mm)  # 校验
                    new_state["time"] = f"{int(hh):02d}:{int(mm):02d}"
                else:
                    # 纯数字视为分钟
                    mins = int(value)
                    base = new_state.get("time", "00:00")
                    h, mm = base.split(":", 1)
                    total = int(h) * 60 + int(mm) + mins
                    total = max(0, min(4 * 60, total))
                    new_state["time"] = f"{total // 60:02d}:{total % 60:02d}"
            except Exception:
                # 忽略无法解析的时间格式
                pass

        return new_state

    def clear_cache(self):
        """清空状态缓存"""
        self.state_cache.clear()
        self.scene_index.clear()

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self.state_cache)

