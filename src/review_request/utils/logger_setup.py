"""Logging setup utilities."""

import logging
import sys
from typing import Optional


class LoggerSetup:
    """Manages logging configuration."""

    DEFAULT_LOG_FILE = "jira_overdue_reminder.log"
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def setup_logger(
        name: str = __name__,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
    ) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers.clear()

        formatter = logging.Formatter(
            LoggerSetup.DEFAULT_LOG_FORMAT,
            datefmt=LoggerSetup.DEFAULT_DATE_FORMAT,
        )

        console_handler = LoggerSetup._setup_console_handler(formatter, level)
        logger.addHandler(console_handler)

        log_file = log_file or LoggerSetup.DEFAULT_LOG_FILE
        file_handler = LoggerSetup._setup_file_handler(log_file, formatter, level)
        logger.addHandler(file_handler)

        return logger

    @staticmethod
    def _setup_console_handler(
        formatter: logging.Formatter, level: int = logging.INFO
    ) -> logging.StreamHandler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        return console_handler

    @staticmethod
    def _setup_file_handler(
        log_file: str,
        formatter: logging.Formatter,
        level: int = logging.INFO,
    ) -> logging.FileHandler:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        return file_handler
