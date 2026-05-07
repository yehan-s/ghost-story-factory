"""极简对话树播放器(v6 图结构兼容版)。

设计:
- 加载手写的 tree.json 内容资产(v5 / v6 schema 均支持)
- 维护状态(PR / GR / inv / 计数器 / route / landmarks / puzzle)
- 渲染当前节点(支持 narrative_variants) + 过滤选项(嵌套 require) + 接受输入 + 跳转(支持 next_variants)
- 不调 LLM,不做去重,不做 BFS,数据天然不循环

向后兼容:
- 不带 narrative_variants / next_variants / 嵌套 require 的 v5 tree 必须仍能跑
- 新字段 (route / skipped_landmarks / visited_landmarks / puzzle_pieces) 在 initial_state 中允许缺失
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


# --- 终端样式(标准库 only,不依赖 rich) ---

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


_COLOR = _supports_color()


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def dim(s: str) -> str:
    return _c("2", s)


def bold(s: str) -> str:
    return _c("1", s)


def red(s: str) -> str:
    return _c("31", s)


def green(s: str) -> str:
    return _c("32", s)


def yellow(s: str) -> str:
    return _c("33", s)


def blue(s: str) -> str:
    return _c("34", s)


def magenta(s: str) -> str:
    return _c("35", s)


def cyan(s: str) -> str:
    return _c("36", s)


# --- 状态 ---

class State:
    """游戏状态。dict-backed,便于 JSON 中 effects 直接操作。"""

    def __init__(self, initial: Dict[str, Any]):
        self.PR: int = int(initial.get("PR", 0))
        self.GR: int = int(initial.get("GR", 0))
        self.shifts_completed: int = int(initial.get("shifts_completed", 0))
        self.shifts_skipped: int = int(initial.get("shifts_skipped", 0))
        self.inv: List[str] = list(initial.get("inv", []))
        self.flags: Dict[str, bool] = dict(initial.get("flags", {}))
        # v6 新增字段(允许缺失,默认空/None)
        self.route: Optional[str] = initial.get("route", None)
        self.skipped_landmarks: List[str] = list(initial.get("skipped_landmarks", []))
        self.visited_landmarks: List[str] = list(initial.get("visited_landmarks", []))
        self.puzzle_pieces: List[str] = list(initial.get("puzzle_pieces", []))
        # v7 多角色伏笔基础设施(默认值不破坏 v6/v7 现有玩法)
        self.character: str = str(initial.get("character", "G-273"))
        self.meta_flags: Dict[str, bool] = dict(initial.get("meta_flags", {}))
        # v7+ 自由移动 / NPC 位置 / 访问计数(默认空)
        self.last_landmark_id: Optional[str] = initial.get("last_landmark_id")
        self.npc_locations: Dict[str, str] = dict(initial.get("npc_locations", {}))
        self.visit_counts: Dict[str, int] = dict(initial.get("visit_counts", {}))
        # 已"知道"的地标(地图上可见;不等于"已访问")
        # 起手只知道 S1(队长简报告诉了第一站)
        self.known_landmarks: List[str] = list(initial.get("known_landmarks", ["S1"]))
        # PR 峰值(给"完全共鸣"成就用 — apply 里更新)
        self.PR_peak: int = int(initial.get("PR_peak", self.PR))
        # apply() 的结构化事件记录(给 UI 卡片化渲染用)
        self._last_events: List[Dict[str, Any]] = []

    # 由 play() 在加载 tree 时注入(可选)。用于获得道具时显示说明。
    inv_descriptions: Dict[str, str] = {}

    def apply(self, effects: Optional[Dict[str, Any]]) -> List[str]:
        """应用 effects 字典,返回简短描述列表(供 UI 反馈,向后兼容)。

        副作用:同时把结构化事件写入 self._last_events,供 UI 卡片化渲染。
        """
        notes: List[str] = []
        events: List[Dict[str, Any]] = []
        if not effects:
            self._last_events = events
            return notes

        # 个人共鸣 / 全局共鸣 是隐藏效果,不向用户反馈数值
        if "PR" in effects:
            delta = int(effects["PR"])
            if delta:
                self.PR = max(0, min(100, self.PR + delta))
                if self.PR > self.PR_peak:
                    self.PR_peak = self.PR
        if "GR" in effects:
            delta = int(effects["GR"])
            if delta:
                self.GR = max(0, min(100, self.GR + delta))
        if "shifts_completed" in effects:
            d = int(effects["shifts_completed"])
            self.shifts_completed += d
            notes.append(f"已完成夜班 +{d}")
            events.append({"type": "shifts_completed", "delta": d,
                           "current": self.shifts_completed})
        if "shifts_skipped" in effects:
            d = int(effects["shifts_skipped"])
            self.shifts_skipped += d
            notes.append(f"漏打卡 +{d}")
            events.append({"type": "shifts_skipped", "delta": d,
                           "current": self.shifts_skipped})
        for item in effects.get("inv_add", []) or []:
            if item not in self.inv:
                self.inv.append(item)
                desc = self.inv_descriptions.get(item) if self.inv_descriptions else None
                if desc:
                    notes.append(f"获得「{item}」 — {desc}")
                else:
                    notes.append(f"获得「{item}」")
                events.append({"type": "inv_add", "key": item, "desc": desc or ""})
        for item in effects.get("inv_remove", []) or []:
            if item in self.inv:
                self.inv.remove(item)
                notes.append(f"失去「{item}」")
                events.append({"type": "inv_remove", "key": item})
        for k, v in (effects.get("flags") or {}).items():
            self.flags[k] = bool(v)

        # v6 新增 effects
        if "set_route" in effects:
            new_route = effects["set_route"]
            if new_route in ("investigator", "witness", "survivor"):
                self.route = new_route
                notes.append(f"路线确立:{new_route}")
        if "landmark_visited" in effects:
            lm = str(effects["landmark_visited"])
            # 记录"刚刚去过哪"用于自由移动 — 即便重复访问也更新
            self.last_landmark_id = lm
            if lm not in self.visited_landmarks:
                self.visited_landmarks.append(lm)
                if lm in ("S1", "S2", "S3", "S4", "S5", "S6"):
                    self.shifts_completed += 1
                    events.append({"type": "shifts_completed", "delta": 1,
                                   "current": self.shifts_completed,
                                   "implicit": True})  # 由 landmark_visited 隐含触发
                notes.append(f"踏入 {lm}")
                events.append({"type": "landmark_visited", "key": lm})
        # NPC 移动:effects.npc_move = {"npc_id": "S2", ...}
        for npc_id, target in (effects.get("npc_move") or {}).items():
            self.npc_locations[npc_id] = str(target)
            events.append({"type": "npc_move", "key": npc_id, "to": str(target)})
        if "landmark_skipped" in effects:
            lm = str(effects["landmark_skipped"])
            if lm not in self.skipped_landmarks:
                self.skipped_landmarks.append(lm)
                notes.append(f"绕开 {lm}")
                events.append({"type": "landmark_skipped", "key": lm})
        if "puzzle_add" in effects:
            piece = str(effects["puzzle_add"])
            if piece not in self.puzzle_pieces:
                self.puzzle_pieces.append(piece)
                notes.append(f"拼图碎片 +1 ({len(self.puzzle_pieces)}/5)")
                events.append({"type": "puzzle_add", "key": piece,
                               "current": len(self.puzzle_pieces), "total": 5})

        self._last_events = events
        return notes

    def _meets_clause(self, require: Optional[Dict[str, Any]]) -> bool:
        """检查单一 require 子句的所有原子条件(AND 关系)。
        不递归处理 any_of/all_of/not。
        """
        if not require:
            return True
        if "PR_min" in require and self.PR < int(require["PR_min"]):
            return False
        if "PR_max" in require and self.PR > int(require["PR_max"]):
            return False
        if "GR_min" in require and self.GR < int(require["GR_min"]):
            return False
        if "GR_max" in require and self.GR > int(require["GR_max"]):
            return False
        for item in require.get("inv_has", []) or []:
            if item not in self.inv:
                return False
        for item in require.get("inv_lacks", []) or []:
            if item in self.inv:
                return False
        for k, v in (require.get("flags") or {}).items():
            if bool(self.flags.get(k, False)) != bool(v):
                return False
        if "shifts_skipped_min" in require and self.shifts_skipped < int(require["shifts_skipped_min"]):
            return False
        if "shifts_completed_min" in require and self.shifts_completed < int(require["shifts_completed_min"]):
            return False
        # v6 新增检查
        if "route_is" in require and self.route != require["route_is"]:
            return False
        for lm in require.get("landmark_visited", []) or []:
            if lm not in self.visited_landmarks:
                return False
        if "puzzle_pieces_min" in require and len(self.puzzle_pieces) < int(require["puzzle_pieces_min"]):
            return False
        # v7+ NPC 访问计数 / 当前位置(给重访 narrative_variants 用)
        for node_id, n in (require.get("visit_count_min") or {}).items():
            if self.visit_counts.get(node_id, 0) < int(n):
                return False
        if "last_landmark" in require:
            expected = require["last_landmark"]
            if isinstance(expected, str):
                if self.last_landmark_id != expected:
                    return False
            elif isinstance(expected, list):
                if self.last_landmark_id not in expected:
                    return False
        # v7 多角色 / 跨周目检查
        if "character" in require:
            expected = require["character"]
            if isinstance(expected, str):
                if self.character != expected:
                    return False
            elif isinstance(expected, list):
                if self.character not in expected:
                    return False
        for k, v in (require.get("meta_flags") or {}).items():
            if bool(self.meta_flags.get(k, False)) != bool(v):
                return False
        return True

    def meets(self, require: Optional[Dict[str, Any]]) -> bool:
        """检查 require 条件是否满足(支持嵌套 any_of/all_of/not 组合)。

        组合优先级: 顶层各项是 AND 关系。
        - 顶层原子键(PR_min/inv_has/flags 等) → AND
        - any_of: [子句, ...] → OR(任一子句满足即可)
        - all_of: [子句, ...] → AND(所有子句必须满足)
        - not: 子句 → NOT(子句必须不满足)

        子句本身递归遵循同样规则(支持嵌套)。
        """
        if not require:
            return True
        # 1. 原子条件(AND-only)
        if not self._meets_clause(require):
            return False
        # 2. any_of: OR
        if "any_of" in require:
            sub = require["any_of"] or []
            if sub and not any(self.meets(c) for c in sub):
                return False
        # 3. all_of: 显式 AND
        if "all_of" in require:
            sub = require["all_of"] or []
            if not all(self.meets(c) for c in sub):
                return False
        # 4. not: NOT
        if "not" in require:
            if self.meets(require["not"]):
                return False
        return True

    # --- 选项可见性分类(visible / locked / hidden) ---

    # 哪些 require 字段是"玩家可知"的(缺失时显示锁定提示),哪些是 spoiler(隐藏)
    _SPOILER_KEYS = (
        "PR_min", "PR_max", "GR_min", "GR_max",
        "flags", "shifts_completed_min", "shifts_skipped_min",
        "landmark_visited", "route_is", "character", "meta_flags", "not",
    )

    def _missing_visible_part(self, req: Optional[Dict[str, Any]]) -> Optional[str]:
        """返回缺失的『玩家可知道具/拼图』提示。None 表示这部分都满足。"""
        if not isinstance(req, dict):
            return None
        parts: List[str] = []
        for it in req.get("inv_has", []) or []:
            if it not in self.inv:
                parts.append(f"「{it}」")
        for it in req.get("inv_lacks", []) or []:
            if it in self.inv:
                parts.append(f"先丢掉「{it}」")
        if "puzzle_pieces_min" in req:
            need = int(req["puzzle_pieces_min"])
            if len(self.puzzle_pieces) < need:
                parts.append(f"拼图 ≥{need}/5")
        # 递归 all_of(收集所有缺失项)
        for sub in req.get("all_of", []) or []:
            sub_msg = self._missing_visible_part(sub)
            if sub_msg:
                # 去掉前缀 "需要 " 避免重复
                parts.append(sub_msg.replace("需要 ", "", 1))
        if not parts:
            return None
        return "需要 " + " + ".join(parts)

    def _meets_spoiler_part(self, req: Optional[Dict[str, Any]]) -> bool:
        """检查 require 里所有 spoiler 类条件是否满足(忽略 inv/puzzle)。"""
        if not isinstance(req, dict):
            return True
        if "PR_min" in req and self.PR < int(req["PR_min"]): return False
        if "PR_max" in req and self.PR > int(req["PR_max"]): return False
        if "GR_min" in req and self.GR < int(req["GR_min"]): return False
        if "GR_max" in req and self.GR > int(req["GR_max"]): return False
        if "shifts_completed_min" in req and self.shifts_completed < int(req["shifts_completed_min"]):
            return False
        if "shifts_skipped_min" in req and self.shifts_skipped < int(req["shifts_skipped_min"]):
            return False
        for k, v in (req.get("flags") or {}).items():
            if bool(self.flags.get(k, False)) != bool(v): return False
        for lm in req.get("landmark_visited", []) or []:
            if lm not in self.visited_landmarks: return False
        if "route_is" in req and self.route != req["route_is"]: return False
        if "character" in req:
            expected = req["character"]
            if isinstance(expected, str) and self.character != expected: return False
            if isinstance(expected, list) and self.character not in expected: return False
        for k, v in (req.get("meta_flags") or {}).items():
            if bool(self.meta_flags.get(k, False)) != bool(v): return False
        if "not" in req:
            if self.meets(req["not"]): return False
        # any_of:任一子句的 spoiler+visible 整体满足即可
        if "any_of" in req:
            sub = req["any_of"] or []
            if sub and not any(self.meets(c) for c in sub):
                return False
        if "all_of" in req:
            for c in req["all_of"] or []:
                if not self._meets_spoiler_part(c):
                    return False
        return True

    def get_choice_status(self, choice: Dict[str, Any]) -> tuple:
        """返回 (status, hint):
        - ('visible', None) 可选
        - ('locked', '需要「X」') 显示但锁定
        - ('hidden', None) 完全隐藏
        """
        require = choice.get("require")
        if not require:
            return ("visible", None)
        if self.meets(require):
            return ("visible", None)
        # 不满足:看是不是仅因 inv/puzzle 缺失(玩家可知)
        spoiler_ok = self._meets_spoiler_part(require)
        missing = self._missing_visible_part(require)
        if spoiler_ok and missing:
            return ("locked", missing)
        return ("hidden", None)

    def hud(self) -> str:
        """常驻顶部状态条 — 不含隐藏效果(个人共鸣 / 全局共鸣)。"""
        inv_str = "·".join(self.inv) if self.inv else "—"
        route_str = ""
        if self.route:
            route_label = {
                "investigator": "调查派",
                "witness": "围观派",
                "survivor": "逃避派",
            }.get(self.route, self.route)
            route_str = f"  {blue('路线')} {route_label}"
        puzzle_str = ""
        if self.puzzle_pieces:
            puzzle_str = f"  {green('拼图')} {len(self.puzzle_pieces)}/5"
        return (
            f"{dim('━' * 60)}\n"
            f"{yellow('夜班')} {self.shifts_completed}/7  "
            f"{red('漏卡')} {self.shifts_skipped}"
            f"{route_str}{puzzle_str}\n"
            f"{dim('随身:')} {inv_str}\n"
            f"{dim('━' * 60)}"
        )

    def full_status(self) -> str:
        """完整状态(s 键调出) — 包含个人共鸣 / 全局共鸣。"""
        inv_str = "·".join(self.inv) if self.inv else "—"
        route_str = ""
        if self.route:
            route_label = {
                "investigator": "调查派",
                "witness": "围观派",
                "survivor": "逃避派",
            }.get(self.route, self.route)
            route_str = f"  {blue('路线')} {route_label}"
        puzzle_str = ""
        if self.puzzle_pieces:
            puzzle_str = f"  {green('拼图')} {len(self.puzzle_pieces)}/5"
        # 用 100 分制 + 中文名,而不是 PR/GR 缩写
        return (
            f"{dim('━' * 60)}\n"
            f"{cyan('个人共鸣')} {self.PR:3d}/100   "
            f"{magenta('全局共鸣')} {self.GR:3d}/100\n"
            f"{dim('  · 个人共鸣 = 你被这个夜班影响的程度。越高越接近精神边缘 / 触发心境分支。')}\n"
            f"{dim('  · 全局共鸣 = 杭州常数对你的注视程度。越高越被异常实体盯上 / 触发实体出现。')}\n"
            f"{yellow('夜班')} {self.shifts_completed}/7  "
            f"{red('漏卡')} {self.shifts_skipped}"
            f"{route_str}{puzzle_str}\n"
            f"{dim('随身:')} {inv_str}\n"
            f"{dim('━' * 60)}"
        )


# --- 渲染 ---

def slow_print(text: str, delay: float = 0.012) -> None:
    """逐字打印,营造紧张感。环境变量 GHOST_FAST=1 关闭。

    ANSI 转义序列整段一次输出,不计时,避免色彩切换打断节奏。
    """
    if os.environ.get("GHOST_FAST"):
        print(text)
        return
    parts = re.split(r"(\x1b\[[0-9;]*m)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("\x1b["):
            sys.stdout.write(part)
            sys.stdout.flush()
            continue
        for ch in part:
            sys.stdout.write(ch)
            sys.stdout.flush()
            if ch in "。！？\n":
                time.sleep(delay * 8)
            elif ch in ",，、；:：":
                time.sleep(delay * 3)
            else:
                time.sleep(delay)
    sys.stdout.write("\n")


def _highlight_narrative(line: str) -> str:
    """给一行 narrative 加色彩层次。规则:
      - **xxx**           → 醒目黄(原文 markdown bold)
      - 「xxx」/『xxx』   → NPC 对话/物件名,cyan
      - 4 位数年份(1985)→ 暗红
      - 时间(20:27)     → 黄
      - SID(S1-S7)       → magenta
    """
    import re

    def _yellow_bold(m): return bold(yellow(m.group(1)))
    def _cyan(m): return cyan(m.group(0))
    def _dim_red(m): return dim(red(m.group(0)))
    def _yellow(m): return yellow(m.group(0))
    def _magenta(m): return bold(magenta(m.group(0)))

    # 顺序:先做 **bold**(避免和 「」 冲突),再做 「」,再 SID,再时间/年份
    out = re.sub(r"\*\*([^*]+?)\*\*", _yellow_bold, line)
    out = re.sub(r"「[^」]+」|『[^』]+』", _cyan, out)
    # SID:S 后接单数字,前后是非字母数字
    out = re.sub(r"(?<![A-Za-z0-9])S[1-7](?![A-Za-z0-9])", _magenta, out)
    # 时间 HH:MM
    out = re.sub(r"\b\d{1,2}:\d{2}\b", _yellow, out)
    # 年份 4 位 19xx/20xx(不在更长数字里)
    out = re.sub(r"(?<!\d)(?:19|20)\d{2}(?!\d)", _dim_red, out)
    return out


def render_narrative(text: str) -> None:
    print()
    for line in text.strip().split("\n"):
        slow_print(_highlight_narrative(line))
    print()


def render_choices(visible: List[Dict[str, Any]],
                   locked: List[tuple] = None) -> None:
    """渲染选项。
    - visible: 可点击,有编号 1..N
    - locked: 显示但禁用,带 🔒 + 缺失道具提示,无编号
    """
    print()
    for i, ch in enumerate(visible, start=1):
        label = ch.get("text", "(无文本)")
        print(f"  {green(str(i))}. {label}")
    if locked:
        for ch, hint in locked:
            label = ch.get("text", "(无文本)")
            print(f"  {dim(red('🔒') + ' ' + label + '  — ' + hint)}")
    print()


# 特殊返回值(prompt_choice 用)
ACTION_STATUS = -1  # 's' 键
ACTION_MAP = -2     # 'm' 键


def prompt_choice(n: int, aliases: Optional[Dict[str, int]] = None) -> int:
    """返回 0-based 选项索引,或 ACTION_* 特殊值。

    aliases: 可选 — {别名: 0-based 索引}。例如 picker 传入 {"S1": 0, "S2": 1, ...},
             玩家可以直接输入 "S1" 而不用看下面是几号。
    """
    aliases_lc = {k.lower(): v for k, v in (aliases or {}).items()}
    while True:
        try:
            raw = input(bold("> 你的选择: ")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + red("中断。"))
            sys.exit(0)
        if raw.lower() in ("q", "quit", "exit"):
            print(dim("退出。"))
            sys.exit(0)
        if raw.lower() in ("h", "help", "?"):
            print(dim("  q 退出  s 状态  m 地图  其它输入数字 / SID(如 S1/S2)选择"))
            continue
        if raw.lower() in ("s", "status"):
            return ACTION_STATUS
        if raw.lower() in ("m", "map", "地图"):
            return ACTION_MAP
        # SID 别名(picker 用)
        if raw.lower() in aliases_lc:
            idx = aliases_lc[raw.lower()]
            if 0 <= idx < n:
                return idx
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= n:
                return idx - 1
        hint = f"  请输入 1-{n}"
        if aliases_lc:
            hint += " 或 " + " / ".join(sorted(aliases.keys()))
        hint += "。"
        print(red(hint))


# --- v6 schema 解析辅助 ---

def resolve_narrative(node: Dict[str, Any], state: State) -> str:
    """解析节点的 narrative。优先按 narrative_variants 顺序匹配,fallback 到 narrative。"""
    variants = node.get("narrative_variants") or []
    for v in variants:
        cond = v.get("if") or {}
        if state.meets(cond):
            return v.get("text", "")
    return node.get("narrative", "")


def resolve_next(chosen: Dict[str, Any], state: State) -> Optional[str]:
    """解析选项的 next 节点。优先按 next_variants 顺序匹配,fallback 到 next。"""
    variants = chosen.get("next_variants") or []
    for v in variants:
        cond = v.get("if") or {}
        if state.meets(cond):
            nxt = v.get("next")
            if nxt:
                return nxt
    return chosen.get("next")


# --- 渲染状态变化事件 ---

def _render_apply_events(events: List[Dict[str, Any]], important_items: set) -> None:
    """根据 state.apply 产出的 events,卡片化渲染各类状态变化。"""
    if not events:
        return
    from ghost_story_factory.v7.animate import card, flash_line  # 局部导入避免循环
    print()  # 与上方 narrative 分开
    for ev in events:
        t = ev.get("type")
        if t == "inv_add":
            key = ev["key"]
            desc = ev.get("desc", "")
            if key in important_items:
                # 关键道具 → 边框卡片 + 用途说明
                card(f"拾起「{key}」", color_fn=lambda s: bold(green(s)))
                if desc:
                    print(f"     {dim(desc)}")
            else:
                # 装饰道具 → 一行 dim
                line = f"  · 获得「{key}」"
                if desc:
                    line += f" — {desc}"
                print(dim(line))
        elif t == "inv_remove":
            print(dim(f"  · 失去「{ev['key']}」"))
        elif t == "shifts_skipped":
            flash_line(f"漏卡 +{ev['delta']}", color_fn=lambda s: bold(red(s)))
        elif t == "shifts_completed" and not ev.get("implicit"):
            cur = ev.get("current", 0)
            flash_line(f"夜班 +{ev['delta']}  ({cur}/7)",
                       color_fn=lambda s: bold(green(s)))
        elif t == "puzzle_add":
            flash_line(f"拼图 +1  ({ev['current']}/{ev['total']})",
                       color_fn=lambda s: bold(cyan(s)))
        elif t == "landmark_visited":
            flash_line(f"踏入 {ev['key']}",
                       color_fn=lambda s: bold(green(s)))
        elif t == "landmark_skipped":
            flash_line(f"绕开 {ev['key']}",
                       color_fn=lambda s: bold(red(s)))
        elif t == "set_route":
            print(dim(f"  · 路线确立:{ev['key']}"))
    print()


# --- 关键道具集合(被 inv_has require 引用过的视为 important) ---

def collect_important_items(tree: Dict[str, Any]) -> set:
    """扫一遍 tree.json 所有 require.inv_has,返回被引用过的道具名集合。

    被引用 = 玩家拿到后影响后续选项可达 = 关键道具,值得卡片化反馈。
    没被引用 = 装饰性道具(只触发 narrative_variants 或 flag),正常 dim 显示。
    """
    important: set = set()

    def _scan_require(req):
        if not isinstance(req, dict):
            return
        for it in req.get("inv_has", []) or []:
            important.add(it)
        for sub in req.get("any_of", []) or []:
            _scan_require(sub)
        for sub in req.get("all_of", []) or []:
            _scan_require(sub)
        if "not" in req:
            _scan_require(req["not"])

    for node in (tree.get("nodes") or {}).values():
        for choice in node.get("choices") or []:
            _scan_require(choice.get("require"))
            for v in choice.get("next_variants") or []:
                _scan_require(v.get("if"))
        for v in node.get("narrative_variants") or []:
            _scan_require(v.get("if"))
    return important


# --- 结局色调映射 ---

# 8 主结局 + 9 mini-ending 各按"基调"染色,玩家通关瞬间能"读出"是哪种结局
_ENDING_COLORS = {
    "E_TRUE": green,           # 关闭杭州常数 — 光明
    "E_HIDDEN": yellow,        # 重投胎 — 隐秘
    "E_TRUTH": cyan,           # 揭穿真相
    "E_DATA": magenta,         # 数据化雪花
    "E_BROADCAST": blue,       # 永生论坛 — 赛博
    "E_BAD_DROWN": red,        # 沉船替死
    "E_BAD_1987": red,         # 无尽 1987
    "E_NEUTRAL": dim,          # 平淡 fallback
}


def ending_color(ending_type: str):
    """按 ending_type 取色函数。未知 → magenta(向后兼容)。"""
    return _ENDING_COLORS.get(ending_type, magenta)


# --- 主循环 ---

def _select_character(characters: Dict[str, Any]) -> Optional[str]:
    """v7 多角色伏笔接口:列出可玩角色,返回 character_id。

    若只有 1 个或 0 个角色,直接返回默认值。
    若 > 1,提示用户选择(v8 扩展点)。
    """
    if not characters:
        return None
    keys = list(characters.keys())
    if len(keys) == 1:
        return keys[0]
    print(bold(magenta("\n  可玩角色:")))
    for i, k in enumerate(keys, start=1):
        label = characters[k].get("label", k)
        print(f"  {green(str(i))}. {label}")
    print()
    while True:
        try:
            raw = input(bold("> 选择角色 (默认 1): ")).strip()
        except (EOFError, KeyboardInterrupt):
            return keys[0]
        if not raw:
            return keys[0]
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            return keys[int(raw) - 1]
        print(red(f"  请输入 1-{len(keys)}。"))


def play(tree_path: Path, character_id: Optional[str] = None) -> None:
    """加载并播放一棵对话树。

    Args:
        tree_path: tree.json 路径
        character_id: 指定角色 ID(若主菜单已选过,跳过角色选择)
    """
    with tree_path.open("r", encoding="utf-8") as f:
        tree = json.load(f)

    title = tree.get("title", "(无题)")
    protagonist = tree.get("protagonist", "(无名)")
    nodes: Dict[str, Dict[str, Any]] = tree["nodes"]

    # v7 多角色伏笔接口(向后兼容:characters 缺失时走默认 G-273 流程)
    initial_state = dict(tree.get("initial_state", {}))
    characters = tree.get("characters") or {}

    # 跨周目存档(SaveManager)
    from ghost_story_factory.v7.save_manager import SaveManager  # 局部导入避免循环
    save_manager = SaveManager()

    # 角色选择:外部传入 > 交互选择 > 默认(单角色或 None)
    if character_id and character_id in characters:
        selected_character = character_id
    else:
        selected_character = _select_character(characters)

    if selected_character and selected_character in characters:
        cdef = characters[selected_character]
        initial_state["character"] = selected_character
        if cdef.get("initial_inv"):
            initial_state["inv"] = list(cdef["initial_inv"])
        if cdef.get("initial_flags"):
            initial_state["flags"] = dict(cdef["initial_flags"])
        # 跨周目记忆:meta_flags 从存档注入
        initial_state["meta_flags"] = dict(save_manager.meta_flags)

    state = State(initial_state)
    # 注入道具说明字典(获得物品时显示用途)
    State.inv_descriptions = tree.get("inv_descriptions", {}) or {}

    story_id = str(tree.get("story_id") or tree_path.stem)
    # 关键道具集合(被 inv_has 引用的视为剧情关键 → 卡片化反馈)
    important_items = collect_important_items(tree)

    print(bold(red("\n" + "═" * 60)))
    print(bold(red(f"   {title}")))
    print(dim(f"   主角: {protagonist}"))
    print(bold(red("═" * 60)))
    print(dim("\n  操作: 输入数字选择, q 退出, s 查看状态, h 帮助\n"))

    # v7 角色起点覆盖(向后兼容:character 没定义 start_node 时使用 tree.start_node)
    current_id = tree.get("start_node", "n_intro")
    if selected_character and selected_character in characters:
        current_id = characters[selected_character].get("start_node", current_id)
    visited: List[str] = []

    while True:
        node = nodes.get(current_id)
        if node is None:
            print(red(f"\n[错误] 节点 {current_id} 不存在,故事中断。"))
            return

        visited.append(current_id)
        # 累计节点访问次数(给 NPC 重访 narrative_variants 用)
        state.visit_counts[current_id] = state.visit_counts.get(current_id, 0) + 1
        # 地标入场 banner — 节点带 _landmark_header 时显示翻页过场
        header = node.get("_landmark_header")
        if header and isinstance(header, dict):
            from ghost_story_factory.v7.animate import (
                fade_lines, pause as _pause, draw_line_progressive,
            )
            t = header.get("time", "")
            p = header.get("place", "")
            print()
            draw_line_progressive(56, char="▔", color_fn=lambda s: dim(red(s)),
                                  char_delay=0.012)
            _pause(0.15)
            fade_lines(
                ["", f"          {bold(yellow(t))}", f"      {bold(red(p))}", ""],
                line_delay=0.12,
            )
            draw_line_progressive(56, char="▁", color_fn=lambda s: dim(red(s)),
                                  char_delay=0.012)
            _pause(0.3)
        # PR ≥ 50 时,在节点叙事前打一段心跳条(暗示焦虑)
        # 但在 picker / 工具节点不显示(避免太频繁)
        if (state.PR >= 50 and not node.get("_is_map_picker")
                and not node.get("_is_tool")):
            from ghost_story_factory.v7.animate import heartbeat_pulse
            heartbeat_pulse(color_fn=lambda s: bold(red(s)),
                            beats=1, period=0.5)
        # 伏笔自动跟踪:_foreshadow_slot 被触发即标记 seen,首次触发显示卡片
        slot_ids = node.get("_foreshadow_slot") or []
        newly_seen_slots: List[str] = []
        for slot in slot_ids:
            if save_manager.mark_foreshadow_seen(story_id, slot):
                newly_seen_slots.append(slot)
        # 伏笔碎片:_foreshadow_clue: [{slot, shard}] — 节点级触发拾取
        node_clues = node.get("_foreshadow_clue") or []
        newly_shard_events: List[Dict[str, Any]] = []  # {slot, shard, fully}
        for clue in node_clues:
            slot = clue.get("slot")
            shard = clue.get("shard")
            if not slot or not shard:
                continue
            newly, fully = save_manager.add_foreshadow_shard(
                tree, story_id, slot, shard
            )
            if newly:
                newly_shard_events.append({"slot": slot, "shard": shard,
                                           "fully": fully})
        # 推论检查 — 看是否有新推论被解锁
        newly_deductions = save_manager.check_deductions(tree, story_id)
        # 成就检查(每节点扫一次,on_ending 时另算)
        newly_achievements = save_manager.check_achievements(
            tree, state, story_id, on_ending=False
        )
        # _is_map_picker 节点:用地图视图替代普通 narrative
        # 先 build picker_choices 算出 travel_indices(让数字贴到地图上)
        if node.get("_is_map_picker"):
            from ghost_story_factory.v7.map_view import (
                render_map_cli, picker_choices
            )
            _picker_pre = picker_choices(tree, state)
            _visible_pre = [c for c in _picker_pre if c.get("_picker_kind") != "locked"]
            travel_idx = {}
            for i, c in enumerate(_visible_pre):
                if c.get("_picker_kind") == "travel":
                    sid = c.get("_landmark_id")
                    if sid:
                        travel_idx[sid] = i + 1
            render_map_cli(tree, state, save_manager,
                           current_node_id=current_id, story_id=story_id,
                           mode="site",
                           travel_indices=travel_idx)
        else:
            # _one_way 节点 — 用 glitch 闪一段红字"无回头路"
            if node.get("_one_way"):
                from ghost_story_factory.v7.animate import glitch_text
                hint = node.get("_one_way_hint",
                                "无回头路 — 你已经踏入此地。")
                print()
                glitch_text(f"  🔒 {hint}",
                            color_fn=lambda s: bold(red(s)),
                            frames=4, frame_delay=0.06,
                            glitch_ratio=0.25)
                print()
            narrative = resolve_narrative(node, state)
            if narrative:
                render_narrative(narrative)
        # 首次发现伏笔 — 用 glitch 闪一段青字(像系统弹窗 corruption 后定下来)
        if newly_seen_slots:
            from ghost_story_factory.v7.animate import glitch_text
            foreshadows = tree.get("foreshadows", {}) or {}
            for slot in newly_seen_slots:
                title = (foreshadows.get(slot) or {}).get("title", slot)
                glitch_text(f"  ▌ 档案 +1  ·  {title} ▐",
                            color_fn=lambda s: bold(cyan(s)),
                            frames=3, frame_delay=0.07,
                            glitch_ratio=0.2)
            print()
        # 拾到伏笔碎片(单条 = 蓝字短闪;集齐 = 黄字长 glitch 表"档案合卷")
        if newly_shard_events:
            from ghost_story_factory.v7.animate import glitch_text
            foreshadows = tree.get("foreshadows", {}) or {}
            for ev in newly_shard_events:
                slot = ev["slot"]
                meta = foreshadows.get(slot) or {}
                title = meta.get("title", slot)
                shards_total = len(meta.get("shards", []) or [])
                got = save_manager.get_shards_collected(story_id, slot)
                glitch_text(
                    f"  ▌ 碎片 +1  ·  {title} ({len(got)}/{shards_total}) ▐",
                    color_fn=lambda s: bold(blue(s)),
                    frames=2, frame_delay=0.06, glitch_ratio=0.15,
                )
                if ev["fully"]:
                    glitch_text(
                        f"  ✦ 档案合卷  ·  {title} ✦",
                        color_fn=lambda s: bold(yellow(s)),
                        frames=4, frame_delay=0.08, glitch_ratio=0.3,
                    )
            print()
        # 推论触发(合并伏笔)
        if newly_deductions:
            from ghost_story_factory.v7.animate import glitch_text
            deductions = tree.get("deductions", {}) or {}
            for ded_id in newly_deductions:
                meta = deductions.get(ded_id) or {}
                title = meta.get("title", ded_id)
                glitch_text(
                    f"  ⟁ 推论合成  ·  {title} ⟁",
                    color_fn=lambda s: bold(magenta(s)),
                    frames=5, frame_delay=0.08, glitch_ratio=0.35,
                )
            print()
        # 成就解锁(金色,庆祝感)
        if newly_achievements:
            from ghost_story_factory.v7.animate import glitch_text
            achievements = tree.get("achievements", {}) or {}
            for ach_id in newly_achievements:
                meta = achievements.get(ach_id) or {}
                icon = meta.get("icon", "🏆")
                name = meta.get("name", ach_id)
                desc = meta.get("description", "")
                glitch_text(
                    f"  {icon} 成就解锁  ·  {name}  {icon}",
                    color_fn=lambda s: bold(yellow(s)),
                    frames=4, frame_delay=0.08, glitch_ratio=0.3,
                )
                if desc:
                    print(f"    {dim(desc)}")
            print()

        # 结局节点
        if node.get("is_ending"):
            ending_type = node.get("ending_type", "E_UNKNOWN")
            ending_name = tree.get("endings", {}).get(ending_type, ending_type)
            ec = ending_color(ending_type)
            from ghost_story_factory.v7.animate import (
                draw_line_progressive, glitch_text,
            )
            print()
            draw_line_progressive(60, char="═", color_fn=lambda s: bold(ec(s)),
                                  char_delay=0.008)
            glitch_text(f"  【结局 · {ending_type}】 {ending_name}",
                        color_fn=lambda s: bold(ec(s)),
                        frames=5, frame_delay=0.07,
                        glitch_ratio=0.35)
            draw_line_progressive(60, char="═", color_fn=lambda s: bold(ec(s)),
                                  char_delay=0.008)
            print(state.hud())
            print(dim(f"\n  共经历 {len(visited)} 个节点。"))
            print(dim("  夜班没有尽头,只有下一班。\n"))
            # 写盘 + 显示解锁
            try:
                newly = save_manager.record_ending(ending_type, story_id=story_id)
                # 伏笔自动解开
                fs_resolved = save_manager.auto_resolve(
                    tree, ending_type, state.character, story_id
                )
                # 显示新解锁角色
                if newly:
                    from ghost_story_factory.v7.save_manager import get_character_info
                    print(bold(green("─" * 60)))
                    print(bold(green("  ★ 新角色解锁:")))
                    for cid in newly:
                        info = get_character_info(cid) or {}
                        label = info.get("label", cid)
                        year = info.get("year", "")
                        sub = info.get("subtitle", "")
                        print(f"    {green('●')} {bold(label)}  {dim(f'· {year} · {sub}')}")
                    print(bold(green("─" * 60)))
                    print(dim("  下次启动主菜单 → 选剧情 → 选角色,即可体验。"))
                # 显示新解开的伏笔
                if fs_resolved:
                    print(bold(cyan("─" * 60)))
                    print(bold(cyan("  ✦ 伏笔已解开:")))
                    foreshadows = tree.get("foreshadows", {}) or {}
                    for slot in fs_resolved:
                        meta = foreshadows.get(slot, {})
                        title = meta.get("title", slot)
                        summary = meta.get("summary_resolved", "")
                        print(f"    {cyan('●')} {bold(title)}")
                        if summary:
                            print(f"      {dim(summary)}")
                    seen, resolved, total = save_manager.foreshadow_progress(tree, story_id)
                    print(dim(f"  档案进度:已发现 {seen}/{total} · 已解开 {resolved}/{total}"))
                    print(bold(cyan("─" * 60)))
                # 通关时再扫一轮成就(on_ending 触发的项)
                ending_achievements = save_manager.check_achievements(
                    tree, state, story_id, on_ending=True
                )
                if ending_achievements:
                    print(bold(yellow("─" * 60)))
                    print(bold(yellow("  🏆 成就解锁:")))
                    achievements = tree.get("achievements", {}) or {}
                    for ach_id in ending_achievements:
                        meta = achievements.get(ach_id) or {}
                        icon = meta.get("icon", "🏆")
                        name = meta.get("name", ach_id)
                        desc = meta.get("description", "")
                        print(f"    {yellow(icon)} {bold(name)}")
                        if desc:
                            print(f"      {dim(desc)}")
                    print(bold(yellow("─" * 60)))
                print()
            except Exception as e:  # 存档失败不阻塞流程
                print(dim(f"  [存档警告] {e}"))
            return

        # 选项分类:visible(可选) / locked(显示但禁用) / hidden(完全隐藏)
        if node.get("_is_map_picker"):
            # 自由移动 picker:动态生成 travel + tool + endshift + locked 选项
            from ghost_story_factory.v7.map_view import picker_choices
            generated = picker_choices(tree, state)
            visible = [c for c in generated if c.get("_picker_kind") != "locked"]
            locked = [(c, c.get("text", "").split("(")[-1].rstrip(")"))
                      for c in generated if c.get("_picker_kind") == "locked"]
        else:
            all_choices: List[Dict[str, Any]] = node.get("choices", []) or []
            visible = []
            locked = []
            for c in all_choices:
                status, hint = state.get_choice_status(c)
                if status == "visible":
                    visible.append(c)
                elif status == "locked":
                    locked.append((c, hint))
                # hidden: 完全跳过
            # _scene_details: 场景细节"看一眼"选项 — stay-effect,不消耗回合
            for det in (node.get("_scene_details") or []):
                require = det.get("require")
                if require and not state.meets(require):
                    continue
                visible.append({
                    "text": f"  · 看一眼 {det.get('label', '场景细节')}",
                    "effects": {"stay": True, **(det.get("effects") or {})},
                    "_detail_text": det.get("text", ""),
                    "_picker_kind": "detail",
                    # 场景细节也可以挂碎片(看清楚才算拾到)
                    "_foreshadow_clue": det.get("_foreshadow_clue") or [],
                    "_foreshadow_slot": det.get("_foreshadow_slot") or [],
                })

        if not visible:
            print(red("[警告] 此节点没有可点击选项,故事中断。检查 tree.json。"))
            return

        # 显示状态(在选项前给一个简短 HUD,不每节点都给)
        if node.get("show_hud", True):
            print(state.hud())

        render_choices(visible, locked)
        # picker 模式下,把 SID 也注册为别名(玩家可以直接 S1/S2... 选)
        _aliases: Dict[str, int] = {}
        if node.get("_is_map_picker"):
            for i, c in enumerate(visible):
                sid = c.get("_landmark_id")
                if sid:
                    _aliases[sid] = i
        idx = prompt_choice(len(visible), aliases=_aliases or None)
        if idx == ACTION_MAP:
            # m 键 → 显示手机地图(phone 模式 — 只看路 + 地名,不剧透 NPC)
            from ghost_story_factory.v7.map_view import render_map_cli
            from ghost_story_factory.v7.animate import (
                fade_lines as _fade_lines, pause as _pause2,
            )
            # 首次开:加一段"掏出手机/打开 XX 地图"的叙事过门
            if not state.flags.get("phone_map_first_opened"):
                state.flags["phone_map_first_opened"] = True
                print()
                _fade_lines([
                    dim("  你停下来,从胸袋里摸出手机。"),
                    dim("  屏幕亮了 — 屏保是你和你媳妇 2023 年的合照。"),
                    dim("  你点开『杭州地铁夜班巡逻图』 — 队长发的内部 app。"),
                    dim("  地图加载,信号是『 4G · 弱』。"),
                    dim("  地图只画了你**已经知道**的几个点。其他位置,只有问号。"),
                ], line_delay=0.18)
                _pause2(0.3)
            if node.get("_one_way"):
                hint = node.get("_one_way_hint",
                                "你已经走进来了 — 这里没有回头路,只是看一眼地图。")
                print(red(f"\n  ▌ {hint} ▐\n"))
            render_map_cli(tree, state, save_manager,
                            current_node_id=current_id, story_id=story_id,
                            mode="phone")
            try:
                input(dim("  按 Enter 继续..."))
            except (EOFError, KeyboardInterrupt):
                pass
            continue
        if idx == ACTION_STATUS:
            # s 键 → 显示完整状态(包含个人共鸣 / 全局共鸣 + 档案 + 推论 + 时间轴)
            from ghost_story_factory.v7.archive_view import render_archive_cli
            print(state.full_status())
            render_archive_cli(tree, save_manager, story_id)
            continue

        chosen = visible[idx]
        # 选项上若挂了 _foreshadow_slot,选了之后也算 seen
        for slot in chosen.get("_foreshadow_slot") or []:
            save_manager.mark_foreshadow_seen(story_id, slot)
        # 选项级伏笔碎片
        for clue in chosen.get("_foreshadow_clue") or []:
            slot = clue.get("slot")
            shard = clue.get("shard")
            if slot and shard:
                save_manager.add_foreshadow_shard(tree, story_id, slot, shard)
        effects = chosen.get("effects") or {}
        state.apply(effects)
        # 渐进展开 known_landmarks(landmark_visited / reveal_landmarks 触发)
        from ghost_story_factory.v7.map_view import expand_known_landmarks
        newly_known = expand_known_landmarks(state, tree, effects)
        if newly_known:
            from ghost_story_factory.v7.animate import flash_line
            for sid in newly_known:
                lm = next((l for l in tree.get("landmark_map", []) if l.get("id") == sid), {})
                short = lm.get("short", sid)
                place = lm.get("place", "")
                flash_line(f"地图 +1  ·  {sid} {short} {place}",
                           color_fn=lambda s: bold(yellow(s)))
        # 卡片化渲染状态变化(根据 events 类型分别用 card / flash_line)
        _render_apply_events(state._last_events, important_items)
        # 工具节点 stay:不跳 next,留在当前节点(由"返回"选项触发)
        if effects.get("stay"):
            # 场景细节:渲染 _detail_text(用色彩层次)
            detail_text = chosen.get("_detail_text")
            if detail_text:
                print()
                print(dim("  ─── 看了一眼 ───"))
                for ln in detail_text.strip().split("\n"):
                    print(_highlight_narrative(ln) if ln.strip() else "")
                print(dim("  ─── 你收回视线 ───"))
                print()
            else:
                print(dim("\n  · 你停留片刻,然后回头。\n"))
            try:
                input(dim("  按 Enter 返回..."))
            except (EOFError, KeyboardInterrupt):
                pass
            continue

        nxt = resolve_next(chosen, state)
        if not nxt:
            print(red("[错误] 选项缺少 next/next_variants 字段。"))
            return
        current_id = nxt


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    if argv:
        path = Path(argv[0])
    else:
        # 默认故事
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / "stories" / "hangzhou_yebanbaoan" / "tree.json"
    if not path.exists():
        print(red(f"找不到对话树: {path}"))
        return 1
    play(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
