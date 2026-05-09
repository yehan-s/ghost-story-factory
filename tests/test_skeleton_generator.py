"""
SkeletonGenerator 冒烟测试

目标：
- 在不依赖真实 LLM / 外部 API 的情况下，验证 SkeletonGenerator 能返回
  一个结构合理的 PlotSkeleton 对象。
- 测试覆盖两种模式：LLMClient 模式和 CrewAI 回退模式
"""

from typing import Any, Dict

from ghost_story_factory.pregenerator import skeleton_generator as sg
from ghost_story_factory.pregenerator.skeleton_model import PlotSkeleton


# 固定 JSON 响应（用于两种模式）
DUMMY_SKELETON_JSON = """
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
          "location_id": "S1_security_room",
          "npc_ids": ["g273"],
          "event_slots": ["hub", "npc_meet"],
          "asset_cues": {
            "background": "security_room",
            "sprite": "g273",
            "sfx": ["radio_noise"]
          },
          "sandbox_role": "hub",
          "revisit_hooks": ["ending_seen:E_TRUTH"],
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


class DummyLLMClient:
    """模拟 LLMClient 用于测试"""

    def __init__(self, *args, **kwargs) -> None:
        self.provider = "dummy"

    def call(self, prompt: str, model=None, max_tokens=None, temperature=None) -> str:
        """返回固定的骨架 JSON"""
        return DUMMY_SKELETON_JSON


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
        """返回固定的骨架 JSON（与 DummyLLMClient 一致）"""
        return DUMMY_SKELETON_JSON.strip()


def test_skeleton_generator_with_llm_client(monkeypatch):
    """验证 SkeletonGenerator 在 LLMClient 模式下能返回合法骨架"""

    # 强制使用 LLMClient 模式
    monkeypatch.setattr(sg, "_USE_LLM_CLIENT", True)
    monkeypatch.setattr(sg, "LLMClient", DummyLLMClient)
    monkeypatch.setattr(sg, "_build_default_llm", lambda: DummyLLMClient())
    monkeypatch.setattr(sg, "_load_prompt", lambda: "")

    gen = sg.SkeletonGenerator(city="测试城")

    # 验证使用了 LLMClient 模式
    assert gen.use_llm_client is True

    skeleton = gen.generate(
        title="测试故事",
        synopsis="这里是一个测试故事简介",
        lore_v2_text="这里是 Lore v2 文本",
        main_story_text="这里是主线故事文本",
    )

    # 验证返回的骨架结构
    assert isinstance(skeleton, PlotSkeleton)
    assert skeleton.title == "测试故事"
    assert skeleton.num_acts >= 3
    assert skeleton.num_beats >= skeleton.config.min_main_depth
    assert skeleton.num_ending_beats >= skeleton.config.target_endings
    assert skeleton.metadata.get("city") == "测试城"
    beat = skeleton.beats[0]
    assert beat.location_id == "S1_security_room"
    assert beat.npc_ids == ["g273"]
    assert beat.event_slots == ["hub", "npc_meet"]
    assert beat.asset_cues["background"] == "security_room"
    assert beat.sandbox_role == "hub"
    assert beat.revisit_hooks == ["ending_seen:E_TRUTH"]


def test_skeleton_generator_smoke(monkeypatch):
    """验证 SkeletonGenerator 在 Crew 回退模式下能返回合法骨架"""

    # 强制禁用 LLMClient，使用 Crew 回退模式
    monkeypatch.setattr(sg, "_USE_LLM_CLIENT", False)
    monkeypatch.setattr(sg, "_CREWAI_AVAILABLE", True)
    monkeypatch.setattr(sg, "_build_default_llm", lambda: object())

    # Monkeypatch skeleton_generator 模块中的 CrewAI 类
    monkeypatch.setattr(sg, "Agent", DummyAgent)
    monkeypatch.setattr(sg, "Task", DummyTask)
    monkeypatch.setattr(sg, "Crew", DummyCrew)
    monkeypatch.setattr(sg, "_load_prompt", lambda: "")

    gen = sg.SkeletonGenerator(city="测试城")

    # 验证使用了 Crew 模式
    assert gen.use_llm_client is False

    skeleton = gen.generate(
        title="测试故事",
        synopsis="这里是一个测试故事简介",
        lore_v2_text="这里是 Lore v2 文本",
        main_story_text="这里是主线故事文本",
    )

    # 验证返回的骨架结构
    assert isinstance(skeleton, PlotSkeleton)
    assert skeleton.title == "测试故事"
    assert skeleton.num_acts >= 3
    assert skeleton.num_beats >= skeleton.config.min_main_depth
    assert skeleton.num_ending_beats >= skeleton.config.target_endings
    assert skeleton.metadata.get("city") == "测试城"


def test_skeleton_generator_json_parsing_robustness(monkeypatch):
    """验证 SkeletonGenerator 的 JSON 解析鲁棒性"""

    class DummyLLMClientWithMarkdown:
        """返回被 markdown 代码块包裹的 JSON"""

        def __init__(self, *args, **kwargs):
            self.provider = "dummy"

        def call(self, *args, **kwargs):
            return f"""
            这里是一些额外的文本。

            ```json
            {DUMMY_SKELETON_JSON.strip()}
            ```

            还有更多文本。
            """

    monkeypatch.setattr(sg, "_USE_LLM_CLIENT", True)
    monkeypatch.setattr(sg, "LLMClient", DummyLLMClientWithMarkdown)
    monkeypatch.setattr(sg, "_build_default_llm", lambda: DummyLLMClientWithMarkdown())
    monkeypatch.setattr(sg, "_load_prompt", lambda: "")

    gen = sg.SkeletonGenerator(city="测试城")
    skeleton = gen.generate(
        title="测试故事",
        synopsis="测试",
        lore_v2_text="测试",
        main_story_text="测试",
    )

    # 即使有 markdown 包裹，也能正确解析
    assert isinstance(skeleton, PlotSkeleton)
    assert skeleton.title == "测试故事"
