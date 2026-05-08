"""GameTree v1 运行时契约。

这里放正式玩法路径的三件基础能力:

- `RequirementEvaluator`:判断一个选择/变体是否满足状态条件;
- `EffectApplier`:把选择后果写回状态;
- `EndingResolver`:识别结局并解析结局展示信息。

注意:本模块只关心数据契约,不关心 CLI 渲染。播放器可以换,契约不能乱。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _list(value: Any) -> List[Any]:
    """把标量/空值统一成列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


class RequirementEvaluator:
    """GameTree `require` 判断器。"""

    @classmethod
    def meets(cls, state: Any, require: Optional[Dict[str, Any]]) -> bool:
        """检查 `require` 是否满足。

        顶层原子条件是 AND 关系;`any_of` 是 OR;`all_of` 是 AND;`not` 是取反。
        """
        if not require:
            return True
        if not cls.meets_clause(state, require):
            return False
        if "any_of" in require:
            sub = require["any_of"] or []
            if sub and not any(cls.meets(state, c) for c in sub):
                return False
        if "all_of" in require:
            sub = require["all_of"] or []
            if not all(cls.meets(state, c) for c in sub):
                return False
        if "not" in require and cls.meets(state, require["not"]):
            return False
        return True

    @classmethod
    def meets_clause(cls, state: Any, require: Optional[Dict[str, Any]]) -> bool:
        """检查不含组合逻辑的单层原子条件。"""
        if not require:
            return True

        if "PR_min" in require and state.PR < int(require["PR_min"]):
            return False
        if "PR_max" in require and state.PR > int(require["PR_max"]):
            return False
        if "GR_min" in require and state.GR < int(require["GR_min"]):
            return False
        if "GR_max" in require and state.GR > int(require["GR_max"]):
            return False

        for item in require.get("inv_has", []) or []:
            if item not in state.inv:
                return False
        for item in require.get("inv_lacks", []) or []:
            if item in state.inv:
                return False

        for key, expected in (require.get("flags") or {}).items():
            if bool(state.flags.get(key, False)) != bool(expected):
                return False

        if "shifts_skipped_min" in require and state.shifts_skipped < int(require["shifts_skipped_min"]):
            return False
        if "shifts_completed_min" in require and state.shifts_completed < int(require["shifts_completed_min"]):
            return False

        for landmark_id in require.get("landmark_visited", []) or []:
            if landmark_id not in state.visited_landmarks:
                return False

        if "puzzle_pieces_min" in require and len(state.puzzle_pieces) < int(require["puzzle_pieces_min"]):
            return False

        for node_id, count in (require.get("visit_count_min") or {}).items():
            if state.visit_counts.get(node_id, 0) < int(count):
                return False

        if "last_landmark" in require:
            expected = require["last_landmark"]
            if isinstance(expected, str):
                if state.last_landmark_id != expected:
                    return False
            elif isinstance(expected, list):
                if state.last_landmark_id not in expected:
                    return False

        if "character" in require:
            expected = require["character"]
            if isinstance(expected, str):
                if state.character != expected:
                    return False
            elif isinstance(expected, list):
                if state.character not in expected:
                    return False

        if not cls._meets_resolved_requirements(state, require):
            return False
        if not cls._meets_ending_seen(state, require):
            return False
        return True

    @classmethod
    def _meets_resolved_requirements(cls, state: Any, require: Dict[str, Any]) -> bool:
        """检查跨周目伏笔/推论/主题条件。"""
        save_manager = getattr(state, "save_manager", None)
        story_id = getattr(state, "story_id", None)
        tree = getattr(state, "tree", None)

        if "deduction_resolved" in require:
            if save_manager is None or story_id is None:
                return False
            ids = _list(require["deduction_resolved"])
            if not any(save_manager.is_deduction_resolved(story_id, x) for x in ids):
                return False

        if "foreshadow_resolved" in require:
            if save_manager is None or story_id is None:
                return False
            ids = _list(require["foreshadow_resolved"])
            if not any(save_manager.is_foreshadow_resolved(story_id, x) for x in ids):
                return False

        if "theme_resolved" in require:
            if save_manager is None or story_id is None or tree is None:
                return False
            ids = _list(require["theme_resolved"])
            themes = (tree.get("themes") or {})
            resolved = save_manager.get_resolved_foreshadows(story_id)

            def theme_done(theme_id: str) -> bool:
                meta = themes.get(theme_id) or {}
                manifestations = set(meta.get("manifestations") or [])
                return bool(manifestations) and manifestations.issubset(resolved)

            if not any(theme_done(str(x)) for x in ids):
                return False

        return True

    @classmethod
    def _meets_ending_seen(cls, state: Any, require: Dict[str, Any]) -> bool:
        """检查跨周目结局条件。"""
        if "ending_seen" not in require:
            return True
        save_manager = getattr(state, "save_manager", None)
        if save_manager is None:
            return False

        spec = require["ending_seen"] or {}
        story_id = spec.get("story_id")
        ending_id = spec.get("ending_id")
        if not story_id or not ending_id:
            return False

        seen = (save_manager.data or {}).get("endings_seen")
        if isinstance(seen, dict):
            story_endings = seen.get(story_id) or []
        elif isinstance(seen, list):
            story_endings = list(seen) if story_id == "杭州_v7" else []
        else:
            story_endings = []

        if ending_id == "*":
            return bool(story_endings)
        return ending_id in story_endings


