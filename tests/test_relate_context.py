import os
from pathlib import Path
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python

# Set up tree-sitter parser for Python
PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)


def extract_related_files(target_file: Path) -> dict[str, list[Path]]:
    """
    Extract file paths that have relationships with the target Python file.

    Relationships include:
    - imported_by: Files that import from the target.

    Uses tree-sitter to parse Python code for import analysis.
    """
    project_root = find_project_root(target_file)
    all_py_files = list(project_root.rglob("*.py"))
    target_module = get_module_name(target_file, project_root)

    result = {
        "imported_by": [],
    }

    # Tree-sitter query for import statements
    query = Query(
        PY_LANGUAGE,
        """
        (import_statement
          name: (dotted_name) @import_name)
        (import_from_statement
          module_name: (dotted_name) @module_name)
        """,
    )

    query_cursor = QueryCursor(query)

    # Find imported_by: scan other files for imports of target_module
    for file in all_py_files:
        if file == target_file:
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()
        except (FileNotFoundError, UnicodeDecodeError):
            continue

        tree = parser.parse(bytes(code, "utf-8"))
        captures = query_cursor.captures(tree.root_node)

        for capture_name in ("import_name", "module_name"):
            if capture_name in captures:
                for node in captures[capture_name]:
                    import_str = code[node.start_byte : node.end_byte]
                    if import_str == target_module or import_str.startswith(
                        target_module + "."
                    ):
                        if file not in result["imported_by"]:
                            result["imported_by"].append(file)
                        break  # No need to check further in this file

    return result


def find_project_root(path: Path) -> Path:
    """Find the project root by looking for .git directory."""
    current = path.resolve().parent  # FIXED: Use resolve() to get absolute path
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback: go up until we find src/ or project structure
    current = path.resolve().parent
    while current != current.parent:
        if (current / "src").exists() or (current / "tests").exists():
            return current
        current = current.parent
    return path.resolve().parent


def get_module_name(file: Path, root: Path) -> str:
    """Convert file path to module name relative to root."""
    file = file.resolve()
    root = root.resolve()
    rel = file.relative_to(root)
    rel_str = str(rel.with_suffix(""))
    if rel_str.startswith("src/"):
        rel_str = rel_str[4:]  # Strip "src/" to get the module name
    return rel_str.replace(os.sep, ".")


def main():
    """Main function to run the file relationship extraction."""
    # FIXED: Use relative path that works when run from project root or tests/
    import sys

    if len(sys.argv) > 1:
        target_file = Path(sys.argv[1])
    else:
        # Default target - adjust this to your actual file
        target_file = Path("src/hinty/core/project_manager.py")

    # Make path absolute if needed
    if not target_file.is_absolute():
        target_file = Path.cwd() / target_file

    if not target_file.exists():
        print(f"Error: File not found: {target_file}")
        print(f"Current working directory: {Path.cwd()}")
        print(f"Resolved path: {target_file.resolve()}")
        return

    print(f"Analyzing file: {target_file}")
    print(f"Current working directory: {Path.cwd()}")

    result = extract_related_files(target_file)

    print("\n=== Related files for", target_file, "===")
    for key, files in result.items():
        print(f"\n{key} ({len(files)} files):")
        for f in files:
            print(f"  - {f}")

    if not any(result.values()):
        print("\nNo related files found. This could mean:")
        print("  - The file has no imports")
        print("  - The imports point to external packages")
        print("  - The project structure couldn't be detected")


if __name__ == "__main__":
    main()
