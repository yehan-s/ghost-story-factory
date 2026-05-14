"""Pass 27a 回归 snapshot — picker variants 死渲染防回归。

背景:
- Pass 27' 修复(2026-05-14 评审决议):tui_player.py:380 + v5/player.py:1162
  picker 分支添加 resolve_narrative 调用 + (占位 guard,
  让 Pass 9/23/24/26 写的 24 picker variants(跨周目反咬、行为画像反喂等)
  在运行时显示给玩家(修复前完全不渲染)。

测试:
- resolve_narrative 在 picker 节点下能正确选 variant
- (占位 前缀 guard 行为
- 引擎层补丁存在(防回滚):tui_player.py + v5/player.py 都调用 resolve_narrative
- audit_state 新规则:picker 节点 narrative 含 (占位 → warnings.placeholder_narratives_picker
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ghost_story_factory.v5.player import State, resolve_narrative
from tools.audit_state import audit_tree


OFFICIAL_TREE = Path("stories/hangzhou_yebanbaoan/tree.json")
TUI_PLAYER = Path("src/ghost_story_factory/v7/tui_player.py")
V5_PLAYER = Path("src/ghost_story_factory/v5/player.py")


# ─── 引擎补丁存在性(防 Pass 27' 修复回滚)─────────────────────────────

def test_v7_picker_branch_calls_resolve_narrative():
    """tui_player.py picker 分支必须调用 resolve_narrative。

    Pass 27' 修复前:_is_map_picker 分支只渲染地图视图,跳过 narrative_variants。
    补丁要求:picker 分支顶部添加 resolve_narrative 调用。
    """
    src = TUI_PLAYER.read_text(encoding="utf-8")
    # 匹配 picker 分支(line 380 起)的 if 块内有 resolve_narrative 调用
    picker_block = re.search(
        r'if node\.get\("_is_map_picker"\):(.*?)(?=^\s*else:|^\s*if\s)',
        src,
        re.DOTALL | re.MULTILINE,
    )
    assert picker_block, "tui_player.py 未找到 _is_map_picker 分支"
    assert "resolve_narrative" in picker_block.group(1), (
        "tui_player.py picker 分支缺 resolve_narrative — Pass 27' 修复被回滚?"
    )


def test_v5_picker_branch_calls_resolve_narrative():
    """v5/player.py picker 分支必须调用 resolve_narrative(同 v7 修复)。"""
    src = V5_PLAYER.read_text(encoding="utf-8")
    picker_block = re.search(
        r'if node\.get\("_is_map_picker"\):(.*?)(?=^\s*else:|^\s*if\s)',
        src,
        re.DOTALL | re.MULTILINE,
    )
    assert picker_block, "v5/player.py 未找到 _is_map_picker 分支"
    assert "resolve_narrative" in picker_block.group(1), (
        "v5/player.py picker 分支缺 resolve_narrative — Pass 27' 修复被回滚?"
    )


def test_picker_branches_have_placeholder_guard():
    """两个 picker 分支都必须有 (占位 guard,防止占位字符串泄漏给玩家。"""
    tui_src = TUI_PLAYER.read_text(encoding="utf-8")
    v5_src = V5_PLAYER.read_text(encoding="utf-8")
    assert "(占位" in tui_src, "tui_player.py 缺 (占位 guard"
    assert "(占位" in v5_src, "v5/player.py 缺 (占位 guard"


# ─── resolve_narrative 行为(picker 节点真实数据)──────────────────────

def _load_tree():
    return json.loads(OFFICIAL_TREE.read_text(encoding="utf-8"))


def test_resolve_narrative_picker_returns_variant_when_match():
    """G-273 主 picker 在 visit_count_min=1 状态下应返回 variant 文本,而非 narrative。"""
    tree = _load_tree()
    node = tree["nodes"]["n_landmark_picker"]

    state = State({"visit_counts": {"n_landmark_picker": 1}})

    text = resolve_narrative(node, state)
    assert text, "首次访问 picker 应该返回非空 narrative"
    # 不应该泄漏占位字符串
    assert not text.startswith("(占位"), (
        f"resolve_narrative 不应返回占位 narrative,实际返回: {text[:60]!r}"
    )


def test_resolve_narrative_linmou_picker_has_fallback_variant():
    """linmou picker 节点必须有 if=[] 兜底 variant 保证 narrative 永远非占位。"""
    tree = _load_tree()
    node = tree["nodes"]["n_l1985_landmark_picker"]

    state = State({})  # 初始状态,无 visit_count / 无 ending_seen 等
    text = resolve_narrative(node, state)
    assert text, "linmou picker 应该总有 fallback variant 返回非空"
    # 注意:linmou picker.narrative 字段本身是 "(占位)",但 if=[] variant 应该兜底
    # 如果这个断言失败,说明 if=[] variant 缺失或 resolve_narrative 行为变了
    assert not text.startswith("(占位"), (
        f"linmou picker resolve_narrative 不应返回占位,实际: {text[:60]!r}"
    )


def test_resolve_narrative_lore_index_has_fallback_variant():
    """n_lore_index(也是 picker)必须有 if=[] 兜底,避免运行时显示占位字符串。"""
    tree = _load_tree()
    node = tree["nodes"]["n_lore_index"]

    state = State({})
    text = resolve_narrative(node, state)
    assert text, "n_lore_index 应该总有 fallback variant"
    assert not text.startswith("(占位"), (
        f"n_lore_index resolve_narrative 不应返回占位,实际: {text[:60]!r}"
    )


# ─── audit_state 防回归 Rule(新增,Pass 27a 配套)──────────────────

def test_audit_state_reports_picker_placeholder_narratives_as_warning():
    """audit_state 新 rule:picker 节点 narrative 含 (占位 应列入 warnings(防回归)。

    现状:n_lore_index 和 n_l1985_landmark_picker 的 narrative 字段都是 (占位)。
    虽然 if=[] 兜底 + 引擎 (占位 guard 已保证安全,但 audit 应主动提醒清理。
    """
    report = audit_tree(OFFICIAL_TREE)
    pickers = report.get("placeholder_narratives_picker", [])
    # 当前已知的 2 个 picker 节点 narrative 是 (占位),audit 应该捞出
    assert "n_lore_index" in pickers, (
        f"audit_state 未识别 n_lore_index 的 (占位 narrative;实际 pickers={pickers}"
    )
    assert "n_l1985_landmark_picker" in pickers, (
        f"audit_state 未识别 n_l1985_landmark_picker 的 (占位 narrative;"
        f"实际 pickers={pickers}"
    )
    # 应该在 severity.warnings 中
    sev_warnings = report["severity"]["warnings"]
    assert "placeholder_narratives_picker" in sev_warnings, (
        "placeholder_narratives_picker 应该在 severity.warnings 中"
    )


def test_audit_state_reports_other_placeholder_narratives_as_info():
    """非 picker 节点的 (占位 narrative 应列入 info(if=[] 兜底已保护)。"""
    report = audit_tree(OFFICIAL_TREE)
    others = report.get("placeholder_narratives_other", [])
    # 至少应有 lore_* 节点(songmuchang_inn 等)
    assert others, "audit_state 应至少识别一些非 picker (占位 narrative"
    # 不应包含 picker 节点
    assert "n_landmark_picker" not in others
    assert "n_lore_index" not in others
    assert "n_l1985_landmark_picker" not in others
    sev_info = report["severity"]["info"]
    assert "placeholder_narratives_other" in sev_info, (
        "placeholder_narratives_other 应该在 severity.info 中"
    )
