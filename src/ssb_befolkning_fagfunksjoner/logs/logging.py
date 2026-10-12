"""Application logging with optional local files and GCS uploads.

Call config_logging() once in the entry point. Other modules need only
get_logger(__name__). GCS uploads require universal-pathlib and gcsfs.
"""

import logging
from pathlib import Path
from typing import Any


class FregLogger:
    """
    Args:
        logfile: Local file to append to, or None for console-only output.
        console_level: Console threshold; defaults to INFO.
        file_level: File threshold; defaults to DEBUG.
        context: Metadata to append as a file header for this run.
    """
    def __init__(
        self,
        logfile: str | Path | None = None,
        *,
        console_log_level: str | int = logging.INFO,
        file_log_level: str | int = logging.DEBUG,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.logfile = (
            Path(logfile).expanduser().resolve()
            if logfile is not None 
            else None
        )

        self._root_logger = logging.getLogger()
        self._handlers: list[logging.Handler] = []

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

    def close(self) -> None:
        """Remove and close only the handlers created by this instance."""
        for handler in self._handlers:
            self._root_logger.removeHandler(handler)
            handler.close()
        self._handlers.clear()

    def _remove_handlers(self) -> None:
        """Clear existing handlers from logger to prevent duplicate printouts."""
        for handler in self._root_logger.handlers.copy():
            self._root_logger.removeHandler(handler)
            handler.close()

    @staticmethod
    def _console_handler(level: str | int) -> logging.StreamHandler:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
        return handler

    def _file_handler(self, level: str | int, context: dict[str, Any] | None) -> logging.FileHandler:
        if self.logfile is None:
            raise ValueError("'logfile' parameter is required.")
            
        self.logfile.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(filename=self.logfile, mode="a", encoding="utf-8")
        try:
            handler.setLevel(level)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            if context is not None:
                self._write_log_header(context)
            return handler

        except Exception:
            handler.close()
            raise


    def _write_log_header(self, context: dict[str, Any]) -> None:
        if self.logfile is None:
            raise ValueError("'logfile' parameter is required.")

        separator = "=" * 60
        lines = [
            separator,
            *[f"{key:<15}: {value}" for key, value in context.items()],
            separator,
        ]

        with self.logfile.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")


def config_logging(
    logfile: str | Path | None = None,
    *,
    console_log_level: str | int = logging.INFO,
    file_log_level: str | int = logging.DEBUG,
    context: dict[str, Any] | None = None,
) -> FregLogger:
    """Initialize logging and return the instance used for GCS uploads."""
    return FregLogger(
        logfile=logfile,
        console_log_level=console_log_level,
        file_log_level=file_log_level,
        context=context,
    )
