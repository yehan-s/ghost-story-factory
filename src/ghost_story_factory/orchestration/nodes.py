"""
LangGraph 节点定义 (ADR-005)

每个节点封装现有模块的功能，并添加节点级遥测。
节点通过 LLMClient 进行 LLM 调用（不直接发 HTTP）。
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

from .state import StoryPipelineState, NodeTelemetry
from ..utils.logging_utils import get_logger

logger, _ = get_logger()


# ============================================================
# Stage 1: Documents
# ============================================================

def stage_docs(state: StoryPipelineState) -> StoryPipelineState:
    """Stage 1: 生成或加载文档（GDD、Lore、主线故事）

    复用现有的文档生成逻辑，但通过 LangGraph 状态传递。
    """
    telemetry = NodeTelemetry(node_name="stage_docs", start_time=time.time())
    logger.info("[LangGraph] stage_docs: 开始")

    try:
        city = state["city"]
        title = state["synopsis_title"]

        # 如果已有缓存，直接使用
        gdd_content = state.get("gdd_content")
        lore_content = state.get("lore_content")
        main_story = state.get("main_story")

        # 尝试自动命中 deliverables 缓存
        if not all([gdd_content, lore_content, main_story]):
            gdd_content, lore_content, main_story = _try_load_cached_docs(
                city, title, gdd_content, lore_content, main_story
            )

        # 如果仍有缺失，使用简化生成
        if gdd_content is None:
            gdd_content = _generate_simple_gdd(state)
        if lore_content is None:
            lore_content = _generate_simple_lore(state)
        if main_story is None:
            main_story = _generate_simple_main_story(state)

        telemetry.status = "success"
        telemetry.end_time = time.time()
        logger.info(f"[LangGraph] stage_docs: 完成 (耗时 {telemetry.end_time - telemetry.start_time:.2f}s)")

        # 更新状态
        state["gdd_content"] = gdd_content
        state["lore_content"] = lore_content
        state["main_story"] = main_story
        state["docs_stage_status"] = "success"
        state["telemetry"]["stage_docs"] = telemetry.to_dict()

        return state

    except Exception as e:
        telemetry.status = "failed"
        telemetry.error = str(e)
        telemetry.end_time = time.time()
        logger.exception(f"[LangGraph] stage_docs: 失败 - {e}")

        state["docs_stage_status"] = "failed"
        state["docs_error"] = str(e)
        state["telemetry"]["stage_docs"] = telemetry.to_dict()

        return state


def _try_load_cached_docs(
    city: str,
    title: str,
    gdd: Optional[str],
    lore: Optional[str],
    story: Optional[str]
) -> tuple:
    """尝试从 deliverables 目录加载缓存文档"""
    import re

    try:
        base_dir = Path(f"deliverables/程序-{city}")
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', title)
        title_dir = base_dir / safe_title

        def _read_if_missing(current, path, label):
            if current is not None:
                return current
            if path.exists():
                logger.info(f"[LangGraph] 自动命中缓存 {label}: {path}")
                return path.read_text(encoding='utf-8')
            return None

        if base_dir.exists():
            if title_dir.exists():
                gdd = _read_if_missing(gdd, title_dir / f"{city}_{safe_title}_gdd.md", "GDD")
                lore = _read_if_missing(lore, title_dir / f"{city}_{safe_title}_lore_v2.md", "Lore v2")
                story = _read_if_missing(story, title_dir / f"{city}_{safe_title}_story.md", "主线")

            gdd = _read_if_missing(gdd, base_dir / f"{city}_gdd.md", "GDD")
            lore = _read_if_missing(lore, base_dir / f"{city}_lore_v2.md", "Lore v2")
            story = _read_if_missing(story, base_dir / f"{city}_story.md", "主线")

    except Exception as e:
        logger.warning(f"[LangGraph] 缓存加载失败: {e}")

    return gdd, lore, story


def _generate_simple_gdd(state: StoryPipelineState) -> str:
    """生成简化版 GDD"""
    return f"""# 游戏设计文档 - {state['synopsis_title']}

## 基本信息
- 城市：{state['city']}
- 主角：{state['synopsis_protagonist']}
- 场景：{state['synopsis_location']}

## 游戏机制
- PR（恐惧值）：0-100
- GR（真相值）：0-100
- WF（世界熟悉度）：0-100

## 场景
- S1：{state['synopsis_location']}（起始场景）
"""


def _generate_simple_lore(state: StoryPipelineState) -> str:
    """生成简化版 Lore"""
    return f"""# 世界观规则 - {state['synopsis_title']}

## 核心规则
1. 恐怖氛围优先
2. 逻辑自洽
3. 伏笔回收

