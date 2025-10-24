"""
游戏时长验证器

确保生成的对话树满足最小游戏时长要求（>= 15 分钟）
"""

from typing import Dict, Any, List, Optional


class TimeValidator:
    """游戏时长验证器"""

    def __init__(self, seconds_per_choice: int = 15):
        """
        初始化验证器

        Args:
            seconds_per_choice: 每个选择的平均耗时（秒）
        """
        self.seconds_per_choice = seconds_per_choice
        self.min_duration_minutes = 15  # 最小游戏时长（分钟）

    def estimate_playtime(self, dialogue_tree: Dict[str, Any]) -> float:
        """
        估算游戏时长

        Args:
            dialogue_tree: 对话树

        Returns:
            预计游戏时长（分钟）
        """
        # 找到主线路径（最长路径）
        main_path = self._find_longest_path(dialogue_tree)

        # 计算选择点数量（减去根节点）
        choice_count = len(main_path) - 1

        # 估算时长
        estimated_seconds = choice_count * self.seconds_per_choice
        estimated_minutes = estimated_seconds / 60

        return estimated_minutes

    def _find_longest_path(self, dialogue_tree: Dict[str, Any]) -> List[str]:
        """
        查找最长路径（BFS/DFS）

        Args:
            dialogue_tree: 对话树

        Returns:
            最长路径的节点ID列表
        """
        if not dialogue_tree or "root" not in dialogue_tree:
            return []

        longest_path = []

        def dfs(node_id: str, current_path: List[str]):
            nonlocal longest_path

            current_path = current_path + [node_id]

            # 更新最长路径
            if len(current_path) > len(longest_path):
                longest_path = current_path.copy()

            # 继续遍历子节点
            node = dialogue_tree.get(node_id)
            if node and "children" in node:
                for child_id in node["children"]:
                    if child_id in dialogue_tree:
                        dfs(child_id, current_path)

        dfs("root", [])
        return longest_path

    def get_main_path_depth(self, dialogue_tree: Dict[str, Any]) -> int:
        """
        获取主线路径深度

        Args:
            dialogue_tree: 对话树

        Returns:
            主线深度
        """
        main_path = self._find_longest_path(dialogue_tree)
        return len(main_path) - 1 if main_path else 0

    def validate(self, dialogue_tree: Dict[str, Any]) -> bool:
        """
        验证对话树是否满足最小时长要求

        Args:
            dialogue_tree: 对话树

        Returns:
            是否通过验证
        """
        estimated_duration = self.estimate_playtime(dialogue_tree)

        if estimated_duration < self.min_duration_minutes:
            print(f"❌ 游戏时长不足：{estimated_duration:.1f} 分钟 < {self.min_duration_minutes} 分钟")
            return False

        print(f"✅ 游戏时长验证通过：{estimated_duration:.1f} 分钟 >= {self.min_duration_minutes} 分钟")
        return True

    def ensure_minimum_depth(
        self,
        dialogue_tree: Dict[str, Any],
        min_depth: int = 15
    ) -> bool:
        """
        确保对话树深度满足要求

        Args:
            dialogue_tree: 对话树
            min_depth: 最小深度

        Returns:
            是否满足要求
        """
        main_path_depth = self.get_main_path_depth(dialogue_tree)

        if main_path_depth < min_depth:
            print(f"❌ 主线深度不足：{main_path_depth} < {min_depth}")
            return False

        print(f"✅ 主线深度验证通过：{main_path_depth} >= {min_depth}")
        return True

    def get_validation_report(self, dialogue_tree: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取详细的验证报告

        Args:
            dialogue_tree: 对话树

        Returns:
            验证报告
        """
        main_path = self._find_longest_path(dialogue_tree)
        main_path_depth = len(main_path) - 1 if main_path else 0
        estimated_duration = self.estimate_playtime(dialogue_tree)

        total_nodes = len(dialogue_tree)

        # 统计结局节点
        ending_nodes = [
            node_id for node_id, node in dialogue_tree.items()
            if node.get("is_ending", False)
        ]

        return {
            "total_nodes": total_nodes,
            "main_path_depth": main_path_depth,
            "main_path_length": len(main_path),
            "estimated_duration_minutes": round(estimated_duration, 1),
            "ending_count": len(ending_nodes),
            "passes_duration_check": estimated_duration >= self.min_duration_minutes,
            "passes_depth_check": main_path_depth >= 15
        }

