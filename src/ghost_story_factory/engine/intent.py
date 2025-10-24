"""意图映射引擎

选项交互式游戏的核心任务：
- 验证选项合法性（前置条件检查）
- 提取选项意图层级（物理动作 → 心理动机 → 叙事意义）
- 绑定后果树节点
- 返回校验结果和映射后的意图对象

可选扩展（自由输入式游戏）：
- 解析自由文本输入
- 将自然语言映射到标准化意图
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

from .state import GameState
from .choices import Choice


class IntentLevel(str, Enum):
    """意图层级"""
    PHYSICAL = "physical"      # 物理动作层
    EMOTIONAL = "emotional"    # 心理动机层
    NARRATIVE = "narrative"    # 叙事意义层


@dataclass
class Intent:
    """意图对象

    表示玩家选择背后的多层意图
    """
    # 物理层：具体动作
    physical_action: str

    # 心理层：动机
    emotional_motivation: str

    # 叙事层：在故事中的意义
    narrative_meaning: str

    # 原始选择
    original_choice: Choice

    # 风险评估
    risk_level: str  # "low" / "medium" / "high"

    def __str__(self) -> str:
        return (
            f"Intent(\n"
            f"  物理: {self.physical_action}\n"
            f"  心理: {self.emotional_motivation}\n"
            f"  叙事: {self.narrative_meaning}\n"
            f"  风险: {self.risk_level}\n"
            f")"
        )


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    reason: Optional[str] = None
    missing_preconditions: Optional[Dict[str, Any]] = None


class IntentMappingEngine:
    """意图映射引擎

    负责验证选项和提取意图层级
    """

    def __init__(self):
        """初始化引擎"""
        pass

    def validate_choice(
        self,
        choice: Choice,
        game_state: GameState
    ) -> ValidationResult:
        """验证选项是否可用

        Args:
            choice: 待验证的选项
            game_state: 当前游戏状态

        Returns:
            ValidationResult: 验证结果
        """
        # 检查前置条件
        if not choice.preconditions:
            return ValidationResult(is_valid=True)

        # 检查各类前置条件
        missing_conditions = {}

        # 检查 PR
        if "PR" in choice.preconditions:
            if not game_state.check_preconditions({"PR": choice.preconditions["PR"]}):
                missing_conditions["PR"] = {
                    "required": choice.preconditions["PR"],
                    "current": game_state.PR
                }

        # 检查 GR
        if "GR" in choice.preconditions:
            if not game_state.check_preconditions({"GR": choice.preconditions["GR"]}):
                missing_conditions["GR"] = {
                    "required": choice.preconditions["GR"],
                    "current": game_state.GR
                }

        # 检查道具
        if "items" in choice.preconditions:
            required_items = choice.preconditions["items"]
            if isinstance(required_items, list):
                missing_items = [
                    item for item in required_items
                    if item not in game_state.inventory
                ]
                if missing_items:
                    missing_conditions["items"] = {
                        "required": required_items,
                        "missing": missing_items
                    }

        # 检查标志位
        if "flags" in choice.preconditions:
            required_flags = choice.preconditions["flags"]
            if isinstance(required_flags, dict):
                missing_flags = {}
                for flag, expected in required_flags.items():
                    if game_state.flags.get(flag) != expected:
                        missing_flags[flag] = {
                            "required": expected,
                            "current": game_state.flags.get(flag, False)
                        }
                if missing_flags:
                    missing_conditions["flags"] = missing_flags

        # 检查时间
        if "timestamp" in choice.preconditions:
            if not game_state.check_preconditions({"timestamp": choice.preconditions["timestamp"]}):
                missing_conditions["timestamp"] = {
                    "required": choice.preconditions["timestamp"],
                    "current": game_state.timestamp
                }

        # 返回结果
        if missing_conditions:
            reason = self._format_missing_conditions(missing_conditions)
            return ValidationResult(
                is_valid=False,
                reason=reason,
                missing_preconditions=missing_conditions
            )

        return ValidationResult(is_valid=True)

    def _format_missing_conditions(self, missing: Dict[str, Any]) -> str:
        """格式化缺失条件的描述

        Args:
            missing: 缺失的条件

        Returns:
            str: 描述文本
        """
        parts = []

        if "PR" in missing:
            parts.append(
                f"PR 需要 {missing['PR']['required']}，"
                f"当前 {missing['PR']['current']}"
            )

        if "GR" in missing:
            parts.append(
                f"GR 需要 {missing['GR']['required']}，"
                f"当前 {missing['GR']['current']}"
            )

        if "items" in missing:
            parts.append(
                f"缺少道具：{', '.join(missing['items']['missing'])}"
            )

        if "flags" in missing:
            flags_desc = []
            for flag, info in missing["flags"].items():
                flags_desc.append(
                    f"{flag}={info['required']} (当前 {info['current']})"
                )
            parts.append(f"标志位不满足：{', '.join(flags_desc)}")

        if "timestamp" in missing:
            parts.append(
                f"时间需要 {missing['timestamp']['required']}，"
                f"当前 {missing['timestamp']['current']}"
            )

        return "；".join(parts)

    def extract_intent(self, choice: Choice) -> Intent:
        """提取选项的意图层级

        Args:
            choice: 选项

        Returns:
            Intent: 意图对象
        """
        # 从选项文本和标签推断意图

        # 物理层：选项文本通常直接描述动作
        physical_action = choice.choice_text

        # 心理层：从标签推断动机
        emotional_motivation = self._infer_motivation(choice.tags)

        # 叙事层：从后果推断意义
        narrative_meaning = self._infer_narrative_meaning(choice.consequences)

        # 风险评估
        risk_level = self._assess_risk(choice)

        return Intent(
            physical_action=physical_action,
            emotional_motivation=emotional_motivation,
            narrative_meaning=narrative_meaning,
            original_choice=choice,
            risk_level=risk_level
        )

    def _infer_motivation(self, tags: List[str]) -> str:
        """从标签推断心理动机

        Args:
            tags: 标签列表

        Returns:
            str: 动机描述
        """
        if not tags:
            return "未知动机"

        # 动机关键词映射
        motivation_map = {
            "保守": "寻求安全",
            "激进": "主动对抗",
            "策略": "权衡利弊",
            "遵守手册": "遵循规则",
            "违反手册": "打破常规",
            "调查": "探索未知",
            "逃避": "回避风险",
            "对抗": "直面威胁"
        }

        # 查找匹配的动机
        for tag in tags:
            if tag in motivation_map:
                return motivation_map[tag]

        # 默认返回第一个标签
        return tags[0]

    def _infer_narrative_meaning(self, consequences: Optional[Dict[str, Any]]) -> str:
        """从后果推断叙事意义

        Args:
            consequences: 后果

        Returns:
            str: 叙事意义描述
        """
        if not consequences:
            return "探索性选择"

        # 分析后果类型
        meanings = []

        # PR 变化
        if "PR" in consequences:
            pr_change = str(consequences["PR"])
            if pr_change.startswith("+"):
                meanings.append("深入灵异世界")
            elif pr_change.startswith("-"):
                meanings.append("保持理智")

        # 道具获得
        if "items" in consequences:
            meanings.append("获得关键线索")

        # 标志位
        if "flags" in consequences:
            meanings.append("触发关键事件")

        # 场景切换
        if "current_scene" in consequences:
            meanings.append("剧情推进")

        if meanings:
            return "、".join(meanings)

        return "日常互动"

    def _assess_risk(self, choice: Choice) -> str:
        """评估选项的风险等级

        Args:
            choice: 选项

        Returns:
            str: 风险等级 "low" / "medium" / "high"
        """
        # 根据选项类型初步判断
        if choice.choice_type.value == "critical":
            base_risk = 3
        elif choice.choice_type.value == "normal":
            base_risk = 2
        else:  # micro
            base_risk = 1

        # 根据后果调整
        if choice.consequences:
            # PR 增加 -> 风险增加
            if "PR" in choice.consequences:
                pr_change = str(choice.consequences["PR"])
                if pr_change.startswith("+"):
                    pr_value = int(pr_change.replace("+", ""))
                    if pr_value >= 20:
                        base_risk += 1

            # 消耗道具 -> 风险增加
            if "items" in choice.consequences:
                # 检查是否是移除道具（负面操作）
                # 这里简化处理，假设道具变化都有一定风险
                pass

        # 根据标签调整
        if choice.tags:
            if "高风险" in choice.tags or "激进" in choice.tags:
                base_risk += 1
            elif "保守" in choice.tags or "安全" in choice.tags:
                base_risk -= 1

        # 映射到三级
        base_risk = max(1, min(3, base_risk))

        risk_map = {1: "low", 2: "medium", 3: "high"}
        return risk_map[base_risk]

    # 可选扩展：自由输入式支持

    def parse_free_text(self, user_input: str, game_state: GameState) -> Optional[Intent]:
        """解析自由文本输入（未来扩展）

        Args:
            user_input: 用户自由输入的文本
            game_state: 当前游戏状态

        Returns:
            Intent: 解析出的意图，如果无法解析则返回 None

        Note:
            这是未来的扩展功能，需要 NLU 模块支持
            当前版本仅支持选项式交互
        """
        # TODO: 实现 NLU 解析
        # 1. 使用 LLM 解析用户意图
        # 2. 映射到标准化的 Intent 对象
        # 3. 验证意图是否合法（在世界规则内）

        raise NotImplementedError(
            "自由文本解析功能尚未实现。"
            "当前版本仅支持选项式交互。"
        )


# 工具函数

def validate_choice_batch(
    choices: List[Choice],
    game_state: GameState
) -> Dict[str, ValidationResult]:
    """批量验证选项

    Args:
        choices: 选项列表
        game_state: 游戏状态

    Returns:
        Dict[str, ValidationResult]: choice_id -> 验证结果
    """
    engine = IntentMappingEngine()
    results = {}

    for choice in choices:
        results[choice.choice_id] = engine.validate_choice(choice, game_state)

    return results


def get_available_choices(
    choices: List[Choice],
    game_state: GameState
) -> List[Choice]:
    """获取所有可用的选项

    Args:
        choices: 选项列表
        game_state: 游戏状态

    Returns:
        List[Choice]: 可用的选项列表
    """
    engine = IntentMappingEngine()
    available = []

    for choice in choices:
        result = engine.validate_choice(choice, game_state)
        if result.is_valid:
            available.append(choice)

    return available

