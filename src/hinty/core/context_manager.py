import json
from pathlib import Path
from typing import List

from loguru import logger

from .models import Mode


class ContextManager:
    """Unified project context for all modes."""

    def __init__(
        self,
        current_mode: Mode = Mode.SMART,
        pwd_path: Path = Path.cwd(),
    ):
        """Initialize project context."""
        logger.debug("Initializing ContextManager")
        self._current_mode = current_mode
        self._pwd_path = pwd_path
        self._files: List[Path] = []
        self._metadata_path = pwd_path / ".hinty"
        self._attached_files_cache_path = self._metadata_path / "attached_files.json"
        self._metadata_path.mkdir(parents=True, exist_ok=True)
        self._load_attached_files()
        logger.debug("ContextManager initialized")

    @property
    def current_mode(self) -> Mode:
        """Get the current mode."""
        return self._current_mode

    @property
    def pwd_path(self) -> Path:
        """Get the present working directory path."""
        return self._pwd_path

    @property
    def hinty_metadata(self) -> Path:
        """Get the path to the .hinty folder containing intermediate data like history."""
        return self._metadata_path

    @property
    def hinty_history_path(self) -> Path:
        """Get the path to the history file."""
        return self.hinty_metadata / "history"

    @property
    def attached_files_cache_path(self) -> Path:
        """Get the path to the attached files cache."""
        return self._attached_files_cache_path

    def set_mode(self, value: Mode):
        """Set the current mode."""
        self._current_mode = value

    def get_all_files(self) -> List[Path]:
        """Get all attached files."""
        return self._files

    def add_file(self, path: Path):
        """Add a file to the list."""
        logger.info(f"Adding file to context: {path}")
        self._files.append(path)
        self._save_attached_files()

    def remove_file(self, path: Path):
        """Remove a file from the list by path."""
        logger.info(f"Removing file from context: {path}")
        self._files.remove(path)
        self._save_attached_files()

    def _save_attached_files(self):
        """Save the list of attached files to cache."""
        logger.debug("Saving attached files to cache")
        try:
            with open(self._attached_files_cache_path, "w") as f:
                json.dump([str(p) for p in self._files], f)
        except Exception as e:
            logger.error(f"Failed to save attached files cache: {e}")

    def _load_attached_files(self):
        """Load the list of attached files from cache."""
        logger.debug("Loading attached files from cache")
        if self._attached_files_cache_path.exists():
            try:
                with open(self._attached_files_cache_path, "r") as f:
                    self._files = [Path(p) for p in json.load(f)]
            except Exception as e:
                logger.error(f"Failed to load attached files cache: {e}")
                self._files = []