class EffectApplier:
    """GameTree `effects` 应用器。"""

    @classmethod
    def apply(cls, state: Any, effects: Optional[Dict[str, Any]]) -> List[str]:
        """把 effects 写入 state,并返回给 CLI 展示的短提示。"""
        notes: List[str] = []
        events: List[Dict[str, Any]] = []
        if not effects:
            state._last_events = events
            return notes

        cls._apply_scores(state, effects)
        cls._apply_inventory(state, effects, notes, events)
        cls._apply_flags(state, effects, events)
        cls._apply_landmarks(state, effects, notes, events)
        cls._apply_npc_and_puzzle(state, effects, notes, events)

        state._last_events = events
        return notes

    @staticmethod
    def _apply_scores(state: Any, effects: Dict[str, Any]) -> None:
        if "PR" in effects:
            delta = int(effects["PR"])
            if delta:
                state.PR = max(0, min(100, state.PR + delta))
                if state.PR > state.PR_peak:
                    state.PR_peak = state.PR
        if "GR" in effects:
            delta = int(effects["GR"])
            if delta:
                state.GR = max(0, min(100, state.GR + delta))

    @staticmethod
    def _apply_inventory(
        state: Any,
        effects: Dict[str, Any],
        notes: List[str],
        events: List[Dict[str, Any]],
    ) -> None:
        descriptions = getattr(state, "inv_descriptions", {}) or {}
        for item in effects.get("inv_add", []) or []:
            if item in state.inv:
                continue
            state.inv.append(item)
            desc = descriptions.get(item)
            notes.append(f"获得「{item}」 — {desc}" if desc else f"获得「{item}」")
            events.append({"type": "inv_add", "key": item, "desc": desc or ""})

        for item in effects.get("inv_remove", []) or []:
            if item not in state.inv:
                continue
            state.inv.remove(item)
            notes.append(f"失去「{item}」")
            events.append({"type": "inv_remove", "key": item})

    @staticmethod
    def _apply_flags(state: Any, effects: Dict[str, Any], events: List[Dict[str, Any]]) -> None:
        for key, value in (effects.get("flags") or {}).items():
            new_value = bool(value)
            old_value = bool(state.flags.get(key, False))
            state.flags[key] = new_value
            if key.startswith("know.") and new_value:
                events.append({
                    "type": "knowledge_learned",
                    "key": key,
                    "is_first_time": not old_value,
                })

    @staticmethod
    def _apply_landmarks(
        state: Any,
        effects: Dict[str, Any],
        notes: List[str],
        events: List[Dict[str, Any]],
    ) -> None:
        if "shifts_skipped" in effects:
            delta = int(effects["shifts_skipped"])
            state.shifts_skipped += delta
            notes.append(f"漏打卡 +{delta}")
            events.append({"type": "shifts_skipped", "delta": delta, "current": state.shifts_skipped})

        if "landmark_visited" in effects:
            landmark_id = str(effects["landmark_visited"])
            state.last_landmark_id = landmark_id
            if landmark_id not in state.visited_landmarks:
                state.visited_landmarks.append(landmark_id)
                if landmark_id in {"S1", "S2", "S3", "S4", "S5", "S6"}:
                    events.append({
                        "type": "shifts_completed",
                        "delta": 1,
                        "current": state.shifts_completed,
                        "implicit": True,
                    })
                notes.append(f"踏入 {landmark_id}")
                events.append({"type": "landmark_visited", "key": landmark_id})

        if "landmark_skipped" in effects:
            landmark_id = str(effects["landmark_skipped"])
            if landmark_id not in state.skipped_landmarks:
                state.skipped_landmarks.append(landmark_id)
                state.shifts_skipped += 1
                notes.append(f"绕开 {landmark_id}(漏卡 +1)")
                events.append({
                    "type": "landmark_skipped",
                    "key": landmark_id,
                    "current": state.shifts_skipped,
                })

    @staticmethod
    def _apply_npc_and_puzzle(
        state: Any,
        effects: Dict[str, Any],
        notes: List[str],
        events: List[Dict[str, Any]],
    ) -> None:
        for npc_id, target in (effects.get("npc_move") or {}).items():
            state.npc_locations[npc_id] = str(target)
            events.append({"type": "npc_move", "key": npc_id, "to": str(target)})

        if "puzzle_add" in effects:
            piece = str(effects["puzzle_add"])
            if piece not in state.puzzle_pieces:
                state.puzzle_pieces.append(piece)
                notes.append(f"拼图碎片 +1 ({len(state.puzzle_pieces)}/5)")
                events.append({
                    "type": "puzzle_add",
                    "key": piece,
                    "current": len(state.puzzle_pieces),
                    "total": 5,
                })


class EndingResolver:
    """GameTree 结局解析器。"""

    @staticmethod
    def is_ending(node: Dict[str, Any]) -> bool:
        """判断节点是否为结局。"""
        return bool(node.get("is_ending"))

    @staticmethod
    def ending_type(node: Dict[str, Any]) -> str:
        """获取结局 ID。"""
        return str(node.get("ending_type") or "E_UNKNOWN")

    @staticmethod
    def ending_name(tree: Dict[str, Any], ending_type: str) -> str:
        """获取结局展示名。"""
        return str((tree.get("endings") or {}).get(ending_type, ending_type))
