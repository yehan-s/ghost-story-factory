"""多结局系统

实现 GDD 中定义的多个结局：
1. 补完：持有失魂核心 + 播放录音
2. 旁观：无核心 + 播放录音
3. 迷失：未播放录音 + 超时

根据后果树计算最终结局，渲染结局文本和统计数据
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

from .state import GameState


class EndingType(str, Enum):
    """结局类型"""
    COMPLETION = "completion"      # 补完结局
    OBSERVER = "observer"          # 旁观结局
    LOST = "lost"                  # 迷失结局
    TIMEOUT = "timeout"            # 超时结局
    SACRIFICE = "sacrifice"        # 献祭结局（隐藏）
    UNKNOWN = "unknown"            # 未知结局


@dataclass
class EndingCondition:
    """结局条件

    定义触发某个结局所需的条件
    """
    # 必须满足的条件（所有条件必须同时满足）
    required_flags: Dict[str, bool]
    required_items: List[str]

    # 可选条件（至少满足一个）
    optional_flags: Optional[Dict[str, bool]] = None

    # PR/GR/WF 范围
    pr_range: Optional[tuple[int, int]] = None  # (min, max)
    gr_range: Optional[tuple[int, int]] = None
    wf_range: Optional[tuple[int, int]] = None

    # 时间范围
    time_before: Optional[str] = None  # 必须在此时间之前
    time_after: Optional[str] = None   # 必须在此时间之后

    # 特殊条件：后果树中必须包含的选择
    required_choices: Optional[List[str]] = None

    def check(self, game_state: GameState) -> bool:
        """检查条件是否满足

        Args:
            game_state: 游戏状态

        Returns:
            bool: 是否满足条件
        """
        # 检查必需标志位
        for flag, expected in self.required_flags.items():
            if game_state.flags.get(flag) != expected:
                return False

        # 检查必需道具
        for item in self.required_items:
            if item not in game_state.inventory:
                return False

        # 检查可选标志位（至少满足一个）
        if self.optional_flags:
            has_optional = False
            for flag, expected in self.optional_flags.items():
                if game_state.flags.get(flag) == expected:
                    has_optional = True
                    break
            if not has_optional:
                return False

        # 检查 PR 范围
        if self.pr_range:
            min_pr, max_pr = self.pr_range
            if not (min_pr <= game_state.PR <= max_pr):
                return False

        # 检查 GR 范围
        if self.gr_range:
            min_gr, max_gr = self.gr_range
            if not (min_gr <= game_state.GR <= max_gr):
                return False

        # 检查 WF 范围
        if self.wf_range:
            min_wf, max_wf = self.wf_range
            if not (min_wf <= game_state.WF <= max_wf):
                return False

        # 检查时间
        if self.time_before or self.time_after:
            current_time = self._parse_time(game_state.timestamp)

            if self.time_before:
                max_time = self._parse_time(self.time_before)
                if current_time >= max_time:
                    return False

            if self.time_after:
                min_time = self._parse_time(self.time_after)
                if current_time <= min_time:
                    return False

        # 检查后果树中的选择
        if self.required_choices:
            for choice_id in self.required_choices:
                if choice_id not in game_state.consequence_tree:
                    return False

        return True

    @staticmethod
    def _parse_time(time_str: str) -> int:
        """解析时间字符串为分钟数"""
        try:
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        except:
            return 0


@dataclass
class Ending:
    """结局定义"""
    ending_type: EndingType
    title: str
    description: str
    condition: EndingCondition

    # 可选：结局的特殊奖励/成就
    achievements: List[str] = None

    # 优先级（用于多个结局同时满足时的选择）
    priority: int = 0


class EndingSystem:
    """多结局系统

    管理所有结局的定义和判定
    """

    def __init__(self, gdd_content: Optional[str] = None):
        """初始化结局系统

        Args:
            gdd_content: GDD 内容（可选，用于自动解析结局定义）
        """
        self.gdd = gdd_content
        self.endings: Dict[EndingType, Ending] = {}

        # 注册默认结局
        self._register_default_endings()

        # 如果提供了 GDD，尝试解析自定义结局
        if gdd_content:
            self._parse_endings_from_gdd(gdd_content)

    def _register_default_endings(self) -> None:
        """注册默认结局（基于杭州故事的设定）"""
        # 结局 1: 补完
        self.register_ending(Ending(
            ending_type=EndingType.COMPLETION,
            title="【补完结局】",
            description="""
