"""v7 主菜单 registry 的无副作用行为。"""

from __future__ import annotations

from ghost_story_factory.v7.menu_registry import Story, list_characters


def test_list_characters_without_save_manager_does_not_touch_real_save(tmp_path, monkeypatch):
    """省略 save_manager 时只按默认解锁展示,不能读写用户真实存档。"""
    import ghost_story_factory.v7.menu_registry as registry

    def fail_if_constructed():
        raise AssertionError("list_characters 不应隐式创建 SaveManager")

    monkeypatch.setattr(registry, "SaveManager", fail_if_constructed)
    story = Story(
        id="demo",
        label="Demo",
        subtitle="",
        playable=True,
        tree_path=tmp_path / "tree.json",
        tree={"characters": {"G-273": {}, "linmou_1985": {}}},
    )

    chars = list_characters(story)

    by_id = {c.id: c for c in chars}
    assert by_id["G-273"].unlocked is True
    assert by_id["linmou_1985"].unlocked is False
