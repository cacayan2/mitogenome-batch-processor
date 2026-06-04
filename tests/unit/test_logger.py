"""test_logger.py

Unit tests for logging behavior for this project. 
"""
from pathlib import Path
import logging
import shutil

from mitopipeline.logging.logger_factory import make_logger

def test_logger():
    """Unit test for logger behavior."""

    # Removing the log file if it already exists. 
    log_file_path = "logtest_tmp/fastqc.log"
    if Path.exists(Path(log_file_path)):
        shutil.rmtree(Path("logtest_tmp"))
    
    # Creating a logger object. 
    logger1 = make_logger(
        name="fastqc",
        log_file_path=Path(log_file_path),
        console_level=logging.INFO,
        file_level=logging.DEBUG
    )

    logger2 = make_logger(
        name="fastqc",
        log_file_path=Path(log_file_path),
        console_level=logging.INFO,
        file_level=logging.DEBUG
    )

    # Creating logger object and logging messages.
    logger1.debug("This should appear only in the file.")
    logger1.info("Starting FastQC.")
    logger1.warning("This is a warning.")
    logger1.error("This is an error.")

    # Assert statements.
    assert Path.exists(Path(log_file_path)) # Asserting the log file path exists. 
    assert "This should appear only in the file." in Path(log_file_path).read_text() # Asserting that the debug info appeared in the log file.log_file_path.read_text() # Asserting that the debug info appeared in the log file.
    assert "Starting FastQC." in Path(log_file_path).read_text() # Asserting that the info info appeared in the log file.
    assert "This is a warning." in Path(log_file_path).read_text() # Asserting that the warning info appeared in the log file.
    assert "This is an error." in Path(log_file_path).read_text() # Asserting that the error info appeared in the log file.

    assert logger1 is not logging.Handler # Asserting that the logger is not a handler.
    assert logger1 is not logging.Formatter # Asserting that the logger is not a formatter.

    assert logger1 == logger2 # Asserting that the logger objects are the same.
    assert len(logger1.handlers) == 2 # Asserting that the logger has only two handlers.
    assert len(logger2.handlers) == 2 # Asserting that the logger has only two handlers.
    
    assert logger1.handlers[0].level == logging.INFO # Asserting that the console logger has a debug level handler.
    assert logger2.handlers[0].level == logging.INFO # Asserting that the console logger has a debug level handler.
    assert logger1.handlers[1].level == logging.DEBUG # Asserting that the file logger has a debug level handler.
    assert logger2.handlers[1].level == logging.DEBUG # Asserting that the file logger has a debug level handler.

    assert logger1.handlers[0] == logger2.handlers[0] # Asserting that the logger has the same handler.

    shutil.rmtree(Path("logtest_tmp"))


