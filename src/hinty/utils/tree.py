import os
from collections import Counter
from pathlib import Path
from tree_format import format_tree
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


def get_tree_with_library(project_root: Path):
    """Generate tree using tree-format library, respecting .gitignore"""
    logger.info("Generating tree for project root: {}", project_root)
    path = project_root.resolve()
    spec = load_gitignore_spec(project_root)

    def is_ignored_local(p):
        return is_ignored(p, path, spec)

    def build_tree(p):
        """Recursively build tree structure"""
        if p.is_file():
            return (p.name, [])

        children = []
        try:
            for child in sorted(p.iterdir()):
                # Skip hidden files/folders starting with .
                if child.name.startswith("."):
                    continue

                # Skip if ignored by .gitignore
                if is_ignored_local(child):
                    continue

                subtree = build_tree(child)
                if subtree:
                    children.append(subtree)
        except PermissionError:
            logger.warning("Permission denied for directory: {}", p)

        return (p.name, children)

    tree = build_tree(path)
    logger.info("Tree generation completed")
    return format_tree(
        tree,
        format_node=lambda node: node[0],
        get_children=lambda node: node[1],
    )


def get_primary_language(project_root: Path):
    """Determine the primary programming language of the project in the given directory."""
    logger.info(
        "Determining primary language for project root: {}", project_root
    )
    path = project_root.resolve()
    spec = load_gitignore_spec(project_root)

    ext_counter = Counter()
    try:
        for root, dirs, files in os.walk(path):
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
