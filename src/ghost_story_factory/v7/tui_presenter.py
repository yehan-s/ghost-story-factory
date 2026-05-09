"""TUI 纯表达层。

这里不操作 Textual widget,不推进状态,不写存档。它只把现有游戏状态格式化为
Rich markup 文本,供 `tui_player.py` 渲染。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from ghost_story_factory.v5.player import (
    choice_affordance_tags,
    format_behavior_profile_lines,
    format_choice_after_feedback_lines,
)


def highlight_narrative_rich(line: str) -> str:
    """给一行 narrative 加 Rich markup 标记。"""
    out = re.sub(r"\*\*([^*]+?)\*\*", r"[bold yellow]\1[/]", line)
    out = re.sub(r"(「[^」]+」|『[^』]+』)", r"[cyan]\1[/]", out)
    out = re.sub(r"(?<![A-Za-z0-9])(S[1-7])(?![A-Za-z0-9])",
                 r"[bold magenta]\1[/]", out)
    out = re.sub(r"\b(\d{1,2}:\d{2})\b", r"[yellow]\1[/]", out)
    out = re.sub(r"(?<!\d)((?:19|20)\d{2})(?!\d)", r"[dim red]\1[/]", out)
    return out


def escape_rich_literal(text: Any) -> str:
    """把外部文本当作 Rich 字面量输出,避免方括号被当成 markup。"""
    return str(text).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def format_choice_badges(choice: Dict[str, Any]) -> str:
    """TUI 专属选择 badge。只表达意图,不暴露数值或内部 key。"""
    tags = choice_affordance_tags(choice)
    if not tags:
        return ""
    color_map = {
        "观察": "cyan",
        "前往": "green",
        "巡点": "green",
        "工具": "yellow",
        "收束": "yellow",
        "记下线索": "cyan",
        "关键线索": "cyan",
        "带走物件": "green",
        "消耗物件": "yellow",
        "漏卡风险": "red",
        "关系推进": "magenta",
        "留下痕迹": "blue",
        "意图选择": "magenta",
        "心境波动": "red",
        "压住心跳": "green",
        "异常注视": "red",
        "注视减弱": "green",
        "伏笔": "cyan",
        "地图线索": "yellow",
        "局势变动": "magenta",
    }
    return " ".join(
        f"[{color_map.get(tag, 'white')}]〈{escape_rich_literal(tag)}〉[/]"
        for tag in tags
    )


def format_choice_option_label(index: int, choice: Dict[str, Any]) -> str:
    """构造 TUI 选择文本,附带适合扫读的非剧透 badge。"""
    label = escape_rich_literal(choice.get("text", "(无文本)"))
    badges = format_choice_badges(choice)
    if not badges:
        return f"{index}. {label}"
    return f"{index}. {label}  {badges}"


def format_scene_strip(node: Dict[str, Any], node_id: str) -> str:
    """顶部场景条。给 TUI 一个稳定的当前场景锚点。"""
    if node.get("is_ending"):
        ending_type = escape_rich_literal(node.get("ending_type", "E_UNKNOWN"))
        return f"[bold magenta]结局[/] [dim]{ending_type}[/]"
    header = node.get("_landmark_header") or {}
    if isinstance(header, dict) and (header.get("place") or header.get("time")):
        place = escape_rich_literal(header.get("place", ""))
        time_text = escape_rich_literal(header.get("time", ""))
        if place and time_text:
            return f"[bold yellow]{time_text}[/] [dim]·[/] [bold red]{place}[/]"
        return f"[bold red]{place or time_text}[/]"
    if node.get("_is_map_picker"):
        return "[bold red]现场视图[/] [dim]· 夜班路线[/]"
    return f"[dim]节点[/] {escape_rich_literal(node_id)}"


def format_tui_status_lines(tree, save_manager, story_id: str, state) -> List[str]:
    """TUI 状态弹层。面向玩家,不显示内部 flag key。"""
    lines = ["[bold cyan]── 路线账本 ──[/]"]
    lines.append(
        f"  [yellow]夜班[/] [bold]{state.shifts_completed}/7[/]   "
        f"[red]漏卡[/] [bold]{state.shifts_skipped}[/]"
    )
    if state.visited_landmarks:
        lines.append("  已踏入: " + escape_rich_literal(", ".join(state.visited_landmarks)))
    if state.skipped_landmarks:
        lines.append("  已绕开: " + escape_rich_literal(", ".join(state.skipped_landmarks)))
    if state.puzzle_pieces:
        pieces = escape_rich_literal(" · ".join(state.puzzle_pieces[:8]))
        lines.append(f"  [green]拼图[/]: {len(state.puzzle_pieces)}/5  [dim]{pieces}[/]")
    if state.inv:
        lines.append(f"  [white]随身[/]: {escape_rich_literal(' · '.join(state.inv))}")

    profile = format_behavior_profile_lines(state)
    if profile:
        lines.append("")
        lines.append("[bold yellow]── 本轮行为画像 ──[/]")
        for line in profile:
            lines.append(f"  [dim]{escape_rich_literal(line)}[/]")

    foreshadows = (tree or {}).get("foreshadows") or {}
    if foreshadows:
        seen = set(save_manager.data.get("foreshadows_seen", {}).get(story_id, []))
        resolved = set(save_manager.data.get("foreshadows_resolved", {}).get(story_id, []))
        lines.append("")
        lines.append(
            f"[bold cyan]── 档案索引({len(seen)}/{len(foreshadows)} 已发现 · "
            f"{len(resolved)}/{len(foreshadows)} 已解开)──[/]"
        )
        unresolved = [slot for slot in seen if slot not in resolved]
        if unresolved:
            lines.append("[dim]  下一轮可追:[/]")
            for slot in unresolved[:3]:
                meta = foreshadows.get(slot, {})
                title = escape_rich_literal(meta.get("title", slot))
                summary = escape_rich_literal(meta.get("summary_locked", ""))
                lines.append(f"  [cyan]?[/] [bold]{title}[/]")
                if summary:
                    lines.append(f"    [dim]{summary}[/]")
        elif seen:
            lines.append("[dim]  这一轮发现的档案暂时没有未解项。[/]")
        else:
            lines.append("[dim]  还没有发现任何伏笔档案。[/]")

    return lines


def format_run_recap_lines(
    tree,
    save_manager,
    story_id: str,
    state,
    visited: List[str],
    ending_type: str,
) -> List[str]:
    """结局页本轮复盘。"""
    lines = ["[bold yellow]── 本轮复盘 ──[/]"]
    profile = format_behavior_profile_lines(state)
    if profile:
        for line in profile:
            lines.append(f"  [dim]{escape_rich_literal(line)}[/]")
    lines.append(f"  [dim]经历节点: {len(visited)}[/]")
    if state.visited_landmarks:
        lines.append(f"  已踏入: {escape_rich_literal(', '.join(state.visited_landmarks))}")
    if state.skipped_landmarks:
        lines.append(f"  已绕开: {escape_rich_literal(', '.join(state.skipped_landmarks))}")
    foreshadows = (tree or {}).get("foreshadows") or {}
    if foreshadows:
        seen = set(save_manager.data.get("foreshadows_seen", {}).get(story_id, []))
        resolved = set(save_manager.data.get("foreshadows_resolved", {}).get(story_id, []))
        lines.append(
            f"  档案进度:已发现 {len(seen)}/{len(foreshadows)} · "
            f"已解开 {len(resolved)}/{len(foreshadows)}"
        )
        unresolved = [slot for slot in seen if slot not in resolved]
        if unresolved:
            titles = [
                escape_rich_literal((foreshadows.get(slot) or {}).get("title", slot))
                for slot in unresolved[:3]
            ]
            lines.append(f"  下一轮可追: {' · '.join(titles)}")
    lines.append(f"  [dim]记录结局:{escape_rich_literal(ending_type)}[/]")
    return lines


def format_transition_lines(
    choice: Dict[str, Any],
    newly_known: List[str],
    landmark_map: List[Dict[str, Any]],
) -> List[str]:
    """格式化节点跳转过门。"""
    lines = [
        f"[bold yellow]▸[/] [bold]{escape_rich_literal(choice.get('text', ''))}[/]"
    ]
    for line in format_choice_after_feedback_lines(choice):
        lines.append(f"[dim]  {escape_rich_literal(line)}[/]")
    for sid in newly_known:
        lm = next((l for l in landmark_map if l.get("id") == sid), {})
        short = escape_rich_literal(lm.get("short", sid))
        place = escape_rich_literal(lm.get("place", ""))
        sid_text = escape_rich_literal(sid)
        lines.append(f"  [bold yellow]▌ 地图 +1  ·  {sid_text} {short} {place} ▐[/]")
    return lines
