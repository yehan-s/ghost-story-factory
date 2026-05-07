"""夜班路线图渲染 — CLI/TUI 共享。

核心函数:
- format_map_lines(tree, state, save_manager) -> List[str]:
    返回地图视图的多行纯文本(无颜色),CLI/TUI 各自染色

地图视图布局:
  ══════════ 夜班路线 ══════════
  [✓] S1  20:27  湖滨第三把绿色长椅       (已走过)
  [▶] S2  21:47  柳浪闻莺                (可去)
  [🔒] S6 01:52  联庄站盾构井             (夜班 ≥3)
  ...
  ══════════ 进度 ══════════
  夜班 1/7 · 漏卡 0 · 伏笔档案 2/9
  ══════════ 工具栏 ══════════
  [📻] 对讲机          已开
  ...
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# 标记符号
_MARK_VISITED = "✓"
_MARK_CURRENT = "●"
_MARK_AVAILABLE = "▶"
_MARK_LOCKED = "🔒"


def _meets(require: Optional[Dict[str, Any]], state) -> bool:
    """检查 require 是否满足 — 复用 State.meets。"""
    if not require:
        return True
    if state is None:
        return True
    if hasattr(state, "meets"):
        return state.meets(require)
    return True


def landmark_status(landmark: Dict[str, Any], state, current_node_id: Optional[str]) -> str:
    """返回单个地标的状态:'visited' / 'current' / 'available' / 'locked'。"""
    sid = landmark.get("id", "")
    node_id = landmark.get("node_id", "")
    if current_node_id == node_id:
        return "current"
    visited = sid in (getattr(state, "visited_landmarks", None) or [])
    if visited:
        return "visited"
    unlock = landmark.get("unlock")
    if unlock and not _meets(unlock, state):
        return "locked"
    return "available"


def _mark_for_status(status: str) -> str:
    return {
        "visited": f"[{_MARK_VISITED}]",
        "current": f"[{_MARK_CURRENT}]",
        "available": f"[{_MARK_AVAILABLE}]",
        "locked": f"[{_MARK_LOCKED}]",
    }.get(status, "[ ]")


def _status_suffix(status: str, landmark: Dict[str, Any]) -> str:
    if status == "visited":
        return "(已走过)"
    if status == "current":
        return "(当前位置)"
    if status == "locked":
        hint = landmark.get("unlock_hint") or "尚未开启"
        return f"({hint})"
    return ""


def format_map_lines(
    tree: Dict[str, Any],
    state,
    save_manager,
    current_node_id: Optional[str] = None,
    story_id: Optional[str] = None,
    width: int = 60,
) -> List[Dict[str, Any]]:
    """返回地图视图各段落,每段一个 dict {"kind": "...", "text": "..."}。

    kind 取值用于 UI 层染色:
      "header"       — 章节大标题
      "landmark"     — 地标行(visited/current/available/locked,见 status)
      "progress"     — 进度统计
      "tool"         — 工具行(open/closed)
      "tool_header"  — 工具栏小标题
      "section"      — 普通分隔
      "footer"       — 底部提示
    """
    lines: List[Dict[str, Any]] = []
    landmark_map = tree.get("landmark_map") or []
    tools = tree.get("tools") or []

    # 段:夜班路线
    lines.append({"kind": "header", "text": "夜班路线"})
    for lm in landmark_map:
        status = landmark_status(lm, state, current_node_id)
        mark = _mark_for_status(status)
        sid = lm.get("id", "")
        time = lm.get("time", "")
        place = lm.get("place", "")
        suffix = _status_suffix(status, lm)
        # 排版:[mark] SID  HH:MM  地名     suffix
        line = f"  {mark} {sid:<3} {time:<7} {place:<22} {suffix}"
        lines.append({
            "kind": "landmark", "status": status,
            "id": sid, "node_id": lm.get("node_id", ""),
            "text": line,
        })

    # 段:进度
    lines.append({"kind": "section", "text": ""})
    lines.append({"kind": "header", "text": "进度"})
    sc = getattr(state, "shifts_completed", 0)
    ss = getattr(state, "shifts_skipped", 0)
    pp = len(getattr(state, "puzzle_pieces", []) or [])
    progress_bits = [f"夜班 {sc}/7", f"漏卡 {ss}"]
    if pp:
        progress_bits.append(f"拼图 {pp}/5")
    if save_manager and story_id:
        try:
            seen, resolved, total = save_manager.foreshadow_progress(tree, story_id)
            if total:
                progress_bits.append(f"伏笔 {resolved}/{total}")
        except Exception:
            pass
    lines.append({"kind": "progress", "text": "  " + " · ".join(progress_bits)})

    # 段:工具栏
    if tools:
        lines.append({"kind": "section", "text": ""})
        lines.append({"kind": "header", "text": "工具栏"})
        flags = getattr(state, "flags", {}) or {}
        for tool in tools:
            icon = tool.get("icon", "·")
            label = tool.get("label", tool.get("id", ""))
            flag = tool.get("state_flag", "")
            on = bool(flags.get(flag, False)) if flag else False
            status_text = tool.get("on_text", "已开") if on else tool.get("off_text", "未开")
            line = f"  [{icon}] {label:<10} {status_text}"
            lines.append({
                "kind": "tool",
                "id": tool.get("id"),
                "node_id": tool.get("node_id"),
                "on": on,
                "text": line,
            })

    return lines


def render_map_cli(tree, state, save_manager, current_node_id=None, story_id=None) -> None:
    """直接 print 到 stdout(CLI 用)— 调用方在打印后等用户输入。"""
    # 局部导入避免循环
    from ghost_story_factory.v5.player import (
        bold, cyan, dim, green, red, yellow, blue, magenta,
    )
    print()
    print(bold(red("══════════════════════════════════════════════════════════")))
    print()
    for entry in format_map_lines(tree, state, save_manager,
                                  current_node_id=current_node_id,
                                  story_id=story_id):
        kind = entry["kind"]
        text = entry["text"]
        if kind == "header":
            print(f"  {bold(yellow(text))}")
        elif kind == "section":
            print()
        elif kind == "landmark":
            status = entry.get("status", "available")
            colorized = {
                "visited": dim,
                "current": lambda s: bold(magenta(s)),
                "available": green,
                "locked": dim,
            }.get(status, lambda s: s)
            print(colorized(text))
        elif kind == "progress":
            print(bold(cyan(text)))
        elif kind == "tool":
            on = entry.get("on", False)
            print((bold(green(text))) if on else dim(text))
        else:
            print(text)
    print()
    print(bold(red("══════════════════════════════════════════════════════════")))
    print()
