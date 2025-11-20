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

    # Flatten config into uppercase env vars (like dotenv)
    def set_env_vars(data, prefix=""):
        for key, value in data.items():
            env_key = f"{prefix}{key}".upper().replace(".", "_")
            if isinstance(value, dict):
                set_env_vars(value, f"{env_key}_")
            else:
                os.environ[env_key] = str(value)

    set_env_vars(config)

    return os.environ.get("LOG_LEVEL", "ERROR").upper()
