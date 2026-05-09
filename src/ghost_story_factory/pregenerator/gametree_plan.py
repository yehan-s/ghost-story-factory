"""GameTreePlan 中间层。

`PlotSkeleton` 只负责内容大纲;`GameTreePlan` 负责把大纲收敛成
GameTree v1 之前的沙盒拓扑计划。这里不生成最终节点文案,也不碰 DB schema。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .skeleton_model import BeatConfig, PlotSkeleton


@dataclass
class LocationPlan:
    """一个可探索地标。"""

    id: str
    label: str
    beat_ids: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)
    npc_ids: List[str] = field(default_factory=list)
    event_slots: List[str] = field(default_factory=list)


@dataclass
class ToolPlan:
    """可反复访问的工具节点计划。"""

    id: str
    location_id: str
    beat_id: str
    revisit_hooks: List[str] = field(default_factory=list)
    asset_cues: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NpcRoutePlan:
    """NPC 在沙盒地图中的最小出没计划。"""

    npc_id: str
    location_ids: List[str] = field(default_factory=list)
    beat_ids: List[str] = field(default_factory=list)


@dataclass
class BeatNodePlan:
    """beat 到未来 GameTree 节点的候选映射。"""

    beat_id: str
    node_id: str
    location_id: str
    sandbox_role: str = "landmark"
    event_slots: List[str] = field(default_factory=list)
    asset_cues: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AcceptancePlan:
    """ADR-010 最小沙盒骨架的计划级验收目标。"""

    min_locations: int = 4
    min_tools: int = 2
    requires_picker_hub: bool = True
    requires_stay_loop: bool = True
    requires_reaction_variant: bool = True


@dataclass
class GameTreePlan:
    """从 PlotSkeleton 派生的 GameTree v1 拓扑计划。"""

    title: str
    picker_location_id: str = ""
    story_id: str = "generated"
    start_node: str = "n_intro"
    locations: List[LocationPlan] = field(default_factory=list)
    tools: List[ToolPlan] = field(default_factory=list)
    npc_routes: List[NpcRoutePlan] = field(default_factory=list)
    beats: List[BeatNodePlan] = field(default_factory=list)
    presentation_defaults: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    acceptance: AcceptancePlan = field(default_factory=AcceptancePlan)

    def to_dict(self) -> Dict[str, Any]:
        """转成可 JSON 序列化的字典。"""
        return asdict(self)

    @classmethod
    def from_skeleton(cls, skeleton: PlotSkeleton) -> "GameTreePlan":
        """从 PlotSkeleton 构建计划。"""
        return build_gametree_plan(skeleton)

    def to_minimal_tree(self) -> Dict[str, Any]:
        """导出一棵最小 GameTree v1 形状的内存树。

        这个导出只服务 M3 单元测试和后续生成器对齐,不是最终剧本。
        """
        picker_node_id = "n_map_picker"
        backgrounds = {"text_fallback": {"text_fallback": "文本演出兜底"}}
        nodes: Dict[str, Dict[str, Any]] = {
            self.start_node: {
                "node_id": self.start_node,
                "narrative": f"{self.title} 的入口。",
                "choices": [{"text": "进入地图", "next": picker_node_id}],
                "presentation": {"background": "text_fallback"},
            },
            picker_node_id: {
                "node_id": picker_node_id,
                "_is_map_picker": True,
                "narrative": "选择要调查的地标。",
                "choices": [],
                "presentation": {"background": "text_fallback"},
            },
        }

        landmark_map: List[Dict[str, Any]] = []
        tool_by_location: Dict[str, List[ToolPlan]] = {}
        for tool in self.tools:
            tool_by_location.setdefault(tool.location_id, []).append(tool)

        for location in self.locations:
            node_id = f"n_loc_{_slug(location.id)}"
            landmark_map.append(
                {
                    "id": location.id,
                    "label": location.label,
                    "node_id": node_id,
                    "connections": list(location.connections),
                }
            )
            choices: List[Dict[str, Any]] = []
            for tool in tool_by_location.get(location.id, []):
                choices.append({"text": f"检查 {tool.id}", "next": f"n_{_slug(tool.id)}"})
            if not choices:
                choices.append({"text": "回到地图", "next": picker_node_id})
            presentation = self.presentation_defaults.get(
                location.id,
                {"background": "text_fallback"},
            )
            _register_background(backgrounds, presentation)
            nodes[node_id] = {
                "node_id": node_id,
                "narrative": f"你抵达 {location.label}。",
                "choices": choices,
                "presentation": presentation,
            }

        for index, tool in enumerate(self.tools):
            node_id = f"n_{_slug(tool.id)}"
            presentation = tool.asset_cues or {"background": "text_fallback"}
            _register_background(backgrounds, presentation)
            node: Dict[str, Any] = {
                "node_id": node_id,
                "_is_tool": True,
                "narrative": f"你反复检查 {tool.id}。",
                "choices": [
                    {
                        "text": "继续检查",
                        "next": node_id,
                        "effects": {"stay": True},
                    }
                ],
                "presentation": presentation,
            }
            if index == 0:
                node["narrative_variants"] = [
                    {
                        "if": {"deduction_resolved": "sandbox_probe"},
                        "text": "你已经知道它真正指向哪里。",
                    }
                ]
            nodes[node_id] = node

        return {
            "story_id": self.story_id,
            "title": self.title,
            "start_node": self.start_node,
            "nodes": nodes,
            "landmark_map": landmark_map,
            "tools": {
                tool.id: {
                    "node_id": f"n_{_slug(tool.id)}",
                    "location_id": tool.location_id,
                    "revisit_hooks": list(tool.revisit_hooks),
                }
                for tool in self.tools
            },
            "endings": {},
            "assets": {
                "backgrounds": backgrounds,
            },
            "reaction_contracts": {
                "deductions": {
                    "sandbox_probe": {"label": "沙盒探针"}
                },
                "foreshadows": {},
                "themes": {},
            },
        }


def build_gametree_plan(skeleton: PlotSkeleton) -> GameTreePlan:
    """从 PlotSkeleton 生成最小 GameTreePlan。

    这是结构计划,不是最终可玩树。它只做几件硬事:
    - 按 `location_id` 聚合 beat;
    - 按出现顺序给地标补双向连接;
    - 把 `tool` beat 抽成可回访工具计划;
    - 把 NPC 出没压成 route;
    - 为后续 presentation 兜底整理 asset cues。
    """
    location_map: Dict[str, LocationPlan] = {}
    npc_map: Dict[str, NpcRoutePlan] = {}
    beat_plans: List[BeatNodePlan] = []
    tools: List[ToolPlan] = []
    presentation_defaults: Dict[str, Dict[str, Any]] = {}
    picker_location_id: Optional[str] = None

    for beat in skeleton.beats:
        location_id = _location_id_for(beat)
        location = location_map.setdefault(
            location_id,
            LocationPlan(
                id=location_id,
                label=location_id,
            ),
        )
        _append_unique(location.beat_ids, beat.id)
        for npc_id in beat.npc_ids:
            _append_unique(location.npc_ids, npc_id)
        for slot in beat.event_slots:
            _append_unique(location.event_slots, slot)

        role = beat.sandbox_role or _role_from_slots(beat.event_slots)
        if picker_location_id is None and (role == "hub" or "hub" in beat.event_slots):
            picker_location_id = location_id

        beat_plans.append(
            BeatNodePlan(
                beat_id=beat.id,
                node_id=f"n_{_slug(beat.id)}",
                location_id=location_id,
                sandbox_role=role,
                event_slots=list(beat.event_slots),
                asset_cues=dict(beat.asset_cues),
            )
        )

        if role == "tool" or "tool" in beat.event_slots:
            tools.append(
                ToolPlan(
                    id=f"tool_{_slug(beat.id)}",
                    location_id=location_id,
                    beat_id=beat.id,
                    revisit_hooks=list(beat.revisit_hooks),
                    asset_cues=dict(beat.asset_cues),
                )
            )

        for npc_id in beat.npc_ids:
            route = npc_map.setdefault(npc_id, NpcRoutePlan(npc_id=npc_id))
            _append_unique(route.location_ids, location_id)
            _append_unique(route.beat_ids, beat.id)

        if beat.asset_cues:
            presentation_defaults[location_id] = {
                **presentation_defaults.get(location_id, {}),
                **beat.asset_cues,
            }

    locations = list(location_map.values())
    _connect_locations(locations)
    if picker_location_id is None and locations:
        picker_location_id = locations[0].id

    return GameTreePlan(
        title=skeleton.title,
        story_id=_slug(skeleton.title) or "generated",
        start_node="n_intro",
        picker_location_id=picker_location_id or "",
        locations=locations,
        tools=tools,
        npc_routes=list(npc_map.values()),
        beats=beat_plans,
        presentation_defaults=presentation_defaults,
    )


def _location_id_for(beat: BeatConfig) -> str:
    """缺少 location_id 时按 act 兜底,不让旧骨架崩。"""
    if beat.location_id:
        return beat.location_id
    return f"act_{beat.act_index}"


def _role_from_slots(event_slots: List[str]) -> str:
    """从事件槽推导沙盒角色。"""
    for role in ("hub", "tool", "ending", "payoff", "landmark"):
        if role in event_slots:
            return role
    if "ending_gate" in event_slots:
        return "ending"
    return "landmark"


def _connect_locations(locations: List[LocationPlan]) -> None:
    """按出现顺序补双向邻接,形成最小可走地图。"""
    for idx, location in enumerate(locations):
        if idx > 0:
            _append_unique(location.connections, locations[idx - 1].id)
        if idx + 1 < len(locations):
            _append_unique(location.connections, locations[idx + 1].id)


def _append_unique(items: List[str], value: str) -> None:
    """保持顺序的去重追加。"""
    if value and value not in items:
        items.append(value)


def _register_background(backgrounds: Dict[str, Dict[str, str]], presentation: Dict[str, Any]) -> None:
    """把演出提示里的背景登记成文本兜底资产。"""
    bg = presentation.get("background")
    if isinstance(bg, str) and bg and bg not in backgrounds:
        backgrounds[bg] = {"text_fallback": bg}


def _slug(value: str) -> str:
    """生成稳定 node/tool ID 片段。"""
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "beat"
