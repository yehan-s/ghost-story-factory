"""Slug 工具

提供稳定的 slug 生成：safe_kebab(title) 与 story_slug(city, title)
"""

from typing import Optional


def safe_kebab(s: str, max_len: int = 80) -> str:
    """将任意字符串标准化为 kebab-case，仅含 [a-z0-9-]。

    规则：
    - NFKC 归一化（全角转半角）
    - 过滤：仅保留字母/数字/空格/下划线/连字符
    - 汉字转拼音（无声调，逐字）若库不可用则跳过
    - 小写；空白/下划线→'-'；折叠多连字符、去首尾'-'
    - 截断到 max_len；为空则返回 'story'
    """
    import unicodedata, re

    if not isinstance(s, str):
        s = str(s or "")

    s = unicodedata.normalize("NFKC", s)
    # 过滤 emoji/符号，仅保留字母数字空格下划线连字符
    s = "".join(ch for ch in s if (ch.isalnum() or ch in " -_"))

    # 汉字转拼音（可选）
    try:
        if any('\u4e00' <= ch <= '\u9fff' for ch in s):
            from pypinyin import lazy_pinyin  # type: ignore
            s = "-".join(lazy_pinyin(s))
    except Exception:
        pass

    s = s.lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return (s or "story")[:max_len]


def story_slug(city: str, title: str) -> str:
    """生成故事 slug：<city_slug>__<title_slug>"""
    city_slug = safe_kebab(city)
    title_slug = safe_kebab(title)
    return f"{city_slug}__{title_slug}"


