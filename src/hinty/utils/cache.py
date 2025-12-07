from pathlib import Path
from typing import List

import pathspec
from loguru import logger

from .tree_sitter import get_all_objects


def _discover_project_files(project_root: Path) -> List[Path]:
    """Discover all files in project, excluding .git directory."""
    all_files = project_root.rglob("*")
    return [f for f in all_files if f.is_file() and ".git" not in f.parts]


def _load_gitignore_spec(
    project_root: Path,
) -> pathspec.PathSpec | None:
    """Load and parse .gitignore file if it exists."""
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return None

    with open(gitignore_path, "r") as f:
        content = f.read()

    return pathspec.PathSpec.from_lines("gitwildmatch", content.splitlines())


def _filter_files_by_gitignore(
    files: List[Path], project_root: Path, spec: pathspec.PathSpec | None
) -> List[Path]:
    """Filter files using gitignore patterns."""
    if spec is None:
        return files

    return [
        f
        for f in files
        if not spec.match_file(str(f.relative_to(project_root)))
    ]


def _validate_file_count(file_count: int, max_files: int) -> bool:
    """Validate that file count doesn't exceed maximum."""
    if file_count > max_files:
        logger.warning(
            f"File count ({file_count}) exceeds limit of {max_files}. "
            "Aborting to prevent performance issues."
        )
        return False
    return True


def _write_file_cache(
    files: List[Path], project_root: Path, cache_path: Path
) -> None:
    """Write relative file paths to cache file."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    relative_paths = [str(f.relative_to(project_root)) for f in files]

    with open(cache_path, "w") as f:
        f.write("\n".join(relative_paths) + "\n")


def cache_available_files(
    project_root: Path, available_files_cache: Path, max_files: int = 10000
) -> None:
    """Cache all project files, respecting .gitignore."""
    files = _discover_project_files(project_root)
    gitignore_spec = _load_gitignore_spec(project_root)
    filtered_files = _filter_files_by_gitignore(
        files, project_root, gitignore_spec
    )

    if not _validate_file_count(len(filtered_files), max_files):
        return

    _write_file_cache(filtered_files, project_root, available_files_cache)

    logger.info(f"Cached {len(filtered_files)} files")


def _collect_objects_from_files(files: List[Path]) -> set[str]:
    """Collect all unique objects from given files."""
    all_objects = set()
    for file in files:
        objects = get_all_objects(file)
        all_objects.update(objects)
    return all_objects


def _write_objects_cache(objects: set[str], cache_path: Path) -> None:
    """Write sorted objects to cache file."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_objects = sorted(objects)

    with open(cache_path, "w") as f:
        f.write("\n".join(sorted_objects) + "\n")


def cache_objects(files: List[Path], objects_cache: Path) -> None:
    """Cache all objects for given files."""
    all_objects = _collect_objects_from_files(files)
    _write_objects_cache(all_objects, objects_cache)

    logger.info(f"Cached {len(all_objects)} unique objects")
