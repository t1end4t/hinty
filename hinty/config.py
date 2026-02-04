import os
import tomllib
from pathlib import Path
from typing import Any
from loguru import logger


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return Path.cwd() / "config.toml"


def load_config_dict(config_path: Path) -> dict[str, Any]:
    """Load and parse the TOML configuration file."""
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Error parsing TOML config: {e}")
        raise


def set_env_vars_from_section(config: dict[str, Any], section: str) -> None:
    """Set environment variables from a specific config section, uppercasing keys."""
    vars_dict = config.get(section, {})
    for key, value in vars_dict.items():
        os.environ[key.upper()] = str(value)


def load_toml_config():
    """Load configuration and set environment variables."""
    config_path = get_config_path()
    config = load_config_dict(config_path)

    # Set environment variables for the paths section.
    paths = config.get("paths", {})
    if "idea_dir" in paths:
        os.environ["IDEA_BASE"] = paths["idea_dir"]
    if "experiment_dir" in paths:
        os.environ["EXPERIMENT_BASE"] = paths["experiment_dir"]

    # Set environment variables for the idea section.
    idea_config = config.get("idea", {})
    if "problem" in idea_config:
        os.environ["IDEA_PROBLEM"] = idea_config["problem"]
    if "constraints" in idea_config:
        os.environ["IDEA_CONSTRAINTS"] = idea_config["constraints"]
    if "current_idea" in idea_config:
        os.environ["IDEA_CURRENT_IDEA"] = idea_config["current_idea"]
    if "failed_ideas" in idea_config:
        os.environ["IDEA_FAILED_IDEAS"] = idea_config["failed_ideas"]
    if "experiment_plan" in idea_config:
        os.environ["IDEA_EXPERIMENT_PLAN"] = idea_config["experiment_plan"]
    if "data_science_plan" in idea_config:
        os.environ["IDEA_DATA_SCIENCE_PLAN"] = idea_config["data_science_plan"]

    # Set environment variables for the experiment section.
    experiment_config = config.get("experiment", {})
    if "data_dir" in experiment_config:
        os.environ["EXPERIMENT_DATA"] = experiment_config["data_dir"]
    if "plans" in experiment_config:
        os.environ["EXPERIMENT_PLANS"] = experiment_config["plans"]
    if "vi_path" in experiment_config:
        os.environ["EXPERIMENT_VI_PATH"] = experiment_config["vi_path"]
    if "plots_dir" in experiment_config:
        os.environ["EXPERIMENT_PLOTS"] = experiment_config["plots_dir"]

    set_env_vars_from_section(config, "models")
    set_env_vars_from_section(config, "logging")
    set_env_vars_from_section(config, "system")
    set_env_vars_from_section(config, "aider")
    logger.info("Configuration loaded and environment variables set.")
