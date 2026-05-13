"""Pass 13 — 选择后反馈与本轮行为画像测试。"""

from __future__ import annotations


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


def test_behavior_profile_no_trace_is_silent():
    """没有行为痕迹时不刷空画像。"""
    from ghost_story_factory.v5.player import format_behavior_profile_lines

    assert format_behavior_profile_lines(_state()) == []


def test_behavior_profile_covers_core_axes_without_scores():
    """画像覆盖取证、曝光、救援、审判、漏卡,但不暴露 PR/GR。"""
    from ghost_story_factory.v5.player import behavior_profile_axes, format_behavior_profile_lines

    state = _state(
        flags={
            "know.redgirl_wants_father": True,
            "oneshot.live_streaming": True,
            "arc.redgirl_trusts_zhao": True,
            "arc.got_judge_seal": True,
        },
        puzzle_pieces=["piece_a"],
        visited_landmarks=["S1", "S2"],
        skipped_landmarks=["S4"],
        shifts_skipped=1,
    )

    axes = behavior_profile_axes(state)
    lines = format_behavior_profile_lines(state)
    body = "\n".join(lines)

    assert "取证:记录已成形" in axes
    assert "曝光:围观已介入" in axes
    assert "救援:有人回应" in axes
    assert "审判:正章在案" in axes
    assert "漏卡:记录有空栏" in axes
    assert "本轮行为画像" in body
    assert "路线账本" in body
    assert "PR" not in body
    assert "GR" not in body


def test_should_show_behavior_profile_only_key_nodes():
    """画像只在关键回收节点或结局节点自动显示。"""
    from ghost_story_factory.v5.player import should_show_behavior_profile

    assert should_show_behavior_profile({}, "n_landmark_picker") is True
    assert should_show_behavior_profile({}, "n_scene_b3_corridor") is True
    assert should_show_behavior_profile({"is_ending": True}, "n_any_end") is True
    assert should_show_behavior_profile({}, "n_s1_arrive") is False


def test_choice_after_feedback_uses_affordance_without_numbers(monkeypatch):
    """选择后反馈复用选择意图,但不输出数值和内部 key。"""
    from ghost_story_factory.v5.player import format_choice_after_feedback_lines

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    choice = {
        "text": "把照片发到夜班论坛。",
        "effects": {
            "PR": 8,
            "flags": {"oneshot.live_streaming": True},
        },
    }

    lines = format_choice_after_feedback_lines(choice)
    body = "\n".join(lines)

    assert lines == ["路线账本: 围观痕迹写入 · 工牌短暂发冷。"]
    assert "8" not in body
    assert "oneshot.live_streaming" not in body


def test_render_choice_after_feedback_cli(capsys, monkeypatch):
    """CLI 选择后反馈不启动完整 play。"""
    from ghost_story_factory.v5.player import render_choice_after_feedback

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    render_choice_after_feedback({
        "text": "拿走旧账本。",
        "effects": {"inv_add": ["old_book"], "GR": 1},
    })

    out = capsys.readouterr().out
    assert "路线账本" in out
    assert "证据栏更新" in out
    assert "工牌短暂发冷" in out


class _MockLog:
    """模拟 RichLog。"""

    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text)


def test_tui_behavior_profile_escapes_markup(monkeypatch):
    """TUI 画像输出走 Rich 字面量转义。"""
    from ghost_story_factory.v7.tui_player import GhostStoryApp

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    app = GhostStoryApp.__new__(GhostStoryApp)
    app.current_id = "n_landmark_picker"
    app.state = _state(
        flags={"oneshot.live_streaming": True},
        visited_landmarks=["S1"],
    )
    log = _MockLog()

    app._render_behavior_profile_tui({}, log)

    body = "\n".join(log.lines)
    assert "本轮行为画像" in body
    assert "曝光:围观已介入" in body


def test_tui_choice_after_feedback_escapes_choice_text(monkeypatch):
    """TUI 选择后反馈和选中文本不应污染 Rich markup。"""
    from ghost_story_factory.v7.tui_player import _format_choice_option_label

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    label = _format_choice_option_label(
        1,
        {"text": "查看[直播]", "effects": {"stay": True, "PR": 1}},
    )

    assert r"查看\[直播\]" in label
    assert "[cyan]〈观察〉[/]" in label
    assert "查看[直播]" not in label


# ============== Pass 20:behavior_profile 反向喂 variants ==============


def test_behavior_profile_require_has_matches_substring():
    """Pass 20:variant if {behavior_profile: {has: '取证'}} 命中取证型玩家。"""
    from ghost_story_factory.runtime.contracts import RequirementEvaluator

    state = _state(flags={"know.archive_visited": True})
    require = {"behavior_profile": {"has": "取证"}}
    assert RequirementEvaluator.meets(state, require)


def test_behavior_profile_require_has_misses_when_axis_absent():
    """没解锁取证轴,has 条件不命中。"""
    from ghost_story_factory.runtime.contracts import RequirementEvaluator

    state = _state()
    require = {"behavior_profile": {"has": "取证"}}
    assert not RequirementEvaluator.meets(state, require)


def test_behavior_profile_require_has_any_matches_at_least_one():
    """has_any 列表里任一命中即可。"""
    from ghost_story_factory.runtime.contracts import RequirementEvaluator

    state = _state(flags={"oneshot.live_streaming": True})  # 曝光轴
    require = {"behavior_profile": {"has_any": ["取证", "曝光", "审判"]}}
    assert RequirementEvaluator.meets(state, require)


def test_behavior_profile_require_dominant_only_matches_first_axis():
    """dominant 只命中主导轴(axes[0]),不考虑次要轴。"""
    from ghost_story_factory.runtime.contracts import RequirementEvaluator

    # 取证轴会先于曝光/救援被加入(代码里第一个判断),所以是 dominant
    state = _state(
        flags={"know.archive_visited": True, "oneshot.live_streaming": True},
    )
    require_match = {"behavior_profile": {"dominant": "取证"}}
    require_miss = {"behavior_profile": {"dominant": "曝光"}}
    assert RequirementEvaluator.meets(state, require_match)
    assert not RequirementEvaluator.meets(state, require_miss)


def test_behavior_profile_require_combines_with_other_keys():
    """behavior_profile 与 character/flags 组合,默认 AND。"""
    from ghost_story_factory.runtime.contracts import RequirementEvaluator

    state = _state(flags={"arc.got_judge_seal": True})  # 审判轴
    require = {
        "character": "G-273",
        "behavior_profile": {"has": "审判"},
    }
    assert RequirementEvaluator.meets(state, require)
    # 同样画像但 character 不符
    state2 = _state(flags={"arc.got_judge_seal": True}, character="linmou_1985")
    assert not RequirementEvaluator.meets(state2, require)
