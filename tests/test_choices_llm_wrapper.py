"""
ChoicePointsGenerator LLM 封装层测试

目标：
- 验证 _extract_llm_text 能够从不同形式的 CrewAI 返回对象中提取文本；
- 验证 _call_llm_with_retry 在解析失败时仍然返回字符串，而不是抛异常。
"""

from typing import Any

from ghost_story_factory.engine.choices import ChoicePointsGenerator


class _DummyResult:
    """模拟 CrewAI 返回对象，带 raw_output 属性。"""

    def __init__(self, text: str) -> None:
        self.raw_output = text


class _DummyTaskResult:
    """模拟带 tasks_output 列表的结果结构。"""

    class _Inner:
        def __init__(self, text: str) -> None:
            self.raw = text

    def __init__(self, text: str) -> None:
        self.tasks_output = [self._Inner(text)]


def _make_generator() -> ChoicePointsGenerator:
    """构造一个最小可用的 ChoicePointsGenerator（不依赖真实 LLM）。"""
    return ChoicePointsGenerator(
        gdd_content="GDD",
        lore_content="LORE",
        main_story="STORY",
    )


def test_extract_llm_text_from_raw_output():
    gen = _make_generator()
    result = _DummyResult("hello-json")

    text = gen._extract_llm_text(result)  # type: ignore[arg-type]
    assert text == "hello-json"


def test_extract_llm_text_from_tasks_output():
    gen = _make_generator()
    result = _DummyTaskResult("world-json")

    text = gen._extract_llm_text(result)  # type: ignore[arg-type]
    assert text == "world-json"


def test_parse_result_updates_metrics_on_success_first_try():
    """首次解析成功时，应只增加 ok_first_try 计数。"""
    gen = _make_generator()

    text = """
    {
      "scene_id": "S1",
      "choices": [
        {
          "id": "A",
          "text": "选项A",
          "immediate_consequences": {
            "resonance": "+1"
          }
        }
      ]
    }
    """

    data = gen._parse_result(text)
    assert data.get("scene_id") == "S1"
    assert isinstance(data.get("choices"), list)
    metrics = gen.get_json_metrics()
    assert metrics["total_calls"] == 1
    assert metrics["ok_first_try"] == 1
    assert metrics["ok_after_fix"] == 0
    assert metrics["salvaged"] == 0
    assert metrics["failures"] == 0


def test_parse_result_salvages_choices_from_truncated_json():
    """
    当顶层 JSON 不完整但 choices 数组中的对象是完整的时，
    _parse_result 应该通过 salvage 路径挽救可用的 choices。
    """
    gen = _make_generator()

    # 顶层缺少收尾的 ]}，模拟日志中的半残 JSON；
    # 第一个 choice 使用 immediate_\\nconsequences 以验证键名修复逻辑。
    broken = (
        '{ "scene_id": "S1", "choices": ['
        '{"id":"A","text":"选项A","immediate_\\nconsequences":{"resonance":"+5"}},'
        '{"id":"B","text":"选项B","immediate_consequences":{"resonance":"+3"}},'
        '{"id":"C","text":"选项C"}'
    )

    data = gen._parse_result(broken)
    choices = data.get("choices") or []

    # salvage 之后应至少保留多个 choice，且 scene_id 被识别出来
    assert data.get("scene_id") == "S1"
    assert isinstance(choices, list)
    assert len(choices) >= 2

    # 校验 JSON 遥测：一次调用，全靠 salvage 成功
    metrics = gen.get_json_metrics()
    assert metrics["total_calls"] == 1
    assert metrics["ok_first_try"] == 0
    # 可能经过 raw_decode 或直接 salvage，这里至少保证 salvage>0 且无最终失败
    assert metrics["salvaged"] >= 1
    assert metrics["failures"] == 0
