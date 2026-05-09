"""动画原语 — 给 CLI 启动屏 / 章节过渡用。

设计:
- 不依赖 textual / rich,只用 ANSI + time.sleep
- 全部尊重 GHOST_FAST=1 跳过(兼容已有 slow_print 约定)
- 不做 cursor 上下移这类高风险操作(终端兼容性)
- KeyboardInterrupt 捕获,Ctrl-C 立即退出

API:
- type_text(text, delay):字符级打字机(标点更长停顿)
- fade_lines(lines, line_delay):行级出现
- pulse_text(text, cycles):呼吸闪烁(亮 ↔ 半暗)
- pause(seconds):可被 GHOST_FAST 跳过的 sleep
- clear_screen():ANSI 清屏
"""

from __future__ import annotations

import os
import sys
import time
from typing import Callable, Iterable, Optional

from ghost_story_factory.v7._utils import visible_width


def _fast() -> bool:
    return bool(os.environ.get("GHOST_FAST"))


def _supports_color() -> bool:
    return not os.environ.get("NO_COLOR") and sys.stdout.isatty()


def pause(seconds: float) -> None:
    """可被 GHOST_FAST 跳过的 sleep。"""
    if _fast() or seconds <= 0:
        return
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        raise


def clear_screen() -> None:
    """ANSI 清屏 + 光标归位。GHOST_FAST 模式仍执行(基础 UX)。"""
    if not _supports_color():
        return
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def type_text(
    text: str,
    delay: float = 0.04,
    end: str = "\n",
    color_fn: Optional[Callable[[str], str]] = None,
) -> None:
    """字符级打字机。标点后停顿更长,营造节奏。

    Args:
        text: 要打印的文本(假定已经过 padding/center)
        delay: 单字符基准延迟(秒)
        end: 行尾字符
        color_fn: 可选着色函数(对每个字符调用)— 若为 None 直接打印
    """
    if _fast():
        if color_fn:
            sys.stdout.write(color_fn(text) + end)
        else:
            sys.stdout.write(text + end)
        sys.stdout.flush()
        return
    try:
        for ch in text:
            out = color_fn(ch) if color_fn else ch
            sys.stdout.write(out)
            sys.stdout.flush()
            if ch in "。!?!?\n":
                time.sleep(delay * 8)
            elif ch in ",,、;;::":
                time.sleep(delay * 3)
            elif ch in " ":
                time.sleep(delay * 0.5)
            else:
                time.sleep(delay)
        sys.stdout.write(end)
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write(end)
        sys.stdout.flush()
        raise


def fade_lines(
    lines: Iterable[str],
    line_delay: float = 0.10,
    color_fn: Optional[Callable[[str], str]] = None,
) -> None:
    """行级出现 — 一行一行打印,每行间停顿。

    Args:
        lines: 要打印的行(可迭代)
        line_delay: 每行间延迟
        color_fn: 整行着色函数
    """
    if _fast():
        for line in lines:
            sys.stdout.write((color_fn(line) if color_fn else line) + "\n")
        sys.stdout.flush()
        return
    try:
        for line in lines:
            sys.stdout.write((color_fn(line) if color_fn else line) + "\n")
            sys.stdout.flush()
            time.sleep(line_delay)
    except KeyboardInterrupt:
        raise


def card(
    text: str,
    color_fn: Optional[Callable[[str], str]] = None,
    width: int = 44,
    indent: str = "  ",
) -> None:
    """单行标题卡片 ╭─ X ─────╮(横线在右侧延伸到 width)。"""
    text_w = visible_width(text)
    # 总 visible 宽 = 1(╭) + 1(─) + 1(空) + text + 1(空) + N(─) + 1(╮) = width
    fill = max(width - text_w - 5, 1)
    line = f"╭─ {text} {'─' * fill}╮"
    if color_fn:
        line = color_fn(line)
    sys.stdout.write(indent + line + "\n")
    sys.stdout.flush()


def flash_line(
    text: str,
    color_fn: Optional[Callable[[str], str]] = None,
    indent: str = "  ",
    width: int = 44,
) -> None:
    """高亮短条: ▌ X ▐ — 比 card 更轻量,用于状态变化。"""
    inner = max(width - 4, visible_width(text) + 2)
    pad = inner - visible_width(text)
    line = f"▌ {text}{' ' * pad}▐"
    if color_fn:
        line = color_fn(line)
    sys.stdout.write(indent + line + "\n")
    sys.stdout.flush()


def separator(
    width: int = 60,
    char: str = "─",
    color_fn: Optional[Callable[[str], str]] = None,
    indent: str = "",
) -> None:
    """横线分隔符 — 节点 header / 章节边界。"""
    line = char * width
    if color_fn:
        line = color_fn(line)
    sys.stdout.write(indent + line + "\n")
    sys.stdout.flush()


_GLITCH_CHARS = "▓░█▒▌▐■□◆◇♠♣◎※"


