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
    - imports_from: Files that the target imports from.
    - imported_by: Files that import from the target.
    - tests: Test files related to the target.

    Uses tree-sitter to parse Python code for import analysis.
    """
    project_root = find_project_root(target_file)
    all_py_files = list(project_root.rglob("*.py"))
    target_module = get_module_name(target_file, project_root)

    result = {
        "imports_from": [],
        "imported_by": [],
        "tests": [],
    }

    # Parse target file to get imports_from
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: Target file not found: {target_file}")
        return result  # Return empty if file not found

    tree = parser.parse(bytes(code, "utf-8"))

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
    captures = query_cursor.captures(tree.root_node)

    for capture_name in ("import_name", "module_name"):
        if capture_name in captures:
            for node in captures[capture_name]:
                import_str = code[node.start_byte : node.end_byte]
                file_path = import_to_file(
                    import_str, project_root, target_file
                )
                if (
                    file_path
                    and file_path.exists()
                    and file_path not in result["imports_from"]
                ):
                    result["imports_from"].append(file_path)

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

    # For now, uses and used_by are the same as imports_from and imported_by
    result["uses"] = result["imports_from"][:]
    result["used_by"] = result["imported_by"][:]

    # Find tests: files in tests/ directory with similar name
    target_name = target_file.stem.lower()
    for file in all_py_files:
        if "test" in str(file).lower() and target_name in file.stem.lower():
            if file not in result["tests"]:
                result["tests"].append(file)

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


def import_to_file(
    import_str: str, root: Path, current_file: Path
) -> Path | None:
    """Convert import string to file path, handling absolute and relative imports."""
    if import_str.startswith("hinty."):
        # Absolute import
        parts = import_str.split(".")
        # Try direct .py file under src/
        path = root / "src" / Path(*parts).with_suffix(".py")
        if path.exists():
            return path
        # Try package __init__.py under src/
        path = root / "src" / Path(*parts) / "__init__.py"
        if path.exists():
            return path
        return None
    elif import_str.startswith("."):
        # Relative import
        current_module = get_module_name(current_file, root)
        current_parts = current_module.split(".")
        # Count leading dots
        dots = 0
        temp_str = import_str
        while temp_str.startswith("."):
            dots += 1
            temp_str = temp_str[1:]
        # Go up (dots - 1) levels if dots > 0, else stay at current
        if dots > len(current_parts):
            return None
        base_parts = current_parts[:-dots] if dots > 0 else current_parts
        import_parts = temp_str.split(".") if temp_str else []
        full_parts = base_parts + import_parts
        # Try direct .py file under src/
        path = root / "src" / Path(*full_parts).with_suffix(".py")
        if path.exists():
            return path
        # Try package __init__.py under src/
        path = root / "src" / Path(*full_parts) / "__init__.py"
        if path.exists():
            return path
        return None
    else:
        return None  # External import


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
