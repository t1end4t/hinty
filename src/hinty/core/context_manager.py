from pathlib import Path
from typing import List

from .models import Mode


class ContextManager:
    """Unified project context for all modes."""

    def __init__(
        self,
        current_mode: Mode = Mode.SMART,
        pwd_path: Path = Path.cwd(),
    ):
        """Initialize project context."""
        self._current_mode = current_mode
        self._pwd_path = pwd_path
        self._files: List[Path] = []
        self._metadata_path = pwd_path / ".hinty"

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

    # TODO: get better name
    @property
    def hinty_available_files_path(self) -> Path:
        """Get the path to the available files cache."""
        return self.hinty_metadata / "available_files.json"

    def set_mode(self, value: Mode):
        """Set the current mode."""
        self._current_mode = value

    def get_all_files(self) -> List[Path]:
        """Get all attached files."""
        return self._files

    def add_file(self, path: Path):
        """Add a file to the list."""
        self._files.append(path)

    def remove_file(self, path: Path):
        """Remove a file from the list by path."""
        self._files.remove(path)
