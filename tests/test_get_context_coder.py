import os
from collections import Counter
from pathlib import Path
from tree_format import format_tree
import pathspec


def get_tree_with_library(directory="."):
    """Generate tree using tree-format library, respecting .gitignore"""
    path = Path(directory).resolve()

    # Load .gitignore patterns
    gitignore_spec = None
    gitignore_path = Path(directory) / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            patterns = f.read().splitlines()
            gitignore_spec = pathspec.PathSpec.from_lines(
                "gitwildmatch", patterns
            )

    def is_ignored(p):
        """Check if path should be ignored"""
        if gitignore_spec is None:
            return False

        # Get relative path from root directory
        try:
            rel_path = p.relative_to(path)
            # Check both the path and path with trailing slash for directories
            if gitignore_spec.match_file(str(rel_path)):
                return True
            if p.is_dir() and gitignore_spec.match_file(str(rel_path) + "/"):
                return True
        except ValueError:
            pass
        return False

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
                if is_ignored(child):
                    continue

                subtree = build_tree(child)
                if subtree:
                    children.append(subtree)
        except PermissionError:
            pass

        return (p.name, children)

    tree = build_tree(path)
    return format_tree(
        tree,
        format_node=lambda node: node[0],
        get_children=lambda node: node[1],
    )


def get_primary_language(directory="."):
    """Determine the primary programming language of the project in the given directory."""
    path = Path(directory).resolve()

    # Load .gitignore patterns
    gitignore_spec = None
    gitignore_path = Path(directory) / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            patterns = f.read().splitlines()
            gitignore_spec = pathspec.PathSpec.from_lines(
                "gitwildmatch", patterns
            )

    def is_ignored(p):
        """Check if path should be ignored"""
        if gitignore_spec is None:
            return False

        # Get relative path from root directory
        try:
            rel_path = p.relative_to(path)
            # Check both the path and path with trailing slash for directories
            if gitignore_spec.match_file(str(rel_path)):
                return True
            if p.is_dir() and gitignore_spec.match_file(str(rel_path) + "/"):
                return True
        except ValueError:
            pass
        return False

    ext_counter = Counter()
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file
            if is_ignored(file_path):
                continue
            ext = file_path.suffix.lower()
            if ext:
                ext_counter[ext] += 1

    if not ext_counter:
        return "Unknown"

    most_common_ext = ext_counter.most_common(1)[0][0]

    lang_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c': 'C',
        '.h': 'C',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
    }

    return lang_map.get(most_common_ext, f"Unknown ({most_common_ext})")


if __name__ == "__main__":
    print(get_tree_with_library())
