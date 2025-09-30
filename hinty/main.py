import os
import sys

import typer
from dotenv import load_dotenv
from loguru import logger

from hinty.cli import start_chat

load_dotenv()

# setup level of logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)


app = typer.Typer()


@app.command()
def cli():
    """Start a chat session with the LLM."""
    start_chat()


if __name__ == "__main__":
    cli()
