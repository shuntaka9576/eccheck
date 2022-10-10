import logging
from logging import Formatter, StreamHandler
from logging import getLogger as logging_get_logger

LOG_FORMAT = Formatter(
    "%(asctime)s %(name)s [%(levelname)s] %(funcName)s [%(threadName)s] (%(thread)d): %(message)s"
)
LOG_LEVEL = "DEBUG"


def init():
    stdout_handler = StreamHandler()
    stdout_handler.setLevel(LOG_LEVEL)
    stdout_handler.setFormatter(LOG_FORMAT)

    logging.basicConfig(level=LOG_LEVEL, handlers=[stdout_handler])


def getLogger(module_name: str):
    return logging_get_logger(module_name)
