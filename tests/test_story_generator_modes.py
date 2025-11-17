"""
StoryGeneratorWithRetry 模式切换测试

目标：
- 验证 USE_PLOT_SKELETON=0 时不会调用 SkeletonGenerator，完全走 v3 兼容路径；
- 验证 USE_PLOT_SKELETON=1 时会调用 SkeletonGenerator，并触发 NodeTextFiller + story_report 流程。
"""

from typing import Any, Dict, List

import pytest

from ghost_story_factory.pregenerator.synopsis_generator import StorySynopsis
from ghost_story_factory.pregenerator import story_generator as sg
from ghost_story_factory.pregenerator.skeleton_model import PlotSkeleton


def _make_dummy_synopsis() -> StorySynopsis:
    """构造一个最小可用的 StorySynopsis"""
    return StorySynopsis(
        title="测试故事",
        synopsis="这里是一段测试故事简介。",
        protagonist="测试主角",
        location="测试地点",
        estimated_duration=20,
    )


def _patch_common_lightweight(monkeypatch) -> Dict[str, Any]:
    """
    为 StoryGeneratorWithRetry 打一层“减负”补丁，避免测试时跑真实流水线。

    返回一个 dict 用于存储调用过程中的关键信息。
    """
    captured: Dict[str, Any] = {}

    # 跳过交互确认
    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_prompt_continue",
        lambda self, msg: None,
    )

    # 文档生成：直接返回固定文本
    def fake_generate_documents(self, gdd_path, lore_path, main_story_path):
        return ("GDD", "Lore", "Main story")

    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_generate_documents",
        fake_generate_documents,
    )

    # 世界书预分析：不做任何事
    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_preflight_analyze_worldbook",
        lambda self, lore: None,
    )

    # 角色列表：固定为一个主角
    def fake_extract_characters(self, main_story: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": self.synopsis.protagonist,
                "is_protagonist": True,
                "description": "测试主角描述",
            }
        ]

    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_extract_characters",
        fake_extract_characters,
    )

    # 检查点相关：全部禁用
    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_load_character_checkpoint",
        lambda self: None,
    )
    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_save_character_checkpoint",
        lambda self, *args, **kwargs: None,
    )
    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_cleanup_all_checkpoints",
        lambda self, chars: None,
    )

    # 元数据计算：返回一个简单标记
    def fake_calculate_metadata(self, main_tree, all_trees):
        captured["metadata_input_main_tree"] = main_tree
        captured["metadata_input_all_trees"] = all_trees
        return {"dummy_meta": True}

    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_calculate_metadata",
        fake_calculate_metadata,
    )

    # 成功摘要：不输出
    monkeypatch.setattr(
        sg.StoryGeneratorWithRetry,
        "_print_success_summary",
        lambda self, metadata: None,
    )

    # TreeBuilder：记录传入的 plot_skeleton，并返回一个最小对话树
    class DummyTreeBuilder:
        def __init__(
            self,
            city: str,
            synopsis: str,
            gdd_content: str,
            lore_content: str,
            main_story: str,
            test_mode: bool,
            plot_skeleton,
        ) -> None:
            captured["tree_builder_plot_skeleton"] = plot_skeleton
            captured["tree_builder_test_mode"] = test_mode

        def generate_tree(
            self,
            max_depth: int,
            min_main_path_depth: int,
            checkpoint_path: str,
        ):
            captured["tree_builder_args"] = {
                "max_depth": max_depth,
                "min_main_path_depth": min_main_path_depth,
                "checkpoint_path": checkpoint_path,
            }
            # 最小树：一个 root 节点
            return {"root": {"id": "root", "depth": 0, "narrative": ""}}

    monkeypatch.setattr(sg, "DialogueTreeBuilder", DummyTreeBuilder)

    # DatabaseManager：不写真实数据库，只记录参数
    class DummyDB:
        def __init__(self) -> None:
            pass

        def save_story(
            self,
            city_name: str,
            title: str,
            synopsis: str,
            characters,
            dialogue_trees,
            metadata,
        ) -> int:
            captured["db_city_name"] = city_name
            captured["db_title"] = title
            captured["db_characters"] = characters
            captured["db_dialogue_trees"] = dialogue_trees
            captured["db_metadata"] = metadata
            return 42

        def close(self) -> None:
            captured["db_closed"] = True

    monkeypatch.setattr(sg, "DatabaseManager", DummyDB)

    return captured


