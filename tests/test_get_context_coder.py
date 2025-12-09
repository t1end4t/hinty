import os
from collections import Counter
from pathlib import Path
from tree_format import format_tree
import pathspec
from dataclasses import dataclass
from typing import List
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser


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

    return lang_map.get(most_common_ext, f"Unknown ({most_common_ext})")


@dataclass
class FileRelationship:
    file_path: str
    relationship: str
    relevant_excerpt: str


def extract_file_relationships(
    target_file: Path, project_root: Path
) -> List[FileRelationship]:
    """Extract relationships for a target file using tree-sitter.
    
    Analyzes imports, function calls, and test relationships.
    """
    if not target_file.exists() or not target_file.is_file():
        return []

    # Only handle Python files for now
    if target_file.suffix != ".py":
        return []

    try:
        parser = get_parser("python")
        with open(target_file, "rb") as f:
            content = f.read()
        tree = parser.parse(content)
    except Exception:
        return []

    relationships = []
    root_node = tree.root_node

    # Extract imports (imports_from relationship)
    import_query = """
    (import_statement
      name: (dotted_name) @import_name)
    (import_from_statement
      module_name: (dotted_name) @module_name)
    (import_from_statement
      module_name: (relative_import) @relative_import)
    """

    try:
        language = get_language("python")
        query = language.query(import_query)
        captures = query.captures(root_node)

        for node, capture_name in captures:
            import_text = node.text.decode("utf-8")
            # Convert module path to file path
            module_parts = import_text.replace(".", "/")
            possible_paths = [
                project_root / f"{module_parts}.py",
                project_root / module_parts / "__init__.py",
            ]

            for possible_path in possible_paths:
                if possible_path.exists():
                    relationships.append(
                        FileRelationship(
                            file_path=str(
                                possible_path.relative_to(project_root)
                            ),
                            relationship="imports_from",
                            relevant_excerpt=f"import {import_text}",
                        )
                    )
                    break
    except Exception:
        pass

    # Extract function and class definitions for context
    def_query = """
    (function_definition
      name: (identifier) @func_name) @func_def
    (class_definition
      name: (identifier) @class_name) @class_def
    """

    try:
        query = language.query(def_query)
        captures = query.captures(root_node)

        definitions = []
        for node, capture_name in captures:
            if capture_name in ["func_name", "class_name"]:
                definitions.append(node.text.decode("utf-8"))

        # Check if this is a test file
        if "test_" in target_file.name or target_file.parent.name == "tests":
            # Look for tested modules
            for definition in definitions:
                if definition.startswith("test_"):
                    tested_name = definition[5:]  # Remove 'test_' prefix
                    relationships.append(
                        FileRelationship(
                            file_path="",  # Would need more context
                            relationship="tests",
                            relevant_excerpt=f"def {definition}()",
                        )
                    )
    except Exception:
        pass

    return relationships


if __name__ == "__main__":
    print(get_tree_with_library())
    print(get_primary_language())
    
    # Test relationship extraction
    test_file = Path("tests/test_get_context_coder.py")
    if test_file.exists():
        relationships = extract_file_relationships(
            test_file, Path(".")
        )
        print("\nFile Relationships:")
        for rel in relationships:
            print(f"  {rel.relationship}: {rel.file_path}")
            print(f"    {rel.relevant_excerpt}")
