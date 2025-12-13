"""RuntimeResponseGenerator 的 LLMClient 路径单元测试

目标：
- 默认优先走 LLMClient（可观测、可控超时）；
- LLMClient 失败时能兜底返回文本，不让主流程崩。

注意：测试中使用 fake client，避免真实网络调用。
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from ghost_story_factory.engine.response import RuntimeResponseGenerator
from ghost_story_factory.engine.state import GameState
from ghost_story_factory.engine.choices import Choice, ChoiceType


class DummyLLMClient:
    def __init__(self, result: str = "OK", raise_error: bool = False):
        self.result = result
        self.raise_error = raise_error
        self.last_kwargs: Dict[str, Any] = {}
        self.default_model = "dummy-model"

    def call(self, **kwargs):
        self.last_kwargs = dict(kwargs)
        if self.raise_error:
            raise RuntimeError("boom")
        return self.result


def test_response_uses_llmclient_by_default(monkeypatch):
    """默认应优先走 LLMClient，并使用 RESPONSE_MAX_TOKENS。"""
    dummy = DummyLLMClient(result="LLM_TEXT")

    import ghost_story_factory.engine.response as resp

    monkeypatch.setenv("USE_LLMCLIENT_RESPONSE", "1")
    monkeypatch.setenv("RESPONSE_MAX_TOKENS", "123")

    monkeypatch.setattr(resp, "_USE_LLM_CLIENT", True)
    monkeypatch.setattr(resp, "create_llm_client", lambda: dummy)
    monkeypatch.setattr(resp, "_CREWAI_AVAILABLE", False)

    gen = RuntimeResponseGenerator(gdd_content="GDD", lore_content="LORE", main_story="")

    state = GameState(PR=10, GR=0, WF=0, current_scene="S1", timestamp="00:10")
    choice = Choice(
        choice_id="S1_A",
        choice_text="继续调查",
        choice_type=ChoiceType.NORMAL,
        consequences={"timestamp": "+5min"},
    )

    text = gen.generate_response(choice, state, apply_consequences=False)
    assert text.strip() == "LLM_TEXT"

    # 关键：max_tokens 应使用 env 配置
    assert dummy.last_kwargs.get("max_tokens") == 123


def test_response_falls_back_to_offline_text_when_llm_fails(monkeypatch):
    """LLMClient 调用失败时，必须兜底返回本地文本。"""
    dummy = DummyLLMClient(result="", raise_error=True)

    import ghost_story_factory.engine.response as resp

    monkeypatch.setenv("USE_LLMCLIENT_RESPONSE", "1")
    monkeypatch.setattr(resp, "_USE_LLM_CLIENT", True)
    monkeypatch.setattr(resp, "create_llm_client", lambda: dummy)
    monkeypatch.setattr(resp, "_CREWAI_AVAILABLE", False)

    gen = RuntimeResponseGenerator(gdd_content="GDD", lore_content="LORE", main_story="")

    state = GameState(PR=10, GR=0, WF=0, current_scene="S1", timestamp="00:10")
    choice = Choice(
        choice_id="S1_A",
        choice_text="继续调查",
        choice_type=ChoiceType.NORMAL,
        consequences={"timestamp": "+5min"},
    )

    text = gen.generate_response(choice, state, apply_consequences=False)
    assert "继续调查" in text
