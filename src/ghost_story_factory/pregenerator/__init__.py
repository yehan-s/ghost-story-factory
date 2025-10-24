"""
预生成系统模块

负责完整故事的预生成，包括：
- 故事简介生成
- 对话树构建
- 状态管理和剪枝
- 进度追踪
"""

from .synopsis_generator import SynopsisGenerator, StorySynopsis

__all__ = ['SynopsisGenerator', 'StorySynopsis']

