import logging
from pathlib import Path
from typing import Any

from fagfunksjoner.fagfunksjoner_logger import logger as faglogger


def config_logging(
    log_level: str = "INFO",
    log_file: str | Path | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    """Sets up logging to both console and a log file.

    Args:
        log_level: Minimum log level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file:  Path to the log file. Pass None to disable file logging.
        context: Optional dictionary containing context metadata to write to the header.
    """
    faglogger.handlers[:] = []

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers[:] = []

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_build_console_formatter())
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if context is not None:
            _write_log_header(log_path, context)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(_build_file_formatter())
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)


def _write_log_header(log_path: Path, context: dict[str, Any]) -> None:
    width = 60
    lines = [
        "=" * width,
        *[f"{k:<12}: {v}" for k, v in context.items()],
        "=" * width + "\n",
    ]

    with log_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _build_console_formatter() -> logging.Formatter:
    return logging.Formatter(fmt="%(levelname)s | %(message)s")


def _build_file_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