def glitch_text(
    text: str,
    color_fn: Optional[Callable[[str], str]] = None,
    frames: int = 4,
    frame_delay: float = 0.08,
    glitch_ratio: float = 0.3,
) -> None:
    """关键时刻字符闪 — text 用同长度的乱码替换 frames 次,最后定到 text。

    用 \\r 单行重写。每帧随机替换 glitch_ratio(0~1)比例的字符为 ▓░█▒…。
    """
    import random
    if not _supports_color() or _fast():
        sys.stdout.write((color_fn(text) if color_fn else text) + "\n")
        sys.stdout.flush()
        return
    try:
        chars = list(text)
        n = len(chars)
        glitch_count = max(1, int(n * glitch_ratio))
        for _ in range(frames):
            scrambled = chars[:]
            indices = random.sample(range(n), min(glitch_count, n))
            for i in indices:
                scrambled[i] = random.choice(_GLITCH_CHARS)
            line = "".join(scrambled)
            sys.stdout.write("\r" + (color_fn(line) if color_fn else line))
            sys.stdout.flush()
            time.sleep(frame_delay)
        # 定到正常
        sys.stdout.write("\r" + (color_fn(text) if color_fn else text) + "\n")
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise


def draw_line_progressive(
    width: int = 60,
    char: str = "▔",
    color_fn: Optional[Callable[[str], str]] = None,
    char_delay: float = 0.012,
) -> None:
    """逐字符画一条横线 — 制造『翻页』感。"""
    if _fast() or not _supports_color():
        line = char * width
        sys.stdout.write((color_fn(line) if color_fn else line) + "\n")
        sys.stdout.flush()
        return
    try:
        sys.stdout.write("  ")
        for _ in range(width):
            sys.stdout.write(color_fn(char) if color_fn else char)
            sys.stdout.flush()
            time.sleep(char_delay)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise


def heartbeat_pulse(
    color_fn: Optional[Callable[[str], str]] = None,
    beats: int = 2,
    period: float = 0.6,
) -> None:
    """心跳条 — 「· · · ●  · · ●」节奏(高 PR 时调用,暗示焦虑)。

    用 \\r 重写,占 1 行,2 次心跳后清掉换行。
    """
    if _fast() or not _supports_color():
        return  # 静默(快进模式不显示)
    frames = [
        "  ·   ·   ·       ",
        "  ·   ·   ·   ●   ",
        "  ·   ·   ●       ",
        "  ·   ●           ",
        "  ●               ",
        "                  ",
    ]
    try:
        for _ in range(beats):
            for frame in frames:
                sys.stdout.write("\r" + (color_fn(frame) if color_fn else frame))
                sys.stdout.flush()
                time.sleep(period / len(frames))
        # 清掉
        sys.stdout.write("\r" + " " * len(frames[0]) + "\r")
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise


def keyword_flash(
    line: str,
    keyword: str,
    color_fn: Optional[Callable[[str], str]] = None,
    cycles: int = 2,
    period: float = 0.4,
) -> None:
    """在一行里只闪烁某个关键词,行内其它部分保持。

    用 \\r 重写,关键词用 ANSI 反白 ↔ 普通色 切换。
    """
    if _fast() or not _supports_color():
        if keyword and color_fn:
            line = line.replace(keyword, color_fn(keyword))
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        return
    if keyword not in line:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        return
    bright = color_fn(keyword) if color_fn else f"\033[7m{keyword}\033[0m"
    plain = keyword
    try:
        for _ in range(cycles):
            sys.stdout.write("\r" + line.replace(keyword, plain))
            sys.stdout.flush()
            time.sleep(period / 2)
            sys.stdout.write("\r" + line.replace(keyword, bright))
            sys.stdout.flush()
            time.sleep(period / 2)
        sys.stdout.write("\r" + line.replace(keyword, bright) + "\n")
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise


def pulse_text(
    text: str,
    cycles: int = 2,
    period: float = 0.9,
    bright_fn: Optional[Callable[[str], str]] = None,
    dim_fn: Optional[Callable[[str], str]] = None,
) -> None:
    """呼吸闪烁 — 亮 ↔ 半暗交替 cycles 次,最后定亮。

    用 \\r 行内重写实现(单行内,不动光标上下)。
    """
    if not _supports_color() or _fast():
        sys.stdout.write((bright_fn(text) if bright_fn else text) + "\n")
        sys.stdout.flush()
        return
    half = period / 2
    try:
        for _ in range(cycles):
            sys.stdout.write("\r" + (dim_fn(text) if dim_fn else text))
            sys.stdout.flush()
            time.sleep(half)
            sys.stdout.write("\r" + (bright_fn(text) if bright_fn else text))
            sys.stdout.flush()
            time.sleep(half)
        # 定格亮色 + 换行
        sys.stdout.write("\r" + (bright_fn(text) if bright_fn else text) + "\n")
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise
