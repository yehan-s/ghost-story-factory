"""v7 档案视图 CLI/TUI 信息一致性。"""

from __future__ import annotations

from ghost_story_factory.v7.archive_view import render_archive_lines_rich


class _Save:
    def __init__(self):
        self.data = {
            "foreshadows_seen": {"杭州_v7": ["F-001"]},
            "foreshadows_resolved": {"杭州_v7": ["F-001"]},
            "deductions_resolved": {"杭州_v7": ["D-001"]},
            "achievements_unlocked": ["A-001"],
            "foreshadow_shards": {"杭州_v7": {"F-001": ["s1"]}},
        }

    def shard_progress(self, tree, story_id, slot_id):
        return (1, 1)

    def get_shards_collected(self, story_id, slot_id):
        return ["s1"]


def test_rich_archive_includes_all_cli_sections():
    """TUI 档案不能漏掉主题、人物志、成就这些用户可见信息。"""
    tree = {
        "themes": {
            "T-001": {
                "name": "替班",
                "icon": "◆",
                "manifestations": ["F-001"],
            }
        },
        "deductions": {
            "D-001": {"title": "互证", "summary": "两份记录对上了。"}
        },
        "foreshadows": {
            "F-001": {
                "title": "铜印",
                "year": 1985,
                "summary_resolved": "你知道铜印来自哪里。",
                "related_npcs": ["npc_a"],
                "shards": [{"id": "s1", "label": "碎片", "text": "一枚印。"}],
            }
        },
        "timeline": [
            {"year": 1985, "event": "林某投湖", "related_foreshadows": ["F-001"]}
        ],
        "achievements": {
            "A-001": {"name": "第一次互证", "description": "把两条线连起来。"}
        },
        "npcs": {
            "npc_a": {
                "label": "林某",
                "death_year": 1985,
                "real_name": "林副科长",
                "related_foreshadows": ["F-001"],
            }
        },
    }

    text = "\n".join(render_archive_lines_rich(tree, _Save(), "杭州_v7"))

    assert "主题" in text
    assert "推论" in text
    assert "档案 · 伏笔" in text
    assert "时间年表" in text
    assert "成就" in text
    assert "人物志" in text
