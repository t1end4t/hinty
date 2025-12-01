import asyncio
from pathlib import Path
from typing import List

import aiofiles
import pathspec
from loguru import logger

from .tree_sitter import get_all_objects


def discover_project_files(project_root: Path) -> List[Path]:
    """Discover all files in project, excluding .git directory."""
    all_files = project_root.rglob("*")
    return [f for f in all_files if f.is_file() and ".git" not in f.parts]


async def load_gitignore_spec(
    project_root: Path,
) -> pathspec.PathSpec | None:
    """Load and parse .gitignore file if it exists."""
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return None

    async with aiofiles.open(gitignore_path, "r") as f:
        content = await f.read()

    return pathspec.PathSpec.from_lines("gitwildmatch", content.splitlines())


def filter_files_by_gitignore(
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


def validate_file_count(file_count: int, max_files: int) -> None:
    """Validate that file count doesn't exceed maximum."""
    if file_count > max_files:
        logger.warning(
            f"File count ({file_count}) exceeds limit of {max_files}"
        )
        raise ValueError(
            f"File count exceeds limit of {max_files}. "
            "Aborting to prevent performance issues."
        )


async def write_file_cache(
    files: List[Path], project_root: Path, cache_path: Path
) -> None:
    """Write relative file paths to cache file."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    relative_paths = [str(f.relative_to(project_root)) for f in files]

    async with aiofiles.open(cache_path, "w") as f:
        await f.write("\n".join(relative_paths) + "\n")


async def cache_available_files(
    project_root: Path, available_files_cache: Path, max_files: int = 10000
) -> None:
    """Cache all project files, respecting .gitignore."""
    logger.info(f"Caching files for {project_root}")

    files = discover_project_files(project_root)
    gitignore_spec = await load_gitignore_spec(project_root)
    filtered_files = filter_files_by_gitignore(
        files, project_root, gitignore_spec
    )

    validate_file_count(len(filtered_files), max_files)
    await write_file_cache(filtered_files, project_root, available_files_cache)

    logger.info(f"Cached {len(filtered_files)} files")


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
