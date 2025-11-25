import asyncio
import sys

from loguru import logger

from hinty.cli import create_cli
from hinty.config import load_config

LOG_LEVEL = load_config()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)


async def cli():
    await create_cli()


if __name__ == "__main__":
    asyncio.run(cli())
