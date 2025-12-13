"""
LangGraph 状态定义 (ADR-005)

定义在 LangGraph 节点之间传递的状态结构。
"""

from typing import TypedDict, Optional, Dict, Any, List
from dataclasses import dataclass


class StoryPipelineState(TypedDict, total=False):
    """故事生成流水线的全局状态

    这个状态在所有 LangGraph 节点之间共享和传递。
    """

    # ========== 输入参数 ==========
    city: str                          # 城市名称
    synopsis_title: str                # 故事标题
    synopsis_text: str                 # 故事简介
    synopsis_protagonist: str          # 主角名称
    synopsis_location: str             # 故事场景
    synopsis_duration: int             # 预计时长（分钟）
    test_mode: bool                    # 测试模式标志

    # ========== Stage 1: Documents ==========
    gdd_content: Optional[str]         # GDD 内容
    lore_content: Optional[str]        # Lore v2 内容
    main_story: Optional[str]          # 主线故事
    docs_stage_status: str             # "pending" | "success" | "failed"
    docs_error: Optional[str]          # 错误信息

    # ========== Stage 2: Skeleton ==========
    skeleton: Optional[Dict[str, Any]] # PlotSkeleton dict 形式
    skeleton_stage_status: str         # "pending" | "success" | "failed" | "skipped"
    skeleton_error: Optional[str]      # 错误信息

    # ========== Stage 3: Tree ==========
    characters: List[Dict[str, Any]]   # 角色列表
    dialogue_trees: Dict[str, Any]     # 对话树（按角色名索引）
    tree_stage_status: str             # "pending" | "success" | "failed"
    tree_error: Optional[str]          # 错误信息

    # ========== Stage 4: Report ==========
    story_id: Optional[int]            # 数据库 ID
    metadata: Optional[Dict[str, Any]] # 元数据
    report: Optional[Dict[str, Any]]   # 结构报告
    report_stage_status: str           # "pending" | "success" | "failed"
    report_error: Optional[str]        # 错误信息

    # ========== 导演上下文 (M2) ==========
    director_context: Dict[str, Any]   # recent_choices, recent_responses, recent_beats

    # ========== 遥测 ==========
    telemetry: Dict[str, Any]          # 节点级遥测数据
    json_metrics: Dict[str, Any]       # JSON 稳定性指标（M2 增强）


@dataclass
class NodeTelemetry:
    """节点遥测数据结构"""
    node_name: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # "running" | "success" | "failed"
    error: Optional[str] = None

    # LLM 调用统计
    llm_calls: int = 0
    llm_successes: int = 0
    llm_failures: int = 0
    total_tokens: int = 0

    # JSON 稳定性指标 (M2 增强)
    json_total_calls: int = 0
    json_ok_first_try: int = 0
    json_ok_after_fix: int = 0
    json_salvaged: int = 0
    json_failures: int = 0

    def merge_json_metrics(self, metrics: Dict[str, int]) -> None:
        """合并来自生成器的 JSON 指标"""
        self.json_total_calls += metrics.get("total_calls", 0)
        self.json_ok_first_try += metrics.get("ok_first_try", 0)
        self.json_ok_after_fix += metrics.get("ok_after_fix", 0)
        self.json_salvaged += metrics.get("salvaged", 0)
        self.json_failures += metrics.get("failures", 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_name": self.node_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": (self.end_time - self.start_time) if self.end_time else None,
            "status": self.status,
            "error": self.error,
            "llm_calls": self.llm_calls,
            "llm_successes": self.llm_successes,
            "llm_failures": self.llm_failures,
            "total_tokens": self.total_tokens,
            # JSON 稳定性指标 (M2)
            "json_metrics": {
                "total_calls": self.json_total_calls,
                "ok_first_try": self.json_ok_first_try,
                "ok_after_fix": self.json_ok_after_fix,
                "salvaged": self.json_salvaged,
                "failures": self.json_failures,
            },
        }


def create_initial_state(
    city: str,
    synopsis_title: str,
    synopsis_text: str,
    synopsis_protagonist: str,
    synopsis_location: str,
    synopsis_duration: int = 20,
    test_mode: bool = False,
    gdd_path: Optional[str] = None,
    lore_path: Optional[str] = None,
    main_story_path: Optional[str] = None,
) -> StoryPipelineState:
    """创建初始状态

    Args:
        city: 城市名称
        synopsis_title: 故事标题
        synopsis_text: 故事简介
        synopsis_protagonist: 主角名称
        synopsis_location: 故事场景
        synopsis_duration: 预计时长
        test_mode: 测试模式
        gdd_path: GDD 文件路径（可选，用于缓存命中）
        lore_path: Lore 文件路径（可选）
        main_story_path: 主线故事路径（可选）

    Returns:
        初始化的 StoryPipelineState
    """
    # 尝试加载缓存文件
    gdd_content = None
    lore_content = None
    main_story = None

    from pathlib import Path

    if gdd_path and Path(gdd_path).exists():
        gdd_content = Path(gdd_path).read_text(encoding='utf-8')
    if lore_path and Path(lore_path).exists():
        lore_content = Path(lore_path).read_text(encoding='utf-8')
    if main_story_path and Path(main_story_path).exists():
        main_story = Path(main_story_path).read_text(encoding='utf-8')

    return StoryPipelineState(
        # 输入
        city=city,
        synopsis_title=synopsis_title,
        synopsis_text=synopsis_text,
        synopsis_protagonist=synopsis_protagonist,
        synopsis_location=synopsis_location,
        synopsis_duration=synopsis_duration,
        test_mode=test_mode,

        # Stage 1
        gdd_content=gdd_content,
        lore_content=lore_content,
        main_story=main_story,
        docs_stage_status="pending",
        docs_error=None,

        # Stage 2
        skeleton=None,
        skeleton_stage_status="pending",
        skeleton_error=None,

        # Stage 3
        characters=[],
        dialogue_trees={},
        tree_stage_status="pending",
        tree_error=None,

        # Stage 4
        story_id=None,
        metadata=None,
        report=None,
        report_stage_status="pending",
        report_error=None,

        # 导演上下文 (M2)
        director_context={
            "recent_choices": [],
            "recent_responses": [],
            "recent_beats": [],
        },

        # 遥测
        telemetry={},
        json_metrics={},
    )
