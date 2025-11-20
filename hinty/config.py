import os
import shutil
import sys
import tomllib
from pathlib import Path

from loguru import logger
from platformdirs import user_config_dir


def get_config_path() -> Path:
    """Get the path to the config file."""
    config_dir = Path(user_config_dir("hinty"))
    return config_dir / "config.toml"


def get_example_config_path() -> Path:
    """Get the path to the example config file."""
    return Path(__file__).parent.parent / "config.example.toml"


def create_config_from_example(config_path: Path) -> None:
    """Create config file from example template."""
    logger.info(f"Creating config file at {config_path}")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    example_config = get_example_config_path()
    shutil.copy(example_config, config_path)
    print(
        f"Config file created at {config_path}. Please edit it with your values."
    )
    sys.exit(1)


def read_config_file(config_path: Path) -> dict:
    """Read and parse the TOML config file."""
    logger.debug(f"Reading config from {config_path}")
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def set_environment_variables(config: dict) -> None:
    """Set environment variables from config sections."""
    sections = ["api_keys", "logging"]
    for section in sections:
        vars_dict = config.get(section, {})
        env_vars = {key.upper(): str(value) for key, value in vars_dict.items()}
        os.environ.update(env_vars)
        logger.debug(f"Set {len(env_vars)} env vars from {section}")


def get_log_level() -> str:
    """Extract log level from environment."""
    return os.environ.get("LOG_LEVEL", "ERROR").upper()


def load_config() -> str:
    """Load configuration and return log level."""
    logger.info("Loading configuration")
    config_path = get_config_path()

    if not config_path.exists():
        create_config_from_example(config_path)

    config = read_config_file(config_path)
    set_environment_variables(config)
    log_level = get_log_level()
    logger.info(f"Configuration loaded with log level: {log_level}")
    return log_level
