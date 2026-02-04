import sys

from hinty.cli import create_cli
from hinty.config import load_config
from loguru import logger

LOG_LEVEL = load_config()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)


def cli():
    create_cli()


if __name__ == "__main__":
    cli()
