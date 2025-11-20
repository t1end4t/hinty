import os
import shutil
import sys
import tomllib
from pathlib import Path

from platformdirs import user_config_dir


def set_env_vars_upper(vars_dict: dict) -> None:
    """Set environment variables with uppercase keys from a dictionary."""
    os.environ.update(
        {key.upper(): str(value) for key, value in vars_dict.items()}
    )


def load_config():
    """Load configuration from config.toml, set all values as uppercase env vars, and return log level."""
    config_dir = Path(user_config_dir("hinty"))
    config_path = config_dir / "config.toml"

    if not config_path.exists():
        # Auto-create config from example
        config_dir.mkdir(parents=True, exist_ok=True)
        example_config = Path(__file__).parent.parent / "config.example.toml"
        shutil.copy(example_config, config_path)
        print(
            f"Config file created at {config_path}. Please edit it with your values."
        )
        sys.exit(1)

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Set api_keys as uppercase env vars
    api_keys = config.get("api_keys", {})
    set_env_vars_upper(api_keys)

    # Set logging as uppercase keys
    logging = config.get("logging", {})
    set_env_vars_upper(logging)

    return os.environ.get("LOG_LEVEL", "ERROR").upper()
