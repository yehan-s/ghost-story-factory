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

    # 由 play() 在加载 tree 时注入(可选)。用于获得道具时显示说明。
    inv_descriptions: Dict[str, str] = {}

    def apply(self, effects: Optional[Dict[str, Any]]) -> List[str]:
        """应用 effects 字典,返回简短描述列表(供 UI 反馈)。"""
        notes: List[str] = []
        if not effects:
            return notes

        # 个人共鸣 / 全局共鸣 是隐藏效果,选择后不向用户反馈具体数值
        # 用户可在 s 键调出的完整状态里看到当前值
        if "PR" in effects:
            delta = int(effects["PR"])
            if delta:
                self.PR = max(0, min(100, self.PR + delta))
        if "GR" in effects:
            delta = int(effects["GR"])
            if delta:
                self.GR = max(0, min(100, self.GR + delta))
        if "shifts_completed" in effects:
            self.shifts_completed += int(effects["shifts_completed"])
            notes.append(f"已完成夜班 +{int(effects['shifts_completed'])}")
        if "shifts_skipped" in effects:
            self.shifts_skipped += int(effects["shifts_skipped"])
            notes.append(f"漏打卡 +{int(effects['shifts_skipped'])}")
        for item in effects.get("inv_add", []) or []:
            if item not in self.inv:
                self.inv.append(item)
                desc = self.inv_descriptions.get(item) if self.inv_descriptions else None
                if desc:
                    notes.append(f"获得「{item}」 — {desc}")
                else:
                    notes.append(f"获得「{item}」")
        for item in effects.get("inv_remove", []) or []:
            if item in self.inv:
                self.inv.remove(item)
                notes.append(f"失去「{item}」")
        for k, v in (effects.get("flags") or {}).items():
            self.flags[k] = bool(v)

        # v6 新增 effects 操作
        if "set_route" in effects:
            new_route = effects["set_route"]
            if new_route in ("investigator", "witness", "survivor"):
                self.route = new_route
                notes.append(f"路线确立:{new_route}")
        if "landmark_visited" in effects:
            lm = str(effects["landmark_visited"])
            if lm not in self.visited_landmarks:
                self.visited_landmarks.append(lm)
                # 首次踏入 S1-S6 自动累计夜班完成数(避免每个 fragment writer 都要手动 +1)
                if lm in ("S1", "S2", "S3", "S4", "S5", "S6"):
                    self.shifts_completed += 1
                notes.append(f"踏入 {lm}")
        if "landmark_skipped" in effects:
            lm = str(effects["landmark_skipped"])
            if lm not in self.skipped_landmarks:
                self.skipped_landmarks.append(lm)
                notes.append(f"绕开 {lm}")
        if "puzzle_add" in effects:
            piece = str(effects["puzzle_add"])
            if piece not in self.puzzle_pieces:
                self.puzzle_pieces.append(piece)
                notes.append(f"拼图碎片 +1 ({len(self.puzzle_pieces)}/5)")

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
    """逐字打印,营造紧张感。环境变量 GHOST_FAST=1 关闭。"""
    if os.environ.get("GHOST_FAST"):
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        if ch in "。！？\n":
            time.sleep(delay * 8)
        elif ch in ",，、；:：":
            time.sleep(delay * 3)
        else:
            time.sleep(delay)
    sys.stdout.write("\n")


def render_narrative(text: str) -> None:
    print()
    for line in text.strip().split("\n"):
        slow_print(line)
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


def prompt_choice(n: int) -> int:
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
            print(dim("  q 退出  s 状态  其它输入数字选择"))
            continue
        if raw.lower() in ("s", "status"):
            return -1
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= n:
                return idx - 1
        print(red(f"  请输入 1-{n}。"))


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
        # 伏笔自动跟踪:节点上的 _foreshadow_slot 被触发即标记为 seen
        slot_ids = node.get("_foreshadow_slot") or []
        for slot in slot_ids:
            save_manager.mark_foreshadow_seen(story_id, slot)
        narrative = resolve_narrative(node, state)
        if narrative:
            render_narrative(narrative)

        # 结局节点
        if node.get("is_ending"):
            ending_type = node.get("ending_type", "E_UNKNOWN")
            ending_name = tree.get("endings", {}).get(ending_type, ending_type)
            print(bold(magenta("\n" + "─" * 60)))
            print(bold(magenta(f"  【结局 · {ending_type}】 {ending_name}")))
            print(bold(magenta("─" * 60)))
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
                print()
            except Exception as e:  # 存档失败不阻塞流程
                print(dim(f"  [存档警告] {e}"))
            return

        # 选项分类:visible(可选) / locked(显示但禁用) / hidden(完全隐藏)
        all_choices: List[Dict[str, Any]] = node.get("choices", []) or []
        visible: List[Dict[str, Any]] = []
        locked: List[tuple] = []
        for c in all_choices:
            status, hint = state.get_choice_status(c)
            if status == "visible":
                visible.append(c)
            elif status == "locked":
                locked.append((c, hint))
            # hidden: 完全跳过

        if not visible:
            print(red("[警告] 此节点没有可点击选项,故事中断。检查 tree.json。"))
            return

        # 显示状态(在选项前给一个简短 HUD,不每节点都给)
        if node.get("show_hud", True):
            print(state.hud())

        render_choices(visible, locked)
        idx = prompt_choice(len(visible))
        if idx == -1:
            # s 键 → 显示完整状态(包含个人共鸣 / 全局共鸣 + 伏笔档案)
            print(state.full_status())
            # 伏笔档案
            foreshadows = tree.get("foreshadows", {}) or {}
            if foreshadows:
                seen_list = save_manager.data.get("foreshadows_seen", {}).get(story_id, [])
                resolved_set = set(save_manager.data.get("foreshadows_resolved", {}).get(story_id, []))
                if seen_list:
                    print(bold(cyan(f"  ── 档案(已发现 {len(seen_list)}/{len(foreshadows)} · 已解 {len(resolved_set)}/{len(foreshadows)})──")))
                    for slot in seen_list:
                        meta = foreshadows.get(slot, {})
                        title = meta.get("title", slot)
                        if slot in resolved_set:
                            summary = meta.get("summary_resolved", "")
                            print(f"  {green('✦')} {bold(title)}")
                            if summary:
                                print(f"    {dim(summary)}")
                        else:
                            summary = meta.get("summary_locked", "")
                            print(f"  {dim('?')} {dim(title)}")
                            if summary:
                                print(f"    {dim(summary)}")
                else:
                    print(dim(f"  档案:0/{len(foreshadows)} · 还没发现任何伏笔"))
            continue

        chosen = visible[idx]
        # 选项上若挂了 _foreshadow_slot,选了之后也算 seen
        for slot in chosen.get("_foreshadow_slot") or []:
            save_manager.mark_foreshadow_seen(story_id, slot)
        notes = state.apply(chosen.get("effects"))
        # 只显示非隐藏的反馈(获得物品 / 踏入地标 / 漏卡 / 拼图碎片)
        # 个人共鸣 / 全局共鸣 已在 apply 内部静默处理
        if notes:
            print(dim("  · " + " · ".join(notes)))

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
