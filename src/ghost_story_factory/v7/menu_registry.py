"""主菜单数据层 — 扫描 stories/ 目录构建可玩剧情列表。

数据结构(扁平,无嵌套花活):
- City: {id, label, subtitle, playable, dir, story_count}
- Story: {id, label, subtitle, playable, tree_path, tree_data(lazy)}
- Character: {id, label, year, subtitle, unlocked, unlock_hint}

扫描规则:
- stories/<city_slug>/ 是一个城市
  - 可选: meta.json {city_label, city_subtitle, locked_reason}
  - tree.json (主线剧本,必有)
- 没有 tree.json 的目录视为"待开发"

不要在菜单层做 require 判断 — 让 SaveManager 决定是否解锁。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghost_story_factory.v7.save_manager import (
    CHARACTER_ROSTER,
    SaveManager,
    get_character_info,
)


# --- 数据类 ---

@dataclass
class City:
    """一个城市(stories/ 下的子目录)。"""
    id: str
    label: str
    subtitle: str
    playable: bool
    dir: Path
    locked_reason: str = ""
    story_count: int = 0  # 该城市下可玩剧本数(动态扫描)


@dataclass
class Story:
    """一个剧本(<city_dir>/tree*.json)。"""
    id: str
    label: str
    subtitle: str
    playable: bool
    tree_path: Path
    tree: Dict[str, Any] = field(default_factory=dict)  # lazy 加载


@dataclass
class CharacterEntry:
    """一个角色卡(在某剧本内可选)。"""
    id: str
    label: str
    year: int
    subtitle: str
    unlocked: bool
    unlock_hint: str = ""


# --- 扫描 ---

# 已知剧本展示顺序(主线 > v6 > v1)
# 剧本默认显示名 fallback(优先读 tree.json 顶层 display_name / display_subtitle)
_TREE_FALLBACK = {
    "tree.json": (0, "断桥残雪", "杭州夜班"),
}

# 默认城市标签(若 meta.json 不存在)— 城市本身只是城市,不带剧本/时段
# 城市的"剧本数 / 已通关数"会动态计算后追加到副标题
_CITY_DEFAULT_LABELS = {
    "hangzhou_yebanbaoan": ("杭州", "西湖周边"),
}


def _stories_root() -> Path:
    """定位 stories/ 根目录。

    优先级:
    1. 环境变量 `GHOST_STORY_STORIES_DIR`(显式覆盖,debug 友好)
    2. PyInstaller 冻结模式 → `sys._MEIPASS/stories`(打包进 binary 的资源)
    3. 源码运行 → `<repo_root>/stories`
    """
    import os
    import sys

    override = os.environ.get("GHOST_STORY_STORIES_DIR")
    if override:
        return Path(override)

    # PyInstaller 冻结模式
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "stories"  # type: ignore[attr-defined]

    # 源码运行:src/ghost_story_factory/v7/menu_registry.py → repo_root
    here = Path(__file__).resolve()
    return here.parents[3] / "stories"


# 公开别名:供其他模块统一使用
stories_root = _stories_root


def list_cities() -> List[City]:
    """列出 stories/ 下所有城市。"""
    root = _stories_root()
    if not root.exists():
        return []
    cities: List[City] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        meta_path = child / "meta.json"
        meta: Dict[str, Any] = {}
        if meta_path.exists():
            try:
                with meta_path.open("r", encoding="utf-8") as f:
                    meta = json.load(f) or {}
            except (json.JSONDecodeError, OSError):
                meta = {}
        default_label, default_sub = _CITY_DEFAULT_LABELS.get(
            child.name, (child.name, "")
        )
        label = meta.get("city_label") or default_label
        subtitle = meta.get("city_subtitle") or default_sub
        # 数主线剧本数(扫 _TREE_FALLBACK 里登记的所有 tree)
        story_count = sum(1 for fn in _TREE_FALLBACK if (child / fn).exists())
        playable = story_count > 0 and not meta.get("disabled", False)
        locked_reason = meta.get("locked_reason", "") or (
            "" if playable else "(剧本待开发)"
        )
        cities.append(City(
            id=child.name,
            label=label,
            subtitle=subtitle,
            playable=playable,
            dir=child,
            locked_reason=locked_reason,
            story_count=story_count,
        ))
    # 占位「待开发」城市:让用户感受到框架可扩展(只是城市,不绑剧本/时段)
    if cities:
        cities.append(City(
            id="__placeholder_wuhan",
            label="武汉",
            subtitle="长江沿岸",
            playable=False,
            dir=Path(),
            locked_reason="(剧本待开发)",
        ))
        cities.append(City(
            id="__placeholder_shanghai",
            label="上海",
            subtitle="外滩 · 黄浦江两岸",
            playable=False,
            dir=Path(),
            locked_reason="(剧本待开发)",
        ))
        cities.append(City(
            id="__placeholder_beijing",
            label="北京",
            subtitle="二环 · 老城区",
            playable=False,
            dir=Path(),
            locked_reason="(剧本待开发)",
        ))
    return cities


def list_stories(city: City) -> List[Story]:
    """列出某城市内所有可玩剧本。

    剧本名优先读 tree.json 顶层 `display_name` / `display_subtitle`;
    缺失则 fallback 到 _TREE_FALLBACK 表。
    """
    if not city.playable or not city.dir.exists():
        return []
    out: List[Story] = []
    for fn, (_rank, fb_label, fb_subtitle) in sorted(
        _TREE_FALLBACK.items(), key=lambda kv: kv[1][0]
    ):
        path = city.dir / fn
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                tree_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        label = tree_data.get("display_name") or fb_label
        subtitle = tree_data.get("display_subtitle") or fb_subtitle
        node_count = len(tree_data.get("nodes", {}))
        out.append(Story(
            id=fn.replace(".json", ""),
            label=label,
            subtitle=f"{subtitle} · {node_count} 节点",
            playable=True,
            tree_path=path,
            tree=tree_data,
        ))
    return out


def list_characters(story: Story, save_manager: Optional[SaveManager] = None) -> List[CharacterEntry]:
    """列出某剧本可选角色 — 用 SaveManager 判断锁定。

    如果 tree.json 没定义 characters,fallback 到 CHARACTER_ROSTER 全集。
    若有 characters,只列出 tree.json 中定义的(交集)。
    save_manager 为 None 时只按 roster 的 default_unlocked 展示,不触碰真实存档。
    """
    tree_chars = story.tree.get("characters") or {}
    if tree_chars:
        # tree.json 中定义的角色 — 与 roster 交叉
        out: List[CharacterEntry] = []
        for cid in tree_chars:
            info = get_character_info(cid) or {}
            label = info.get("label", tree_chars[cid].get("label", cid))
            year = int(info.get("year", 0) or 0)
            subtitle = info.get("subtitle", tree_chars[cid].get("subtitle", ""))
            unlocked = bool(info.get("default_unlocked", False))
            if save_manager is not None:
                unlocked = save_manager.is_unlocked(cid) or unlocked
            hint = info.get("unlock_hint", "")
            out.append(CharacterEntry(
                id=cid, label=label, year=year, subtitle=subtitle,
                unlocked=unlocked, unlock_hint=hint,
            ))
        # 加上 roster 中其他角色(未在 tree 中实现 → 显示锁定 + 待开发)
        defined = set(tree_chars.keys())
        for c in CHARACTER_ROSTER:
            if c["id"] in defined:
                continue
            unlocked = save_manager.is_unlocked(c["id"]) if save_manager else False
            hint = c.get("unlock_hint", "")
            if unlocked:
                hint = "已解锁,但本剧本暂无该角色线 — 待开发"
            out.append(CharacterEntry(
                id=c["id"],
                label=c["label"],
                year=int(c.get("year", 0) or 0),
                subtitle=c["subtitle"] + "  · 待开发",
                unlocked=False,  # 锁住,即便 SaveManager 解锁了也不可玩
                unlock_hint=hint,
            ))
        return out
    # 无 characters → roster 全集
    out = []
    for c in CHARACTER_ROSTER:
        unlocked = bool(c.get("default_unlocked", False))
        if save_manager is not None:
            unlocked = save_manager.is_unlocked(c["id"]) or unlocked
        out.append(CharacterEntry(
            id=c["id"],
            label=c["label"],
            year=int(c.get("year", 0) or 0),
            subtitle=c["subtitle"],
            unlocked=unlocked,
            unlock_hint=c.get("unlock_hint", ""),
        ))
    return out
