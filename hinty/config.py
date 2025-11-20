import os
import shutil
import tomllib
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from platformdirs import user_config_dir


def get_config_paths() -> tuple[Path, Path]:
    """Return paths for config directory and file."""
    config_dir = Path(user_config_dir("hinty"))
    config_path = config_dir / "config.toml"
    return config_dir, config_path


def get_example_config_path() -> Path:
    """Return path to example config file."""
    return Path(__file__).parent.parent / "config.example.toml"


def ensure_config_exists(
    config_dir: Path, config_path: Path, example_path: Path
) -> None:
    """Create config from example if missing, log error and exit."""
    if config_path.exists():
        return
    config_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(example_path, config_path)
    logger.error(
        f"Config file created at {config_path}. Please edit it with your values."
    )
    raise SystemExit(1)


def load_config_dict(config_path: Path) -> Dict[str, Any]:
    """Load and return config dict from file."""
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def set_env_vars_from_config(config: Dict[str, Any]) -> None:
    """Set environment variables from config sections."""
    api_keys = config.get("api_keys", {})
    for key, value in api_keys.items():
        os.environ[key.upper()] = str(value)

    logging_config = config.get("logging", {})
    for key, value in logging_config.items():
        os.environ[key.upper()] = str(value)


def get_log_level_from_config(config: Dict[str, Any]) -> str:
    """Extract and return log level from config."""
    return config.get("logging", {}).get("LOG_LEVEL", "ERROR").upper()


def load_config() -> str:
    """Load config, set env vars, and return log level."""
    config_dir, config_path = get_config_paths()
    example_path = get_example_config_path()
    ensure_config_exists(config_dir, config_path, example_path)
    config = load_config_dict(config_path)
    set_env_vars_from_config(config)
    return get_log_level_from_config(config)
