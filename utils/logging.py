"""
Logging configuration for the application.
"""

import logging
import os
import sys
from datetime import datetime


def setup_logging(log_level: int = logging.INFO, log_to_file: bool = True) -> None:
    """
    Set up logging for the application.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_to_file: Whether to log to a file
    """
    # Create logs directory if it doesn't exist
    if log_to_file and not os.path.exists("logs"):
        os.makedirs("logs")

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if requested
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/scraper_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add some basic logging filters
    class SensitiveDataFilter(logging.Filter):
        def filter(self, record):
            # Filter out API keys and other sensitive data
            if hasattr(record, "msg"):
                if isinstance(record.msg, str):
                    record.msg = record.msg.replace(
                        os.environ.get("LLM_API_KEY", ""), "***API_KEY***"
                    )
            return True

    logger.addFilter(SensitiveDataFilter())
