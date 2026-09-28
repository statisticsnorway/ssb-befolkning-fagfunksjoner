import logging
from pathlib import Path

from ssb_befolkning_fagfunksjoner.logs.logging import config_logging


def test_config_logging_console() -> None:
    config_logging(log_level="DEBUG")
    
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    
    # Verify a StreamHandler was configured
    assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)


def test_config_logging_file(tmp_path: Path) -> None:
    log_file = tmp_path / "test.log"
    context = {"test_key": "test_val", "another_key": "another_val"}
    
    config_logging(log_level="INFO", log_file=log_file, context=context)
    
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