def test_story_generator_uses_v3_when_skeleton_disabled(monkeypatch):
    """当 USE_PLOT_SKELETON=0 时，不应调用 SkeletonGenerator，且 TreeBuilder 收到的 plot_skeleton 为 None。"""

    captured = _patch_common_lightweight(monkeypatch)

    # 显式关闭骨架模式
    monkeypatch.setenv("USE_PLOT_SKELETON", "0")

    # 如果 SkeletonGenerator 被调用，立即失败
    class FailSkeletonGenerator:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("SkeletonGenerator 应在 USE_PLOT_SKELETON=0 时完全不被调用")

    monkeypatch.setattr(sg, "SkeletonGenerator", FailSkeletonGenerator)

    # 额外保险：若 NodeTextFiller / build_story_report 被使用，同样视为错误
    class FailFiller:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("NodeTextFiller 不应在 v3 回退路径中被调用")

    def fail_story_report(*args, **kwargs):
        raise AssertionError("build_story_report 不应在 v3 回退路径中被调用")

    monkeypatch.setattr(sg, "NodeTextFiller", FailFiller)
    monkeypatch.setattr(sg, "build_story_report", fail_story_report)

    synopsis = _make_dummy_synopsis()
    gen = sg.StoryGeneratorWithRetry(
        city="测试城",
        synopsis=synopsis,
        test_mode=True,
        multi_character=False,
    )

    result = gen.generate_full_story()

    # 基本结果检查
    assert result["story_id"] == 42
    assert result["title"] == synopsis.title
    assert isinstance(result["metadata"], dict)

    # 确认 TreeBuilder 在 v3 模式下收到的是 None 骨架
    assert captured.get("tree_builder_plot_skeleton") is None


