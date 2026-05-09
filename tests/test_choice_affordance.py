"""Pass 11 — 选择意图与风险提示测试。"""

from __future__ import annotations


def test_choice_affordance_missing_is_silent(monkeypatch):
    """无 effects 的旧选择不显示标签。"""
    from ghost_story_factory.v5.player import choice_affordance_suffix, choice_affordance_tags

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    choice = {"text": "推门进去"}

    assert choice_affordance_tags(choice) == []
    assert choice_affordance_suffix(choice) == ""


def test_choice_affordance_effects_are_non_spoilery(monkeypatch):
    """标签只暴露意图和风险性质,不暴露数值或内部 key。"""
    from ghost_story_factory.v5.player import choice_affordance_suffix, choice_affordance_tags

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    choice = {
        "text": "把照片发到夜班论坛。",
        "effects": {
            "PR": 8,
            "GR": 5,
            "flags": {"know.redgirl_wants_father": True},
        },
    }

    tags = choice_affordance_tags(choice)
    suffix = choice_affordance_suffix(choice)

    assert tags == ["记下线索", "心境波动"]
    assert suffix == "〔记下线索 · 心境波动〕"
    assert len(tags) <= 2
    assert "8" not in suffix
    assert "5" not in suffix
    assert "PR" not in suffix
    assert "GR" not in suffix
    assert "know.redgirl_wants_father" not in suffix


def test_choice_affordance_can_be_disabled(monkeypatch):
    """选择提示可被环境变量关闭。"""
    from ghost_story_factory.v5.player import choice_affordance_suffix

    monkeypatch.setenv("GHOST_CHOICE_HINTS", "0")
    choice = {"text": "看一眼", "effects": {"stay": True, "PR": 1}}

    assert choice_affordance_suffix(choice) == ""


def test_render_choices_cli_shows_hints_without_play(capsys, monkeypatch):
    """CLI 接线只测 render_choices,不启动完整 play()。"""
    from ghost_story_factory.v5.player import render_choices

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    monkeypatch.setattr("ghost_story_factory.v7.animate.pause", lambda *_args, **_kw: None)

    render_choices([
        {"text": "蹲下来查看门缝。", "effects": {"stay": True, "PR": 1}},
    ])

    out = capsys.readouterr().out
    assert "蹲下来查看门缝" in out
    assert "〔观察 · 心境波动〕" in out


def test_render_choices_grouped_keeps_original_indices(capsys, monkeypatch):
    """分组选项加标签后仍保留原始编号。"""
    from ghost_story_factory.v5.player import render_choices

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    monkeypatch.setattr("ghost_story_factory.v7.animate.pause", lambda *_args, **_kw: None)

    render_choices([
        {"text": "看窗台。", "effects": {"stay": True}},
        {"text": "看门牌。", "effects": {"stay": True}},
        {"text": "继续往前。", "effects": {"PR": 1}},
        {"text": "拍照存证。", "effects": {"inv_add": ["photo"]}},
        {"text": "离开这里。", "effects": {"GR": 1}},
    ])

    out = capsys.readouterr().out
    assert "在这里看一眼" in out
    assert "走出去" in out
    assert "1. 看窗台" in out
    assert "3. 继续往前" in out
    assert "4. 拍照存证" in out
    assert "5. 离开这里" in out


def test_locked_choice_does_not_leak_hint(capsys, monkeypatch):
    """锁定选项只显示锁定原因,不泄露未来收益。"""
    from ghost_story_factory.v5.player import render_choices

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    monkeypatch.setattr("ghost_story_factory.v7.animate.pause", lambda *_args, **_kw: None)

    locked_choice = {
        "text": "打开地下门",
        "effects": {"puzzle_add": ["truth"], "PR": 9},
    }
    render_choices([], locked=[(locked_choice, "需要「旧钥匙」")])

    out = capsys.readouterr().out
    assert "需要「旧钥匙」" in out
    assert "关键线索" not in out
    assert "心境波动" not in out


def test_tui_choice_label_escapes_rich_markup(monkeypatch):
    """TUI 选择文本和提示都要按字面量转义。"""
    from ghost_story_factory.v7.tui_player import _format_choice_option_label

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    choice = {"text": "查看[档案]", "effects": {"stay": True, "PR": 1}}

    label = _format_choice_option_label(1, choice)

    assert r"查看\[档案\]" in label
    assert "[cyan]〈观察〉[/]" in label
    assert "[red]〈心境波动〉[/]" in label
    assert "查看[档案]" not in label
