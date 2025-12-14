from pathlib import Path

import pathspec
from loguru import logger


def load_gitignore_spec(project_root: Path) -> pathspec.PathSpec | None:
    """Load .gitignore patterns into a PathSpec if .gitignore exists."""
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return None
    try:
        with open(gitignore_path, "r") as f:
            patterns = f.read().splitlines()
        spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        logger.debug("Loaded .gitignore spec from {}", gitignore_path)
        return spec
    except Exception as e:
        logger.error("Failed to load .gitignore from {}: {}", gitignore_path, e)
        return None


def is_ignored(path: Path, root: Path, spec: pathspec.PathSpec | None) -> bool:
    """Check if a path should be ignored based on the gitignore spec."""
    if spec is None:
        return False
    try:
        rel_path = path.relative_to(root)
        if spec.match_file(str(rel_path)):
            return True
        if path.is_dir() and spec.match_file(str(rel_path) + "/"):
            return True
    except ValueError:
        pass
    return False
