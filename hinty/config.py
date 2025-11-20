import os
import shutil
import sys
import tomllib
from pathlib import Path

from platformdirs import user_config_dir


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

    # Set api_keys as {KEY}_API_KEY
    api_keys = config.get("api_keys", {})
    for key, value in api_keys.items():
        env_var = f"{key.upper()}"
        os.environ[env_var] = str(value)
        print(f"{env_var} set: {bool(os.environ.get(env_var))}")

    # Set logging as uppercase keys
    logging = config.get("logging", {})
    for key, value in logging.items():
        env_var = key.upper()
        os.environ[env_var] = str(value)
        print(f"{env_var} set: {os.environ.get(env_var)}")

    return os.environ.get("LOG_LEVEL", "ERROR").upper()
