import logging
from pathlib import Path
from typing import Any
from upath import UPath

# Noisy libraries we want to silence from root logging
SILENCED_LOGGERS = [
    "google",
    "gcsfs",
    "fsspec",
    "urllib3",
    "matplotlib",
    "asyncio",
]


class BefolkningLogger:
    """Configure the Root logger once at application startup.

    Defaults to INFO console output and DEBUG file output.
    Re-initialization replaces existing root handlers.
    """

    def __init__(
        self,
        logfile: str | Path | None = None,
        *,
        console_level: str | int = logging.INFO,
        file_level: str | int = logging.DEBUG,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.logger = logging.getLogger()
        self._remove_handlers()

        self._add_console_handler(console_level)
        self.local_logfile = Path(logfile) if logfile is not None else None

        if self.local_logfile is not None:
            self._add_file_handler(self.local_logfile, file_level, context)

        # Set root logger level to minimum needed to reach any destination
        self.logger.setLevel(min(handler.level for handler in self.logger.handlers))

    def _remove_handlers(self) -> None:
        """Clear existing handlers from root logger to prevent duplicate printouts."""
        for handler in self.logger.handlers.copy():
            self.logger.removeHandler(handler)
            handler.close()

    def _add_console_handler(self, level: str | int) -> None:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
        self.logger.addHandler(handler)

    def _add_file_handler(
        self,
        log_path: Path,
        level: str | int,
        context: dict[str, Any] | None,
    ) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if context is not None:
            self._write_log_header(log_path, context)

        handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        try:
            handler.setLevel(level)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            self.logger.addHandler(handler)
        except Exception:
            handler.close()
            raise

    @staticmethod
    def _write_log_header(log_path: Path, context: dict[str, Any]) -> None:
        separator = "=" * 60
        lines = [
            separator,
            *[f"{key:<15}: {value}" for key, value in context.items()],
            separator,
        ]
        with log_path.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")

    def upload_to_gcs(self, gcs_logpath: str | Path | UPath) -> None:
        """Close handlers to flush logs, then upload the local logfile to GCS."""
        if self.local_logfile is None:
            raise ValueError("Cannot upload to GCS: no local logfile was configured.")

        self._remove_handlers()
        try:
            gcs_path = UPath(gcs_logpath)
            if self.local_logfile.exists():
                gcs_path.write_bytes(self.local_logfile.read_bytes())
        except Exception as e:
            import sys
            print(f"Error copying logfile to GCS: {e}", file=sys.stderr)


def config_logging(
    logfile: str | Path | None = None,
    *,
    console_level: str | int = logging.INFO,
    file_level: str | int = logging.DEBUG,
    context: dict[str, Any] | None = None,
) -> BefolkningLogger:
    """Wrapper function to configure logging globally for the application."""
    # Silence third-party noise
    for lib in SILENCED_LOGGERS:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return BefolkningLogger(
        logfile=logfile,
        console_level=console_level,
        file_level=file_level,
        context=context,
    )
