import logging
from pathlib import Path

import pytest

from ssb_befolkning_fagfunksjoner.logs.logging import config_logging


def test_config_logging_console() -> None:
    config_logging(console_level="DEBUG")

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG

    # Verify a StreamHandler was configured
    assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)


def test_config_logging_file(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    context = {"test_key": "test_val", "another_key": "another_val"}

    config_logging(console_level="INFO", logfile=log_file, context=context)

    logger = logging.getLogger("test_logger")
    logger.info("This is a test log message")

    # Check that the file was created and written to
    assert log_file.exists()

    content = log_file.read_text(encoding="utf-8")
    assert "test_key" in content
    assert "test_val" in content
    assert "another_key" in content
    assert "another_val" in content
    assert "This is a test log message" in content


def test_upload_to_gcs(tmp_path: Path) -> None:
    # 1. Test error when no local logfile configured
    logger_no_file = config_logging()
    with pytest.raises(ValueError, match="Cannot upload to GCS"):
        logger_no_file.upload_to_gcs("gcs://bucket/test.log")

    # 2. Test successful upload
    log_file = tmp_path / "test.log"
    gcs_mock_path = tmp_path / "gcs_mock.log"

    befolkning_logger = config_logging(logfile=log_file)
    logger = logging.getLogger("test_logger")
    logger.info("Message for GCS")

    befolkning_logger.upload_to_gcs(gcs_mock_path)

    assert gcs_mock_path.exists()
    assert "Message for GCS" in gcs_mock_path.read_text(encoding="utf-8")
