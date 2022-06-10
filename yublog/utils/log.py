from functools import wraps
import time

from loguru import logger

from yublog.utils.times import time_ms


def log_time(func):
    def wrapped(*args, **kwargs):
        start = time_ms()
        result = func(*args, **kwargs)
        end = time_ms()
        logger.debug(f"{func.__name__} executed in {end - start} ms")
        return result

    return wrapped


def log_param(*, entry=True, exit=True, level="DEBUG"):
    """logging of parameters and return

    Args:
        entry: record parameters
        exit: record return
        level: logger level
    """
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            logger_ = logger.opt(depth=1)
            if entry:
                logger_.log(level, f"{func.__name__}({args, kwargs})")

            result = func(*args, **kwargs)
            if exit:
                logger_.log(level, f"{func.__name__} return {result}")
            return result

        return wrapped

    return wrapper
