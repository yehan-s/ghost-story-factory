"""
轻量日志工具

目标：
- 在每次生成会话启动时创建一个 logs/<app>_YYYYmmdd_HHMMSS.log 文件
- 返回统一的 logger 与日志路径，供整个进程复用
- 自动安装 sys.excepthook，确保未捕获异常也会写入日志

用法：
    from ghost_story_factory.utils.logging_utils import get_run_logger, get_logger
    logger, log_path = get_run_logger("generate_mvp", {"city": "杭州"})
    logger.info("启动生成……")
    # 在其他模块中：
    logger, log_path = get_logger()
    logger.exception("出错了")
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict

_LOGGER: Optional[logging.Logger] = None
_LOG_FILE_PATH: Optional[str] = None


def _ensure_logs_dir() -> Path:
    root = Path(os.getcwd())
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _install_excepthook(logger: logging.Logger) -> None:
    def _hook(exc_type, exc_value, exc_traceback):
        try:
            logger.exception("未捕获异常", exc_info=(exc_type, exc_value, exc_traceback))
        finally:
            # 继续默认输出到控制台
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = _hook


def get_run_logger(app_name: str, context: Optional[Dict[str, object]] = None) -> Tuple[logging.Logger, str]:
    """
    初始化（或复用）本次运行的文件日志并返回 logger 与日志文件路径。

    若已初始化，则直接返回同一 logger/路径，确保全程写入同一个日志文件。
    """
    global _LOGGER, _LOG_FILE_PATH

    if _LOGGER is not None and _LOG_FILE_PATH is not None:
        # 已初始化，补充一次上下文即可
        if context:
            try:
                _LOGGER.info("context=%s", context)
            except Exception:
                pass
        return _LOGGER, _LOG_FILE_PATH

    logs_dir = _ensure_logs_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{app_name}_{ts}.log"
    log_path = str(logs_dir / filename)

    logger = logging.getLogger("ghost_story_factory")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # 防止重复 handler
    for h in list(logger.handlers):
        logger.removeHandler(h)

    fmt = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # 写入一次启动信息
    logger.info("日志初始化: %s", filename)
    if context:
        logger.info("context=%s", context)

    _install_excepthook(logger)

    _LOGGER = logger
    _LOG_FILE_PATH = log_path
    return logger, log_path


def get_logger() -> Tuple[logging.Logger, Optional[str]]:
    """
    获取已初始化的 logger；若未初始化，则返回一个基础控制台 logger。
    返回: (logger, log_file_path|None)
    """
    global _LOGGER, _LOG_FILE_PATH
    if _LOGGER is not None:
        return _LOGGER, _LOG_FILE_PATH

    # 未通过 get_run_logger 初始化时，提供退化 logger（仅控制台）
    logger = logging.getLogger("ghost_story_factory")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(console_handler)
        logger.propagate = False
    return logger, None


