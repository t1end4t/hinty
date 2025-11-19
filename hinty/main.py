import shutil
import sys
import tomllib
from pathlib import Path

from loguru import logger
from platformdirs import user_config_dir

from hinty.cli import create_cli

# setup level of logging
config_dir = Path(user_config_dir("hinty"))
config_path = config_dir / "config.toml"

if not config_path.exists():
    # Auto-create config from example
    config_dir.mkdir(parents=True, exist_ok=True)
    example_config = Path(__file__).parent.parent / "config.example.toml"
    shutil.copy(example_config, config_path)
    print(
        f"Config file created at {config_path}. Please edit it with your API keys."
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
