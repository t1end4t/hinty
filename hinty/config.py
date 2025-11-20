import os
import shutil
import sys
import tomllib
from pathlib import Path

from platformdirs import user_config_dir


def load_config():
    """Load configuration, set API keys, and return log level."""
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

    # Load API keys into environment variables
    api_keys = config.get("api_keys", {})
    for key, value in api_keys.items():
        env_var_name = f"{key.upper()}_API_KEY"
        os.environ[env_var_name] = value

    return config.get("logging", {}).get("log_level", "ERROR").upper()
