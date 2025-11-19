import os
import sys
import tomllib
from pathlib import Path

from loguru import logger

from hinty.cli import create_cli

# setup level of logging
config_path = Path.home() / ".config" / "hinty" / "config.toml"
if not config_path.exists():
    print(
        "Config file not found at ~/.config/hinty/config.toml. Please initialize it by copying config.example.toml to that location."
    )
    sys.exit(1)

with open(config_path, "rb") as f:
    config = tomllib.load(f)

LOG_LEVEL = config.get("logging", {}).get("log_level", "ERROR").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)


def cli():
    create_cli()


if __name__ == "__main__":
    cli()
