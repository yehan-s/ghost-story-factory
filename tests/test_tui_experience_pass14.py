"""Pass 14 — TUI 体验收束回归测试。"""

from __future__ import annotations

from pathlib import Path


class _Save:
    """最小存档替身。"""

    def __init__(self):
        self.data = {
            "foreshadows_seen": {"story": ["fs_a"]},
            "foreshadows_resolved": {"story": []},
            "deductions_resolved": {"story": []},
            "achievements_unlocked": [],
        }

    def mark_foreshadow_seen(self, *_args, **_kwargs):
        return True

    def get_shards_collected(self, *_args, **_kwargs):
        return []


class _Log:
    """模拟 RichLog。"""

    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text)


class _Status:
    """模拟 StatusBar。"""

    def __init__(self):
        self.updated = False

    def update_state(self, _state):
        self.updated = True


class _Scroll:
    """模拟滚动容器。"""

    def __init__(self):
        self.scrolled = False

    def scroll_end(self, animate=False):
        self.scrolled = True


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
    """构造最小 TUI 测试树。"""
    return {
        "story_id": "story",
        "foreshadows": {
            "fs_a": {
                "title": "井口[旧声]",
                "summary_locked": "还差一段夜班记录。",
            }
        },
        "nodes": {
            "n": {
                "narrative": "原文",
                "_scene_details": [
                    {
                        "label": "门牌[反光]",
                        "text": "门牌背面有划痕。",
                        "effects": {"flags": {"know.door_plate": True}},
                    }
                ],
                "choices": [{"text": "离开", "next": "end"}],
            },
            "end": {"is_ending": True, "ending_type": "E_TEST", "choices": []},
        },
    }


def test_tui_choice_badges_replace_cli_suffix(monkeypatch):
    """TUI 选择项使用 badge,不是 CLI 的整段后缀。"""
    from ghost_story_factory.v7.tui_player import _format_choice_option_label

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    label = _format_choice_option_label(
        1,
        {"text": "查看[档案]", "effects": {"stay": True, "PR": 1}},
    )

    assert r"查看\[档案\]" in label
    assert "[cyan]〈观察〉[/]" in label
    assert "[red]〈心境波动〉[/]" in label
    assert "〔观察 · 心境波动〕" not in label
    assert "PR" not in label


def test_format_tui_status_lines_hides_internal_flags():
    """TUI 状态页是玩家档案,不是内部 flag dump。"""
    from ghost_story_factory.v7.tui_player import format_tui_status_lines

    state = _state(
        flags={"know.door_plate": True, "oneshot.live_streaming": True},
        visited_landmarks=["S1"],
        puzzle_pieces=["piece_a"],
    )
    lines = format_tui_status_lines(_tree(), _Save(), "story", state)
    body = "\n".join(lines)

    assert "路线账本" in body
    assert "本轮行为画像" in body
    assert "档案索引" in body
    assert r"井口\[旧声\]" in body
    assert "井口[旧声]" not in body
    assert "内部标记" not in body
    assert "know.door_plate" not in body
    assert "oneshot.live_streaming" not in body
    assert "PR" not in body
    assert "GR" not in body


def test_format_scene_strip_uses_landmark_header():
    """顶部场景条优先展示时间和地点。"""
    from ghost_story_factory.v7.tui_player import format_scene_strip

    line = format_scene_strip(
        {"_landmark_header": {"time": "02:10", "place": "B3[站台]"}},
        "n_b3",
    )

    assert "02:10" in line
    assert r"B3\[站台\]" in line


def test_run_recap_lines_include_profile_and_archive_without_scores():
    """结局复盘要给回玩方向,但不泄露内部数值。"""
    from ghost_story_factory.v7.tui_player import format_run_recap_lines

    state = _state(
        flags={"know.door_plate": True},
        visited_landmarks=["S1", "S2"],
        skipped_landmarks=["S4"],
        shifts_skipped=1,
        puzzle_pieces=["piece_a"],
    )
    lines = format_run_recap_lines(_tree(), _Save(), "story", state, ["n", "end"], "E_TEST")
    body = "\n".join(lines)

    assert "本轮复盘" in body
    assert "本轮行为画像" in body
    assert "档案进度" in body
    assert r"井口\[旧声\]" in body
    assert "PR" not in body
    assert "GR" not in body


def test_stay_choice_refreshes_choices_without_rerendering_node(monkeypatch):
    """stay/detail 是当前节点内动作,不能重复调用整段 _render_node。"""
    from ghost_story_factory.v7.tui_player import GhostStoryApp

    monkeypatch.delenv("GHOST_CHOICE_HINTS", raising=False)
    app = GhostStoryApp.__new__(GhostStoryApp)
    app._tree = _tree()
    app.nodes = app._tree["nodes"]
    app._tree_path = Path("story.json")
    app.current_id = "n"
    app.state = _state()
    app.state.visit_counts["n"] = 1
    app.save_manager = _Save()
    app.visible_choices = [{
        "text": "  · 看一眼 门牌[反光]",
        "effects": {"stay": True, "flags": {"know.door_plate": True}},
        "_detail_text": "门牌背面有划痕。",
    }]
    app._ended = False

    log = _Log()
    status = _Status()
    scroll = _Scroll()

    def query_one(selector, *_args):
        if selector == "#narrative":
            return log
        if selector == "#status-bar":
            return status
        if selector == "#narrative-box":
            return scroll
        raise AssertionError(selector)

    app.query_one = query_one
    called = {"render_node": 0, "refresh": 0}
    app._render_node = lambda: called.__setitem__("render_node", called["render_node"] + 1)

    def refresh(visible, locked, out_log):
        called["refresh"] += 1
        app.visible_choices = visible
        assert locked == []
        assert out_log is log

    app._refresh_choices = refresh

    app._apply_choice(0)

    body = "\n".join(log.lines)
    assert "门牌背面有划痕" in body
    assert called["render_node"] == 0
    assert called["refresh"] == 1
    assert app.state.visit_counts["n"] == 1
    assert status.updated is True
    assert scroll.scrolled is True


def test_action_show_status_pushes_modal_without_writing_log(monkeypatch):
    """s 键打开 Modal,不再向 narrative log 倾倒状态。"""
    from ghost_story_factory.v7.tui_player import GhostStoryApp, StatusScreen

    app = GhostStoryApp.__new__(GhostStoryApp)
    app._tree = _tree()
    app._tree_path = Path("story.json")
    app.state = _state(flags={"know.secret": True})
    app.save_manager = _Save()
    pushed = []
    app.push_screen = lambda screen: pushed.append(screen)

    app.action_show_status()

    assert len(pushed) == 1
    assert isinstance(pushed[0], StatusScreen)
