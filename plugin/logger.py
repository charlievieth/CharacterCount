import logging
import sys


def load_logger(name="CC") -> logging.Logger:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter_default = logging.Formatter(
        "[%(name)s:%(levelname)s]:[%(filename)s:%(lineno)d]: %(message)s",
    )
    ch.setFormatter(formatter_default)
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    if not log.hasHandlers():
        log.addHandler(ch)
    return log
