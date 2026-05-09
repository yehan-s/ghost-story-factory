"""Pass 16 — TUI presenter 边界测试。"""

from __future__ import annotations


class _Save:
    """最小存档替身。"""

    def __init__(self):
        self.data = {
            "foreshadows_seen": {"story": ["fs_a"]},
            "foreshadows_resolved": {"story": []},
        }


def _state(**overrides):
    """构造最小 State。"""
    from ghost_story_factory.v5.player import State

    initial = {
        "flags": {},
        "inv": [],
        "visited_landmarks": [],
        "skipped_landmarks": [],
        "puzzle_pieces": [],
        "character": "G-273",
    }
    initial.update(overrides)
    return State(initial)


def _tree():
    """构造最小树。"""
    return {
        "foreshadows": {
            "fs_a": {
                "title": "井口[旧声]",
                "summary_locked": "还差一段记录。",
            }
        }
    }


def test_presenter_choice_label_escapes_and_uses_badges(monkeypatch):
    """选择标签由 presenter 负责,不回退到 CLI 后缀。"""
    from ghost_story_factory.v7.tui_presenter import format_choice_option_label

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    line = format_choice_option_label(
        1,
        {"text": "查看[档案]", "effects": {"stay": True, "PR": 1}},
    )

    assert r"查看\[档案\]" in line
    assert "[cyan]〈观察〉[/]" in line
    assert "[red]〈心境波动〉[/]" in line
    assert "〔观察 · 心境波动〕" not in line


def test_presenter_status_lines_do_not_leak_internal_flags():
    """状态页 presenter 不能泄露内部 flag key。"""
    from ghost_story_factory.v7.tui_presenter import format_tui_status_lines

    state = _state(
        flags={"know.secret": True, "oneshot.live_streaming": True},
        visited_landmarks=["S1"],
    )
    body = "\n".join(format_tui_status_lines(_tree(), _Save(), "story", state))

    assert "路线账本" in body
    assert "档案索引" in body
    assert r"井口\[旧声\]" in body
    assert "know.secret" not in body
    assert "oneshot.live_streaming" not in body


def test_presenter_transition_lines_are_standalone(monkeypatch):
    """过门反馈只依赖 choice 和地标表,不需要 Textual App 实例。"""
    from ghost_story_factory.v7.tui_presenter import format_transition_lines

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    lines = format_transition_lines(
        {"text": "走向[S1]", "effects": {"PR": 1}},
        ["S1"],
        [{"id": "S1", "short": "湖边[一号]", "place": "断桥"}],
    )
    body = "\n".join(lines)

    assert r"走向\[S1\]" in body
    assert "路线账本" in body
    assert r"湖边\[一号\]" in body
    assert "PR" not in body


def test_tui_player_reexports_presenter_helpers():
    """旧测试入口仍可用,但实现来自 presenter 边界。"""
    import ghost_story_factory.v7.tui_player as player
    import ghost_story_factory.v7.tui_presenter as presenter

    assert player._format_choice_option_label is presenter.format_choice_option_label
    assert player._escape_rich_literal is presenter.escape_rich_literal
