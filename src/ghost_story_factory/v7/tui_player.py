"""v7 TUI Player(Textual full-screen interface)。

复用 v5/player.py 的 State / resolve_narrative / resolve_next 状态逻辑。
本文件只负责渲染 + 输入。

布局:
┌─────────────────────────────┐
│ Header (title + protagonist)│
├─────────────────────────────┤
│ StatusBar (PR/GR/夜班/inv)   │
├─────────────────────────────┤
│ Narrative (RichLog,可滚动)  │
├─────────────────────────────┤
│ Choices (OptionList)         │
├─────────────────────────────┤
│ Footer (keybindings)         │
└─────────────────────────────┘

输入:
- ↑↓        移动选项
- Enter     确认
- 1-9       数字键快选
- s         显示完整状态
- q         退出
- 鼠标点击  选项
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, OptionList, RichLog, Static
from textual.widgets.option_list import Option

from ghost_story_factory.v5.player import (
    State, collect_important_items, resolve_narrative, resolve_next,
)
from ghost_story_factory.v7.map_view import format_map_lines
from ghost_story_factory.v7.save_manager import (
    SaveManager,
    get_character_info,
)


class MapScreen(ModalScreen):
    """地图屏 — 可由任意节点按 m 键弹出,任意键关闭。"""

    BINDINGS = [
        Binding("m", "app.pop_screen", "关闭"),
        Binding("escape", "app.pop_screen", "关闭"),
        Binding("enter", "app.pop_screen", "关闭"),
        Binding("q", "app.pop_screen", "关闭"),
    ]

    DEFAULT_CSS = """
    MapScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.85);
    }
    #map-box {
        width: 70;
        max-width: 90%;
        height: auto;
        padding: 1 2;
        background: #0a0505;
        border: heavy #800000;
    }
    #map-content {
        height: auto;
    }
    #map-hint {
        height: auto;
        color: #707070;
        text-align: center;
        padding-top: 1;
    }
    """

    def __init__(self, tree, state, save_manager, current_node_id, story_id):
        super().__init__()
        self._tree = tree
        self._state = state
        self._sm = save_manager
        self._current_node_id = current_node_id
        self._story_id = story_id

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical
        with Vertical(id="map-box"):
            yield Static(self._render_content(), id="map-content")
            yield Static("[dim]m / Enter / Esc 关闭[/]", id="map-hint")

    def _render_content(self) -> str:
        entries = format_map_lines(
            self._tree, self._state, self._sm,
            current_node_id=self._current_node_id,
            story_id=self._story_id,
        )
        out = ["[bold red]══════ 夜班路线图 ══════[/]", ""]
        for entry in entries:
            kind = entry["kind"]
            text = entry["text"]
            if kind == "header":
                out.append(f"[bold yellow]{text}[/]")
            elif kind == "section":
                out.append("")
            elif kind == "landmark":
                status = entry.get("status", "available")
                color = {
                    "visited": "dim",
                    "current": "bold magenta",
                    "available": "green",
                    "locked": "dim red",
                }.get(status, "white")
                out.append(f"[{color}]{text}[/]")
            elif kind == "progress":
                out.append(f"[bold cyan]{text}[/]")
            elif kind == "tool":
                on = entry.get("on", False)
                out.append(f"[bold green]{text}[/]" if on else f"[dim]{text}[/]")
            else:
                out.append(text)
        return "\n".join(out)


class StatusBar(Static):
    """顶部状态栏。每次 state 变化时调 update_state。"""

    def update_state(self, s: State) -> None:
        """常驻状态栏 — 不显示个人共鸣 / 全局共鸣(隐藏效果)。"""
        line1 = (
            f"[yellow]夜班[/] [bold]{s.shifts_completed}/7[/]  "
            f"[red]漏卡[/] [bold]{s.shifts_skipped}[/]"
        )
        if s.puzzle_pieces:
            line1 += f"  [green]拼图[/] [bold]{len(s.puzzle_pieces)}/5[/]"
        if s.character and s.character != "G-273":
            line1 += f"  [white on blue] {s.character} [/]"
        inv_str = " · ".join(s.inv) if s.inv else "—"
        line2 = f"[dim]随身:[/] {inv_str}"
        self.update(f"{line1}\n{line2}")


class GhostStoryApp(App):
    """v7 TUI 应用。"""

    CSS = """
    Screen {
        background: #0a0a0a;
        color: #d0d0d0;
    }

    Header {
        background: #1a0000;
        color: #ff8080;
    }

    #status-bar {
        height: 3;
        padding: 0 1;
        border: solid #800000;
        background: #100000;
    }

    #narrative-box {
        border: round #404040;
        padding: 0 1;
        margin: 0;
        background: #050505;
    }

    #narrative {
        background: #050505;
    }

    #choices {
        height: auto;
        max-height: 12;
        border: round #ffaa00;
        background: #0f0a00;
    }

    #choices > .option-list--option-highlighted {
        background: #ffaa00;
        color: #000000;
        text-style: bold;
    }

    Footer {
        background: #1a0a00;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("s", "show_status", "状态"),
        Binding("m", "show_map", "地图"),
        Binding("1", "select_choice(0)", "1", show=False),
        Binding("2", "select_choice(1)", "2", show=False),
        Binding("3", "select_choice(2)", "3", show=False),
        Binding("4", "select_choice(3)", "4", show=False),
        Binding("5", "select_choice(4)", "5", show=False),
        Binding("6", "select_choice(5)", "6", show=False),
        Binding("7", "select_choice(6)", "7", show=False),
        Binding("8", "select_choice(7)", "8", show=False),
        Binding("9", "select_choice(8)", "9", show=False),
    ]

    def __init__(self, tree_path: Path, character_id: Optional[str] = None):
        super().__init__()
        self._tree_path = tree_path
        with tree_path.open("r", encoding="utf-8") as f:
            self._tree = json.load(f)
        self.nodes: Dict[str, Dict[str, Any]] = self._tree["nodes"]
        self.title = self._tree.get("title", "断桥残雪")
        self.sub_title = self._tree.get("protagonist", "")
        # 跨周目存档
        self.save_manager = SaveManager()
        # 初始状态
        initial_state = dict(self._tree.get("initial_state", {}))
        # 多角色伏笔接口(默认 G-273,可被外部传入覆盖)
        characters = self._tree.get("characters") or {}
        chosen = character_id if character_id and character_id in characters else None
        if not chosen and characters and "G-273" in characters:
            chosen = "G-273"
        if chosen and chosen in characters:
            cdef = characters[chosen]
            initial_state["character"] = chosen
            if cdef.get("initial_inv"):
                initial_state["inv"] = list(cdef["initial_inv"])
            if cdef.get("initial_flags"):
                initial_state["flags"] = dict(cdef["initial_flags"])
        # 跨周目记忆 → State.meta_flags
        initial_state["meta_flags"] = dict(self.save_manager.meta_flags)
        self._character_id = chosen or "G-273"
        self.state = State(initial_state)
        # 注入道具说明字典(获得物品时显示用途)
        State.inv_descriptions = self._tree.get("inv_descriptions", {}) or {}
        # 关键道具集合(被 inv_has require 引用的视为剧情关键)
        self._important_items = collect_important_items(self._tree)
        # 起点:角色级 start_node 优先于 tree.start_node
        self.current_id = self._tree.get("start_node", "n_intro")
        if chosen and chosen in characters:
            self.current_id = characters[chosen].get("start_node", self.current_id)
        self.visible_choices: List[Dict[str, Any]] = []
        self.visited: List[str] = []
        self._ended = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatusBar(id="status-bar")
        with VerticalScroll(id="narrative-box"):
            yield RichLog(highlight=False, markup=True, wrap=True, id="narrative")
        yield OptionList(id="choices")
        yield Footer()

    def on_mount(self) -> None:
        self._render_node()

    def _render_node(self) -> None:
        if self._ended:
            return
        node = self.nodes.get(self.current_id)
        log = self.query_one("#narrative", RichLog)
        if node is None:
            log.write(f"[red bold][错误] 节点 {self.current_id} 不存在,故事中断。[/]")
            return

        self.visited.append(self.current_id)
        # 地标入场 banner — 节点带 _landmark_header 时显示
        header = node.get("_landmark_header")
        if header and isinstance(header, dict):
            t = header.get("time", "")
            p = header.get("place", "")
            log.write("")
            log.write(f"[dim]{'─' * 58}[/]")
            log.write("")
            log.write(f"          [bold yellow]{t}[/]")
            log.write(f"      [bold red]{p}[/]")
            log.write("")
            log.write(f"[dim]{'─' * 58}[/]")
            log.write("")
        # 伏笔自动跟踪 — 收集首次触发的 slot,稍后渲染卡片
        story_id = str(self._tree.get("story_id") or self._tree_path.stem)
        newly_seen_slots: List[str] = []
        for slot in node.get("_foreshadow_slot") or []:
            if self.save_manager.mark_foreshadow_seen(story_id, slot):
                newly_seen_slots.append(slot)
        # _is_map_picker 节点:用地图视图替代普通 narrative
        if node.get("_is_map_picker"):
            entries = format_map_lines(
                self._tree, self.state, self.save_manager,
                current_node_id=self.current_id,
                story_id=story_id,
            )
            log.write(f"\n[bold red]{'═' * 58}[/]")
            log.write("[bold red]              ══ 夜班路线图 ══[/]")
            log.write(f"[bold red]{'═' * 58}[/]\n")
            for entry in entries:
                kind = entry["kind"]
                text = entry["text"]
                if kind == "header":
                    log.write(f"[bold yellow]{text}[/]")
                elif kind == "section":
                    log.write("")
                elif kind == "landmark":
                    status = entry.get("status", "available")
                    color = {
                        "visited": "dim",
                        "current": "bold magenta",
                        "available": "green",
                        "locked": "dim red",
                    }.get(status, "white")
                    log.write(f"[{color}]{text}[/]")
                elif kind == "progress":
                    log.write(f"[bold cyan]{text}[/]")
                elif kind == "tool":
                    on = entry.get("on", False)
                    log.write(f"[bold green]{text}[/]" if on else f"[dim]{text}[/]")
                else:
                    log.write(text)
            log.write(f"\n[dim]{'─' * 58}[/]\n")
        else:
            narrative = resolve_narrative(node, self.state)
            if narrative:
                # 分隔线
                log.write(f"\n[dim]{'─' * 60}[/]")
                # 写 narrative
                for line in narrative.strip().split("\n"):
                    if line.strip():
                        log.write(line)
                    else:
                        log.write("")
                log.write("")

        # 首次发现伏笔 — 用青色短条反馈
        if newly_seen_slots:
            foreshadows = self._tree.get("foreshadows", {}) or {}
            for slot in newly_seen_slots:
                title = (foreshadows.get(slot) or {}).get("title", slot)
                log.write(f"  [bold cyan]▌ 档案 +1  ·  {title} ▐[/]")
            log.write("")

        # 更新状态栏
        self.query_one("#status-bar", StatusBar).update_state(self.state)

        # 滚动到底
        self.query_one("#narrative-box", VerticalScroll).scroll_end(animate=False)

        # 结局节点
        if node.get("is_ending"):
            ending_type = node.get("ending_type", "E_UNKNOWN")
            ending_name = self._tree.get("endings", {}).get(ending_type, ending_type)
            # 按结局类型分色 — 让 8 主结局视觉差异化
            ec_map = {
                "E_TRUE": "green",
                "E_HIDDEN": "yellow",
                "E_TRUTH": "cyan",
                "E_DATA": "magenta",
                "E_BROADCAST": "blue",
                "E_BAD_DROWN": "red",
                "E_BAD_1987": "red",
                "E_NEUTRAL": "white",
            }
            ec = ec_map.get(ending_type, "magenta")
            log.write(f"\n[bold {ec}]{'═' * 60}[/]")
            log.write(f"[bold {ec}]  【结局 · {ending_type}】 {ending_name}[/]")
            log.write(f"[bold {ec}]{'═' * 60}[/]")
            log.write(f"\n[dim]共经历 {len(self.visited)} 个节点。[/]")
            log.write(f"[dim]夜班没有尽头,只有下一班。[/]")
            # 写盘 + 显示解锁
            try:
                story_id = str(self._tree.get("story_id") or self._tree_path.stem)
                newly = self.save_manager.record_ending(ending_type, story_id=story_id)
                fs_resolved = self.save_manager.auto_resolve(
                    self._tree, ending_type, self.state.character, story_id
                )
                if newly:
                    log.write(f"\n[bold green]{'─' * 60}[/]")
                    log.write(f"[bold green]  ★ 新角色解锁:[/]")
                    for cid in newly:
                        info = get_character_info(cid) or {}
                        label = info.get("label", cid)
                        year = info.get("year", "")
                        sub = info.get("subtitle", "")
                        log.write(f"    [green]●[/] [bold]{label}[/]  [dim]· {year} · {sub}[/]")
                    log.write(f"[bold green]{'─' * 60}[/]")
                    log.write(f"[dim]下次启动主菜单 → 选剧情 → 选角色,即可体验。[/]")
                if fs_resolved:
                    log.write(f"\n[bold cyan]{'─' * 60}[/]")
                    log.write(f"[bold cyan]  ✦ 伏笔已解开:[/]")
                    foreshadows = self._tree.get("foreshadows", {}) or {}
                    for slot in fs_resolved:
                        meta = foreshadows.get(slot, {})
                        title = meta.get("title", slot)
                        summary = meta.get("summary_resolved", "")
                        log.write(f"    [cyan]●[/] [bold]{title}[/]")
                        if summary:
                            log.write(f"      [dim]{summary}[/]")
                    seen, resolved, total = self.save_manager.foreshadow_progress(
                        self._tree, story_id
                    )
                    log.write(f"[dim]  档案进度:已发现 {seen}/{total} · 已解开 {resolved}/{total}[/]")
                    log.write(f"[bold cyan]{'─' * 60}[/]")
            except Exception as e:
                log.write(f"[dim red]存档警告: {e}[/]")
            opts = self.query_one("#choices", OptionList)
            opts.clear_options()
            opts.add_option(Option("[退出] 按 Enter / q 结束", id="__end__"))
            self.visible_choices = []
            self._ended = True
            self.query_one("#narrative-box", VerticalScroll).scroll_end(animate=False)
            return

        # 选项分类:visible / locked / hidden
        all_choices = node.get("choices", []) or []
        self.visible_choices = []
        locked: List[tuple] = []
        for c in all_choices:
            status, hint = self.state.get_choice_status(c)
            if status == "visible":
                self.visible_choices.append(c)
            elif status == "locked":
                locked.append((c, hint))
            # hidden 跳过

        opts = self.query_one("#choices", OptionList)
        opts.clear_options()
        if not self.visible_choices and not locked:
            log.write("[red][警告] 此节点没有可用选项,故事中断。[/]")
            opts.add_option(Option("[退出] 按 Enter / q 结束", id="__end__"))
            self._ended = True
            return
        if not self.visible_choices:
            log.write("[red][警告] 所有选项都被锁住 — 缺关键道具。[/]")

        # 选项纯文本,不显示效果 hint(增强代入感)
        for i, ch in enumerate(self.visible_choices):
            label = ch.get("text", "(无文本)")
            opts.add_option(Option(f"{i+1}. {label}", id=str(i)))
        # 锁定选项:可见但禁用,带 🔒 + 缺失道具提示
        for ch, hint in locked:
            label = ch.get("text", "(无文本)")
            opts.add_option(
                Option(f"[red]🔒[/] [dim]{label}  — {hint}[/]",
                       id=f"__locked_{id(ch)}__", disabled=True)
            )

    @on(OptionList.OptionSelected, "#choices")
    def on_choice_selected(self, event: OptionList.OptionSelected) -> None:
        oid = event.option.id
        if oid == "__end__":
            self.exit()
            return
        try:
            idx = int(oid) if oid is not None else -1
        except (ValueError, TypeError):
            return
        self._apply_choice(idx)

    def _apply_choice(self, idx: int) -> None:
        if self._ended:
            return
        if idx < 0 or idx >= len(self.visible_choices):
            return
        chosen = self.visible_choices[idx]
        # 选项上若挂了 _foreshadow_slot,选了之后也算 seen
        story_id = str(self._tree.get("story_id") or self._tree_path.stem)
        for slot in chosen.get("_foreshadow_slot") or []:
            self.save_manager.mark_foreshadow_seen(story_id, slot)
        self.state.apply(chosen.get("effects"))
        log = self.query_one("#narrative", RichLog)
        log.write(f"\n[bold yellow]▸[/] [bold]{chosen.get('text', '')}[/]")
        # 卡片化渲染状态变化
        self._render_apply_events_tui(self.state._last_events, log)
        nxt = resolve_next(chosen, self.state)
        if not nxt:
            log.write("[red][错误] 选项缺少 next/next_variants 字段。[/]")
            self._ended = True
            return
        self.current_id = nxt
        self._render_node()

    def _render_apply_events_tui(self, events, log) -> None:
        """根据 events 在 RichLog 里卡片化渲染状态变化。"""
        if not events:
            return
        log.write("")
        for ev in events:
            t = ev.get("type")
            if t == "inv_add":
                key = ev["key"]
                desc = ev.get("desc", "")
                if key in self._important_items:
                    # 关键道具 — 边框卡片
                    fill = max(44 - 5 - len(key) - 4, 1)  # 粗略 visible 估算
                    log.write(f"  [bold green]╭─ 拾起「{key}」 {'─' * fill}╮[/]")
                    if desc:
                        log.write(f"     [dim]{desc}[/]")
                else:
                    line = f"  · 获得「{key}」"
                    if desc:
                        line += f" — {desc}"
                    log.write(f"[dim]{line}[/]")
            elif t == "inv_remove":
                log.write(f"[dim]  · 失去「{ev['key']}」[/]")
            elif t == "shifts_skipped":
                log.write(f"  [bold red]▌ 漏卡 +{ev['delta']} ▐[/]")
            elif t == "shifts_completed" and not ev.get("implicit"):
                cur = ev.get("current", 0)
                log.write(f"  [bold green]▌ 夜班 +{ev['delta']}  ({cur}/7) ▐[/]")
            elif t == "puzzle_add":
                log.write(f"  [bold cyan]▌ 拼图 +1  ({ev['current']}/{ev['total']}) ▐[/]")
            elif t == "landmark_visited":
                log.write(f"  [bold green]▌ 踏入 {ev['key']} ▐[/]")
            elif t == "landmark_skipped":
                log.write(f"  [bold red]▌ 绕开 {ev['key']} ▐[/]")
            elif t == "set_route":
                log.write(f"[dim]  · 路线确立:{ev['key']}[/]")

    def action_select_choice(self, idx: int) -> None:
        """1-9 数字键快选。"""
        self._apply_choice(idx)

    def action_show_map(self) -> None:
        """m 键 — 弹出夜班路线图(只读)。"""
        story_id = str(self._tree.get("story_id") or self._tree_path.stem)
        self.push_screen(MapScreen(
            self._tree, self.state, self.save_manager,
            self.current_id, story_id,
        ))

    def action_show_status(self) -> None:
        """s 键 — 显示完整状态(含个人共鸣 / 全局共鸣的具体数值 + 解释)。"""
        s = self.state
        log = self.query_one("#narrative", RichLog)
        log.write(f"\n[bold cyan]── 完整状态 ──[/]")
        log.write(f"  [cyan]个人共鸣[/] [bold]{s.PR}/100[/]   "
                  f"[magenta]全局共鸣[/] [bold]{s.GR}/100[/]")
        log.write(f"  [dim]· 个人共鸣 = 你被这个夜班影响的程度。越高越触发心境分支。[/]")
        log.write(f"  [dim]· 全局共鸣 = 杭州常数对你的注视。越高越被异常实体盯上。[/]")
        log.write(f"  [yellow]夜班[/] {s.shifts_completed}/7   "
                  f"[red]漏卡[/] {s.shifts_skipped}")
        if s.character and s.character != "G-273":
            log.write(f"  [blue]角色[/]: {s.character}")
        if s.puzzle_pieces:
            log.write(f"  [green]拼图[/]: {len(s.puzzle_pieces)}/5 — {' · '.join(s.puzzle_pieces[:8])}")
        if s.inv:
            log.write(f"  [white]随身[/]: {' · '.join(s.inv)}")
        if s.visited_landmarks:
            log.write(f"  已踏入: {', '.join(s.visited_landmarks)}")
        if s.skipped_landmarks:
            log.write(f"  已跳过: {', '.join(s.skipped_landmarks)}")
        if s.flags:
            true_flags = [k for k, v in s.flags.items() if v]
            if true_flags:
                shown = ', '.join(true_flags[:12])
                more = f" (+{len(true_flags) - 12} 更多)" if len(true_flags) > 12 else ""
                log.write(f"  [dim]内部标记[/]: {shown}{more}")
        # 伏笔档案
        foreshadows = self._tree.get("foreshadows", {}) or {}
        if foreshadows:
            story_id = str(self._tree.get("story_id") or self._tree_path.stem)
            seen_list = self.save_manager.data.get("foreshadows_seen", {}).get(story_id, [])
            resolved_set = set(self.save_manager.data.get("foreshadows_resolved", {}).get(story_id, []))
            if seen_list:
                log.write(f"\n[bold cyan]── 档案(已发现 {len(seen_list)}/{len(foreshadows)} · 已解 {len(resolved_set)}/{len(foreshadows)})──[/]")
                for slot in seen_list:
                    meta = foreshadows.get(slot, {})
                    title = meta.get("title", slot)
                    if slot in resolved_set:
                        summary = meta.get("summary_resolved", "")
                        log.write(f"  [green]✦[/] [bold]{title}[/]")
                        if summary:
                            log.write(f"    [dim]{summary}[/]")
                    else:
                        summary = meta.get("summary_locked", "")
                        log.write(f"  [dim]?[/] [dim]{title}[/]")
                        if summary:
                            log.write(f"    [dim]{summary}[/]")
            else:
                log.write(f"\n[dim]档案:0/{len(foreshadows)} · 还没发现任何伏笔[/]")
        log.write("")
        self.query_one("#narrative-box", VerticalScroll).scroll_end(animate=False)


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        path = Path(argv[0])
    else:
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / "stories" / "hangzhou_yebanbaoan" / "tree.json"
    if not path.exists():
        print(f"找不到对话树: {path}")
        return 1
    app = GhostStoryApp(path)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
