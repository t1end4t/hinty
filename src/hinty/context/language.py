import os
from collections import Counter
from pathlib import Path

from loguru import logger

from .helpers import is_ignored, load_gitignore_spec


def get_primary_language(project_root: Path) -> str:
    """Determine the primary programming language of the project in the given directory."""
    logger.info(
        "Determining primary language for project root: {}", project_root
    )
    path = project_root.resolve()
    spec = load_gitignore_spec(project_root)

    ext_counter = Counter()
    try:
        for root, _, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                if is_ignored(file_path, path, spec):
                    continue
                ext = file_path.suffix.lower()
                if ext:
                    ext_counter[ext] += 1
    except PermissionError as e:
        logger.warning("Permission error during file scan: {}", e)

    if not ext_counter:
        logger.info("No files found, returning Unknown")
        return "Unknown"

    most_common_ext = ext_counter.most_common(1)[0][0]

    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".c": "C",
        ".h": "C",
        ".rb": "Ruby",
        ".php": "PHP",
        ".go": "Go",
        ".rs": "Rust",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
    }

    lang = lang_map.get(most_common_ext, f"Unknown ({most_common_ext})")
    logger.info("Primary language determined: {}", lang)
    return lang
