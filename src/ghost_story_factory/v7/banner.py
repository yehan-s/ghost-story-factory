"""标题 banner — CLI/TUI 共享。

设计:
- 不引入 figlet 依赖(已有 rich + 自定义 ANSI 足够)
- 硬编码两段:英文像素字主标题 + 中文副标题
- 提供 render_banner_lines() 返回纯文本行(无颜色),由调用方加颜色
"""

from __future__ import annotations

from typing import List


# 主标题:GHOST STORIES (用 ANSI Shadow 风格手写,7 行高)
# 字宽控制在 60 字符内,适配标准终端
_BANNER_LINES: List[str] = [
    " ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗",
    "██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝",
    "██║  ███╗███████║██║   ██║███████╗   ██║   ",
    "██║   ██║██╔══██║██║   ██║╚════██║   ██║   ",
    "╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ",
    " ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ",
]

_SUBTITLE = "鬼  夜  班"
_TAGLINE = "—— 选一座城,开始你的班 ——"


def render_banner_lines(width: int = 60) -> List[str]:
    """返回 banner 多行纯文本(无颜色),调用方自行染色。

    Args:
        width: 目标终端宽度(用于居中)

    Returns:
        List[str]: 多行文本,每行已居中
    """
    out: List[str] = [""]
    for line in _BANNER_LINES:
        out.append(_center(line, width))
    out.append("")
    out.append(_center(_SUBTITLE, width))
    out.append("")
    out.append(_center(_TAGLINE, width))
    out.append("")
    return out


def _center(text: str, width: int) -> str:
    """中文 + ASCII 混合居中(中文按 2 宽度算)。"""
    visible = _visible_width(text)
    if visible >= width:
        return text
    pad = (width - visible) // 2
    return " " * pad + text


def _visible_width(text: str) -> int:
    """估算可见宽度(中文 2,ASCII 1,box drawing 块字符 1)。"""
    w = 0
    for ch in text:
        # 中文 / 全角字符 → 2
        if "\u4e00" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef":
            w += 2
        else:
            w += 1
    return w


# Rich-friendly markup 版本(给 textual 用)
def render_banner_rich(width: int = 60) -> str:
    """返回带 rich markup 的多行字符串。"""
    lines = []
    lines.append("")
    for line in _BANNER_LINES:
        lines.append(f"[bold red]{_center(line, width)}[/]")
    lines.append("")
    lines.append(f"[bold yellow]{_center(_SUBTITLE, width)}[/]")
    lines.append("")
    lines.append(f"[dim]{_center(_TAGLINE, width)}[/]")
    return "\n".join(lines)
