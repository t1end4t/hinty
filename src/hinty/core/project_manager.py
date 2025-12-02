from pathlib import Path
from typing import List

from .models import Mode


class ProjectManager:
    """Manages project context, including mode, attached files, and metadata."""

    def __init__(
        self,
        mode: Mode = Mode.CHATGPT,
        project_root: Path = Path.cwd(),
    ):
        """Initialize project context."""
        self._mode = mode
        self._project_root = project_root
        self._attached_files: List[Path] = []
        self._metadata_directory = project_root / ".hinty"

    @property
    def mode(self) -> Mode:
        """Get the current mode."""
        return self._mode

    @property
    def project_root(self) -> Path:
        """Get the project root directory path."""
        return self._project_root

    @property
    def metadata_directory(self) -> Path:
        """Get the path to the .hinty folder containing intermediate data like history."""
        return self._metadata_directory

    @property
    def history_file(self) -> Path:
        """Get the path to the history file."""
        return self.metadata_directory / "history.txt"

    @property
    def available_files_cache(self) -> Path:
        """Get the path to the available files cache."""
        return self.metadata_directory / "project_files.txt"

    @property
    def objects_cache(self) -> Path:
        """Get the path to the objects cache."""
        return self.metadata_directory / "objects.txt"

    def change_mode(self, new_mode: Mode):
        """Change the current mode."""
        self._mode = new_mode

    def get_attached_files(self) -> List[Path]:
        """Get all attached files."""
        return self._attached_files

    def attach_file(self, file_path: Path):
        """Attach a file to the list."""
        if file_path not in self._attached_files:
            self._attached_files.append(file_path)

    def detach_file(
        self, file_path: Path | None = None, remove_all: bool = False
    ):
        """Detach a file from the list by path, or remove all files if specified."""
        if remove_all:
            self._attached_files.clear()
        elif file_path is not None:
            self._attached_files.remove(file_path)
