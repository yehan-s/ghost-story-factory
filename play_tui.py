#!/usr/bin/env python3
"""v7 TUI 入口 — 使用 textual 全屏接管。

跑法:
    python play_tui.py                                       # 主菜单
    python play_tui.py stories/hangzhou_yebanbaoan/tree.json # 跳过菜单直接玩

依赖: textual >= 8.0 (uv pip install textual)

操作(菜单):
    ↑↓ 移动选项 · Enter 选择 · b/Esc 返回 · q 退出

操作(游戏):
    ↑↓ 移动 · Enter 确认 · 1-9 快选 · s 状态 · q 退出
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main() -> int:
    # 显式 path → 跳过菜单(开发/快速测试)
    if len(sys.argv) > 1:
        from ghost_story_factory.v7.tui_player import main as legacy_main
        return legacy_main()
    # 默认 → 菜单 → 游戏
    from ghost_story_factory.v7.menu_tui import run_menu
    from ghost_story_factory.v7.tui_player import GhostStoryApp
    tree_path, character_id = run_menu()
    if tree_path is None:
        return 0
    app = GhostStoryApp(tree_path, character_id=character_id)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
