"""
LangGraph 图定义 (ADR-005)

定义故事生成的 StateGraph：
    StageDocs → StageSkeleton → StageTree → StageReport
"""

import os
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from .state import StoryPipelineState, create_initial_state
from .nodes import stage_docs, stage_skeleton, stage_tree, stage_report
from ..utils.logging_utils import get_logger

logger, _ = get_logger()


def create_story_graph() -> StateGraph:
    """创建故事生成的 LangGraph StateGraph

    Graph 结构：
        START → stage_docs → stage_skeleton → stage_tree → stage_report → END

    Returns:
        编译后的 StateGraph
    """
    # 创建 StateGraph
    workflow = StateGraph(StoryPipelineState)

    # 添加节点
    workflow.add_node("stage_docs", stage_docs)
    workflow.add_node("stage_skeleton", stage_skeleton)
    workflow.add_node("stage_tree", stage_tree)
    workflow.add_node("stage_report", stage_report)

    # 定义边（线性流程）
    workflow.set_entry_point("stage_docs")
    workflow.add_edge("stage_docs", "stage_skeleton")
    workflow.add_edge("stage_skeleton", "stage_tree")
    workflow.add_edge("stage_tree", "stage_report")
    workflow.add_edge("stage_report", END)

    # 编译图
    app = workflow.compile()

    return app


def run_story_pipeline(
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
) -> Dict[str, Any]:
    """运行 LangGraph 故事生成流水线

    这是 LangGraph 路径的主入口。

    Args:
        city: 城市名称
        synopsis_title: 故事标题
        synopsis_text: 故事简介
        synopsis_protagonist: 主角名称
        synopsis_location: 故事场景
        synopsis_duration: 预计时长（分钟）
        test_mode: 测试模式
        gdd_path: GDD 文件路径（可选）
        lore_path: Lore 文件路径（可选）
        main_story_path: 主线故事路径（可选）

    Returns:
        最终状态（包含 story_id、metadata、telemetry 等）
    """
    logger.info(f"[LangGraph] 启动流水线: city={city}, title={synopsis_title}")

    # 创建初始状态
    initial_state = create_initial_state(
        city=city,
        synopsis_title=synopsis_title,
        synopsis_text=synopsis_text,
        synopsis_protagonist=synopsis_protagonist,
        synopsis_location=synopsis_location,
        synopsis_duration=synopsis_duration,
        test_mode=test_mode,
        gdd_path=gdd_path,
        lore_path=lore_path,
        main_story_path=main_story_path,
    )

    # 创建并运行图
    app = create_story_graph()
    final_state = app.invoke(initial_state)

    # 打印遥测摘要
    _print_telemetry_summary(final_state)

    # 检查最终状态
    if final_state.get("report_stage_status") == "success":
        logger.info(f"[LangGraph] 流水线成功完成: story_id={final_state.get('story_id')}")
    else:
        failed_stage = _find_failed_stage(final_state)
        logger.error(f"[LangGraph] 流水线失败: stage={failed_stage}")

    return final_state


def _print_telemetry_summary(state: StoryPipelineState) -> None:
    """打印遥测摘要"""
    telemetry = state.get("telemetry", {})

    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║              📊 LangGraph 流水线遥测摘要                         ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    total_duration = 0

    for stage_name in ["stage_docs", "stage_skeleton", "stage_tree", "stage_report"]:
        stage_data = telemetry.get(stage_name, {})
        status = stage_data.get("status", "未执行")
        duration = stage_data.get("duration_seconds")
        error = stage_data.get("error")

        if duration:
            total_duration += duration
            duration_str = f"{duration:.2f}s"
        else:
            duration_str = "-"

        status_icon = {
            "success": "✅",
            "failed": "❌",
            "skipped": "⏭️",
            "running": "🔄",
        }.get(status, "❓")

        print(f"  {status_icon} {stage_name}: {status} ({duration_str})")
        if error:
            print(f"      └─ Error: {error[:80]}...")

    print()
    print(f"  总耗时: {total_duration:.2f}s")
    print()

    # 最终状态
    if state.get("story_id"):
        print(f"  📦 story_id: {state['story_id']}")
    if state.get("metadata"):
        meta = state["metadata"]
        print(f"  📊 节点数: {meta.get('total_nodes', 0)}")
        print(f"  📊 主线深度: {meta.get('max_depth', 0)}")
        print(f"  📊 预计时长: {meta.get('estimated_duration', 0)} 分钟")

    print()


def _find_failed_stage(state: StoryPipelineState) -> str:
    """找到第一个失败的阶段"""
    for stage in ["docs", "skeleton", "tree", "report"]:
        status_key = f"{stage}_stage_status"
        if state.get(status_key) == "failed":
            return f"stage_{stage}"
    return "unknown"


# ============================================================
# 开关：选择使用 LangGraph 还是旧路径
# ============================================================

def should_use_langgraph() -> bool:
    """检查是否应该使用 LangGraph 流水线

    通过环境变量 USE_LANGGRAPH_PIPELINE 控制：
        - "1" 或 "true": 使用 LangGraph
        - "0" 或 "false" 或未设置: 使用旧路径

    Returns:
        是否使用 LangGraph
    """
    value = os.getenv("USE_LANGGRAPH_PIPELINE", "0").lower()
    return value in ("1", "true", "yes")
