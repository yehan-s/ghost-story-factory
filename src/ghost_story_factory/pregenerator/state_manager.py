"""状态管理器

负责游戏状态的哈希、去重和剪枝。

v4 guided 模式约束：
- 支持“近似状态合并”但必须允许按 scope（例如 depth/beat）做分桶，
  避免跨深度合并导致主线深度被压扁。
- 旧 checkpoint 可能保存的是 legacy 结构（scene -> list[...]），需要保持兼容。
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Any, Optional
from copy import deepcopy


class StateManager:
    """游戏状态管理器"""

    def __init__(self):
        """初始化状态管理器"""
        self.state_cache: Dict[str, str] = {}  # 状态哈希 -> 节点ID 的映射
        # 近似状态合并索引：
        # - 新结构：scene -> {scope_key -> list[(state_hash, key_state)]}
        # - legacy：scene -> list[(state_hash, key_state)]
        self.scene_index: Dict[str, Any] = {}

    def get_state_hash(self, game_state: Dict[str, Any]) -> str:
        """计算游戏状态的哈希值（用于精确去重）。"""
        key_state = {
            "scene": game_state.get("current_scene"),
            "PR": game_state.get("PR", 0),
            "GR": game_state.get("GR", 0),
            "time": game_state.get("time", "00:00"),
            "flags": sorted(game_state.get("flags", {}).items()),
            "inventory": sorted(game_state.get("inventory", [])),
        }

        state_json = json.dumps(key_state, sort_keys=True)
        return hashlib.md5(state_json.encode()).hexdigest()

    def _quantize_key_state(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """对关键状态做量化，便于近似匹配。

        注意：这不是“真相”，只是为了削减状态爆炸的近似索引。
        guided 模式应通过 scope 限制合并范围，避免跨深度合并。
        """
        return {
            "scene": game_state.get("current_scene"),
            "PR": int(round(game_state.get("PR", 0) / 5) * 5),
            "GR": int(round(game_state.get("GR", 0) / 5) * 5),
            "time_bin": self._quantize_time(game_state.get("time", "00:00")),
            "flags": tuple(
                sorted(
                    [(k, v) for k, v in game_state.get("flags", {}).items() if k.startswith("关键_")]
                )
            ),
            "inventory_core": tuple(sorted(game_state.get("inventory", [])[:3])),
        }

    def _quantize_time(self, time_str: str) -> str:
        """将时间量化到 10 分钟粒度，减少状态爆炸。"""
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
        return state_hash in self.state_cache

    def register_state(self, state_hash: str, node_id: str):
        self.state_cache[state_hash] = node_id

    def _ensure_scene_bucket(self, scene: str, scope_key: str):
        """确保 scene_index[scene] 是 dict 并返回指定 scope 的 bucket list。

        兼容：
        - 若 scene_index[scene] 是 legacy list，则转换为 {"": legacy_list}。
        """
        container = self.scene_index.get(scene)
        if container is None:
            self.scene_index[scene] = {scope_key: []}
            return self.scene_index[scene][scope_key]

        if isinstance(container, list):
            # legacy checkpoint
            self.scene_index[scene] = {"": container}
            container = self.scene_index[scene]

        if not isinstance(container, dict):
            # 异常结构，直接重置（不破坏主流程）
            self.scene_index[scene] = {scope_key: []}
            return self.scene_index[scene][scope_key]

        container.setdefault(scope_key, [])
        return container[scope_key]

    def register_scene_index(self, game_state: Dict[str, Any], state_hash: str, scope: Optional[str] = None):
        """注册到场景近似索引，用于后续近似合并。

        Args:
            game_state: 游戏状态
            state_hash: 精确哈希
            scope: 近似合并的分桶键（例如 depth/beat）。None 表示 legacy 全场景桶。
        """
        scene = game_state.get("current_scene")
        if not scene:
            return
        scope_key = str(scope or "")
        key = self._quantize_key_state(game_state)
        bucket = self._ensure_scene_bucket(scene, scope_key)
        bucket.append((state_hash, key))

    def find_approximate(self, game_state: Dict[str, Any], scope: Optional[str] = None) -> Optional[str]:
        """在同场景内查找近似状态对应的节点ID（若已注册）。

        Args:
            game_state: 待匹配状态
            scope: 分桶键。None 表示 legacy 行为（全场景桶）。
        """
        scene = game_state.get("current_scene")
        if not scene:
            return None

        scope_key = str(scope or "")
        container = self.scene_index.get(scene, {})

        if isinstance(container, list):
            # legacy
            candidates = container if scope_key == "" else []
        elif isinstance(container, dict):
            candidates = container.get(scope_key, [])
        else:
            candidates = []

        target = self._quantize_key_state(game_state)
        for state_hash, key in candidates:
            if key == target and state_hash in self.state_cache:
                return self.state_cache[state_hash]
        return None

    def get_node_by_state(self, state_hash: str) -> Optional[str]:
        return self.state_cache.get(state_hash)

    def should_merge_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> bool:
        """判断两个状态是否应该合并（当前未用于核心路径，保留历史实现）。"""
        pr_diff = abs(state1.get("PR", 0) - state2.get("PR", 0))
        gr_diff = abs(state1.get("GR", 0) - state2.get("GR", 0))

        if pr_diff > 5 or gr_diff > 5:
            return False

        if state1.get("current_scene") != state2.get("current_scene"):
            return False

        flags1 = state1.get("flags", {})
        flags2 = state2.get("flags", {})

        key_flags1 = {k: v for k, v in flags1.items() if k.startswith("关键_")}
        key_flags2 = {k: v for k, v in flags2.items() if k.startswith("关键_")}

        return key_flags1 == key_flags2

    def should_prune(self, game_state: Dict[str, Any], depth: int, max_depth: int) -> bool:
        """判断是否应该剪枝（停止生成）。"""
        if depth >= max_depth:
            return True

        if game_state.get("PR", 0) >= 100:
            return True

        flags = game_state.get("flags", {})
        if any(k.startswith("结局_") for k in flags.keys()):
            return True

        return False

    def update_state(self, base_state: Dict[str, Any], consequences: Dict[str, Any]) -> Dict[str, Any]:
        """根据选择的后果更新游戏状态。"""
        new_state = deepcopy(base_state)

        normalized = dict(consequences or {})
        if "timestamp" in normalized and "time" not in normalized:
            normalized["time"] = normalized.pop("timestamp")
        if "current_scene" in normalized and "scene" not in normalized:
            normalized["scene"] = normalized.pop("current_scene")
        if "resonance" in normalized and "GR" not in normalized:
            normalized["GR"] = normalized.pop("resonance")

        if "PR" in normalized:
            try:
                delta = int(normalized["PR"]) if not isinstance(normalized["PR"], bool) else 0
            except Exception:
                delta = 0
            new_state["PR"] = max(0, min(100, int(new_state.get("PR", 0)) + delta))

        if "GR" in normalized:
            try:
                delta = int(normalized["GR"]) if not isinstance(normalized["GR"], bool) else 0
            except Exception:
                delta = 0
            new_state["GR"] = max(0, min(100, int(new_state.get("GR", 0)) + delta))

        if "WF" in normalized:
            try:
                delta = int(normalized["WF"]) if not isinstance(normalized["WF"], bool) else 0
            except Exception:
                delta = 0
            new_state["WF"] = max(0, min(100, int(new_state.get("WF", 0)) + delta))

        if "scene" in normalized:
            new_state["current_scene"] = normalized["scene"]

        if "flags" in normalized:
            new_state.setdefault("flags", {})
            new_state["flags"].update(normalized["flags"])

        if "inventory" in normalized:
            new_state.setdefault("inventory", [])
            for item in normalized["inventory"]:
                if item not in new_state["inventory"]:
                    new_state["inventory"].append(item)

        if "time" in normalized:
            value = str(normalized["time"]).strip()
            try:
                if value.startswith(("+", "-")):
                    import re

                    m = re.match(r"([+-])(\d+)(?:\s*(?:min|m|分钟)?)?", value)
                    if m:
                        sign, mins = m.groups()
                        delta = int(mins) * (1 if sign == "+" else -1)
                        base = new_state.get("time", "00:00")
                        h, mm = base.split(":", 1)
                        total = int(h) * 60 + int(mm) + delta
                        total = max(0, min(4 * 60, total))
                        new_state["time"] = f"{total // 60:02d}:{total % 60:02d}"
                elif ":" in value:
                    hh, mm = value.split(":", 1)
                    _ = int(hh)
                    _ = int(mm)
                    new_state["time"] = f"{int(hh):02d}:{int(mm):02d}"
                else:
                    mins = int(value)
                    base = new_state.get("time", "00:00")
                    h, mm = base.split(":", 1)
                    total = int(h) * 60 + int(mm) + mins
                    total = max(0, min(4 * 60, total))
                    new_state["time"] = f"{total // 60:02d}:{total % 60:02d}"
            except Exception:
                pass

        return new_state

    def clear_cache(self):
        self.state_cache.clear()
        self.scene_index.clear()

    def get_cache_size(self) -> int:
        return len(self.state_cache)