def test_story_generator_uses_v4_pipeline_when_enabled(monkeypatch):
    """当 USE_PLOT_SKELETON=1 时，应调用 SkeletonGenerator，并触发 NodeTextFiller + story_report。"""

    captured = _patch_common_lightweight(monkeypatch)

    # 开启骨架模式（默认即为 1，这里显式设置以便测试清晰）
    monkeypatch.setenv("USE_PLOT_SKELETON", "1")

    # Stub SkeletonGenerator，返回一个最小 PlotSkeleton
    class DummySkeletonGenerator:
        def __init__(self, city: str) -> None:
            captured["skeleton_city"] = city

        def generate(
            self,
            title: str,
            synopsis: str,
            lore_v2_text: str,
            main_story_text: str,
        ) -> PlotSkeleton:
            captured["skeleton_generate_called"] = {
                "title": title,
                "synopsis": synopsis,
            }
            data = {
                "title": title,
                "config": {
                    "min_main_depth": 3,
                    "target_main_depth": 5,
                    "target_endings": 1,
                    "max_branches_per_node": 1,
                },
                "acts": [
                    {
                        "index": 1,
                        "label": "Act I",
                        "beats": [
                            {
                                "id": "A1_B1",
                                "act_index": 1,
                                "beat_type": "setup",
                                "tension_level": 3,
                                "is_critical_branch_point": False,
                                "leads_to_ending": False,
                                "branches": [
                                    {
                                        "branch_type": "NORMAL",
                                        "max_children": 1,
                                        "notes": "测试分支",
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "metadata": {"city": "测试城"},
            }
            return PlotSkeleton.from_dict(data)

    monkeypatch.setattr(sg, "SkeletonGenerator", DummySkeletonGenerator)

    # 记录 NodeTextFiller 与 build_story_report 的调用
    calls: Dict[str, Any] = {"fills": [], "reports": []}

    class DummyFiller:
        def __init__(self, skeleton) -> None:
            calls["filler_skeleton"] = skeleton

        def fill(self, dialogue_tree: Dict[str, Any]) -> Dict[str, Any]:
            calls["fills"].append(dialogue_tree)
            # 标记已填充
            for node in dialogue_tree.values():
                node["narrative"] = node.get("narrative", "") + "[filled]"
            return dialogue_tree

    def dummy_story_report(dialogue_tree: Dict[str, Any], skeleton: PlotSkeleton) -> Dict[str, Any]:
        calls["reports"].append((dialogue_tree, skeleton))
        return {
            "tree_metrics": {"passes_depth_check": True, "passes_duration_check": True, "passes_endings_check": True},
            "skeleton_metrics": {},
            "verdict": {"passes": True, "depth_ok": True, "duration_ok": True, "endings_ok": True},
        }

    monkeypatch.setattr(sg, "NodeTextFiller", DummyFiller)
    monkeypatch.setattr(sg, "build_story_report", dummy_story_report)

    synopsis = _make_dummy_synopsis()
    gen = sg.StoryGeneratorWithRetry(
        city="测试城",
        synopsis=synopsis,
        test_mode=True,
        multi_character=False,
    )

    result = gen.generate_full_story()

    # 基本结果检查
    assert result["story_id"] == 42
    assert result["title"] == synopsis.title

    # SkeletonGenerator 应被调用一次
    assert "skeleton_generate_called" in captured
    # TreeBuilder 应收到非 None 的骨架（v4 guided 模式）
    assert captured.get("tree_builder_plot_skeleton") is not None

    # NodeTextFiller / story_report 应至少各调用一次
    assert len(calls["fills"]) >= 1
    assert len(calls["reports"]) >= 1

    # 数据库收到的对话树应已被填充
    db_trees = captured.get("db_dialogue_trees") or {}
    main_tree = db_trees.get(synopsis.protagonist)
    assert isinstance(main_tree, dict)
    # root 节点 narrative 应包含我们标记的 “[filled]”
    assert "[filled]" in main_tree["root"]["narrative"]


def test_story_generator_stage_docs_skips_tree_and_db(monkeypatch):
    """stage='docs' 时，只生成文档，不应触发 Skeleton/TreeBuilder/DB。"""

    captured = _patch_common_lightweight(monkeypatch)

    # SkeletonGenerator 若被调用则视为错误
    class FailSkeletonGenerator:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("SkeletonGenerator 不应在 stage=docs 被调用")

    monkeypatch.setenv("USE_PLOT_SKELETON", "1")
    monkeypatch.setattr(sg, "SkeletonGenerator", FailSkeletonGenerator)

    synopsis = _make_dummy_synopsis()
    gen = sg.StoryGeneratorWithRetry(
        city="测试城",
        synopsis=synopsis,
        test_mode=True,
        multi_character=False,
    )

    result = gen.generate_full_story(stage="docs")

    assert result["stage"] == "docs"
    assert result["city"] == "测试城"
    assert result["title"] == synopsis.title
    assert "gdd" in result and "lore" in result and "main_story" in result

    # TreeBuilder 与 DB 都不应被触发
    assert "tree_builder_plot_skeleton" not in captured
    assert "db_city_name" not in captured


def test_story_generator_stage_skeleton_runs_without_tree(monkeypatch):
    """stage='skeleton' 时，应生成骨架，但不进入 TreeBuilder/DB。"""

    captured = _patch_common_lightweight(monkeypatch)

    # Dummy SkeletonGenerator：返回最小骨架，同时记录调用
    class DummySkeletonGenerator:
        def __init__(self, city: str) -> None:
            captured["skeleton_city_stage"] = city

        def generate(self, title: str, synopsis: str, lore_v2_text: str, main_story_text: str) -> PlotSkeleton:
            captured["skeleton_generate_stage"] = {
                "title": title,
                "synopsis": synopsis,
            }
            data = {
                "title": title,
                "config": {
                    "min_main_depth": 3,
                    "target_main_depth": 5,
                    "target_endings": 1,
                    "max_branches_per_node": 1,
                },
                "acts": [
                    {
                        "index": 1,
                        "label": "Act I",
                        "beats": [
                            {
                                "id": "A1_B1",
                                "act_index": 1,
                                "beat_type": "setup",
                                "tension_level": 3,
                                "is_critical_branch_point": False,
                                "leads_to_ending": False,
                                "branches": [],
                            }
                        ],
                    }
                ],
                "metadata": {"city": "测试城"},
            }
            return PlotSkeleton.from_dict(data)

    monkeypatch.setenv("USE_PLOT_SKELETON", "1")
    monkeypatch.setattr(sg, "SkeletonGenerator", DummySkeletonGenerator)

    synopsis = _make_dummy_synopsis()
    gen = sg.StoryGeneratorWithRetry(
        city="测试城",
        synopsis=synopsis,
        test_mode=True,
        multi_character=False,
    )

    result = gen.generate_full_story(stage="skeleton")

    assert result["stage"] == "skeleton"
    assert result["city"] == "测试城"
    assert result["title"] == synopsis.title
    assert result.get("skeleton") is not None

    # SkeletonGenerator 应被调用
    assert "skeleton_generate_stage" in captured
    # TreeBuilder 与 DB 仍不应被触发
    assert "tree_builder_plot_skeleton" not in captured
    assert "db_city_name" not in captured
