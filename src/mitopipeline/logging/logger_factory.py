"""
logger_factory.py

Creates a console and file logger for the mitogenome pipeline.
"""

# Imports
from __future__ import annotations
import logging
from pathlib import Path

def make_logger(
    name: str,
    log_file_path: str | Path, 
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    This returns a logger with a concise console and detailed file output.

    A logger is keyed by both logical name and resolved logfile, which prevents two samples
    from using the same tool name from accidentally sharing the same file handler
    when they execute the same Python process.

    All logging will also output to a dedicated global logfile. Everytime this type of logger 
    is required, output will ALWAYS go to the global logger. 

    Args:
        name (str): The name of the logger.
        log_file_path (str | Path): The path to the log file to be written to (this is for a particular step of the process).
        console_level (int): The level of logging information to send to the console (INFO).
        file_level (int): The level of logging information to send to the log file (DEBUG).
    
    Returns:
        logging.Logger: A configured logger.
    """
    # Resolving the path to the logfile. 
    log_file = Path(log_file_path).resolve()
    log_file.parent.mkdir(parents = True, exist_ok = True)

    # Setting the name of the log and its corresponding logfile. 
    logger_name = f"{name}:{log_file}"

    # Creating a new logger object with the corresponding name. 
    logger = logging.getLogger(logger_name)
    
    # Setting the level of the logger to debug
    logger.setLevel(logging.Debug)
    logger.propogate = False

    if logger.handlers:
        return logger

    console_formatter = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s" | [%()]
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