## 故事背景
{state['synopsis_text']}
"""


def _generate_simple_main_story(state: StoryPipelineState) -> str:
    """生成简化版主线故事"""
    return f"""# 主线故事 - {state['synopsis_title']}

{state['synopsis_text']}

主角：{state['synopsis_protagonist']}
场景：{state['synopsis_location']}
"""


# ============================================================
# Stage 2: Skeleton
# ============================================================

def stage_skeleton(state: StoryPipelineState) -> StoryPipelineState:
    """Stage 2: 生成故事骨架（PlotSkeleton）

    使用 SkeletonGenerator + LLMClient 生成结构化骨架。
    """
    telemetry = NodeTelemetry(node_name="stage_skeleton", start_time=time.time())
    logger.info("[LangGraph] stage_skeleton: 开始")

    # 检查前置条件
    if state.get("docs_stage_status") != "success":
        logger.warning("[LangGraph] stage_skeleton: 跳过（docs 阶段未成功）")
        state["skeleton_stage_status"] = "skipped"
        state["skeleton_error"] = "前置阶段失败"
        return state

    # 检查是否禁用骨架模式
    use_plot_skeleton = os.getenv("USE_PLOT_SKELETON", "1")
    if use_plot_skeleton == "0":
        logger.info("[LangGraph] stage_skeleton: 跳过（USE_PLOT_SKELETON=0）")
        state["skeleton_stage_status"] = "skipped"
        state["skeleton"] = None
        return state

    try:
        from ..pregenerator.skeleton_generator import SkeletonGenerator

        generator = SkeletonGenerator(city=state["city"])
        skeleton = generator.generate(
            title=state["synopsis_title"],
            synopsis=state["synopsis_text"],
            lore_v2_text=state.get("lore_content", ""),
            main_story_text=state.get("main_story", ""),
        )

        telemetry.status = "success"
        telemetry.llm_calls = 1
        telemetry.llm_successes = 1
        telemetry.end_time = time.time()

        logger.info(
            f"[LangGraph] stage_skeleton: 完成 "
            f"(acts={skeleton.num_acts}, beats={skeleton.num_beats}, "
            f"耗时 {telemetry.end_time - telemetry.start_time:.2f}s)"
        )

        state["skeleton"] = skeleton.to_dict()
        state["skeleton_stage_status"] = "success"
        state["telemetry"]["stage_skeleton"] = telemetry.to_dict()

        return state

    except Exception as e:
        telemetry.status = "failed"
        telemetry.error = str(e)
        telemetry.llm_calls = 1
        telemetry.llm_failures = 1
        telemetry.end_time = time.time()

        logger.exception(f"[LangGraph] stage_skeleton: 失败 - {e}")

        # 骨架失败不阻断，回退到非 guided 模式
        state["skeleton"] = None
        state["skeleton_stage_status"] = "failed"
        state["skeleton_error"] = str(e)
        state["telemetry"]["stage_skeleton"] = telemetry.to_dict()

        return state


# ============================================================
# Stage 3: Tree
# ============================================================

def stage_tree(state: StoryPipelineState) -> StoryPipelineState:
    """Stage 3: 生成对话树

    使用 DialogueTreeBuilder + LLMClient 生成完整对话树。
    内部调用 ChoicePointsGenerator 和 RuntimeResponseGenerator。

    M2 增强：收集 JSON 稳定性指标 + 导演上下文
    """
    telemetry = NodeTelemetry(node_name="stage_tree", start_time=time.time())
    logger.info("[LangGraph] stage_tree: 开始")

    # 检查前置条件
    if state.get("docs_stage_status") != "success":
        logger.warning("[LangGraph] stage_tree: 跳过（docs 阶段未成功）")
        state["tree_stage_status"] = "skipped"
        state["tree_error"] = "前置阶段失败"
        return state

    try:
        from ..pregenerator.tree_builder import DialogueTreeBuilder
        from ..pregenerator.skeleton_model import PlotSkeleton

        # 重建 PlotSkeleton 对象（如果存在）
        plot_skeleton = None
        if state.get("skeleton"):
            plot_skeleton = PlotSkeleton.from_dict(state["skeleton"])

        # 提取角色
        characters = _extract_characters(state)
        state["characters"] = characters

        # 测试模式调整
        test_mode = state.get("test_mode", False)
        if test_mode:
            max_depth = int(os.getenv("MAX_DEPTH", "12"))
            min_main_path = int(os.getenv("MIN_MAIN_PATH_DEPTH", "6"))
            characters = characters[:2]  # 测试模式只生成 2 个角色
        else:
            max_depth = int(os.getenv("MAX_DEPTH", "50"))
            min_main_path = int(os.getenv("MIN_MAIN_PATH_DEPTH", "30"))

        # 骨架模式下使用骨架配置的深度
        if plot_skeleton is not None:
            try:
                sk_min_depth = int(plot_skeleton.config.min_main_depth)
                if sk_min_depth > 0:
                    min_main_path = sk_min_depth
            except Exception:
                pass

        dialogue_trees = {}
        last_director_context = None

        for char in characters:
            char_name = char["name"]
            logger.info(f"[LangGraph] stage_tree: 生成角色 '{char_name}' 的对话树...")

            checkpoint_path = f"checkpoints/{state['city']}_{char_name}_tree.json"

            tree_builder = DialogueTreeBuilder(
                city=state["city"],
                synopsis=state["synopsis_text"],
                gdd_content=state.get("gdd_content", ""),
                lore_content=state.get("lore_content", ""),
                main_story=state.get("main_story", ""),
                test_mode=test_mode,
                plot_skeleton=plot_skeleton,
            )

            tree = tree_builder.generate_tree(
                max_depth=max_depth,
                min_main_path_depth=min_main_path,
                checkpoint_path=checkpoint_path,
            )

            dialogue_trees[char_name] = tree
            telemetry.llm_calls += 1
            telemetry.llm_successes += 1

            # M2: 收集 JSON 稳定性指标
            try:
                if hasattr(tree_builder, "choice_generator") and tree_builder.choice_generator:
                    json_metrics = tree_builder.choice_generator.get_json_metrics()
                    telemetry.merge_json_metrics(json_metrics)
                    logger.info(
                        f"[LangGraph] stage_tree: '{char_name}' JSON 指标: "
                        f"total={json_metrics.get('total_calls', 0)}, "
                        f"ok={json_metrics.get('ok_first_try', 0)}, "
                        f"salvaged={json_metrics.get('salvaged', 0)}, "
                        f"failures={json_metrics.get('failures', 0)}"
                    )
            except Exception as e:
                logger.debug(f"[LangGraph] stage_tree: JSON 指标收集失败: {e}")

            # M2: 保存导演上下文（用于诊断）
            try:
                if hasattr(tree_builder, "director_context"):
                    last_director_context = tree_builder.director_context.copy()
            except Exception:
                pass

            logger.info(f"[LangGraph] stage_tree: '{char_name}' 完成 ({len(tree)} 节点)")

        telemetry.status = "success"
        telemetry.end_time = time.time()

        # M2: 汇总 JSON 稳定性指标到 state
        state["json_metrics"] = telemetry.to_dict().get("json_metrics", {})

        # M2: 保存最后一个 builder 的导演上下文
        if last_director_context:
            state["director_context"] = last_director_context

        logger.info(
            f"[LangGraph] stage_tree: 全部完成 "
            f"({len(dialogue_trees)} 角色, 耗时 {telemetry.end_time - telemetry.start_time:.2f}s)"
        )

        # M2: 日志记录 JSON 稳定性汇总
        json_summary = telemetry.to_dict().get("json_metrics", {})
        if json_summary.get("total_calls", 0) > 0:
            logger.info(
                f"[LangGraph] stage_tree: JSON 稳定性汇总: "
                f"total={json_summary['total_calls']}, "
                f"ok_first={json_summary['ok_first_try']}, "
                f"salvaged={json_summary['salvaged']}, "
                f"failures={json_summary['failures']}"
            )

        state["dialogue_trees"] = dialogue_trees
        state["tree_stage_status"] = "success"
        state["telemetry"]["stage_tree"] = telemetry.to_dict()

        return state

    except Exception as e:
        telemetry.status = "failed"
        telemetry.error = str(e)
        telemetry.end_time = time.time()

        logger.exception(f"[LangGraph] stage_tree: 失败 - {e}")

        state["tree_stage_status"] = "failed"
        state["tree_error"] = str(e)
        state["telemetry"]["stage_tree"] = telemetry.to_dict()

        return state


def _extract_characters(state: StoryPipelineState) -> list:
    """提取角色列表"""
    protagonist_name = state["synopsis_protagonist"]

    characters = [
        {
            "name": protagonist_name,
            "is_protagonist": True,
            "description": f"{state['synopsis_title']} - {protagonist_name}的故事"
        }
    ]

    return characters


# ============================================================
# Stage 4: Report
# ============================================================

def stage_report(state: StoryPipelineState) -> StoryPipelineState:
    """Stage 4: 生成报告并保存到数据库

    填充节点文本、生成结构报告、保存到 SQLite。
    """
    telemetry = NodeTelemetry(node_name="stage_report", start_time=time.time())
    logger.info("[LangGraph] stage_report: 开始")

    # 检查前置条件
    if state.get("tree_stage_status") != "success":
        logger.warning("[LangGraph] stage_report: 跳过（tree 阶段未成功）")
        state["report_stage_status"] = "skipped"
        state["report_error"] = "前置阶段失败"
        return state

    try:
        from ..pregenerator.text_filler import NodeTextFiller
        from ..pregenerator.story_report import build_story_report
        from ..pregenerator.skeleton_model import PlotSkeleton
        from ..pregenerator.time_validator import TimeValidator
        from ..database import DatabaseManager

        dialogue_trees = state["dialogue_trees"]
        characters = state["characters"]

        # 重建 PlotSkeleton（如果存在）
        plot_skeleton = None
        if state.get("skeleton"):
            plot_skeleton = PlotSkeleton.from_dict(state["skeleton"])

        # 骨架模式下填充节点文本和生成报告
        per_char_reports = {}
        if plot_skeleton is not None:
            filler = NodeTextFiller(skeleton=plot_skeleton)

            for char in characters:
                char_name = char["name"]
                tree = dialogue_trees.get(char_name)
                if not isinstance(tree, dict):
                    continue

                dialogue_trees[char_name] = filler.fill(tree)

                try:
                    per_char_reports[char_name] = build_story_report(
                        dialogue_tree=dialogue_trees[char_name],
                        skeleton=plot_skeleton,
                    )
                except Exception as e:
                    logger.warning(f"[LangGraph] 报告生成失败 (角色={char_name}): {e}")

        # 保存到数据库
        db = DatabaseManager()

        main_tree = dialogue_trees[characters[0]["name"]]
        validator = TimeValidator()
        report = validator.get_validation_report(main_tree)

        total_nodes = sum(len(tree) for tree in dialogue_trees.values())

        metadata = {
            "estimated_duration": report["estimated_duration_minutes"],
            "total_nodes": total_nodes,
            "max_depth": report["main_path_depth"],
            "cost": 0.0,
            "total_tokens": 0,
            "generation_time": 0,
            "model": os.getenv("KIMI_MODEL_RESPONSE", "kimi-k2-0905-preview"),
            "pipeline": "langgraph",  # 标记使用 LangGraph 流水线
        }

        # M2: 添加 JSON 稳定性指标到 metadata
        json_metrics = state.get("json_metrics", {})
        if json_metrics:
            metadata["json_stability"] = json_metrics
            logger.info(
                f"[LangGraph] stage_report: JSON 稳定性指标已写入 metadata: "
                f"total={json_metrics.get('total_calls', 0)}, "
                f"success_rate={_calc_json_success_rate(json_metrics):.1f}%"
            )

        # M2: 添加遥测摘要到 metadata
        telemetry_summary = state.get("telemetry", {})
        if telemetry_summary:
            metadata["telemetry"] = telemetry_summary

        # 添加结构报告
        if plot_skeleton is not None and per_char_reports:
            main_report = per_char_reports.get(characters[0]["name"])
            if main_report:
                verdict = main_report.get("verdict", {}) or {}
                quality_state = "accepted" if verdict.get("passes") else "warning"
                metadata["structure"] = {
                    "report": main_report,
                    "quality_state": quality_state,
                }

        story_id = db.save_story(
            city_name=state["city"],
            title=state["synopsis_title"],
            synopsis=state["synopsis_text"],
            characters=characters,
            dialogue_trees=dialogue_trees,
            metadata=metadata,
        )

        db.close()

        telemetry.status = "success"
        telemetry.end_time = time.time()

        logger.info(
            f"[LangGraph] stage_report: 完成 "
            f"(story_id={story_id}, 耗时 {telemetry.end_time - telemetry.start_time:.2f}s)"
        )

        state["story_id"] = story_id
        state["metadata"] = metadata
        state["report"] = per_char_reports.get(characters[0]["name"]) if per_char_reports else None
        state["report_stage_status"] = "success"
        state["telemetry"]["stage_report"] = telemetry.to_dict()

        return state

    except Exception as e:
        telemetry.status = "failed"
        telemetry.error = str(e)
        telemetry.end_time = time.time()

        logger.exception(f"[LangGraph] stage_report: 失败 - {e}")

        state["report_stage_status"] = "failed"
        state["report_error"] = str(e)
        state["telemetry"]["stage_report"] = telemetry.to_dict()

        return state


# ============================================================
# M2: 辅助函数
# ============================================================

def _calc_json_success_rate(metrics: Dict[str, Any]) -> float:
    """计算 JSON 解析成功率"""
    total = metrics.get("total_calls", 0)
    if total == 0:
        return 100.0
    ok = metrics.get("ok_first_try", 0) + metrics.get("ok_after_fix", 0)
    salvaged = metrics.get("salvaged", 0)
    return (ok + salvaged) / total * 100
