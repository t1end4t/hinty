from pathlib import Path

from loguru import logger
from tree_format import format_tree

from .helpers import is_ignored, load_gitignore_spec


def get_tree(project_root: Path) -> str:
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
