from pathlib import Path
from typing import List, Set

from rich.console import Console

from ..cli.theme import BaseTheme


class ProjectContext:
    """Manages project context including chat files and paths."""

    def __init__(self):
        self._files: Set[Path] = set()
        self._pwd_path: Path = Path.cwd()

    def add_file(self, file_path: Path) -> bool:
        """Add a file to context. Returns True if file was newly added."""
        if file_path in self._files:
            return False
        self._files.add(file_path)
        return True

    def remove_file(self, file_path: Path) -> bool:
        """Remove a file from context. Returns True if file was removed."""
        if file_path in self._files:
            self._files.remove(file_path)
            return True
        return False

    def get_files(self) -> List[Path]:
        """Get list of files in context, sorted by name."""
        return sorted(self._files, key=lambda p: p.name)

    def has_files(self) -> bool:
        """Check if any files are in context."""
        return len(self._files) > 0

    def clear_files(self):
        """Clear all files from context."""
        self._files.clear()

    def get_pwd_path(self) -> Path:
        """Get the current working directory path."""
        return self._pwd_path


def print_message(console: Console, theme: BaseTheme, message: str, color: str):
    """Print a styled message to console."""
    console.print(
        f"[bold {getattr(theme, color)}]{message}[/bold {getattr(theme, color)}]"
    )
