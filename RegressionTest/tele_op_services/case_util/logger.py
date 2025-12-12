import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str = "tele_op_tests") -> logging.Logger:
    """Return a configured logger instance.

    - Logs to stdout and to a rotating file under ``logs/``.
    - Log level can be controlled via ``TELE_TEST_LOG_LEVEL`` env.
    """

    logger = logging.getLogger(name)
    # Avoid adding duplicate handlers when called multiple times
    if logger.handlers:
        return logger

    log_level = os.getenv("TELE_TEST_LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "tele_op_tests.log")

    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
