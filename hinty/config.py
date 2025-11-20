import os
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Dict

from loguru import logger
from platformdirs import user_config_dir


def get_config_path() -> Path:
    """Get the path to the config file."""
    config_dir = Path(user_config_dir("hinty"))
    return config_dir / "config.toml"


def get_example_config_path() -> Path:
    """Get the path to the example config file."""
    return Path(__file__).parent.parent / "config.example.toml"


def ensure_config_directory_exists(config_path: Path) -> None:
    """Ensure the config directory exists."""
    config_path.parent.mkdir(parents=True, exist_ok=True)


def copy_example_to_config(example_path: Path, config_path: Path) -> None:
    """Copy example config to config path."""
    shutil.copy(example_path, config_path)


def notify_user_and_exit(config_path: Path) -> None:
    """Notify user about config creation and exit."""
    print(
        f"Config file created at {config_path}. Please edit it with your values."
    )
    sys.exit(1)


def create_config_from_example(config_path: Path) -> None:
    """Create config file from example template."""
    logger.info(f"Creating config file at {config_path}")
    ensure_config_directory_exists(config_path)
    example_path = get_example_config_path()
    copy_example_to_config(example_path, config_path)
    notify_user_and_exit(config_path)


def read_config_file(config_path: Path) -> Dict:
    """Read and parse the TOML config file."""
    logger.debug(f"Reading config from {config_path}")
    try:
        with open(config_path, "rb") as file:
            return tomllib.load(file)
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {config_path}")
        raise e
    except tomllib.TOMLKitError as e:
        logger.error(f"Error parsing TOML config: {e}")
        raise e


def get_env_vars_from_section(config: Dict, section: str) -> Dict[str, str]:
    """Extract environment variables from a config section."""
    vars_dict = config.get(section, {})
    return {key.upper(): str(value) for key, value in vars_dict.items()}


def set_environment_variables(config: Dict) -> None:
    """Set environment variables from config sections."""
    sections = ["api_keys", "logging"]
    for section in sections:
        env_vars = get_env_vars_from_section(config, section)
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
