"""pytest 配置:让 tests/ 能 import tools/ 模块(tools 不是正规 Python 包)。

Pass 1 期间的临时方案,等 tools/ 被升级为正规包(加 __init__.py)后可删。
"""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_SRC_ROOT = _PROJECT_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
