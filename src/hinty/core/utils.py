
import asyncio
from pathlib import Path

async def cache_available_files(project_root: Path, available_files_cache: Path):
    """Load all files in project root recursively and save to cache."""

    def _load():
        files = list(project_root.rglob("*"))
        files = [f for f in files if f.is_file()]
        available_files_cache.parent.mkdir(parents=True, exist_ok=True)
        file_names = [str(f.relative_to(project_root)) for f in files]
        with open(available_files_cache, "w") as f:
            for file_name in file_names:
                f.write(file_name + "\n")

    await asyncio.to_thread(_load)
