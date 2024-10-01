import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(session_dir, level=logging.INFO):
    log_dir = os.path.join(session_dir)
    os.makedirs(log_dir, exist_ok=True)

    # Set up the log file path
    log_file = os.path.join(log_dir, "codeaide.log")

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Set up the file handler with rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Set up the console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add the new handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger():
    return logging.getLogger()
