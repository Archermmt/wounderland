"""wounderland.utils.log"""

import os
import logging
from typing import Union


class IOLogger(object):
    """IO Logger for MSC"""

    def __init__(self):
        self._printers = {
            "red": (lambda m: print("\033[91m {}\033[00m".format(m))),
            "green": (lambda m: print("\033[92m {}\033[00m".format(m))),
            "yellow": (lambda m: print("\033[93m {}\033[00m".format(m))),
            "purple": (lambda m: print("\033[95m {}\033[00m".format(m))),
            "cyan": (lambda m: print("\033[96m {}\033[00m".format(m))),
            "gray": (lambda m: print("\033[97m {}\033[00m".format(m))),
            "black": (lambda m: print("\033[98m {}\033[00m".format(m))),
        }

    def info(self, msg):
        self._printers["green"]("[MSC_INFO] " + str(msg))

    def debug(self, msg):
        self._printers["green"]("[MSC_DEBUG] " + str(msg))

    def warning(self, msg):
        self._printers["yellow"]("[MSC_WARNING] " + str(msg))

    def error(self, msg):
        self._printers["red"]("[MSC_ERROR] " + str(msg))
        raise Exception(msg)


def create_file_logger(
    path: str, level: Union[str, int] = logging.INFO
) -> logging.Logger:
    """Create file logger

    Parameters
    ----------
    level: logging level
        The logging level.
    path: str
        The file path.

    Returns
    -------
    logger: logging.Logger
        The logger.
    """

    if isinstance(level, str):
        if level.startswith("debug"):
            level = logging.DEBUG
        elif level == "info":
            level = logging.INFO
        elif level == "warn":
            level = logging.WARN
        elif level == "error":
            level = logging.ERROR
        elif level == "critical":
            level = logging.CRITICAL
        else:
            raise Exception("Unexcept verbose {}, should be debug| info| warn")

    log_name = os.path.basename(path)
    logger = logging.getLogger(log_name)
    logger.setLevel(level)
    if any(
        isinstance(h, logging.FileHandler) and h.baseFilename == path
        for h in logger.handlers
    ):
        return logger
    formatter = logging.Formatter(
        "%(asctime)s %(filename)s[ln:%(lineno)d]<%(levelname)s> %(message)s"
    )
    handlers = [
        logging.FileHandler(path, mode="a", encoding=None, delay=False),
        logging.StreamHandler(),
    ]
    for handler in handlers:
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def set_global_logger(
    level: Union[str, int] = logging.INFO, path: str = None
) -> logging.Logger:
    """Create file logger and set to global

    Parameters
    ----------
    level: logging level
        The logging level.
    path: str
        The file path.

    Returns
    -------
    logger: logging.Logger
        The logger.
    """

    logger = create_file_logger(level, path)
    MSCMap.set(MSCKey.GLOBALE_LOGGER, logger)
    return logger


def get_global_logger() -> logging.Logger:
    """Get the global logger

    Returns
    -------
    logger: logging.Logger
        The logger.
    """

    if not MSCMap.get(MSCKey.GLOBALE_LOGGER):
        MSCMap.set(MSCKey.GLOBALE_LOGGER, IOLogger())
    return MSCMap.get(MSCKey.GLOBALE_LOGGER)


def get_log_file(logger: logging.Logger) -> str:
    """Get the log file from logger

    Parameters
    ----------
    logger: logging.Logger
        The logger.

    Returns
    -------
    log_file: str
        The log file.
    """

    for log_h in logger.handlers:
        if isinstance(log_h, logging.FileHandler):
            return log_h.baseFilename
    return None


def remove_loggers():
    """Remove the logger handlers"""

    logger = MSCMap.get(MSCKey.GLOBALE_LOGGER)
    if logger:
        logger.handlers.clear()


def split_line(msg: str, symbol: str = "#", width: int = 100) -> str:
    """Mark message to split line

    Parameters
    ----------
    msg: str
        The message.
    symbol: str
        The split symbol.
    width: int
        The line width.

    Returns
    -------
    split_line: str
        The split line with message.
    """

    return "\n{0}{1}{0}".format(20 * symbol, msg.center(width - 40))
