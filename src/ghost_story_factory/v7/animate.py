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


def _visible_width(text: str) -> int:
    """估算可见宽度(中文 2,ASCII 1)— 给居中和卡片对齐用。"""
    w = 0
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef":
            w += 2
        else:
            w += 1
    return w


def card(
    text: str,
    color_fn: Optional[Callable[[str], str]] = None,
    width: int = 44,
    indent: str = "  ",
) -> None:
    """单行标题卡片 ╭─ X ─────╮(横线在右侧延伸到 width)。"""
    text_w = _visible_width(text)
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
    inner = max(width - 4, _visible_width(text) + 2)
    pad = inner - _visible_width(text)
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
