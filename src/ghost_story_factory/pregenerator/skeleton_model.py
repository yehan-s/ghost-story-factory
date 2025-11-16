"""
故事骨架模型（PlotSkeleton）

用于描述结构层面的「幕 / 节拍 / 分支」信息，完全独立于具体文案。
后续 TreeBuilder 将在 guided 模式下按该骨架生成对话树。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional


BeatType = Literal["setup", "escalation", "twist", "climax", "aftermath"]
BranchType = Literal["CRITICAL", "NORMAL", "MICRO"]


@dataclass
class BranchSpec:
    """分支规格（定义某个节拍下可用的分支类型与数量约束）"""

    branch_type: BranchType = "NORMAL"
    max_children: int = 2
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BranchSpec":
        """从字典构建 BranchSpec（容错处理缺省字段）"""
        if data is None:
            return cls()
        return cls(
            branch_type=data.get("branch_type", "NORMAL") or "NORMAL",
            max_children=int(data.get("max_children", 2) or 2),
            notes=str(data.get("notes", "") or ""),
        )


@dataclass
class BeatConfig:
    """单个节拍配置"""

    id: str
    act_index: int
    beat_type: BeatType
    tension_level: int = 5
    is_critical_branch_point: bool = False
    leads_to_ending: bool = False
    branches: List[BranchSpec] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatConfig":
        """从字典构建 BeatConfig，并做轻量校验"""
        if not isinstance(data, dict):
            raise ValueError(f"BeatConfig 需要字典输入，得到: {type(data)}")

        beat_type = data.get("beat_type", "setup") or "setup"
        if beat_type not in ("setup", "escalation", "twist", "climax", "aftermath"):
            raise ValueError(f"非法 beat_type: {beat_type}")

        tension = int(data.get("tension_level", 5) or 5)
        # 简单裁剪到 1-10 区间，避免乱值
        tension = max(1, min(10, tension))

        branches_raw = data.get("branches") or []
        branches = [BranchSpec.from_dict(b) for b in branches_raw if isinstance(b, dict)]

        return cls(
            id=str(data.get("id") or ""),
            act_index=int(data.get("act_index", 1) or 1),
            beat_type=beat_type,  # type: ignore[arg-type]
            tension_level=tension,
            is_critical_branch_point=bool(data.get("is_critical_branch_point", False)),
            leads_to_ending=bool(data.get("leads_to_ending", False)),
            branches=branches,
        )


@dataclass
class ActConfig:
    """单幕配置"""

    index: int
    label: str
    beats: List[BeatConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActConfig":
        """从字典构建 ActConfig"""
        if not isinstance(data, dict):
            raise ValueError(f"ActConfig 需要字典输入，得到: {type(data)}")

        beats_raw = data.get("beats") or []
        beats = [BeatConfig.from_dict(b) for b in beats_raw if isinstance(b, dict)]

        return cls(
            index=int(data.get("index", 1) or 1),
            label=str(data.get("label") or f"Act {data.get('index', 1)}"),
            beats=beats,
        )


@dataclass
class SkeletonConfig:
    """骨架全局配置（深度 / 结局等约束）"""

    # 默认按中长篇都市恐怖故事的规模设计：
    # - 主线最小深度 ~18
    # - 目标主线深度 ~24
    # 可通过骨架 JSON 或环境进一步调整。
    min_main_depth: int = 18
    target_main_depth: int = 24
    target_endings: int = 3
    max_branches_per_node: int = 3

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SkeletonConfig":
        """从字典构建 SkeletonConfig"""
        if not isinstance(data, dict):
            return cls()
        return cls(
            min_main_depth=int(data.get("min_main_depth", 20) or 20),
            target_main_depth=int(data.get("target_main_depth", 30) or 30),
            target_endings=int(data.get("target_endings", 3) or 3),
            max_branches_per_node=int(data.get("max_branches_per_node", 3) or 3),
        )


@dataclass
class PlotSkeleton:
    """故事骨架顶层对象"""

    title: str
    acts: List[ActConfig]
    config: SkeletonConfig = field(default_factory=SkeletonConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlotSkeleton":
        """
        从字典构建 PlotSkeleton。

        期望结构：
        {
          "title": "...",
          "config": {...},
          "acts": [ { "index": 1, "label": "...", "beats": [...] }, ... ],
          "metadata": {...}  # 可选
        }
        """
        if not isinstance(data, dict):
            raise ValueError(f"PlotSkeleton 需要字典输入，得到: {type(data)}")

        acts_raw = data.get("acts") or []
        if not acts_raw:
            raise ValueError("PlotSkeleton.acts 不能为空")

        acts = [ActConfig.from_dict(a) for a in acts_raw if isinstance(a, dict)]
        if not acts:
            raise ValueError("PlotSkeleton.acts 解析失败（无有效幕信息）")

        cfg = SkeletonConfig.from_dict(data.get("config") or {})
        title = str(data.get("title") or "")
        if not title:
            title = "未命名故事"

        meta = data.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = {}

        return cls(
            title=title,
            acts=acts,
            config=cfg,
            metadata=meta,
        )

    def to_dict(self) -> Dict[str, Any]:
        """转为可 JSON 序列化的字典结构"""
        return asdict(self)

    # 一些便捷属性 / 统计函数，供指标脚本或调试使用

    @property
    def num_acts(self) -> int:
        return len(self.acts)

    @property
    def beats(self) -> List[BeatConfig]:
        """展开所有节拍为一维列表"""
        items: List[BeatConfig] = []
        for act in self.acts:
            items.extend(act.beats)
        return items

    @property
    def num_beats(self) -> int:
        return len(self.beats)

    @property
    def num_critical_beats(self) -> int:
        return sum(1 for b in self.beats if b.is_critical_branch_point)

    @property
    def num_ending_beats(self) -> int:
        return sum(1 for b in self.beats if b.leads_to_ending)
