from pathlib import Path
from typing import List

import pathspec
from loguru import logger

from .tree_sitter import get_all_objects


def cache_available_files(
    project_root: Path, available_files_cache: Path, max_files: int = 10000
):
    """Load all files in project root recursively and save to cache, respecting .gitignore."""
    logger.info(f"Starting cache_available_files for {project_root}")

    files = list(project_root.rglob("*"))
    files = [f for f in files if f.is_file()]
    # Exclude .git directory to avoid loading large or unwanted files
    files = [f for f in files if ".git" not in f.parts]

    # Respect .gitignore to avoid loading large or unwanted files
    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", f)
        files = [
            f
            for f in files
            if not spec.match_file(str(f.relative_to(project_root)))
        ]

    if len(files) > max_files:
        logger.warning(
            f"Too many files ({len(files)}) in {project_root}, aborting cache to prevent slowdown. Consider adjusting max_files or project_root."
        )
        raise ValueError(
            f"File count exceeds limit of {max_files}. Aborting to prevent performance issues."
        )

    available_files_cache.parent.mkdir(parents=True, exist_ok=True)
    file_names = [str(f.relative_to(project_root)) for f in files]
    with open(available_files_cache, "w") as f:
        for file_name in file_names:
            f.write(file_name + "\n")

    logger.info(f"Cached {len(files)} files for {project_root}")


def cache_objects(files: List[Path], objects_cache: Path):
    """Cache all objects for given files."""

    all_objects = set()
    for file in files:
        objs = get_all_objects(file)
        all_objects.update(objs)
    objects_cache.parent.mkdir(parents=True, exist_ok=True)
    with open(objects_cache, "w") as f:
        for obj in sorted(all_objects):
            f.write(obj + "\n")
