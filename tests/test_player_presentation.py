"""Pass 10 — VN presentation 运行时文本 fallback 测试。"""

from __future__ import annotations


def _tree():
    """构造最小资产表,不读取正式大树。"""
    return {
        "assets": {
            "backgrounds": {
                "bg_lake": {"kind": "text_fallback", "label": "西湖水汽"},
                "bg_bad": {"kind": "text_fallback", "label": "电话[坏]"},
            },
            "bgm": {
                "bgm_lake": {"kind": "text_fallback", "label": "湖面远汽笛"},
            },
            "sfx": {
                "sfx_water": {"kind": "text_fallback", "label": "湖水拍岸"},
                "sfx_click": {"kind": "text_fallback", "label": "电闸轻响"},
            },
            "sprites": {
                "sp_zhao": {"kind": "text_fallback", "label": "赵某 G-273"},
            },
        }
    }


def test_format_presentation_basic_fields(monkeypatch):
    """完整字段应压缩为 1-2 行,并优先显示资产 label。"""
    from ghost_story_factory.v5.player import format_presentation_lines

    monkeypatch.delenv("GHOST_VN_CUES", raising=False)
    node = {
        "presentation": {
            "background": "bg_lake",
            "bgm": "bgm_lake",
            "sfx": ["sfx_water", "sfx_click"],
            "sprite": "sp_zhao",
            "expression": "neutral",
            "transition": "fade",
            "camera": "close",
            "cg_intent": "handheld_flashlight",
            "transition_intent": "hard_cut",
            "cg_unlock": "cg_lake_truth",
        }
    }

    lines = format_presentation_lines(_tree(), node)

    assert len(lines) == 2
    body = "\n".join(lines)
    assert "西湖水汽" in body
    assert "湖面远汽笛" in body
    assert "湖水拍岸,电闸轻响" in body
    assert "赵某 G-273(neutral)" in body
    assert "镜头=close" in body
    assert "CG意图=handheld_flashlight" in body
    assert "CG解锁=cg_lake_truth" in body
    assert "bg_lake" not in body


def test_format_presentation_missing_is_silent(monkeypatch):
    """旧树没有 presentation 时必须静默,不能污染旧 narrative。"""
    from ghost_story_factory.v5.player import format_presentation_lines

    monkeypatch.delenv("GHOST_VN_CUES", raising=False)
    assert format_presentation_lines(_tree(), {"narrative": "旧节点"}) == []


def test_format_presentation_partial_fields_no_none(monkeypatch):
    """缺省字段不能输出 None / [] 这类实现细节。"""
    from ghost_story_factory.v5.player import format_presentation_lines

    monkeypatch.delenv("GHOST_VN_CUES", raising=False)
    lines = format_presentation_lines(_tree(), {"presentation": {"background": "bg_lake"}})
    body = "\n".join(lines)
    assert lines == ["演出: 背景=西湖水汽"]
    assert "None" not in body
    assert "[]" not in body


def test_format_presentation_can_be_disabled(monkeypatch):
    """文本 fallback 可关闭,给后续真实资产渲染或玩家偏好留出口。"""
    from ghost_story_factory.v5.player import format_presentation_lines

    monkeypatch.setenv("GHOST_VN_CUES", "0")
    node = {"presentation": {"background": "bg_lake"}}
    assert format_presentation_lines(_tree(), node) == []


def test_render_presentation_cli_stdout(capsys, monkeypatch):
    """CLI 接线只测轻量 stdout,不启动完整 play()。"""
    from ghost_story_factory.v5.player import render_presentation

    monkeypatch.delenv("GHOST_VN_CUES", raising=False)
    render_presentation(_tree(), {"presentation": {"background": "bg_lake"}})
    out = capsys.readouterr().out
    assert "演出" in out
    assert "西湖水汽" in out


class _MockLog:
    """模拟 RichLog,捕获 TUI 输出文本。"""

    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text)


def test_tui_presentation_escapes_rich_markup(monkeypatch):
    """TUI 输出前必须 escape,否则资产 label 里的方括号会破坏 Rich markup。"""
    from ghost_story_factory.v7.tui_player import GhostStoryApp

    monkeypatch.delenv("GHOST_VN_CUES", raising=False)
    app = GhostStoryApp.__new__(GhostStoryApp)
    app._tree = _tree()
    log = _MockLog()

    app._render_presentation_tui({"presentation": {"background": "bg_bad"}}, log)

    body = "\n".join(log.lines)
    assert "演出" in body
    assert r"\[坏\]" in body
    assert "电话[坏]" not in body
