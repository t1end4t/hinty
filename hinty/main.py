import sys

from loguru import logger

# Temporarily set logger to ERROR to prevent debug output during config loading
logger.remove()
logger.add(sys.stdout, level="ERROR")

from hinty.cli import create_cli
from hinty.config import load_config

LOG_LEVEL = load_config()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)


def cli():
    create_cli()


if __name__ == "__main__":
    cli()
