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

    def set_mode(self, value: Mode) -> None:
        """Set the current mode."""
        self._current_mode = value

    @property
    def pwd_path(self) -> Path:
        """Get the present working directory path."""
        return self._pwd_path

    @property
    def attached_files(self) -> List[Path]:
        """Get the list of attached files."""
        return self._files

    def add_file(self, path: Path) -> None:
        """Add a file to the list."""
        self._files.append(path)
