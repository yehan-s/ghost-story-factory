"""TUI 主菜单 — 三屏(城市 → 剧情 → 角色)。

设计:
- 复用 menu_registry 的扫描逻辑
- 用 Textual Screen 栈管理导航(push/pop)
- 选择完毕后退出 App,返回 (tree_path, character_id),由调用者启动 game App

为什么不和 GhostStoryApp 合并到一个 App 里?
- 保持职责单一:menu 只做选择,game 只做玩法,出 bug 互不影响
- App 退出 / 切换 App 在 Textual 中是干净的(不会留残留)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option

import os
import random

from ghost_story_factory.v7.banner import banner_pieces
from ghost_story_factory.v7.menu_registry import (
    City, Story,
    list_cities, list_stories, list_characters,
)
from ghost_story_factory.v7.save_manager import SaveManager


CSS = """
Screen { background: #0a0a0a; color: #d0d0d0; }
Header { background: #1a0000; color: #ff8080; }

#status {
    height: 3;
    padding: 0 2;
    border: solid #800000;
    background: #100000;
    color: #ffaa00;
}

#title {
    height: auto;
    padding: 1 2;
    color: #ff8080;
    text-style: bold;
}

#options {
    height: auto;
    border: round #ffaa00;
    background: #0f0a00;
    padding: 0 1;
}

#options > .option-list--option-highlighted {
    background: #ffaa00;
    color: #000000;
    text-style: bold;
}

#hint {
    height: auto;
    padding: 1 2;
    color: #707070;
}

#intro-fog {
    height: 1;
    padding: 0 2;
    color: #404040;
    text-align: center;
}

#intro-banner {
    height: auto;
    padding: 1 2 0 2;
    background: #050000;
    text-align: center;
    color: #400000;
}

#intro-subtitle {
    height: auto;
    padding: 1 2 0 2;
    text-align: center;
    color: #ffaa00;
    text-style: bold;
}

#intro-tagline {
    height: auto;
    padding: 0 2 1 2;
    color: #707070;
    text-align: center;
}

#intro-summary {
    height: auto;
    padding: 0 2;
    color: #707070;
    text-align: center;
}

