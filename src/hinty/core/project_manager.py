from pathlib import Path
from typing import List

from loguru import logger

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

    def ensure_metadata_exists(self):
        """Ensure the metadata directory and necessary files exist."""
        self._metadata_directory.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Ensured metadata directory exists: {self._metadata_directory}"
        )
        # Ensure files exist
        for file_path in [
            self.history_file,
            self.available_files_cache,
            self.objects_cache,
        ]:
            if not file_path.exists():
                file_path.touch()
                logger.info(f"Created metadata file: {file_path}")

        # Ensure images directory exists
        self.images_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured images directory exists: {self.images_directory}")

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

    @property
    def images_directory(self) -> Path:
        """Get the path to the images directory."""
        return self.metadata_directory / "images"

    def get_pdf_cache_path(self, pdf_path: Path) -> Path:
        """Get the cache path for a PDF file."""
        import hashlib

        hash_obj = hashlib.md5(str(pdf_path).encode())
        cache_filename = f"pdf_cache_{hash_obj.hexdigest()}.txt"
        return self.metadata_directory / cache_filename

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
