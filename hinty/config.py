import os
import sys
import tomllib
from pathlib import Path

from platformdirs import user_config_dir


def load_config():
    """Load configuration, set API keys, and return log level."""
    config_dir = Path(user_config_dir("hinty"))
    config_path = config_dir / "config.toml"

    if not config_path.exists():
        # Prompt for API keys and create config
        config_dir.mkdir(parents=True, exist_ok=True)
        groq_key = input("Enter GROQ API key: ")
        gemini_key = input("Enter GEMINI API key: ")
        openrouter_key = input("Enter OPENROUTER API key: ")
        config_content = f"""[api_keys]
groq = "{groq_key}"
gemini = "{gemini_key}"
openrouter = "{openrouter_key}"
    
[logging]
log_level = "DEBUG"
"""
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"Config file created at {config_path}.")

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Load API keys into environment variables
    api_keys = config.get("api_keys", {})
    for key, value in api_keys.items():
        env_var_name = f"{key.upper()}_API_KEY"
        os.environ[env_var_name] = value

    return config.get("logging", {}).get("log_level", "ERROR").upper()
