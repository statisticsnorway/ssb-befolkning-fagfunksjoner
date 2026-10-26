"""Configure console and file logging.

Call config_logging() once at application startup.
Other modules should use logging.getLogger(__name__).
"""

import logging
from pathlib import Path
from typing import Any


class FregLogger:
    """Configure console and file logging."""

    def __init__(
        self,
        logfile: str | Path | None = None,
        *,
        console_log_level: str | int = logging.INFO,
        file_log_level: str | int = logging.DEBUG,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize logging handlers.

        Args:
            logfile: Local file to append to, or None for console-only output.
            console_log_level: Console threshold; defaults to INFO.
            file_log_level: File threshold; defaults to DEBUG.
            context: Metadata to append as a file header for this run.

        Raises:
            Exception: If logging configuration fails. The original exception
                is re-raised after closing any handlers created by this instance.
        """
        self.logfile = (
            Path(logfile).expanduser().resolve() if logfile is not None else None
        )

        self._root_logger = logging.getLogger()
        self._handlers: list[logging.Handler] = []

        console_log_level = self._normalize_level(console_log_level)
        file_log_level = self._normalize_level(file_log_level)

        # Build FregLogger handlers for console and file
        try:
            self._handlers.append(self._console_handler(console_log_level))
            if self.logfile is not None:
                self._handlers.append(self._file_handler(file_log_level, context))

            # force=True removes and closes the previous root handlers.
            logging.basicConfig(
                level=min(handler.level for handler in self._handlers),
                handlers=self._handlers,
                force=True,
            )

        except Exception:
            self.close()
            raise

    @staticmethod
    def _normalize_level(level: str | int) -> int:
        """Convert a logging level to its numeric representation."""
        if isinstance(level, str):
            try:
                return logging.getLevelNamesMapping()[level.upper()]
            except KeyError:
                raise ValueError(f"Invalid logging level: {level}") from None

        return level

    def close(self) -> None:
        """Remove and close only the handlers created by this instance."""
        for handler in self._handlers:
            self._root_logger.removeHandler(handler)
            handler.close()
        self._handlers.clear()

    @staticmethod
    def _console_handler(level: int) -> logging.StreamHandler:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
        return handler

    def _file_handler(
        self, level: int, context: dict[str, Any] | None
    ) -> logging.FileHandler:
        if self.logfile is None:
            raise ValueError("'logfile' parameter is required.")

        self.logfile.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(filename=self.logfile, mode="a", encoding="utf-8")
        try:
            handler.setLevel(level)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            if context is not None:
                self._write_log_header(handler, context)
            return handler

        except Exception:
            handler.close()
            raise

    @staticmethod
    def _write_log_header(
        handler: logging.FileHandler, context: dict[str, Any]
    ) -> None:
        """Append metadata 'header' to the existing log stream."""
        separator = "=" * 60

        lines = [
            separator,
            *[f"{key:<15}: {value}" for key, value in context.items()],
            separator,
        ]

        if handler.stream is None:
            raise RuntimeError("Log file is not open.")

        handler.stream.write("\n".join(lines) + "\n")
        handler.flush()


def config_logging(
    logfile: str | Path | None = None,
    *,
    console_log_level: str | int = logging.INFO,
    file_log_level: str | int = logging.DEBUG,
    context: dict[str, Any] | None = None,
) -> FregLogger:
    """Configure logging and return the configuration instance."""
    return FregLogger(
        logfile=logfile,
        console_log_level=console_log_level,
        file_log_level=file_log_level,
        context=context,
    )
