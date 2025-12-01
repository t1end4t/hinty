import asyncio
import json
from pathlib import Path
from typing import List

import pathspec

from .tree_sitter import get_top_level_objects


async def cache_available_files(
    project_root: Path, available_files_cache: Path
):
    """Load all files in project root recursively and save to cache, respecting .gitignore."""

    def _load():
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

        available_files_cache.parent.mkdir(parents=True, exist_ok=True)
        file_names = [str(f.relative_to(project_root)) for f in files]
        with open(available_files_cache, "w") as f:
            for file_name in file_names:
                f.write(file_name + "\n")

    await asyncio.to_thread(_load)


async def cache_objects(files: List[Path], objects_cache: Path):
    """Cache top-level objects for given files."""

    def _load():
        objects = {}
        for file in files:
            objs = get_top_level_objects(file)
            objects[str(file)] = objs
        objects_cache.parent.mkdir(parents=True, exist_ok=True)
        with open(objects_cache, "w") as f:
            json.dump(objects, f)

    await asyncio.to_thread(_load)
