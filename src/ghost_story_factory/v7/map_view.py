"""夜班路线图渲染 — CLI/TUI 共享。

核心函数:
- format_map_lines(tree, state, save_manager, ...) -> List[Dict]:
    返回地图视图各段落,每段一个 dict {"kind": ..., "text": ...},
    UI 层负责按 kind 染色

视图层结构:
  ╔══════ 夜班路线·西湖周边 ══════╗

      S5 留下 ─────────  S1 湖滨 ───── S7 平海
      [✓]                  [●]              [X]
      01:08              20:27           04:17 终
        │                  │
        │                  │
      S6 联庄              S4 羊血
      [X]                  [✓]
      01:52              00:11
                           │
                         S2 柳浪 ─── S3 九溪
                         [▶]            [▶]
                         21:47        22:48

  [●]当前  [✓]已走过  [▶]可去  [X]锁定

  ╔══════ 进度 ══════╗
  夜班 1/7 · 漏卡 0 · 伏笔档案 2/9

  ╔══════ 工具栏 ══════╗
  [📻] 对讲机          已开
  ...
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# 标记符号(全部 3 个 ASCII 列宽,确保对齐)
_MARK_VISITED = "[✓]"
_MARK_CURRENT = "[●]"
_MARK_AVAILABLE = "[▶]"
_MARK_LOCKED = "[X]"


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
        "visited": _MARK_VISITED,
        "current": _MARK_CURRENT,
        "available": _MARK_AVAILABLE,
        "locked": _MARK_LOCKED,
    }.get(status, "[ ]")


def _render_topology(landmark_map: List[Dict[str, Any]], state, current_node_id) -> List[str]:
    """绘制点状拓扑地图(纯文本)。

    硬编码 7 地标布局,反映西湖周边真实地理:
        S5(留下) ──────── S1(湖滨) ──── S7(平海)
          │                  │
        S6(联庄)           S4(羊血)
                              │
                            S2(柳浪) ─── S3(九溪)
    """
    # 把 landmark_map 里的状态查出来
    status_by_id: Dict[str, str] = {}
    for lm in landmark_map:
        status_by_id[lm.get("id", "")] = landmark_status(lm, state, current_node_id)

    def m(sid: str) -> str:
        return _mark_for_status(status_by_id.get(sid, "available"))

    # 终局标记(无论解锁与否,S7 都标"终")
    s7_suffix = " 终"

    # 构造模板。每行用空格定位列,box-drawing 字符画连线
    # 列对齐:
    #   col  4-9:   左列(S5/S6)
    #   col 27-32:  中列(S1/S4/S2)
    #   col 47-52:  右列(S7/S3)
    lines = [
        "                                                              ",
        "    S5 留下 ──────────── S1 湖滨 ────── S7 平海               ",
        f"    {m('S5')}                  {m('S1')}             {m('S7')}                ",
        f"    01:08                20:27          04:17{s7_suffix}              ",
        "      │                    │                                  ",
        "      │                    │                                  ",
        "    S6 联庄                S4 羊血弄                          ",
        f"    {m('S6')}                  {m('S4')}                                ",
        "    01:52                00:11                                ",
        "                           │                                  ",
        "                           │                                  ",
        "                         S2 柳浪 ────── S3 九溪               ",
        f"                         {m('S2')}             {m('S3')}                ",
        "                         21:47          22:48                 ",
        "                                                              ",
    ]
    return lines


def _render_legend() -> str:
    return (f"  {_MARK_CURRENT} 当前  "
            f"{_MARK_VISITED} 已走过  "
            f"{_MARK_AVAILABLE} 可去  "
            f"{_MARK_LOCKED} 锁定")


def _npcs_at_landmark(state, tree: Dict[str, Any], landmark_id: str) -> List[str]:
    """返回当前在指定地标的 NPC 短描述。state.npc_locations 可能不存在(向后兼容)。"""
    npc_loc = getattr(state, "npc_locations", None) or {}
    npc_meta = (tree or {}).get("npcs") or {}
    result: List[str] = []
    for npc_id, loc in npc_loc.items():
        if loc == landmark_id:
            label = npc_meta.get(npc_id, {}).get("label", npc_id) if npc_meta else npc_id
            result.append(label)
    return result


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
      "topology"     — 拓扑地图行(原样输出)
      "legend"       — 图例
      "landmark"     — 单地标详情(在 picker 视图里用)
      "npc_at"       — 地标处的 NPC 列表
      "progress"     — 进度统计
      "tool"         — 工具行(open/closed)
      "section"      — 普通分隔(空行)
      "footer"       — 底部提示
    """
    lines: List[Dict[str, Any]] = []
    landmark_map = tree.get("landmark_map") or []
    tools = tree.get("tools") or []

    # 段:点状拓扑地图
    lines.append({"kind": "header", "text": "夜班路线·西湖周边"})
    for line in _render_topology(landmark_map, state, current_node_id):
        lines.append({"kind": "topology", "text": line})

    # 图例
    lines.append({"kind": "legend", "text": _render_legend()})

    # 段:NPC 出没(根据 state.npc_locations,逐地标列出)
    npc_loc = getattr(state, "npc_locations", None) or {}
    if npc_loc:
        any_npc = False
        npc_lines: List[Dict[str, Any]] = []
        for lm in landmark_map:
            sid = lm.get("id", "")
            present = _npcs_at_landmark(state, tree, sid)
            if present:
                any_npc = True
                short = lm.get("short", "")
                npc_lines.append({
                    "kind": "npc_at",
                    "id": sid,
                    "text": f"  {sid} {short} → " + " · ".join(f"👤 {n}" for n in present),
                })
        if any_npc:
            lines.append({"kind": "section", "text": ""})
            lines.append({"kind": "header", "text": "今夜在场"})
            lines.extend(npc_lines)

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

    # 段:工具栏(过滤掉 unlock 不满足的工具 — 防止剧透)
    visible_tools = [t for t in tools if _meets(t.get("unlock"), state)]
    if visible_tools:
        lines.append({"kind": "section", "text": ""})
        lines.append({"kind": "header", "text": "工具栏"})
        flags = getattr(state, "flags", {}) or {}
        for tool in visible_tools:
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


