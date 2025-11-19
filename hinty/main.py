import os
import sys

from dotenv import load_dotenv
from loguru import logger

from hinty.cli import create_cli

load_dotenv()

# setup level of logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)


def cli():
    create_cli()


if __name__ == "__main__":
    cli()
