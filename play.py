#!/usr/bin/env python3
"""Ghost Story Factory — CLI 入口。

用法:
    python play.py                           # 主菜单(选城市 → 剧情 → 角色)
    python play.py path/to/tree.json         # 跳过菜单直接玩指定 tree
    GHOST_FAST=1 python play.py              # 关闭逐字打印

零依赖。不需要 pip install。直接 python play.py 即可。
"""

import sys
from pathlib import Path

# 让脚本独立可跑,不要求 pip install -e .
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main() -> int:
    # 显式 path → 跳过菜单直接玩(开发/快速测试)
    if len(sys.argv) > 1:
        from ghost_story_factory.v5.player import main as legacy_main
        return legacy_main()
    # 默认 → 进主菜单
    from ghost_story_factory.v7.menu_cli import main_menu
    return main_menu()


if __name__ == "__main__":
    sys.exit(main())
