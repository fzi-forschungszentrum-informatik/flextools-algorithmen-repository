import logging
import sys

from log_config.config import LOGGING_FILE, LOGGING_LEVEL


def set_logger(name):
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    )

    handler1 = logging.StreamHandler(stream=sys.stdout)
    handler1.setFormatter(formatter)
    handler2 = logging.FileHandler(LOGGING_FILE)
    handler2.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_LEVEL)
    logger.addHandler(handler1)
    logger.addHandler(handler2)
    return logger
