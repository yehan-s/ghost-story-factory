"""游戏状态管理器

管理核心游戏变量：PR、GR、WF、时间戳、道具、标志位等
支持状态查询、更新、回滚、持久化
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import re


@dataclass
class GameState:
    """游戏状态

    管理所有游戏运行时状态，包括：
    - 核心数值：PR（个人共鸣度）、GR（全局共鸣度）、WF（世界疲劳值）
    - 游戏进度：当前场景、时间戳
    - 玩家资源：道具栏、标志位、后果树
    """

    # 核心变量
    PR: int = 5          # 个人共鸣度 (0-100)
    GR: int = 0          # 全局共鸣度 (0-100)
    WF: int = 0          # 世界疲劳值 (0-10)

    # 游戏进度
    current_scene: str = "S1"
    timestamp: str = "00:00"  # 游戏内时间 (00:00-04:00)

    # 玩家资源
    inventory: List[str] = field(default_factory=list)
    flags: Dict[str, bool] = field(default_factory=dict)
    consequence_tree: List[str] = field(default_factory=list)

    def update(self, changes: Dict[str, Any]) -> None:
        """应用状态变化并校验

        Args:
            changes: 状态变化字典，支持的格式：
                - PR/GR/WF: 绝对值 (50) 或相对值 ("+5", "-10")
                - inventory: 添加道具列表 ["道具1", "道具2"]
                - flags: 更新标志位 {"flag1": True}
                - timestamp: 更新时间 "02:30"
                - current_scene: 切换场景 "S3"

        Example:
            state.update({
                "PR": "+5",
                "inventory": ["暗号:36-3=33"],
                "flags": {"失魂者_已拍照": True}
            })
        """
        for key, value in changes.items():
            if key in ["PR", "GR", "WF"]:
                # 数值变化（支持 +5, -10 等相对值）
                if isinstance(value, str) and value[:1] in ['+', '-','＋','－']:
                    current = getattr(self, key)
                    delta = self._parse_signed_int(value)
                    new_value = current + delta

                    # 校验边界
                    if key in ["PR", "GR"]:
                        new_value = max(0, min(100, new_value))
                    elif key == "WF":
                        new_value = max(0, min(10, new_value))

                    setattr(self, key, new_value)
                else:
                    # 绝对值（健壮解析）
                    setattr(self, key, self._parse_signed_int(value, absolute=True))

            elif key == "inventory":
                # 添加道具（去重）
                if isinstance(value, list):
                    for item in value:
                        if item not in self.inventory:
                            self.inventory.append(item)

            elif key == "flags":
                # 更新标志位
                if isinstance(value, dict):
                    self.flags.update(value)

            elif key in ["timestamp", "current_scene"]:
                # 直接更新
                setattr(self, key, value)

            elif key == "consequence_tree":
                # 添加后果树节点
                if isinstance(value, list):
                    self.consequence_tree.extend(value)

    def check_preconditions(self, conditions: Dict[str, Any]) -> bool:
        """检查前置条件是否满足

        Args:
            conditions: 前置条件字典，支持的格式：
                - PR/GR/WF: 比较表达式 ">=40", "<60", "==50"
                - items: 所需道具列表 ["道具1", "道具2"]
                - flags: 所需标志位 {"flag1": True}
                - timestamp: 时间范围 "<=03:00"

        Returns:
            bool: 是否满足所有前置条件

        Example:
            state.check_preconditions({
                "PR": ">=40",
                "items": ["暗号:36-3=33"],
                "flags": {"失魂者_已拍照": True}
            })
        """
        for key, value in conditions.items():
            if key in ["PR", "GR", "WF"]:
                # 数值比较
                if not self._check_comparison(getattr(self, key), value):
                    return False

            elif key == "items":
                # 道具检查
                if isinstance(value, list):
                    if not all(item in self.inventory for item in value):
                        return False

            elif key == "flags":
                # 标志位检查
                if isinstance(value, dict):
                    for flag, expected in value.items():
                        if self.flags.get(flag) != expected:
                            return False

            elif key == "timestamp":
                # 时间检查
                if not self._check_time_condition(value):
                    return False

        return True

    def _check_comparison(self, current_value: int, condition: str) -> bool:
        """检查数值比较条件

        Args:
            current_value: 当前值
            condition: 比较条件，如 ">=40", "<60", "==50"

        Returns:
            bool: 是否满足条件
        """
        match = re.match(r'([><=]+)(\d+)', str(condition))
        if not match:
            # 如果没有比较符，默认为相等
            try:
                return current_value == int(str(condition))
            except Exception:
                return False

        operator, threshold = match.groups()
        threshold = int(threshold)

        if operator == ">=":
            return current_value >= threshold
        elif operator == "<=":
            return current_value <= threshold
        elif operator == ">":
            return current_value > threshold
        elif operator == "<":
            return current_value < threshold
        elif operator == "==":
            return current_value == threshold
        else:
            return False

    @staticmethod
    def _parse_signed_int(value: Any, absolute: bool = False) -> int:
        """健壮解析带符号的整数字符串，容忍全角/噪声/小数。

        规则：
        - 归一化 NFKC（全角转半角），去除不必要空白
        - 优先提取浮点数（带符号），再四舍五入为 int
        - 若存在 '+'/'-' 但仅有小数 < 1，则按 +/-1 处理
        - 若完全无法解析：返回 0（不破坏用户空间）
        """
        import unicodedata, re
        s = str(value)
        s = unicodedata.normalize("NFKC", s).strip()
        # 提取第一个带符号的浮点或整数
        m = re.search(r'[\+\-]?\d+(?:\.\d+)?', s)
        if m:
            num_str = m.group(0)
            try:
                num_float = float(num_str)
                # 绝对值场景允许负数吗？保留原符号，按四舍五入
                parsed = int(round(num_float))
                # 特殊：+0.x / -0.x 归一到 +/-1 以体现趋势
                if parsed == 0 and (num_float > 0):
                    return 1
                if parsed == 0 and (num_float < 0):
                    return -1
                return parsed
            except Exception:
                pass
        # 无法提取数字，按符号给最小步长
        if s.startswith(('+', '＋')):
            return 1
        if s.startswith(('-', '－')):
            return -1
        # 绝对值且完全无数字：视为 0（不变）
        return 0

    def _check_time_condition(self, condition: str) -> bool:
        """检查时间条件

        Args:
            condition: 时间条件，如 "<=03:00", ">01:30"

        Returns:
            bool: 是否满足时间条件
        """
        match = re.match(r'([><=]+)(\d{2}:\d{2})', str(condition))
        if not match:
            return self.timestamp == condition

        operator, time_str = match.groups()

        # 转换为分钟数比较
        def time_to_minutes(t: str) -> int:
            h, m = map(int, t.split(':'))
            return h * 60 + m

        current_minutes = time_to_minutes(self.timestamp)
        threshold_minutes = time_to_minutes(time_str)

        if operator == ">=":
            return current_minutes >= threshold_minutes
        elif operator == "<=":
            return current_minutes <= threshold_minutes
        elif operator == ">":
            return current_minutes > threshold_minutes
        elif operator == "<":
            return current_minutes < threshold_minutes
        elif operator == "==":
            return current_minutes == threshold_minutes
        else:
            return False

    def save(self, filepath: str) -> None:
        """保存状态到文件

        Args:
            filepath: 保存路径，如 "saves/杭州_S4_02:30.save"
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'GameState':
        """从文件加载状态

        Args:
            filepath: 存档路径

        Returns:
            GameState: 加载的游戏状态

        Raises:
            FileNotFoundError: 存档文件不存在
            json.JSONDecodeError: 存档文件格式错误
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return asdict(self)

    def __str__(self) -> str:
        """字符串表示（用于调试）"""
        return (
            f"GameState(PR={self.PR}, GR={self.GR}, WF={self.WF}, "
            f"scene={self.current_scene}, time={self.timestamp}, "
            f"items={len(self.inventory)}, flags={len(self.flags)})"
        )

