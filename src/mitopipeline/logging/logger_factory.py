"""logger_factory.py

Given a logger name and a log file path, it returns a configgured logger.

"""

# Imports
import logging
from pathlib import Path

def make_logger(name: str, 
                log_file_path: str | Path, 
                console_level: int = logging.INFO,
                file_level: int = logging.DEBUG) -> logging.Logger: 
    """This function returns a configured logger object. It generates 
    a file handler and a console handler and associates them with the logger.

    Args:
        name (str): The name of the logger.
        log_file_path (str | Path): The path to the log file.
        level (str): The level of the logger.
        console_level (int, optional): The level of the console handler. Defaults to logging.INFO.
        file_level (int, optional): The level of the file handler. Defaults to logging.DEBUG.

    Returns:
        logger: A configured logger object.
    """

    # Setting the log_file, creating a parent directory if necessary.
    log_file = Path(log_file_path)
    log_file.parent.mkdir(parents = True, exist_ok = True)

    # Creating the logger object and setting the level. 
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if get_logger() is called multiple times.
    if logger.handlers:
        return logger
    
    # Our logger will write both to the terminal and to a logfile.
    # This specifies what each of those will look like.
    console_formatter = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s | [%(levelname)s] | %(message)s | %(filename)s:%(lineno)d | %(message)s"
    )

    # Creating the console handler and setting level and formatter.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # Creating the file handler and setting level and formatter.
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    # Assigning the handlers to the logger.
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Returning the logger.
    return logger