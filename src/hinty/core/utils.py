import asyncio
from pathlib import Path

import pathspec


async def cache_available_files(
    project_root: Path, available_files_cache: Path
):
    """Load all files in project root recursively and save to cache, respecting .gitignore."""

    def _load():
        files = list(project_root.rglob("*"))
        files = [f for f in files if f.is_file()]

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
