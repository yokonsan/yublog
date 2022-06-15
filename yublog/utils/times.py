import datetime
import time


def time_ms():
    return int(time.time() * 1000)


def nowstr(fmt="%Y-%m-%d %H:%M:%S"):
    t = datetime.datetime.now()
    return t.strftime(fmt)
