"""CLI 主菜单 — 三屏(城市 → 剧情 → 角色)。

设计:
- 复用 v5/player.py 的颜色函数,不引入新依赖
- 每屏一个函数,返回 None 表示退出
- 锁定项可见但不能选,提示解锁条件
- 通关后自动回到主菜单(可选)

入口:
    from ghost_story_factory.v7.menu_cli import main_menu
    main_menu()
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import random

from ghost_story_factory.v5 import player as v5player
from ghost_story_factory.v5.player import (
    bold, cyan, dim, green, magenta, red, yellow,
)
from ghost_story_factory.v7.animate import (
    clear_screen, fade_lines, pause, pulse_text, type_text,
)
from ghost_story_factory.v7.banner import banner_pieces, render_banner_lines
from ghost_story_factory.v7.menu_registry import (
    City, Story, CharacterEntry,
    list_cities, list_stories, list_characters,
)
from ghost_story_factory.v7.save_manager import SaveManager


# --- 输入 ---

def _read_choice(n: int, prompt: str = "请选择") -> Optional[int]:
    """读取 1..n 数字,q 退出,返回 0-based idx 或 None(退出)。"""
    while True:
        try:
            raw = input(bold(f"  {prompt} (1-{n}, q 退出): ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if raw.lower() in ("q", "quit", "exit"):
            return None
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= n:
                return idx - 1
        print(red(f"  请输入 1-{n}。"))


def _banner(title: str, subtitle: str = "") -> None:
    # 轻微切换停顿,营造屏幕过渡感(GHOST_FAST 跳过)
    pause(0.15)
    print(bold(red("\n" + "═" * 60)))
    print(bold(red(f"   {title}")))
    if subtitle:
        print(dim(f"   {subtitle}"))
    print(bold(red("═" * 60)))


def _fog_line(width: int = 60) -> str:
    """生成一行雾雪纹(随机 ░ ▒ ▓ 空格混合)— 营造氛围。"""
    chars = "░░░▒▒▓  "  # 空格多 → 稀疏感
    return "".join(random.choice(chars) for _ in range(width))


def screen_intro(sm: SaveManager) -> bool:
    """屏 0:启动屏(像素字标题 + 渐进入场)。返回 True 进入,False 退出。

    入场序列(GHOST_FAST=1 跳过 sleep):
      T=0.0s    清屏 + 黑屏 0.3s
      T=0.3s    顶部一行雾纹 0.4s 后被换行盖掉
      T=0.7s    像素字 6 行渐进出现(每行 0.10s)
      T=1.5s    副标题"鬼  夜  班"打字机
      T=2.0s    tagline 打字机
      T=2.5s    存档摘要(若有)灰色打字机
      T=3.0s    "按 Enter 开始" 呼吸闪烁 2 次后定亮
    """
    pieces = banner_pieces(60)

    # T=0:清屏 + 黑场
    clear_screen()
    pause(0.3)

    # T=0.3:雾纹一闪
    print(dim(_fog_line(60)))
    pause(0.4)

    # T=0.7:像素字渐进
    print()  # 上空行
    fade_lines(pieces["ascii_lines"], line_delay=0.10,
               color_fn=lambda l: bold(red(l)))
    print()
    pause(0.25)

    # T=1.5:副标题打字机(每个汉字慢一点)
    type_text(pieces["subtitle"], delay=0.07,
              color_fn=lambda c: bold(yellow(c)))
    pause(0.3)
    print()

    # T=2.0:tagline 打字机
    type_text(pieces["tagline"], delay=0.035,
              color_fn=lambda c: dim(c))
    pause(0.3)
    print()

    # T=3.0:呼吸闪烁按钮
    prompt = "  按 Enter 开始    q 退出  "
    pulse_text(
        prompt,
        cycles=2,
        period=0.9,
        bright_fn=lambda t: bold(green(t)),
        dim_fn=lambda t: dim(t),
    )
    print()

    # 阻塞等待
    while True:
        try:
            raw = input(bold("  > ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        if raw.lower() in ("q", "quit", "exit"):
            return False
        return True


# --- 三屏 ---

def screen_city(sm: SaveManager) -> Optional[City]:
    """屏 1:选城市。"""
    cities = list_cities()
    if not cities:
        print(red("\n  [错误] stories/ 下没有任何城市目录。"))
        return None
    _banner("选择城市", "")
    print(bold(cyan("\n  ┌── 城市列表 ──")))
    print()
    for i, c in enumerate(cities, start=1):
        if c.playable:
            count_tag = f"  {dim(f'· {c.story_count} 个剧本')}" if c.story_count else ""
            print(f"  {green(str(i))}. {bold(c.label)}{count_tag}")
            if c.subtitle:
                print(f"      {dim(c.subtitle)}")
        else:
            print(f"  {dim(red('🔒') + ' ' + c.label)}")
            if c.subtitle:
                print(f"      {dim(c.subtitle)}")
            if c.locked_reason:
                print(f"      {dim(c.locked_reason)}")
    print()
    # 只允许选 playable 的
    while True:
        idx = _read_choice(len(cities), prompt="选择城市")
        if idx is None:
            return None
        if cities[idx].playable:
            return cities[idx]
        print(red(f"  「{cities[idx].label}」未解锁:{cities[idx].locked_reason}"))


def screen_story(city: City, sm: SaveManager) -> Optional[Story]:
    """屏 2:选剧情(同城市内)。"""
    stories = list_stories(city)
    if not stories:
        print(red(f"\n  [错误] {city.label} 下没有可玩剧本。"))
        return None
    _banner(f"{city.label}", "选一个剧本。")
    print(bold(cyan("\n  ┌── 选择剧情 ──")))
    print()
    for i, s in enumerate(stories, start=1):
        # 通关标记 + 伏笔进度
        story_save_id = str(s.tree.get("story_id") or s.id)
        cleared_for_story = sm.data.get("stories_completed", {}).get(story_save_id, [])
        marker = green(f" ✓ {len(cleared_for_story)} 结局") if cleared_for_story else ""
        seen, resolved, total = sm.foreshadow_progress(s.tree, story_save_id)
        fs_marker = ""
        if total:
            fs_marker = f"  {dim('伏笔')} {cyan(f'{resolved}/{total}')}"
        print(f"  {green(str(i))}. {bold(s.label)}{marker}{fs_marker}")
        print(f"      {dim(s.subtitle)}")
    print()
    print(dim("  b 返回上级,q 退出\n"))
    while True:
        try:
            raw = input(bold(f"  选择剧情 (1-{len(stories)}, b 返回, q 退出): ")).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if raw.lower() in ("q", "quit", "exit"):
            return None
        if raw.lower() in ("b", "back"):
            return "BACK"  # type: ignore[return-value]
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(stories):
                return stories[idx - 1]
        print(red(f"  请输入 1-{len(stories)}。"))


def screen_character(story: Story, sm: SaveManager) -> Optional[str]:
    """屏 3:选角色。返回 character_id 或 None(退出)/'BACK'。"""
    chars = list_characters(story, sm)
    if not chars:
        # 无 characters 字段 → 直接进游戏
        return "G-273"
    _banner(f"{story.label}", "选择视角进入。")
    print(bold(cyan("\n  ┌── 选择角色 ──")))
    print()
    for i, c in enumerate(chars, start=1):
        marker = ""
        if sm.has_seen_ending("E_NEUTRAL") and c.id == "G-273":
            marker = ""  # 不重复 marker
        if c.unlocked:
            print(f"  {green(str(i))}. {bold(c.label)} · {dim(str(c.year))}")
            print(f"      {dim(c.subtitle)}")
        else:
            print(f"  {dim(red('🔒') + ' ' + c.label + ' · ' + str(c.year))}")
            print(f"      {dim(c.subtitle)}")
            if c.unlock_hint:
                # 已解锁但剧本未实现 vs 未达成解锁条件 → 用不同 prefix
                prefix = "状态" if c.unlock_hint.startswith("已解锁") else "解锁条件"
                print(f"      {yellow(prefix)}: {dim(c.unlock_hint)}")
    print()
    print(dim("  b 返回上级,q 退出\n"))
    while True:
        try:
            raw = input(bold(f"  选择角色 (1-{len(chars)}, b 返回, q 退出): ")).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if raw.lower() in ("q", "quit", "exit"):
            return None
        if raw.lower() in ("b", "back"):
            return "BACK"
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(chars):
                ch = chars[idx - 1]
                if not ch.unlocked:
                    print(red(f"  「{ch.label}」尚未解锁:{ch.unlock_hint}"))
                    continue
                return ch.id
        print(red(f"  请输入 1-{len(chars)}。"))


# --- 主流程 ---

def main_menu() -> int:
    """主菜单循环。返回 exit code。"""
    sm = SaveManager()
    # 只在首次进入显示启动屏(回主菜单后跳过,避免反复看)
    if not screen_intro(sm):
        return 0
    while True:
        city = screen_city(sm)
        if city is None:
            print(dim("\n  夜班暂歇。再见。\n"))
            return 0
        # 进入剧情屏(支持回退)
        story = screen_story(city, sm)
        if story is None:
            return 0
        if story == "BACK":
            continue
        # 选角色
        char_id = screen_character(story, sm)
        if char_id is None:
            return 0
        if char_id == "BACK":
            continue
        # 进入游戏 — 复用 v5/player.play(),传入 character_id
        v5player.play(story.tree_path, character_id=char_id)
        # 通关后:重新 load SaveManager 显示新解锁,然后回主菜单
        sm = SaveManager()
        print(bold(cyan("\n  返回主菜单...\n")))


def main(argv: Optional[list] = None) -> int:
    return main_menu()


if __name__ == "__main__":
    sys.exit(main())
