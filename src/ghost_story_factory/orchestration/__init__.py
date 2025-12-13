"""
LangGraph 编排层 (ADR-005)

用 LangGraph 收敛 Agent 编排，保留 LLMClient 为唯一 LLM I/O 通道。

Graph 结构：
    StageDocs → StageSkeleton → StageTree → StageReport

使用方式：
    from ghost_story_factory.orchestration import run_story_pipeline
    result = run_story_pipeline(city, synopsis)
"""

from .graph import run_story_pipeline, create_story_graph

__all__ = ["run_story_pipeline", "create_story_graph"]
