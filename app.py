import os
import sys

from dotenv import load_dotenv
from loguru import logger

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# logger config
_lvl = os.getenv("LOG_LEVEL", default="TRACE")
_format = "<green>{time:%Y-%m-%d %H:%M:%S}</> | " + \
          "<level>{level}</> | " + \
          "{process.id}-{thread.id} | " + \
          "{file.path}:{line}:<blue>{function}</> " + \
          "- <level>{message}</>"
logger.remove()
logger.add(
    sys.stdout, level=_lvl, format=_format, colorize=True,
)

logger.add(
    f"log/open.log",
    level=_lvl,
    format=_format,
    rotation="00:00",
    retention="10 days",
    backtrace=True,
    diagnose=True,
    enqueue=True
)

from yublog import create_app  # noqa

app = create_app()

if __name__ == '__main__':
    app.run()
