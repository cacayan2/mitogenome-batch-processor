"""Create console and file loggers for MitoPipeline."""

from __future__ import annotations

import logging
from pathlib import Path


def make_logger(
    name: str,
    log_file_path: str | Path,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """Return a logger with concise console and detailed file output.

    A logger is keyed by both logical name and resolved logfile. This prevents
    two samples using the same tool name from accidentally sharing a file
    handler when they execute in the same Python process.
    """
    log_file = Path(log_file_path).expanduser().resolve()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger_name = f"{name}:{log_file}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        return logger

    console_formatter = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s | [%(levelname)s] | %(message)s | "
        "%(filename)s:%(lineno)d"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
