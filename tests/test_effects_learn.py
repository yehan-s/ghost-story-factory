"""Pass 2 — knowledge_learned 事件源单元测试。

ADR/Spec: docs/team-reviews/2026-05-07-pass2-effects-learn-and-npc-drowned-pilot.md
Plan:    docs/superpowers/plans/2026-05-08-pass2-effects-learn-and-npc-drowned-pilot.md

测试矩阵(Phase 1 引擎层):
- know.* false→true: emit knowledge_learned, is_first_time=True
- know.* 复读 (已经 True 再 set True): emit, is_first_time=False
- 非 know.* flag: 静默(不 emit knowledge_learned)
- know.* set False: 静默(知识不可"unlearn")
- 单 apply 多 know: 各自独立 emit

测试矩阵(Phase 2 UI 层):
- CLI _render_apply_events: 默认 / 档案补遗 / 复读 / 禁 HUD 符号
- TUI _render_apply_events_tui: 默认 / 档案补遗 / 复读
"""

from __future__ import annotations

from ghost_story_factory.v5.player import State


# ---------- Phase 1: 引擎事件源 ----------

def _new_state() -> State:
    """构造最小 State(不依赖 tree / save_manager)。"""
    return State(initial={"flags": {}, "character": "G-273"})


def test_know_first_set_emits_event():
    s = _new_state()
    s.apply({"flags": {"know.linmou_badge": True}})
    learned = [e for e in s._last_events if e.get("type") == "knowledge_learned"]
    assert len(learned) == 1
    assert learned[0]["key"] == "know.linmou_badge"
    assert learned[0]["is_first_time"] is True


def test_know_repeat_set_emits_re_learn_event():
    s = _new_state()
    s.apply({"flags": {"know.linmou_badge": True}})  # first
    s.apply({"flags": {"know.linmou_badge": True}})  # repeat
    learned = [e for e in s._last_events if e.get("type") == "knowledge_learned"]
    assert len(learned) == 1
    assert learned[0]["is_first_time"] is False


def test_non_know_flag_silent():
    s = _new_state()
    s.apply({"flags": {"oneshot.s1_signed_book": True}})
    learned = [e for e in s._last_events if e.get("type") == "knowledge_learned"]
    assert learned == []


def test_know_set_false_silent():
    """know.X = False 不算 learn 事件(知识不会"unlearn")。"""
    s = _new_state()
    s.apply({"flags": {"know.linmou_badge": False}})
    learned = [e for e in s._last_events if e.get("type") == "knowledge_learned"]
    assert learned == []


def test_multiple_know_in_one_apply():
    """单次 apply 多个 know 跳变,各自 emit 一个事件。"""
    s = _new_state()
    s.apply({"flags": {"know.a": True, "know.b": True, "oneshot.x": True}})
    learned = [e for e in s._last_events if e.get("type") == "knowledge_learned"]
    assert len(learned) == 2
    assert {e["key"] for e in learned} == {"know.a", "know.b"}


# ---------- Phase 2.1: CLI 反馈条 ----------

def test_render_default_carrier_first_time(capsys):
    """默认载体:值班记录本(非 archive 类 know.*)。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": True}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "值班记录本上记下" in out
    # know_text 是 key 去掉 "know." 前缀
    assert "linmou_badge" in out


def test_render_archive_carrier_first_time(capsys):
    """档案知识:archive / corruption 类走『档案补遗』前缀。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.linmou_archive_1985", "is_first_time": True}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "档案补遗" in out


def test_render_corruption_carrier_first_time(capsys):
    """corruption 也走档案补遗。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.linmou_corruption", "is_first_time": True}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "档案补遗" in out


def test_render_re_learn_dim_short(capsys):
    """复读:短 dim 文案『(已知 · X)』,不弹『记下』。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": False}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "已知" in out
    assert "记下" not in out


def test_render_no_hud_symbols(capsys):
    """禁用 ▌▐ HUD 符号(Lore R-L2 + UX R-U1)。"""
    from ghost_story_factory.v5.player import _render_apply_events
    events = [{"type": "knowledge_learned", "key": "know.x", "is_first_time": True}]
    _render_apply_events(events, important_items=set())
    out = capsys.readouterr().out
    assert "▌" not in out
    assert "▐" not in out
    assert "[get]" not in out
    assert "[unlock]" not in out


# ---------- Phase 2.2: TUI 反馈条 ----------

class _MockLog:
    """模拟 RichLog,捕获所有 write 调用文本。"""

    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text)


def _make_tui_player_for_test():
    """构造一个最小 TUI player 实例(只用来调 _render_apply_events_tui)。"""
    from ghost_story_factory.v7.tui_player import GhostStoryApp
    app = GhostStoryApp.__new__(GhostStoryApp)  # 跳过 __init__
    app._important_items = set()
    return app


def test_tui_render_default_carrier_first_time():
    app = _make_tui_player_for_test()
    log = _MockLog()
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": True}]
    app._render_apply_events_tui(events, log)
    body = "\n".join(log.lines)
    assert "值班记录本上记下" in body
    assert "▌" not in body  # HUD 符号禁用


def test_tui_render_archive_carrier():
    app = _make_tui_player_for_test()
    log = _MockLog()
    events = [{"type": "knowledge_learned", "key": "know.linmou_corruption", "is_first_time": True}]
    app._render_apply_events_tui(events, log)
    body = "\n".join(log.lines)
    assert "档案补遗" in body


def test_tui_render_re_learn():
    app = _make_tui_player_for_test()
    log = _MockLog()
    events = [{"type": "knowledge_learned", "key": "know.linmou_badge", "is_first_time": False}]
    app._render_apply_events_tui(events, log)
    body = "\n".join(log.lines)
    assert "已知" in body
    assert "记下" not in body
