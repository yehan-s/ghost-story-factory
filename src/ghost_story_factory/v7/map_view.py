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


def _landmarks_for(tree: Dict[str, Any], state) -> List[Dict[str, Any]]:
    """ADR-010 沙盒契约:按 state.character 过滤 landmark_map。

    匹配规则:
    - 当前 character == landmark.character → 显示
    - landmark.character 缺失(None)→ 视为通用,所有角色显示(向后兼容)
    - 其它 → 隐藏(linmou 不显示 G-273 的 S1-S7,反之亦然)
    """
    landmark_map = tree.get("landmark_map") or []
    character = getattr(state, "character", None) if state is not None else None
    if not character:
        return list(landmark_map)
    return [
        lm for lm in landmark_map
        if lm.get("character") in (None, character)
    ]


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


def _render_topology(
    landmark_map: List[Dict[str, Any]],
    state,
    current_node_id,
    travel_indices: Optional[Dict[str, int]] = None,
) -> List[str]:
    """绘制点状拓扑地图(纯文本)。

    硬编码 7 地标布局,反映西湖周边真实地理:
        S5(留下) ──────── S1(湖滨) ──── S7(平海)
          │                  │
        S6(联庄)           S4(羊血)
                              │
                            S2(柳浪) ─── S3(九溪)

    travel_indices: 可选 — {SID: 选项编号} 映射,把数字贴到地标旁,
                    让玩家"看着地图按数字"。
    """
    known = set(getattr(state, "known_landmarks", None) or [])
    # 把 landmark_map 里的状态查出来
    status_by_id: Dict[str, str] = {}
    for lm in landmark_map:
        status_by_id[lm.get("id", "")] = landmark_status(lm, state, current_node_id)

    def m(sid: str) -> str:
        # 未知地标:用 [?] 占位
        if sid not in known:
            return "[?]"
        return _mark_for_status(status_by_id.get(sid, "available"))

    def name(sid: str, short: str) -> str:
        """SID + short_name(2字),共 6 cols(SID + space + 4 CJK cols)"""
        if sid not in known:
            return "?? ???"  # 占位
        prefix = ""
        if travel_indices and sid in travel_indices:
            prefix = f"({travel_indices[sid]})"
        # eg. "(3)S1 湖滨"
        return f"{prefix}{sid} {short}"

    def time_for(sid: str, t: str, suffix: str = "") -> str:
        if sid not in known:
            return "??:??"
        return f"{t}{suffix}"

    # 名称查找
    by_id = {lm.get("id", ""): lm for lm in landmark_map}
    def short_of(sid):
        return by_id.get(sid, {}).get("short", "??")
    def time_of(sid):
        return by_id.get(sid, {}).get("time", "??:??")

    s7_suffix = " 终" if "S7" in known else ""

    # 构造每个地标的双行块(name + mark+time),让连线对齐
    def block(sid, suffix=""):
        return name(sid, short_of(sid)), m(sid), time_for(sid, time_of(sid), suffix)

    n_s5, m_s5, t_s5 = block("S5")
    n_s1, m_s1, t_s1 = block("S1")
    n_s7, m_s7, t_s7 = block("S7", s7_suffix)
    n_s6, m_s6, t_s6 = block("S6")
    n_s4, m_s4, t_s4 = block("S4")
    n_s2, m_s2, t_s2 = block("S2")
    n_s3, m_s3, t_s3 = block("S3")

    # 连线只在两端都已知时画实线,否则画虚线/空白
    def edge(a, b, dash):
        # 都已知 → 实线;一端未知 → 虚线;都未知 → 空格
        if a in known and b in known:
            return dash
        if a in known or b in known:
            return "·" * len(dash)
        return " " * len(dash)

    e_s5_s1 = edge("S5", "S1", "────────────")  # 12 cols
    e_s1_s7 = edge("S1", "S7", "──────")         # 6 cols
    e_s2_s3 = edge("S2", "S3", "──────")
    v_s5_s6 = "│" if ("S5" in known and "S6" in known) else (":" if ("S5" in known or "S6" in known) else " ")
    v_s1_s4 = "│" if ("S1" in known and "S4" in known) else (":" if ("S1" in known or "S4" in known) else " ")
    v_s4_s2 = "│" if ("S4" in known and "S2" in known) else (":" if ("S4" in known or "S2" in known) else " ")

    lines = [
        "                                                                ",
        f"    {n_s5:<10} {e_s5_s1} {n_s1:<10} {e_s1_s7} {n_s7:<10}    ",
        f"    {m_s5:<10}              {m_s1:<10}        {m_s7:<10}    ",
        f"    {t_s5:<10}              {t_s1:<10}        {t_s7:<10}    ",
        f"      {v_s5_s6}                          {v_s1_s4}                                ",
        f"      {v_s5_s6}                          {v_s1_s4}                                ",
        f"    {n_s6:<10}                  {n_s4:<10}                          ",
        f"    {m_s6:<10}                  {m_s4:<10}                          ",
        f"    {t_s6:<10}                  {t_s4:<10}                          ",
        f"                                       {v_s4_s2}                                ",
        f"                                       {v_s4_s2}                                ",
        f"                                     {n_s2:<10} {e_s2_s3} {n_s3:<10}      ",
        f"                                     {m_s2:<10}        {m_s3:<10}      ",
        f"                                     {t_s2:<10}        {t_s3:<10}      ",
        "                                                                ",
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
    mode: str = "site",
    travel_indices: Optional[Dict[str, int]] = None,
) -> List[Dict[str, Any]]:
    """返回地图视图各段落,每段一个 dict {"kind": "...", "text": "..."}。

    mode:
      "site"  — 现场视图(picker 用):显示 NPC、线索、工具栏全套
      "phone" — 手机地图(m 键用):只看路 + 已知地名,不剧透 NPC

    travel_indices: {SID: 选项编号},把数字贴到地标旁(让玩家按数字直选)

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
    landmark_map = _landmarks_for(tree, state)
    tools = tree.get("tools") or []

    # 段:点状拓扑地图
    title = "手机地图 · 西湖周边" if mode == "phone" else "夜班路线·西湖周边"
    lines.append({"kind": "header", "text": title})
    for line in _render_topology(landmark_map, state, current_node_id, travel_indices):
        lines.append({"kind": "topology", "text": line})

    # 图例 + 输入提示(只在 site 且有 travel_indices 时给提示)
    lines.append({"kind": "legend", "text": _render_legend()})
    if mode == "site" and travel_indices:
        lines.append({"kind": "footer",
                      "text": "  · 按括号里的数字 / SID(如 S1)直接走过去"})

    # phone 模式:不显示 NPC / 工具(只看路+地名)
    if mode == "phone":
        # 进度依然显示(玩家自己的状态可见)
        lines.append({"kind": "section", "text": ""})
        lines.append({"kind": "header", "text": "进度"})
        sc = getattr(state, "shifts_completed", 0)
        ss = getattr(state, "shifts_skipped", 0)
        progress_bits = [f"夜班 {sc}/7", f"漏卡 {ss}"]
        lines.append({"kind": "progress", "text": "  " + " · ".join(progress_bits)})
        lines.append({"kind": "footer", "text": "  · 手机地图只显示路 — 现场看到的线索,只有亲自去才能见。"})
        return lines

    # 段:NPC 出没 — 仅显示玩家"已访问过"的地标的 NPC(否则剧透)
    visited_set = set(getattr(state, "visited_landmarks", None) or [])
    npc_loc = getattr(state, "npc_locations", None) or {}
    if npc_loc:
        any_npc = False
        npc_lines: List[Dict[str, Any]] = []
        for lm in landmark_map:
            sid = lm.get("id", "")
            if sid not in visited_set:
                continue  # 没去过 — 不知道那里有谁
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
            lines.append({"kind": "header", "text": "今夜在场(你亲眼见过的)"})
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


def expand_known_landmarks(state, tree: Dict[str, Any], effects: Optional[Dict[str, Any]]) -> List[str]:
    """根据 effects 和最近事件展开 state.known_landmarks。返回新加入的 SID 列表。

    展开规则:
      1. effects.landmark_visited X → 把 X 自己 + X.connections 加进 known
      2. effects.reveal_landmarks ["S6", ...] → 显式揭示
    """
    landmark_map = _landmarks_for(tree or {}, state)
    by_id = {lm.get("id", ""): lm for lm in landmark_map}
    newly: List[str] = []

    if not isinstance(state.known_landmarks, list):
        state.known_landmarks = list(state.known_landmarks)

    def _add(sid: str):
        if sid and sid in by_id and sid not in state.known_landmarks:
            state.known_landmarks.append(sid)
            newly.append(sid)

    # 1. 这一次 effects 里的 landmark_visited(value 是 SID)
    if effects:
        if "landmark_visited" in effects:
            sid = str(effects["landmark_visited"])
            _add(sid)
            for c in (by_id.get(sid, {}).get("connections") or []):
                _add(c)
        # 2. 显式揭示
        for sid in (effects.get("reveal_landmarks") or []):
            _add(str(sid))

    return newly


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
    node: Optional[Dict[str, Any]] = None,
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
    landmark_map = _landmarks_for(tree, state)
    tools = tree.get("tools") or []
    by_id = {lm.get("id", ""): lm for lm in landmark_map}
    visited = set(getattr(state, "visited_landmarks", None) or [])
    known = set(getattr(state, "known_landmarks", None) or [])
    current_lid = getattr(state, "last_landmark_id", None)

    choices: List[Dict[str, Any]] = []

    # 自由移动 — 邻接地标 + 已解锁 + 已知道
    if current_lid and current_lid in by_id:
        cur = by_id[current_lid]
        # 当前位置出发,可达 = connections + 自身(允许"留在原地再走一遍")
        target_ids = list(dict.fromkeys((cur.get("connections") or []) + [current_lid]))
    else:
        # 还没去过任何地标 — 只有"已知"的才能去(开局只知道 S1)
        target_ids = [sid for sid in known]
        if not target_ids:  # 兜底:如果 known 为空,显示 S1
            target_ids = ["S1"]

    for sid in target_ids:
        lm = by_id.get(sid)
        if not lm:
            continue
        # 必须是已知的(否则你不知道路怎么走)
        if sid not in known:
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

    # 退出节奏 endshift —
    # 优先节点级 `_picker_endshift_choice`(由 fragment 自定义),否则走 G-273 默认。
    custom_endshift = (node or {}).get("_picker_endshift_choice") if node else None
    if custom_endshift:
        require = custom_endshift.get("require")
        if not require or _meets(require, state):
            choices.append({
                "text": custom_endshift.get("text", "[结束] 离开"),
                "next": custom_endshift.get("next"),
                "_picker_kind": "endshift",
            })
    elif getattr(state, "shifts_completed", 0) >= 4:
        # G-273 兜底:打满 4 班可下班
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


def render_map_cli(tree, state, save_manager, current_node_id=None, story_id=None,
                   mode: str = "site",
                   travel_indices: Optional[Dict[str, int]] = None) -> None:
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
                                  story_id=story_id,
                                  mode=mode,
                                  travel_indices=travel_indices):
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
        elif kind == "footer":
            print(dim(text))
        else:
            print(text)
    print()
    print(bold(red("══════════════════════════════════════════════════════════")))
    print()