def reachable_landmarks(
    landmark_map: List[Dict[str, Any]],
    current_landmark_id: Optional[str],
    state,
) -> List[Dict[str, Any]]:
    """返回从当前地标可直接走到的地标列表(已解锁 + 在 connections 内)。

    若 current_landmark_id 为 None(玩家不在任何地标),返回所有已解锁地标。
    """
    by_id = {lm.get("id", ""): lm for lm in landmark_map}
    if current_landmark_id and current_landmark_id in by_id:
        cur = by_id[current_landmark_id]
        connections = cur.get("connections") or []
        targets = [by_id[c] for c in connections if c in by_id]
    else:
        targets = list(landmark_map)

    result = []
    for lm in targets:
        unlock = lm.get("unlock")
        if unlock and not _meets(unlock, state):
            continue
        result.append(lm)
    return result


def picker_choices(
    tree: Dict[str, Any],
    state,
) -> List[Dict[str, Any]]:
    """生成 picker 节点的动态选项列表(自由移动版)。

    返回 dict 与 tree.json choices 同形:
      - text: 显示文本
      - next: 目标节点 ID
      - _picker_kind: "travel" / "tool" / "endshift" / "locked"

    自由移动规则:
      - 玩家位置 = state.last_landmark_id(初次为 None,可去任何已解锁地标)
      - 邻接地标(通过 connections)且已解锁 → travel
      - 已访问过的地标显示"(回访)"
      - 工具节点常驻
      - shifts_completed ≥ 4 显示"结束夜班"
      - 锁定地标显示但带提示
    """
    landmark_map = tree.get("landmark_map") or []
    tools = tree.get("tools") or []
    by_id = {lm.get("id", ""): lm for lm in landmark_map}
    visited = set(getattr(state, "visited_landmarks", None) or [])
    current_lid = getattr(state, "last_landmark_id", None)

    choices: List[Dict[str, Any]] = []

    # 自由移动 — 邻接地标 + 已解锁
    if current_lid and current_lid in by_id:
        cur = by_id[current_lid]
        # 当前位置出发,可达 = connections + 自身(允许"留在原地再走一遍")
        target_ids = list(dict.fromkeys((cur.get("connections") or []) + [current_lid]))
    else:
        # 还没去过任何地标 — 所有已解锁的都可去
        target_ids = [lm.get("id", "") for lm in landmark_map]

    for sid in target_ids:
        lm = by_id.get(sid)
        if not lm:
            continue
        unlock = lm.get("unlock")
        if unlock and not _meets(unlock, state):
            continue  # 锁定的下面单独显示
        short = lm.get("short", "")
        place = lm.get("place", "")
        time = lm.get("time", "")
        revisit_tag = "(回访)" if sid in visited else ""
        # S7 是终局,特别标注
        ending_tag = " · 终局" if sid == "S7" else ""
        text = f"→ {sid} {short} · {place} ({time}){ending_tag} {revisit_tag}".strip()
        choices.append({
            "text": text,
            "next": lm.get("node_id"),
            "_picker_kind": "travel",
            "_landmark_id": sid,
        })

    # 工具(过滤 unlock — 防止前期就显示后期才能用的传闻线索)
    for tool in tools:
        if not _meets(tool.get("unlock"), state):
            continue
        node_id = tool.get("node_id")
        if not node_id:
            continue
        icon = tool.get("icon", "·")
        label = tool.get("label", tool.get("id", ""))
        flag = tool.get("state_flag", "")
        flags = getattr(state, "flags", {}) or {}
        on = bool(flags.get(flag, False)) if flag else False
        status_text = tool.get("on_text", "已开") if on else tool.get("off_text", "未开")
        text = f"[{icon}] {label} · {status_text}"
        choices.append({
            "text": text,
            "next": node_id,
            "_picker_kind": "tool",
            "_tool_id": tool.get("id"),
        })

    # 结束夜班(shifts_completed ≥ 4 解锁)
    if getattr(state, "shifts_completed", 0) >= 4:
        choices.append({
            "text": "[结束] 直接交班 — 你已经打了 4 个点,可以下班了。",
            "next": "n_scene_morning_lakeside",
            "_picker_kind": "endshift",
        })

    # 锁定地标(显示提示,不可选)
    for lm in landmark_map:
        sid = lm.get("id", "")
        unlock = lm.get("unlock")
        if not unlock:
            continue
        if _meets(unlock, state):
            continue
        hint = lm.get("unlock_hint") or "尚未开启"
        short = lm.get("short", "")
        text = f"[X] {sid} {short} ({hint})"
        choices.append({
            "text": text,
            "next": None,
            "_picker_kind": "locked",
            "_landmark_id": sid,
        })

    return choices


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
        elif kind == "topology":
            # 用淡色,但当前位置 [●] 标记部分会因为字符在文本里所以无法单独染色,
            # 整行直接用普通色调,玩家通过符号本身辨认状态
            print(text)
        elif kind == "legend":
            print(dim(text))
        elif kind == "npc_at":
            print(magenta(text))
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
