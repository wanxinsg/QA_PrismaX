import logging
import os
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)

    logger = logging.getLogger(name if name else __name__)
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler()
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


