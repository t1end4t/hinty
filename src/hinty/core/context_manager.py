from pathlib import Path
from typing import List

from .models import Mode


class ContextManager:
    """Unified project context for all modes."""

    def __init__(
        self,
        current_mode: Mode = Mode.ROUTER,
        pwd_path: Path = Path.cwd(),
    ):
        """Initialize project context."""
        self._current_mode = current_mode
        self._pwd_path = pwd_path
        self._files: List[Path] = []

    @property
    def current_mode(self) -> Mode:
        """Get the current mode."""
        return self._current_mode

    @property
    def pwd_path(self) -> Path:
        """Get the present working directory path."""
        return self._pwd_path

    def set_mode(self, value: Mode) -> None:
        """Set the current mode."""
        self._current_mode = value

    def get_all_files(self) -> List[Path]:
        """Get a specific attached file by index."""
        return self._files

    def add_file(self, path: Path) -> None:
        """Add a file to the list."""
        self._files.append(path)

    def remove_file(self, path: Path) -> None:
        """Remove a file from the list by path."""
        self._files.remove(path)
