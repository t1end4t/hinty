import os
import sys
from pathlib import Path
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python

# Set up tree-sitter parser for Python
PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)


def module_to_file(module: str, root: Path) -> Path | None:
    """Convert module name to file path relative to root."""
    if not module:
        return None
    rel_path = module.replace(".", os.sep) + ".py"
    candidates = [
        root / "src" / rel_path,
        root / rel_path,
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def extract_related_files(target_file: Path) -> dict[str, list[Path]]:
    """
    Extract file paths that have relationships with the target Python file.
    Handles both absolute and relative imports.
    """
    project_root = find_project_root(target_file)
    all_py_files = list(project_root.rglob("*.py"))

    result = {
        "imported_from": [],
    }

    # UPDATED QUERY:
    # 1. Capture `relative_import` (e.g., ..core)
    # 2. Capture `dotted_name` (e.g., hinty.core)
    query = Query(
        PY_LANGUAGE,
        """
        (import_statement
          name: (dotted_name) @import_name)
          
        (import_from_statement
          module_name: [
            (dotted_name) 
            (relative_import)
          ] @module_name)
        """,
    )

    query_cursor = QueryCursor(query)

    # Now, find files imported by target_file
    code = ""
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            code = f.read()
    except (FileNotFoundError, UnicodeDecodeError):
        pass  # already checked exists

    tree = parser.parse(bytes(code, "utf-8"))
    captures = query_cursor.captures(tree.root_node)

    current_file_module = get_module_name(target_file, project_root)

    for capture_name in ("import_name", "module_name"):
        if capture_name in captures:
            for node in captures[capture_name]:
                import_str = code[node.start_byte : node.end_byte]

                resolved_import = resolve_relative_import(
                    import_str, current_file_module
                )

                # Convert resolved_import to file path
                file_path = module_to_file(resolved_import, project_root)
                if (
                    file_path
                    and file_path.exists()
                    and file_path not in result["imported_from"]
                ):
                    result["imported_from"].append(file_path)

    return result


def resolve_relative_import(import_str: str, current_module: str) -> str:
    """
    Resolves a relative import string (e.g., '..utils') to an absolute
    module path (e.g., 'hinty.core.utils') based on the current file's module.
    """
    if not import_str.startswith("."):
        return import_str  # It is already absolute

    # Count leading dots
    dot_count = 0
    for char in import_str:
        if char == ".":
            dot_count += 1
        else:
            break

    # Strip the dots from the import string to get the suffix
    suffix = import_str[dot_count:]

    # Get the parent package of the current module
    # If current_module is 'hinty.services.api':
    # dot_count=1 (from . import) -> stays in 'hinty.services'
    # dot_count=2 (from .. import) -> goes to 'hinty'

    parts = current_module.split(".")

    # If the file is a module (not __init__), the first dot means "current package".
    # So we essentially remove 'dot_count' number of segments from the end.
    # Note: This logic assumes standard file-to-module mapping.
    if dot_count > len(parts):
        # Scan went too far up (error in code or logic), fallback to original
        return import_str

    # Python relative import logic:
    # 1 dot = current package (remove filename component)
    # 2 dots = parent of current package (remove filename + parent)
    base_parts = parts[:-dot_count]

    base_path = ".".join(base_parts)

    if base_path and suffix:
        return f"{base_path}.{suffix}"
    elif base_path:
        return base_path
    else:
        return suffix


def find_project_root(path: Path) -> Path:
    """Find the project root by looking for .git directory."""
    current = path.resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
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
    try:
        rel = file.relative_to(root)
    except ValueError:
        return ""  # File is outside root

    rel_str = str(rel.with_suffix(""))
    if rel_str.startswith("src" + os.sep):
        rel_str = rel_str[4:]  # Strip "src/"
    elif rel_str == "src":
        rel_str = ""

    return rel_str.replace(os.sep, ".")


def main():
    if len(sys.argv) > 1:
        target_file = Path(sys.argv[1])
    else:
        target_file = Path("src/hinty/core/project_manager.py")

    if not target_file.is_absolute():
        target_file = Path.cwd() / target_file

    if not target_file.exists():
        print(f"Error: File not found: {target_file}")
        return

    print(f"Analyzing file: {target_file}")
    result = extract_related_files(target_file)

    print("\n=== Related files for", target_file.name, "===")
    for key, files in result.items():
        print(f"\n{key} ({len(files)} files):")
        for f in files:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