你持有失魂核心，播放了录音。

那些失魂者...终于找到了归宿。
阵眼祭坛的光芒褪去，八口棺材沉入地下。

这座城市的裂缝，被你修补了。
至少，暂时如此。

你走出 B3，迎接黎明。
""",
            condition=EndingCondition(
                required_flags={"录音_已播放": True},
                required_items=["失魂核心"],
                time_before="06:00"
            ),
            achievements=["完美结局", "守护者"],
            priority=100
        ))

        # 结局 2: 旁观
        self.register_ending(Ending(
            ending_type=EndingType.OBSERVER,
            title="【旁观结局】",
            description="""
你播放了录音，但没有核心。

失魂者们听到了呼唤，但无法回归。
他们聚集在你身边，像是在哭泣。

你只是一个见证者。
你看到了真相，但无法改变什么。

那些失魂者仍在游荡。
而你...活了下来。
""",
            condition=EndingCondition(
                required_flags={"录音_已播放": True},
                required_items=[],  # 没有核心
                time_before="06:00"
            ),
            achievements=["见证者"],
            priority=90
        ))

        # 结局 3: 迷失
        self.register_ending(Ending(
            ending_type=EndingType.LOST,
            title="【迷失结局】",
            description="""
共鸣度达到 100%。

你的意识...溶解了。
你感受到八个失魂者的记忆，像潮水般涌来。

你看到了他们的过去：
一个在五楼跳皮球的孩子，
一个在四楼算账的店主，
一个在三楼试衣服的女孩...

你成为了第九个失魂者。

在凌晨 04:44，你会出现在某个楼层，
重复着某个动作，
等待下一个守夜人。
""",
            condition=EndingCondition(
                required_flags={},
                required_items=[],
                pr_range=(100, 100)  # PR 达到 100
            ),
            achievements=["第九个失魂者"],
            priority=80
        ))

        # 结局 4: 超时
        self.register_ending(Ending(
            ending_type=EndingType.TIMEOUT,
            title="【超时结局】",
            description="""
06:00 AM。天亮了。

早班员工陆续到来，商场恢复了生机。
你打卡下班，像往常一样走出大门。

阳光刺眼，你眯起了眼睛。

你回头看了一眼商场的玻璃外墙。
玻璃反射着清晨的阳光，什么都看不清。

但你知道，
今晚发生的一切，都是真的。

你会回来值夜班吗？
""",
            condition=EndingCondition(
                required_flags={},
                required_items=[],
                time_after="06:00"
            ),
            achievements=["幸存者", "逃避"],
            priority=70
        ))

        # 结局 5: 献祭（隐藏结局）
        self.register_ending(Ending(
            ending_type=EndingType.SACRIFICE,
            title="【献祭结局】",
            description="""
你选择了献祭自己。

你站在阵眼祭坛前，看着那八口棺材。
你知道，它们需要一个"锚点"。

你走向祭坛的中心，
那里有一个空位，
一直在等待第九个人。

你躺下，闭上眼睛。

冰冷的感觉包裹着你，
但你的意识却无比清晰。

你成为了新的阵眼。
那八个失魂者，获得了安息。

这座城市的裂缝，被彻底修复了。
代价是，你。