#intro-prompt {
    height: auto;
    padding: 2 2;
    text-align: center;
    color: #ffaa00;
}
"""


# --- 启动屏 ---

class IntroScreen(Screen):
    """启动屏 — 像素字标题 + 渐进入场。

    入场序列(GHOST_FAST=1 一次性显示):
      0.0s  雾纹一闪
      0.4s  像素字逐行渐进 + 颜色从暗红到亮红
      1.5s  副标题"鬼  夜  班"
      2.1s  tagline
      2.6s  存档摘要
      3.0s  按钮显现并开始呼吸闪烁
    """

    BINDINGS = [
        Binding("enter", "begin", "开始", priority=True),
        Binding("space", "begin", "开始", priority=True),
        Binding("q", "app.exit", "退出"),
        Binding("escape", "app.exit", "退出"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("", id="intro-fog")
        yield Static("", id="intro-banner")
        yield Static("", id="intro-subtitle")
        yield Static("", id="intro-tagline")
        yield Static("", id="intro-prompt")
        yield Footer()

    def on_mount(self) -> None:
        self._pieces = banner_pieces(60)
        self._ascii_revealed = 0
        self._pulse_bright = True
        self._fast = bool(os.environ.get("GHOST_FAST"))

        if self._fast:
            # 一次性显示完整画面
            self._show_fog()
            for _ in self._pieces["ascii_lines"]:
                self._reveal_next_ascii_line()
            self._show_subtitle()
            self._show_tagline()
            self._show_prompt()
            return

        # 分阶段调度
        self.set_timer(0.05, self._show_fog)
        # 像素字 6 行,每行 0.10s
        for i in range(len(self._pieces["ascii_lines"])):
            self.set_timer(0.45 + i * 0.10, self._reveal_next_ascii_line)
        self.set_timer(1.4, self._show_subtitle)
        self.set_timer(2.0, self._show_tagline)
        self.set_timer(2.6, self._show_prompt)
        self.set_timer(2.8, self._start_pulse)

    # --- 阶段 ---

    def _show_fog(self) -> None:
        chars = "░░░▒▒▓  "
        fog = "".join(random.choice(chars) for _ in range(60))
        self.query_one("#intro-fog", Static).update(f"[dim]{fog}[/]")

    def _reveal_next_ascii_line(self) -> None:
        i = self._ascii_revealed
        lines = self._pieces["ascii_lines"]
        if i >= len(lines):
            return
        # 累积已显示的行,新行 bold red,前面行也是 bold red
        revealed = lines[: i + 1]
        text = "\n".join(f"[bold red]{l}[/]" for l in revealed)
        self.query_one("#intro-banner", Static).update(text)
        self._ascii_revealed = i + 1

    def _show_subtitle(self) -> None:
        self.query_one("#intro-subtitle", Static).update(
            f"[bold yellow]{self._pieces['subtitle']}[/]"
        )

    def _show_tagline(self) -> None:
        self.query_one("#intro-tagline", Static).update(
            f"[dim]{self._pieces['tagline']}[/]"
        )

    def _show_prompt(self) -> None:
        self.query_one("#intro-prompt", Static).update(
            "[bold yellow]按 Enter 开始[/]    [dim]q 退出[/]"
        )

    def _start_pulse(self) -> None:
        # 1.2s 周期闪烁:bold yellow ↔ dim
        self.set_interval(0.6, self._toggle_prompt)

    def _toggle_prompt(self) -> None:
        self._pulse_bright = not self._pulse_bright
        if self._pulse_bright:
            self.query_one("#intro-prompt", Static).update(
                "[bold yellow]按 Enter 开始[/]    [dim]q 退出[/]"
            )
        else:
            self.query_one("#intro-prompt", Static).update(
                "[#806000]按 Enter 开始[/]    [dim]q 退出[/]"
            )

    def action_begin(self) -> None:
        self.app.push_screen(CityScreen())


# --- 城市屏 ---

class CityScreen(Screen):
    BINDINGS = [
        Binding("q", "app.exit", "退出"),
        Binding("escape", "app.exit", "退出"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(
            "[bold]选择城市[/]",
            id="title",
        )
        opts = OptionList(id="options")
        cities = list_cities()
        self._cities = cities
        for i, c in enumerate(cities):
            if c.playable:
                count_tag = f"  [dim]· {c.story_count} 个剧本[/]" if c.story_count else ""
                sub_line = f"\n   [dim]{c.subtitle}[/]" if c.subtitle else ""
                label = f"{i+1}. [bold]{c.label}[/]{count_tag}{sub_line}"
                opts.add_option(Option(label, id=f"city:{i}"))
            else:
                sub_line = f"\n   [dim]{c.subtitle}[/]" if c.subtitle else ""
                lock_line = f"\n   [dim]{c.locked_reason}[/]" if c.locked_reason else ""
                label = f"[red]🔒[/] [dim]{c.label}[/]{sub_line}{lock_line}"
                opts.add_option(Option(label, id=f"locked:{i}", disabled=True))
        yield opts
        yield Static("[dim]↑↓ 移动 · Enter 选择 · q 退出[/]", id="hint")
        yield Footer()

    @on(OptionList.OptionSelected, "#options")
    def on_select(self, event: OptionList.OptionSelected) -> None:
        oid = event.option.id or ""
        if not oid.startswith("city:"):
            return
        idx = int(oid.split(":", 1)[1])
        city = self._cities[idx]
        if not city.playable:
            return
        self.app.push_screen(StoryScreen(city))


# --- 剧情屏 ---

class StoryScreen(Screen):
    BINDINGS = [
        Binding("q", "app.exit", "退出"),
        Binding("b", "app.pop_screen", "返回"),
        Binding("escape", "app.pop_screen", "返回"),
    ]

    def __init__(self, city: City):
        super().__init__()
        self.city = city

    def compose(self) -> ComposeResult:
        sm: SaveManager = self.app.save_manager  # type: ignore[attr-defined]
        yield Header(show_clock=False)
        yield Static(
            f"[bold red]{self.city.label}[/]\n"
            f"[dim]{self.city.subtitle} · 选一个剧本[/]",
            id="title",
        )
        opts = OptionList(id="options")
        stories = list_stories(self.city)
        self._stories = stories
        for i, s in enumerate(stories):
            story_save_id = str(s.tree.get("story_id") or s.id)
            cleared = sm.data.get("stories_completed", {}).get(story_save_id, [])
            mark = f" [green]✓ {len(cleared)} 结局[/]" if cleared else ""
            seen, resolved, total = sm.foreshadow_progress(s.tree, story_save_id)
            fs_mark = f"  [cyan]伏笔 {resolved}/{total}[/]" if total else ""
            label = f"{i+1}. [bold]{s.label}[/]{mark}{fs_mark}\n   [dim]{s.subtitle}[/]"
            opts.add_option(Option(label, id=f"story:{i}"))
        yield opts
        yield Static("[dim]↑↓ 移动 · Enter 选择 · b/Esc 返回 · q 退出[/]", id="hint")
        yield Footer()

    @on(OptionList.OptionSelected, "#options")
    def on_select(self, event: OptionList.OptionSelected) -> None:
        oid = event.option.id or ""
        if not oid.startswith("story:"):
            return
        idx = int(oid.split(":", 1)[1])
        self.app.push_screen(CharacterScreen(self.city, self._stories[idx]))


# --- 角色屏 ---

class CharacterScreen(Screen):
    BINDINGS = [
        Binding("q", "app.exit", "退出"),
        Binding("b", "app.pop_screen", "返回"),
        Binding("escape", "app.pop_screen", "返回"),
    ]

    def __init__(self, city: City, story: Story):
        super().__init__()
        self.city = city
        self.story = story

    def compose(self) -> ComposeResult:
        sm: SaveManager = self.app.save_manager  # type: ignore[attr-defined]
        yield Header(show_clock=False)
        yield Static(
            f"[bold red]{self.story.label}[/]\n"
            f"[dim]{self.story.subtitle} · 选择视角[/]",
            id="title",
        )
        opts = OptionList(id="options")
        chars = list_characters(self.story, sm)
        self._chars = chars
        for i, c in enumerate(chars):
            if c.unlocked:
                label = (
                    f"{i+1}. [bold]{c.label}[/]  [dim]· {c.year}[/]\n"
                    f"   [dim]{c.subtitle}[/]"
                )
                opts.add_option(Option(label, id=f"char:{i}"))
            else:
                if c.unlock_hint:
                    prefix = "状态" if c.unlock_hint.startswith("已解锁") else "解锁条件"
                    hint_line = f"   [yellow]{prefix}[/]: [dim]{c.unlock_hint}[/]"
                else:
                    hint_line = ""
                label = (
                    f"[red]🔒[/] [dim]{c.label}  · {c.year}\n"
                    f"   {c.subtitle}[/]\n"
                    f"{hint_line}"
                )
                opts.add_option(Option(label, id=f"locked:{i}", disabled=True))
        yield opts
        yield Static("[dim]↑↓ 移动 · Enter 选择 · b/Esc 返回 · q 退出[/]", id="hint")
        yield Footer()

    @on(OptionList.OptionSelected, "#options")
    def on_select(self, event: OptionList.OptionSelected) -> None:
        oid = event.option.id or ""
        if not oid.startswith("char:"):
            return
        idx = int(oid.split(":", 1)[1])
        char = self._chars[idx]
        if not char.unlocked:
            return
        # 选定 → 把结果挂到 app 上,退出
        app: MenuApp = self.app  # type: ignore[assignment]
        app.selected_tree = self.story.tree_path
        app.selected_character = char.id
        app.exit()


# --- 主 App ---

class MenuApp(App):
    """主菜单 App。退出时通过 selected_tree / selected_character 返回选择。"""

    CSS = CSS
    TITLE = "Ghost Story Factory"

    def __init__(self):
        super().__init__()
        self.save_manager = SaveManager()
        self.selected_tree: Optional[Path] = None
        self.selected_character: Optional[str] = None

    def on_mount(self) -> None:
        self.push_screen(IntroScreen())


def run_menu() -> Tuple[Optional[Path], Optional[str]]:
    """运行主菜单,返回 (tree_path, character_id)。
    用户退出 → (None, None)。"""
    app = MenuApp()
    app.run()
    return app.selected_tree, app.selected_character
