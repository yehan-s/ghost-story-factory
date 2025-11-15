"""
节点文本填充器（Stage D）

用途：
- 在对话树结构稳定之后，根据 PlotSkeleton 的节拍信息为节点追加元数据；
- 对缺失或过于空白的叙事文本做占位填充，避免出现完全空节点。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .skeleton_model import PlotSkeleton


class NodeTextFiller:
    """节点文本填充器"""

    def __init__(self, skeleton: Optional[PlotSkeleton] = None):
        """
        初始化填充器

        Args:
            skeleton: 可选的 PlotSkeleton，用于提供 beat_type / tension 信息
        """
        self.skeleton = skeleton

    # ---------------- 内部辅助：节拍映射 ----------------

    def _get_flat_beats(self):
        """展开骨架的所有节拍为一维列表"""
        if not self.skeleton:
            return []
        try:
            return list(self.skeleton.beats)
        except Exception:
            return []

    def _beat_for_depth(self, depth: int):
        """
        根据节点深度获取对应节拍。

        约定：
        - root 深度为 0；
        - depth=1 对应第一个节拍；
        - 超出范围时使用最后一个节拍。
        """
        beats = self._get_flat_beats()
        if not beats:
            return None
        idx = max(0, depth - 1)
        if idx >= len(beats):
            idx = len(beats) - 1
        return beats[idx]

    # ---------------- 对外入口 ----------------

    def fill(self, dialogue_tree: Dict[str, Any]) -> Dict[str, Any]:
        """
        填充对话树中的节点文本与节拍元数据。

        行为：
        - 为每个节点追加 metadata.beat_type / metadata.tension_level / metadata.act_index；
        - 若 narrative 为空或全空白，则生成一个简单占位叙事。

        Args:
            dialogue_tree: 对话树字典（node_id -> node_dict）

        Returns:
            更新后的对话树（同一对象）
        """
        for node_id, node in dialogue_tree.items():
            if not isinstance(node, dict):
                continue

            depth = int(node.get("depth", 0))
            beat = self._beat_for_depth(depth)

            # 填写元数据
            meta = node.setdefault("metadata", {})
            if beat is not None:
                try:
                    bt = getattr(beat, "beat_type", None)
                    tl = getattr(beat, "tension_level", None)
                    act_idx = getattr(beat, "act_index", None)
                    if bt and "beat_type" not in meta:
                        meta["beat_type"] = bt
                    if tl is not None and "tension_level" not in meta:
                        meta["tension_level"] = tl
                    if act_idx is not None and "act_index" not in meta:
                        meta["act_index"] = act_idx
                except Exception:
                    # 元数据失败时静默忽略，避免影响主流程
                    pass

            # 填充叙事占位
            narrative = node.get("narrative")
            if not isinstance(narrative, str) or not narrative.strip():
                if beat is not None:
                    bt = getattr(beat, "beat_type", "beat")
                    node["narrative"] = f"[{bt}] 占位叙事（自动填充）。"
                else:
                    node["narrative"] = "占位叙事（自动填充）。"

        return dialogue_tree

