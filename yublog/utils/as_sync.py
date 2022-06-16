from os import cpu_count
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
from flask import current_app, _app_ctx_stack, copy_current_request_context  # noqa

pool = ThreadPoolExecutor(max(cpu_count(), 10))


def push_app_context(func):
    app = current_app._get_current_object()  # noqa

    @wraps(func)
    def wrapper(*args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)

    return wrapper


def copy_current_app_context(func):
    """retain the app context in the thread pool"""
    app_context = _app_ctx_stack.top

    @wraps(func)
    def wrapper(*args, **kwargs):
        with app_context:
            return func(*args, **kwargs)

    return wrapper


def as_sync(func):
    def log_callback(f):
        logger.info(f"Executor over: {func.__name__}")

        e = f.exception()
        if e is not None:
            logger.error(f"Executor error: {type(e).__name__}: {str(e)}")
        return

    @wraps(func)
    def wrapper(*args, **kwargs):
        pool.submit(func, *args, **kwargs).add_done_callback(log_callback)
        return

    return wrapper


def sync_copy_app_context(func):
    return as_sync(copy_current_app_context(func))


def sync_push_app_context(func):
    return as_sync(push_app_context(func))


def sync_request_context(func):
    """retain the app request context in the thread pool"""
    return sync_copy_app_context(copy_current_request_context(func))
