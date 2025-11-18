"""
SkeletonGenerator 冒烟测试

目标：
- 在不依赖真实 LLM / 外部 API 的情况下，验证 SkeletonGenerator 能返回
  一个结构合理的 PlotSkeleton 对象。
"""

from typing import Any, Dict

from ghost_story_factory.pregenerator import skeleton_generator as sg
from ghost_story_factory.pregenerator.skeleton_model import PlotSkeleton


class DummyAgent:
    def __init__(self, *args, **kwargs) -> None:
        pass


class DummyTask:
    def __init__(self, *args, **kwargs) -> None:
        pass


class DummyCrew:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def kickoff(self, *args, **kwargs) -> str:
        # 返回一个满足基础结构约束的 PlotSkeleton JSON：
        # - 至少 3 幕；
        # - beats 总数 >= min_main_depth；
        # - leads_to_ending 为 True 的节拍数量 >= target_endings。
        return """
        {
          "title": "测试故事",
          "config": {
            "min_main_depth": 4,
            "target_main_depth": 6,
            "target_endings": 2,
            "max_branches_per_node": 2
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
                  "is_critical_branch_point": false,
                  "leads_to_ending": false,
                  "branches": [
                    {
                      "branch_type": "NORMAL",
                      "max_children": 2,
                      "notes": "测试分支"
                    }
                  ]
                },
                {
                  "id": "A1_B2",
                  "act_index": 1,
                  "beat_type": "setup",
                  "tension_level": 4,
                  "is_critical_branch_point": false,
                  "leads_to_ending": false,
                  "branches": [
                    {
                      "branch_type": "NORMAL",
                      "max_children": 2,
                      "notes": "测试分支 2"
                    }
                  ]
                }
              ]
            },
            {
              "index": 2,
              "label": "Act II",
              "beats": [
                {
                  "id": "A2_B1",
                  "act_index": 2,
                  "beat_type": "escalation",
                  "tension_level": 6,
                  "is_critical_branch_point": true,
                  "leads_to_ending": false,
                  "branches": [
                    {
                      "branch_type": "CRITICAL",
                      "max_children": 2,
                      "notes": "关键分支"
                    }
                  ]
                },
                {
                  "id": "A2_B2",
                  "act_index": 2,
                  "beat_type": "escalation",
                  "tension_level": 7,
                  "is_critical_branch_point": false,
                  "leads_to_ending": true,
                  "branches": [
                    {
                      "branch_type": "NORMAL",
                      "max_children": 2,
                      "notes": "结局入口 1"
                    }
                  ]
                }
              ]
            },
            {
              "index": 3,
              "label": "Act III",
              "beats": [
                {
                  "id": "A3_B1",
                  "act_index": 3,
                  "beat_type": "climax",
                  "tension_level": 9,
                  "is_critical_branch_point": true,
                  "leads_to_ending": true,
                  "branches": [
                    {
                      "branch_type": "CRITICAL",
                      "max_children": 2,
                      "notes": "结局入口 2"
                    }
                  ]
                },
                {
                  "id": "A3_B2",
                  "act_index": 3,
                  "beat_type": "aftermath",
                  "tension_level": 4,
                  "is_critical_branch_point": false,
                  "leads_to_ending": false,
                  "branches": []
                }
              ]
            }
          ],
          "metadata": {
            "city": "测试城"
          }
        }
        """


def test_skeleton_generator_smoke(monkeypatch):
    """验证 SkeletonGenerator 在 fake Crew 下能返回合法骨架"""

    # 避免真实 LLM 初始化
    monkeypatch.setattr(sg, "_build_default_llm", lambda: object())
    # 替换 Agent / Task / Crew 为 Dummy 实现
    monkeypatch.setattr(sg, "Agent", DummyAgent)
    monkeypatch.setattr(sg, "Task", DummyTask)
    monkeypatch.setattr(sg, "Crew", DummyCrew)
    # 避免依赖真实 prompt 文件
    monkeypatch.setattr(sg, "_load_prompt", lambda: "")

    gen = sg.SkeletonGenerator(city="测试城")
    skeleton = gen.generate(
        title="测试故事",
        synopsis="这里是一个测试故事简介",
        lore_v2_text="这里是 Lore v2 文本",
        main_story_text="这里是主线故事文本",
    )

    assert isinstance(skeleton, PlotSkeleton)
    assert skeleton.title == "测试故事"
    assert skeleton.num_acts >= 3
    assert skeleton.num_beats >= skeleton.config.min_main_depth
    assert skeleton.num_ending_beats >= skeleton.config.target_endings
    assert skeleton.metadata.get("city") == "测试城"
