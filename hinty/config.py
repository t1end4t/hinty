import os
import shutil
import tomllib
from pathlib import Path
from typing import Dict, Any, Tuple
  
from loguru import logger
from platformdirs import user_config_dir
  
  
def get_paths() -> Tuple[Path, Path, Path]:
    """Return paths for config directory, file, and example."""
    config_dir = Path(user_config_dir("hinty"))
    config_path = config_dir / "config.toml"
    example_path = Path(__file__).parent.parent / "config.example.toml"
    return config_dir, config_path, example_path
  
  
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
  
  
def load_and_set_config(config_path: Path) -> Dict[str, Any]:
    """Load config dict and set env vars from it."""
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    api_keys = config.get("api_keys", {})
    for key, value in api_keys.items():
        os.environ[key.upper()] = str(value)
    logging_config = config.get("logging", {})
    for key, value in logging_config.items():
        os.environ[key.upper()] = str(value)
    return config
  
  
def get_log_level_from_config(config: Dict[str, Any]) -> str:
    """Extract and return log level from config."""
    return config.get("logging", {}).get("LOG_LEVEL", "ERROR").upper()
  
  
def load_config() -> str:
    """Load config, set env vars, and return log level."""
    config_dir, config_path, example_path = get_paths()
    ensure_config_exists(config_dir, config_path, example_path)
    config = load_and_set_config(config_path)
    return get_log_level_from_config(config)