有人会记得你吗？
""",
            condition=EndingCondition(
                required_flags={"祭坛_献祭": True},
                required_items=[],
                required_choices=["献祭_自己"]
            ),
            achievements=["献祭者", "终极守护者", "隐藏结局"],
            priority=110  # 最高优先级
        ))

    def register_ending(self, ending: Ending) -> None:
        """注册一个结局

        Args:
            ending: 结局定义
        """
        self.endings[ending.ending_type] = ending

    def check_ending(self, game_state: GameState) -> Optional[EndingType]:
        """检查是否达成结局

        Args:
            game_state: 游戏状态

        Returns:
            EndingType: 达成的结局类型，如果没有则返回 None
        """
        # 按优先级排序
        sorted_endings = sorted(
            self.endings.values(),
            key=lambda e: e.priority,
            reverse=True
        )

        # 检查每个结局
        for ending in sorted_endings:
            if ending.condition.check(game_state):
                return ending.ending_type

        return None

    def get_ending(self, ending_type: EndingType) -> Optional[Ending]:
        """获取结局定义

        Args:
            ending_type: 结局类型

        Returns:
            Ending: 结局定义
        """
        return self.endings.get(ending_type)

    def render_ending(
        self,
        ending_type: EndingType,
        game_state: GameState
    ) -> str:
        """生成结局文本

        Args:
            ending_type: 结局类型
            game_state: 游戏状态

        Returns:
            str: 完整的结局文本（包含标题、描述、统计）
        """
        ending = self.get_ending(ending_type)
        if not ending:
            ending = self._get_unknown_ending()

        # 构建结局文本
        text = f"\n{'=' * 70}\n"
        text += f"                     {ending.title}\n"
        text += f"{'=' * 70}\n\n"
        text += ending.description
        text += "\n"

        # 添加成就
        if ending.achievements:
            text += "\n**【解锁成就】**\n"
            for achievement in ending.achievements:
                text += f"🏆 {achievement}\n"

        # 添加统计数据
        text += self._render_statistics(game_state)

        text += f"\n{'=' * 70}\n"
        text += "                      感谢游玩！\n"
        text += f"{'=' * 70}\n"

        return text

    def _get_unknown_ending(self) -> Ending:
        """获取未知结局（回退）"""
        return Ending(
            ending_type=EndingType.UNKNOWN,
            title="【未知结局】",
            description="""
你的故事，以一种意想不到的方式结束了。

也许，这就是你选择的结果。
""",
            condition=EndingCondition(
                required_flags={},
                required_items=[]
            )
        )

    def _render_statistics(self, game_state: GameState) -> str:
        """渲染统计数据"""
        stats = "\n**【统计数据】**\n\n"
        stats += f"- 最终 PR：{game_state.PR}/100\n"
        stats += f"- 最终 GR：{game_state.GR}/100\n"
        stats += f"- 最终 WF：{game_state.WF}/10\n"
        stats += f"- 游戏时长：{game_state.timestamp}\n"
        stats += f"- 做出选择：{len(game_state.consequence_tree)} 次\n"
        stats += f"- 获得道具：{len(game_state.inventory)} 个\n"

        if game_state.inventory:
            stats += f"- 最终道具：{', '.join(game_state.inventory)}\n"

        return stats

    def _parse_endings_from_gdd(self, gdd_content: str) -> None:
        """从 GDD 中解析结局定义（可选功能）

        Args:
            gdd_content: GDD 内容

        Note:
            这是一个可选的高级功能，用于从 GDD 文档中自动提取结局定义
            当前版本使用硬编码的默认结局
        """
        # TODO: 实现 GDD 解析逻辑
        # 1. 识别 GDD 中的结局定义部分
        # 2. 解析结局条件
        # 3. 解析结局文本
        # 4. 注册到系统中
        pass


# 工具函数

def create_default_ending_system() -> EndingSystem:
    """创建默认的结局系统"""
    return EndingSystem()


def check_all_endings(game_state: GameState) -> List[EndingType]:
    """检查所有可能达成的结局（用于调试）

    Args:
        game_state: 游戏状态

    Returns:
        List[EndingType]: 所有满足条件的结局
    """
    system = EndingSystem()
    possible_endings = []

    for ending_type, ending in system.endings.items():
        if ending.condition.check(game_state):
            possible_endings.append(ending_type)

    return possible_endings

