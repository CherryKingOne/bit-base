"""日志配置"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """配置日志"""
    log_dir = Path.home() / ".bit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    if log_file is None:
        log_file = str(log_dir / "bit.log")

    # 格式
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    # Root logger
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    root.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    root.addHandler(file_handler)

    # 降低第三方库日志级别
    for name in ("httpx", "httpcore", "uvicorn", "fastapi"):
        logging.getLogger(name).setLevel(logging.WARNING)
