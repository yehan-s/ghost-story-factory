"""跨周目存档管理器(v7+)。

设计原则(Linus 风格):
- 数据结构是核心:存档就是一个扁平 JSON,没有嵌套花活
- 单一职责:只管 load/save/record_ending,不管菜单 UI
- 容错优先:文件损坏 / 缺失 / 字段丢失 → 静默降级到默认值,从不抛异常
- 向后兼容:旧版本(只有 meta_flags)能无缝升级

存档文件位置: ~/.ghost_save.json

数据结构:
{
    "version": 1,
    "meta_flags": {"cleared_g273_truth": true, ...},
    "unlocked_characters": ["G-273", "linmou_1985"],
    "endings_seen": ["E_TRUTH", "E_NEUTRAL"],
    "last_played": "2026-05-07T03:00:00",
    "playthroughs": 2,
    "stories_completed": {"杭州_v7": ["E_TRUTH"], ...}
}

解锁矩阵: 见 ENDING_UNLOCKS / CHARACTER_ROSTER
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# --- 解锁映射(单一数据源) ---

# 通关哪个 ending → 解锁哪个角色
# 见 docs/superpowers/specs/2026-05-07-PROJECT-STATE-AND-FORESHADOW-REGISTRY.md §7
ENDING_UNLOCKS: Dict[str, str] = {
    "E_TRUTH": "linmou_1985",        # 揭穿真相 → 1985 林副科长
    "E_TRUE": "yeh_1991",            # 关闭杭州常数 → 1991 叶某
    "E_DATA": "predecessor_1998",    # 数据化 → 1998 前任 G-273
    "E_BROADCAST": "predecessor_2009",  # 永生论坛 → 2009 前任 G-273
    "E_BAD_DROWN": "worker_1986",    # 沉船替死 → 1986 工人
    "E_BAD_1987": "red_victim_13",   # 无尽 1987 → 1987 红衣 13 号
    "E_HIDDEN": "worker_1980",       # 重投胎 → 1980 工人
    # E_NEUTRAL 不解锁(默认结局)
    # E_TRUTH 同时也可作为 1996 红衣女孩的解锁(若达成额外 flag)
}

# 8 棺角色 roster(主角 + 8 个未来可玩角色)
CHARACTER_ROSTER: List[Dict[str, Any]] = [
    {
        "id": "G-273",
        "label": "赵某 G-273",
        "year": 2024,
        "subtitle": "现役夜班保安(主角)",
        "default_unlocked": True,
        "unlock_hint": "(默认可玩)",
    },
    {
        "id": "linmou_1985",
        "label": "林副科长",
        "year": 1985,
        "subtitle": "投湖前夜的财务科副科长",
        "default_unlocked": False,
        "unlock_hint": "通关 E_TRUTH(揭穿真相)解锁",
    },
    {
        "id": "yeh_1991",
        "label": "叶某",
        "year": 1991,
        "subtitle": "11 岁,留下小学",
        "default_unlocked": False,
        "unlock_hint": "通关 E_TRUE(关闭杭州常数)解锁",
    },
    {
        "id": "worker_1986",
        "label": "1986 工人",
        "year": 1986,
        "subtitle": "联庄站盾构井,沉船 7 工人之一",
        "default_unlocked": False,
        "unlock_hint": "通关 E_BAD_DROWN(沉船替死)解锁",
    },
    {
        "id": "red_victim_13",
        "label": "红衣 13 号",
        "year": 1987,
        "subtitle": "1987 柳浪闻莺,308 阶上的红衣",
        "default_unlocked": False,
        "unlock_hint": "通关 E_BAD_1987(无尽 1987)解锁",
    },
    {
        "id": "worker_1980",
        "label": "1980 工人",
        "year": 1980,
        "subtitle": "羊血弄,牲畜行学徒",
        "default_unlocked": False,
        "unlock_hint": "通关 E_HIDDEN(重投胎)解锁",
    },
    {
        "id": "red_girl_1996",
        "label": "何小燕",
        "year": 1996,
        "subtitle": "1996-08-23 货梯失踪的小女孩",
        "default_unlocked": False,
        "unlock_hint": "通关 E_TRUTH 且收集红衣线索后解锁",
    },
    {
        "id": "predecessor_1998",
        "label": "前任 G-273(1998)",
        "year": 1998,
        "subtitle": "12 任叠在同位置的工牌之一",
        "default_unlocked": False,
        "unlock_hint": "通关 E_DATA(数据化)解锁",
    },
    {
        "id": "predecessor_2009",
        "label": "前任 G-273(2009)",
        "year": 2009,
        "subtitle": "永生于夜班论坛的对讲机声",
        "default_unlocked": False,
        "unlock_hint": "通关 E_BROADCAST(永生论坛)解锁",
    },
]


# --- 默认存档 ---

SAVE_VERSION = 4  # v4:加 achievements_unlocked
DEFAULT_SAVE: Dict[str, Any] = {
    "version": SAVE_VERSION,
    "meta_flags": {},
    "unlocked_characters": ["G-273"],
    "endings_seen": [],
    "last_played": "",
    "playthroughs": 0,
    "stories_completed": {},
    # 伏笔进度:每个 story_id 维护两个集合
    # foreshadows_seen[story_id] = [slot_id, ...]    玩家见过/触发过相关节点
    # foreshadows_resolved[story_id] = [slot_id, ...]  真正解开(角色/ending 满足)
    "foreshadows_seen": {},
    "foreshadows_resolved": {},
    # v3 新增字段:
    # foreshadow_shards[story_id][slot_id] = [shard_id, ...]
    # deductions_resolved[story_id] = [deduction_id, ...]
    "foreshadow_shards": {},
    "deductions_resolved": {},
    # v4 新增:跨周目成就解锁(achievement id 列表)
    "achievements_unlocked": [],
}


def _save_path() -> Path:
    return Path.home() / ".ghost_save.json"


# --- SaveManager ---

class SaveManager:
    """单一存档管理器。线程不安全(单玩家本地游戏,够用)。"""

    def __init__(self, path: Optional[Path] = None):
        self.path: Path = path if path is not None else _save_path()
        self.data: Dict[str, Any] = dict(DEFAULT_SAVE)
        self.data["unlocked_characters"] = list(DEFAULT_SAVE["unlocked_characters"])
        self.data["foreshadows_seen"] = {}
        self.data["foreshadows_resolved"] = {}
        self.data["foreshadow_shards"] = {}
        self.data["deductions_resolved"] = {}
        self.data["achievements_unlocked"] = []
        self.load()

    # --- IO ---

    def load(self) -> None:
        """从磁盘加载。文件缺失/损坏 → 用默认值。"""
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(raw, dict):
            return
        # 字段级合并:旧版本只有 meta_flags 也能用
        self.data["meta_flags"] = dict(raw.get("meta_flags") or {})
        unlocked = raw.get("unlocked_characters") or ["G-273"]
        if "G-273" not in unlocked:
            unlocked = ["G-273"] + list(unlocked)
        self.data["unlocked_characters"] = list(unlocked)
        self.data["endings_seen"] = list(raw.get("endings_seen") or [])
        self.data["last_played"] = str(raw.get("last_played") or "")
        self.data["playthroughs"] = int(raw.get("playthroughs") or 0)
        self.data["stories_completed"] = dict(raw.get("stories_completed") or {})
        # v2:伏笔进度(向后兼容,字段缺失 → 空字典)
        fs_seen = raw.get("foreshadows_seen") or {}
        fs_resolved = raw.get("foreshadows_resolved") or {}
        self.data["foreshadows_seen"] = {
            k: list(v) for k, v in fs_seen.items() if isinstance(v, list)
        }
        self.data["foreshadows_resolved"] = {
            k: list(v) for k, v in fs_resolved.items() if isinstance(v, list)
        }
        # v3:碎片 / 推论(向后兼容缺失字段)
        fs_shards = raw.get("foreshadow_shards") or {}
        self.data["foreshadow_shards"] = {
            sid: {slot: list(shards) for slot, shards in by_slot.items()
                  if isinstance(shards, list)}
            for sid, by_slot in fs_shards.items()
            if isinstance(by_slot, dict)
        }
        ded = raw.get("deductions_resolved") or {}
        self.data["deductions_resolved"] = {
            k: list(v) for k, v in ded.items() if isinstance(v, list)
        }
        # v4:成就(向后兼容缺失字段)
        self.data["achievements_unlocked"] = list(
            raw.get("achievements_unlocked") or []
        )
        self.data["version"] = SAVE_VERSION

    def save(self) -> bool:
        """写盘。失败时静默返回 False。"""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)
            return True
        except OSError:
            return False

    # --- 查询 API ---

    @property
    def meta_flags(self) -> Dict[str, bool]:
        return self.data.get("meta_flags", {})

    @property
    def unlocked_characters(self) -> List[str]:
        return list(self.data.get("unlocked_characters", []))

    @property
    def endings_seen(self) -> List[str]:
        return list(self.data.get("endings_seen", []))

    def is_unlocked(self, character_id: str) -> bool:
        return character_id in self.data.get("unlocked_characters", [])

    def has_seen_ending(self, ending_type: str) -> bool:
        return ending_type in self.data.get("endings_seen", [])

    # --- 修改 API ---

    def record_ending(self, ending_type: str, story_id: str = "杭州_v7") -> List[str]:
        """记录一个 ending 通关。返回本次新解锁的角色 ID 列表。

        副作用:
        - endings_seen 追加(去重)
        - unlocked_characters 根据 ENDING_UNLOCKS 解锁(去重)
        - meta_flags 设置 cleared_<character>_<ending_lower>
        - playthroughs += 1
        - last_played 更新
        - stories_completed[story_id] 追加
        - 自动写盘
        """
        if not ending_type:
            return []

        newly_unlocked: List[str] = []

        endings = self.data.setdefault("endings_seen", [])
        if ending_type not in endings:
            endings.append(ending_type)

        unlocked = self.data.setdefault("unlocked_characters", ["G-273"])
        target = ENDING_UNLOCKS.get(ending_type)
        if target and target not in unlocked:
            unlocked.append(target)
            newly_unlocked.append(target)

        # meta_flag: 通关标记(剧本层可读)
        meta_flag_key = f"cleared_g273_{ending_type.lower().replace('e_', '')}"
        self.data.setdefault("meta_flags", {})[meta_flag_key] = True

        # stories_completed
        sc = self.data.setdefault("stories_completed", {})
        story_endings = sc.setdefault(story_id, [])
        if ending_type not in story_endings:
            story_endings.append(ending_type)

        self.data["playthroughs"] = int(self.data.get("playthroughs", 0)) + 1
        self.data["last_played"] = datetime.now().isoformat(timespec="seconds")

        self.save()
        return newly_unlocked

    def reset(self) -> None:
        """清空存档(开发/测试用)。"""
        self.data = dict(DEFAULT_SAVE)
        self.data["unlocked_characters"] = list(DEFAULT_SAVE["unlocked_characters"])
        self.data["foreshadows_seen"] = {}
        self.data["foreshadows_resolved"] = {}
        self.save()

    # --- 伏笔 API(v2) ---

    def mark_foreshadow_seen(self, story_id: str, slot_id: str) -> bool:
        """标记伏笔已被玩家触发(玩到了相关节点)。返回是否首次触发。"""
        if not story_id or not slot_id:
            return False
        seen = self.data.setdefault("foreshadows_seen", {}).setdefault(story_id, [])
        if slot_id in seen:
            return False
        seen.append(slot_id)
        return True

    def mark_foreshadow_resolved(self, story_id: str, slot_id: str) -> bool:
        """标记伏笔已解开。返回是否本次新解开。"""
        if not story_id or not slot_id:
            return False
        # 解开的同时也算"看过"
        self.mark_foreshadow_seen(story_id, slot_id)
        resolved = self.data.setdefault("foreshadows_resolved", {}).setdefault(story_id, [])
        if slot_id in resolved:
            return False
        resolved.append(slot_id)
        return True

    def auto_resolve(
        self, tree: Dict[str, Any], ending_type: str,
        character_id: str, story_id: str,
    ) -> List[str]:
        """通关 ending 时自动判断哪些伏笔被解开。返回本次新解开的 slot_id 列表。

        规则:遍历 tree.foreshadows,逐个 slot 判断:
        - explained_by_ending == ending_type → 解开
        - explained_by_character == character_id → 解开(任意 ending)
        """
        foreshadows = (tree or {}).get("foreshadows") or {}
        if not foreshadows:
            return []
        newly: List[str] = []
        for slot_id, meta in foreshadows.items():
            by_end = meta.get("explained_by_ending")
            by_char = meta.get("explained_by_character")
            should_resolve = False
            if by_end and by_end == ending_type:
                should_resolve = True
            if by_char and by_char == character_id:
                should_resolve = True
            if should_resolve and self.mark_foreshadow_resolved(story_id, slot_id):
                newly.append(slot_id)
        if newly:
            self.save()
        return newly

    def foreshadow_progress(
        self, tree: Dict[str, Any], story_id: str,
    ) -> tuple:
        """返回 (seen_count, resolved_count, total) 三元组。"""
        foreshadows = (tree or {}).get("foreshadows") or {}
        total = len(foreshadows)
        seen = len(self.data.get("foreshadows_seen", {}).get(story_id, []))
        resolved = len(self.data.get("foreshadows_resolved", {}).get(story_id, []))
        return (seen, resolved, total)

    def is_foreshadow_seen(self, story_id: str, slot_id: str) -> bool:
        return slot_id in self.data.get("foreshadows_seen", {}).get(story_id, [])

    def is_foreshadow_resolved(self, story_id: str, slot_id: str) -> bool:
        return slot_id in self.data.get("foreshadows_resolved", {}).get(story_id, [])

    # --- 碎片 API(v3) ---

    def add_foreshadow_shard(
        self, tree: Dict[str, Any], story_id: str, slot_id: str, shard_id: str,
    ) -> tuple:
        """加一个伏笔碎片。返回 (newly_added, fully_collected)。

        - newly_added: 是否本次新增(已有则 False)
        - fully_collected: 加完后是否齐全(齐则同时标记 resolved)
        """
        if not story_id or not slot_id or not shard_id:
            return (False, False)
        # 同时标记 seen
        self.mark_foreshadow_seen(story_id, slot_id)
        story_shards = self.data.setdefault("foreshadow_shards", {}).setdefault(
            story_id, {}
        )
        owned = story_shards.setdefault(slot_id, [])
        newly = shard_id not in owned
        if newly:
            owned.append(shard_id)
        # 检查是否集齐
        meta = (tree.get("foreshadows") or {}).get(slot_id) or {}
        all_shards = meta.get("shards") or []
        all_ids = {s.get("id") for s in all_shards if s.get("id")}
        fully = bool(all_ids) and all_ids.issubset(set(owned))
        if fully and not self.is_foreshadow_resolved(story_id, slot_id):
            self.mark_foreshadow_resolved(story_id, slot_id)
        return (newly, fully)

    def get_shards_collected(self, story_id: str, slot_id: str) -> List[str]:
        return list(
            self.data.get("foreshadow_shards", {})
            .get(story_id, {}).get(slot_id, [])
        )

    def shard_progress(
        self, tree: Dict[str, Any], story_id: str, slot_id: str,
    ) -> tuple:
        """返回 (collected_count, total)。total=0 表示该伏笔未启用碎片机制。"""
        meta = (tree.get("foreshadows") or {}).get(slot_id) or {}
        total = len(meta.get("shards") or [])
        collected = len(self.get_shards_collected(story_id, slot_id))
        return (collected, total)

    # --- 推论 API(v3) ---

    def check_deductions(
        self, tree: Dict[str, Any], story_id: str,
    ) -> List[str]:
        """扫所有 deductions,看哪些前置 foreshadow 全 resolved 了 → 触发解锁。

        返回本次新触发的 deduction id 列表。
        """
        deductions = (tree or {}).get("deductions") or {}
        if not deductions:
            return []
        resolved_set = set(
            self.data.get("foreshadows_resolved", {}).get(story_id, [])
        )
        already = set(
            self.data.get("deductions_resolved", {}).get(story_id, [])
        )
        newly: List[str] = []
        for ded_id, meta in deductions.items():
            if ded_id in already:
                continue
            requires = set(meta.get("requires_resolved") or [])
            if requires and requires.issubset(resolved_set):
                self.data.setdefault("deductions_resolved", {}).setdefault(
                    story_id, []
                ).append(ded_id)
                newly.append(ded_id)
        if newly:
            self.save()
        return newly

    def is_deduction_resolved(self, story_id: str, deduction_id: str) -> bool:
        return deduction_id in self.data.get("deductions_resolved", {}).get(
            story_id, []
        )

    # --- 成就 API(v4) ---

    def check_achievements(
        self, tree: Dict[str, Any], state, story_id: str,
        on_ending: bool = False,
    ) -> List[str]:
        """扫所有 achievements,看哪些条件满足 → 触发解锁。

        on_ending: 是否结局时调用(影响 trigger.on_ending 类型成就)
        返回本次新解锁的 achievement id 列表。
        """
        achievements = (tree or {}).get("achievements") or {}
        if not achievements:
            return []
        already = set(self.data.get("achievements_unlocked") or [])
        newly: List[str] = []

        # 准备各种统计值
        shards_total = 0
        for slot_shards in (
            self.data.get("foreshadow_shards", {}).get(story_id, {}).values()
        ):
            shards_total += len(slot_shards)
        deductions_count = len(
            self.data.get("deductions_resolved", {}).get(story_id, [])
        )
        endings_seen_count = len(self.data.get("endings_seen") or [])
        seen_set = set(self.data.get("foreshadows_seen", {}).get(story_id, []))
        resolved_set = set(
            self.data.get("foreshadows_resolved", {}).get(story_id, [])
        )
        themes = (tree or {}).get("themes") or {}

        for ach_id, meta in achievements.items():
            if ach_id in already:
                continue
            trigger = meta.get("trigger") or {}
            if trigger.get("on_ending") and not on_ending:
                continue
            ok = True
            # 各种条件
            if "shards_collected_min" in trigger:
                if shards_total < int(trigger["shards_collected_min"]):
                    ok = False
            if "deductions_resolved_min" in trigger:
                if deductions_count < int(trigger["deductions_resolved_min"]):
                    ok = False
            if "endings_seen_min" in trigger:
                if endings_seen_count < int(trigger["endings_seen_min"]):
                    ok = False
            if "visited_landmarks_count" in trigger and state is not None:
                visited = getattr(state, "visited_landmarks", None) or []
                if len(visited) < int(trigger["visited_landmarks_count"]):
                    ok = False
            if "shifts_skipped_max" in trigger and state is not None:
                if getattr(state, "shifts_skipped", 0) > int(
                    trigger["shifts_skipped_max"]
                ):
                    ok = False
            if "PR_max" in trigger and state is not None:
                if getattr(state, "PR", 0) > int(trigger["PR_max"]):
                    ok = False
            if "PR_peak_min" in trigger and state is not None:
                peak = getattr(state, "PR_peak", 0)
                if peak < int(trigger["PR_peak_min"]):
                    ok = False
            if "visit_count_min" in trigger and state is not None:
                visit_counts = getattr(state, "visit_counts", {}) or {}
                for nid, n in trigger["visit_count_min"].items():
                    if visit_counts.get(nid, 0) < int(n):
                        ok = False
                        break
            if "foreshadow_seen" in trigger:
                if trigger["foreshadow_seen"] not in seen_set:
                    ok = False
            if "theme_resolved" in trigger:
                theme_id = trigger["theme_resolved"]
                theme_meta = themes.get(theme_id) or {}
                manifestations = theme_meta.get("manifestations") or []
                if not manifestations or not all(
                    m in resolved_set for m in manifestations
                ):
                    ok = False
            if ok:
                self.data.setdefault("achievements_unlocked", []).append(ach_id)
                newly.append(ach_id)
        if newly:
            self.save()
        return newly

    def is_achievement_unlocked(self, ach_id: str) -> bool:
        return ach_id in (self.data.get("achievements_unlocked") or [])


# --- 便利函数 ---

def get_character_info(character_id: str) -> Optional[Dict[str, Any]]:
    """从 roster 查角色信息。"""
    for c in CHARACTER_ROSTER:
        if c["id"] == character_id:
            return c
    return None
