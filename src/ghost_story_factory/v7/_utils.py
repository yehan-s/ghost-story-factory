"""v7 共享小工具。"""

from __future__ import annotations


def visible_width(text: str) -> int:
    """估算终端可见宽度:中文/全角算 2,其余字符算 1。"""
    width = 0
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef":
            width += 2
        else:
            width += 1
    return width
