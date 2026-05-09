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
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ghost_story_factory.runtime.contracts import (
    EffectApplier,
    EndingResolver,
    RequirementEvaluator,
)


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

    def __init__(
        self,
        initial: Dict[str, Any],
        save_manager: Any = None,
        story_id: Optional[str] = None,
    ):
        self.PR: int = int(initial.get("PR", 0))
        self.GR: int = int(initial.get("GR", 0))
        self.shifts_skipped: int = int(initial.get("shifts_skipped", 0))
        self.inv: List[str] = list(initial.get("inv", []))
        self.flags: Dict[str, bool] = dict(initial.get("flags", {}))
        # v6 新增字段(允许缺失,默认空/None)
        self.skipped_landmarks: List[str] = list(initial.get("skipped_landmarks", []))
        self.visited_landmarks: List[str] = list(initial.get("visited_landmarks", []))
        self.puzzle_pieces: List[str] = list(initial.get("puzzle_pieces", []))
        # v7 多角色伏笔基础设施(默认值不破坏 v6/v7 现有玩法)
        self.character: str = str(initial.get("character", "G-273"))
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
        # 反应机制(ADR-008):跨周目持久化层引用(单一真相源 = save_manager),
        # 给 _meets_clause 的 deduction_resolved / foreshadow_resolved / theme_resolved 用。
        # 默认 None 时三个新条件安全降级返回 False,不破坏现有测试与 v6/v7 启动路径。
        self.save_manager: Any = save_manager
        self.story_id: Optional[str] = story_id
        self.tree: Optional[Dict[str, Any]] = None

    @property
    def shifts_completed(self) -> int:
        """从 visited_landmarks 派生:已访问的 S1-S6 地标数量。"""
        return len([l for l in self.visited_landmarks if l in {"S1", "S2", "S3", "S4", "S5", "S6"}])

    # 由 play() 在加载 tree 时注入(可选)。用于获得道具时显示说明。
    inv_descriptions: Dict[str, str] = {}

    def apply(self, effects: Optional[Dict[str, Any]]) -> List[str]:
        """应用 effects 字典,返回简短描述列表(供 UI 反馈,向后兼容)。

        副作用:同时把结构化事件写入 self._last_events,供 UI 卡片化渲染。
        """
        return EffectApplier.apply(self, effects)

    def _meets_clause(self, require: Optional[Dict[str, Any]]) -> bool:
        """检查单一 require 子句的所有原子条件(AND 关系)。
        不递归处理 any_of/all_of/not。
        """
        return RequirementEvaluator.meets_clause(self, require)

    def meets(self, require: Optional[Dict[str, Any]]) -> bool:
        """检查 require 条件是否满足(支持嵌套 any_of/all_of/not 组合)。

        组合优先级: 顶层各项是 AND 关系。
        - 顶层原子键(PR_min/inv_has/flags 等) → AND
        - any_of: [子句, ...] → OR(任一子句满足即可)
        - all_of: [子句, ...] → AND(所有子句必须满足)
        - not: 子句 → NOT(子句必须不满足)

        子句本身递归遵循同样规则(支持嵌套)。
        """
        return RequirementEvaluator.meets(self, require)

    # --- 选项可见性分类(visible / locked / hidden) ---

    # 哪些 require 字段是"玩家可知"的(缺失时显示锁定提示),哪些是 spoiler(隐藏)
    _SPOILER_KEYS = (
        "PR_min", "PR_max", "GR_min", "GR_max",
        "flags", "shifts_completed_min", "shifts_skipped_min",
        "landmark_visited", "character", "not",
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
        if "character" in req:
            expected = req["character"]
            if isinstance(expected, str) and self.character != expected: return False
            if isinstance(expected, list) and self.character not in expected: return False
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
        puzzle_str = ""
        if self.puzzle_pieces:
            puzzle_str = f"  {green('拼图')} {len(self.puzzle_pieces)}/5"
        return (
            f"{dim('━' * 60)}\n"
            f"{yellow('夜班')} {self.shifts_completed}/7  "
            f"{red('漏卡')} {self.shifts_skipped}"
            f"{puzzle_str}\n"
            f"{dim('随身:')} {inv_str}\n"
            f"{dim('━' * 60)}"
        )

    def full_status(self) -> str:
        """完整状态(s 键调出) — 包含个人共鸣 / 全局共鸣。"""
        inv_str = "·".join(self.inv) if self.inv else "—"
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
            f"{puzzle_str}\n"
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
    """渲染 narrative。当文本含 `\n---\n` 段落分隔符且 ≥ 2 段时,分屏渲染:
    每段读完 → 短暂呼吸 → 渐入 Enter 提示 → 玩家继续 → 再呼吸再下段。
    GHOST_FAST=1 跳过分屏直出。
    """
    from ghost_story_factory.v7.animate import pause as _pause, fade_lines as _fade

    print()
    segments = [s.strip() for s in text.strip().split("\n---\n") if s.strip()]

    if os.environ.get("GHOST_FAST") or len(segments) <= 1:
        for line in text.strip().split("\n"):
            slow_print(_highlight_narrative(line))
        print()
        return

    total = len(segments)
    for idx, seg in enumerate(segments):
        for line in seg.split("\n"):
            slow_print(_highlight_narrative(line))
        if idx < total - 1:
            _pause(0.6)  # 段读完,先静默一拍(让玩家"消化")
            print()
            _fade([dim(f"  ── 按 Enter 继续 · {idx + 2}/{total} ──")], line_delay=0.12)
            try:
                input("")  # 不要再多打一行字,纯等待 Enter
            except (EOFError, KeyboardInterrupt):
                print("\n" + red("中断。"))
                sys.exit(0)
            _pause(0.4)  # Enter 之后,下段渐入前再停一拍
            print()
    print()


def _presentation_enabled() -> bool:
    """判断是否显示 VN 文本演出提示。默认开启,便于无素材时仍能看到演出意图。"""
    raw = os.environ.get("GHOST_VN_CUES", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _asset_label(tree: Dict[str, Any], section: str, asset_id: Any) -> str:
    """把资产 id 转成 label。找不到 label 时保留 id,方便定位坏数据。"""
    if not asset_id:
        return ""
    key = str(asset_id)
    meta = ((tree.get("assets") or {}).get(section) or {}).get(key)
    if isinstance(meta, dict):
        label = meta.get("label")
        if label:
            return str(label)
    return key


def format_presentation_lines(
    tree: Dict[str, Any],
    node: Dict[str, Any],
) -> List[str]:
    """把节点 presentation 格式化成玩家可见的短文本演出提示。

    这是运行时的文本 fallback,不是资产加载器。真实图片 / 音频以后可以替换
    这一层,但当前 CLI/TUI 至少不能继续丢掉演出契约。
    """
    if not _presentation_enabled():
        return []

    presentation = node.get("presentation") or {}
    if not isinstance(presentation, dict):
        return []

    base_parts: List[str] = []
    detail_parts: List[str] = []

    background = _asset_label(tree, "backgrounds", presentation.get("background"))
    if background:
        base_parts.append(f"背景={background}")

    bgm = _asset_label(tree, "bgm", presentation.get("bgm"))
    if bgm:
        base_parts.append(f"音乐={bgm}")

    sfx_values = presentation.get("sfx") or []
    if isinstance(sfx_values, str):
        sfx_values = [sfx_values]
    elif not isinstance(sfx_values, list):
        sfx_values = [sfx_values]
    sfx_labels: List[str] = []
    for sfx in sfx_values:
        label = _asset_label(tree, "sfx", sfx)
        if label:
            sfx_labels.append(label)
    if sfx_labels:
        base_parts.append(f"音效={','.join(sfx_labels)}")

    sprite = _asset_label(tree, "sprites", presentation.get("sprite"))
    expression = presentation.get("expression")
    if sprite and expression:
        base_parts.append(f"角色={sprite}({expression})")
    elif sprite:
        base_parts.append(f"角色={sprite}")

    camera = presentation.get("camera")
    if camera:
        detail_parts.append(f"镜头={camera}")

    transition = presentation.get("transition")
    if transition:
        detail_parts.append(f"转场={transition}")

    transition_intent = presentation.get("transition_intent")
    if transition_intent:
        detail_parts.append(f"转场意图={transition_intent}")

    cg_intent = presentation.get("cg_intent")
    if cg_intent:
        detail_parts.append(f"CG意图={cg_intent}")

    cg_unlock = presentation.get("cg_unlock")
    if cg_unlock:
        detail_parts.append(f"CG解锁={cg_unlock}")

    lines: List[str] = []
    if base_parts:
        lines.append("演出: " + " · ".join(base_parts))
    if detail_parts:
        lines.append("镜头: " + " · ".join(detail_parts))
    return lines


def render_presentation(tree: Dict[str, Any], node: Dict[str, Any]) -> None:
    """CLI 文本演出提示。无 presentation 时保持静默。"""
    lines = format_presentation_lines(tree, node)
    if not lines:
        return
    print()
    for line in lines:
        print(dim(f"  {line}"))


def render_choices(
    visible: List[Dict[str, Any]],
    locked: Optional[List[Tuple[Dict[str, Any], str]]] = None,
) -> None:
    """渲染选项。
    - visible: 可点击,有编号 1..N
    - locked: 显示但禁用,带 🔒 + 缺失道具提示,无编号

    普通节点 ≥ 5 选项时按 stay-互动 vs 推进 分组;picker 节点保持平铺。
    """
    from ghost_story_factory.v7.animate import pause as _pause
    _pause(0.35)  # narrative 读完到选项之间留呼吸,避免节奏断
    print()
    # picker 节点(travel/tool/endshift)保持原列表;普通节点尝试分组
    is_picker = any(
        c.get("_landmark_id")
        or c.get("_picker_kind") in ("travel", "tool", "endshift")
        for c in visible
    )

    def _is_stay(c: Dict[str, Any]) -> bool:
        eff = c.get("effects") or {}
        return bool(eff.get("stay")) or c.get("_picker_kind") == "detail"

    stay_idx = [i for i, c in enumerate(visible) if _is_stay(c)]
    fwd_idx = [i for i, c in enumerate(visible) if not _is_stay(c)]

    if (not is_picker) and len(visible) >= 5 and stay_idx and fwd_idx:
        # 分组渲染:stay 互动在上,推进选项在底(显眼"出口")
        print(dim("  ── 在这里看一眼 ──"))
        for i in stay_idx:
            label = visible[i].get("text", "(无文本)")
            print(f"  {green(str(i + 1))}. {label}")
        print()
        print(dim("  ── 走出去 ──"))
        for i in fwd_idx:
            label = visible[i].get("text", "(无文本)")
            print(f"  {green(str(i + 1))}. {label}")
    else:
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
        elif t == "knowledge_learned":
            # Pass2 反馈条:正文打字结束后先 400ms 停顿,再整行淡入。
            # 载体三态:复读(已知 · X)/ 档案补遗(archive/corruption)/ 默认值班记录本。
            # 文案禁用 ▌▐ HUD 符号,只用 dim 着色保持 Lore 物件感。
            from ghost_story_factory.v7.animate import pause as _pause
            key = ev["key"]
            know_text = key[len("know."):] if key.startswith("know.") else key
            is_first = ev.get("is_first_time", True)
            is_archive = ("archive" in key) or ("corruption" in key)
            _pause(0.4)
            if not is_first:
                # 复读:短 dim,不弹"记下"
                print(dim(f"  (已知 · {know_text})"))
            elif is_archive:
                print(dim(f"  档案补遗 · {know_text}"))
            else:
                print(dim(f"  (你在值班记录本上记下:{know_text})"))
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


def mark_tool_visit(tree: Dict[str, Any], state: State, node: Dict[str, Any]) -> None:
    """进入工具节点时,把对应 toolbar 状态标记为已访问。

    工具栏的状态不应该靠每个 choice 手写一套 flag。节点已经声明 `_tool_id`,
    顶层 `tools` 已经声明 `state_flag`,这两个字段才是单一真相源。
    """
    tool_id = node.get("_tool_id")
    if not tool_id:
        return
    for tool in tree.get("tools") or []:
        if tool.get("id") != tool_id:
            continue
        flag = tool.get("state_flag")
        if flag:
            state.flags[str(flag)] = True
        return


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

def _select_character(
    characters: Dict[str, Any],
    save_manager: Any = None,
) -> Optional[str]:
    """v8 三态主菜单:locked / unlockable / playable。

    - locked:角色未解锁 → 灰剪影 + 锁定提示(无法选)
    - unlockable:首次解锁后未玩 → "! 新解锁" 标记
    - playable:已通关 → 显示通关 ending 数 + 徽章

    向后兼容:save_manager=None 时回退到旧行为(全部可选)。
    """
    if not characters:
        return None
    keys = list(characters.keys())

    # 查解锁状态(若有 save_manager)
    if save_manager is not None:
        unlocked = set(save_manager.unlocked_characters)
        all_endings_seen = set(save_manager.endings_seen)
    else:
        unlocked = set(keys)
        all_endings_seen = set()

    # 单角色 + 已解锁 → 直接返回
    if len(keys) == 1 and keys[0] in unlocked:
        return keys[0]

    print(bold(magenta("\n  可玩角色:")))
    selectable_indices: List[int] = []
    for i, k in enumerate(keys, start=1):
        cdef = characters[k] or {}
        label = cdef.get("label", k)
        if k in unlocked:
            # 统计该角色 ending 数(按 ENDING_UNLOCKS 反查 + 命名前缀)
            char_endings = sum(
                1 for e in all_endings_seen
                if e.upper().startswith(f"E_{k.upper().replace('-', '_')}_")
            )
            if char_endings > 0:
                badge = "★" * min(char_endings, 4)
                print(f"  {green(str(i))}. {bold(label)}  {green(badge)}")
            else:
                # unlockable(已解锁但未通关任一该角色 ending)
                tag = "  ! 新解锁" if k != "G-273" else ""
                print(f"  {green(str(i))}. {bold(label)}{cyan(tag)}")
            selectable_indices.append(i)
        else:
            # locked
            hint = cdef.get("_unlock_hint") or "需通关特定结局解锁"
            print(f"  {dim(str(i))}. {dim('???' + ' ' * 4)}  {dim('🔒 ' + hint)}")
    print()

    if not selectable_indices:
        return None
    if len(selectable_indices) == 1:
        only = keys[selectable_indices[0] - 1]
        return only
    while True:
        try:
            raw = input(bold(f"> 选择角色 (默认 {selectable_indices[0]}): ")).strip()
        except (EOFError, KeyboardInterrupt):
            return keys[selectable_indices[0] - 1]
        if not raw:
            return keys[selectable_indices[0] - 1]
        if raw.isdigit():
            n = int(raw)
            if n in selectable_indices:
                return keys[n - 1]
            if 1 <= n <= len(keys):
                print(red(f"  角色 {n} 锁定中,无法选择。"))
                continue
        print(red(f"  请输入 {selectable_indices}(已解锁)。"))


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
        selected_character = _select_character(characters, save_manager=save_manager)

    if selected_character and selected_character in characters:
        cdef = characters[selected_character]
        initial_state["character"] = selected_character
        if cdef.get("initial_inv"):
            initial_state["inv"] = list(cdef["initial_inv"])
        if cdef.get("initial_flags"):
            initial_state["flags"] = dict(cdef["initial_flags"])
        # ADR-010 沙盒契约:角色周目自带"已知地标"集合(默认 G-273=[S1])
        if cdef.get("initial_known_landmarks"):
            initial_state["known_landmarks"] = list(cdef["initial_known_landmarks"])

    story_id = str(tree.get("story_id") or tree_path.stem)
    # 反应机制(ADR-008):State 持 save_manager + story_id + tree 引用,
    # 让 _meets_clause 的 deduction/foreshadow/theme_resolved 条件能查询单一真相源。
    state = State(initial_state, save_manager=save_manager, story_id=story_id)
    state.tree = tree
    # NPC 初始位置:从 tree.npcs[*].initial_location 注入到 state.npc_locations
    # 玩家从未见过 NPC 时,地图也能显示 NPC 在哪 — 而不是空白
    if not state.npc_locations:
        for npc_id, meta in (tree.get("npcs") or {}).items():
            loc = (meta or {}).get("initial_location")
            if loc:
                state.npc_locations[npc_id] = str(loc)
    # 注入道具说明字典(获得物品时显示用途)
    State.inv_descriptions = tree.get("inv_descriptions", {}) or {}
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
        mark_tool_visit(tree, state, node)
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
        render_presentation(tree, node)
        # _is_map_picker 节点:用地图视图替代普通 narrative
        # 先 build picker_choices 算出 travel_indices(让数字贴到地图上)
        if node.get("_is_map_picker"):
            from ghost_story_factory.v7.map_view import (
                render_map_cli, picker_choices
            )
            _picker_pre = picker_choices(tree, state, node=node)
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
        if EndingResolver.is_ending(node):
            ending_type = EndingResolver.ending_type(node)
            ending_name = EndingResolver.ending_name(tree, ending_type)
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
            generated = picker_choices(tree, state, node=node)
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
