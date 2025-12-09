import os
import sys
from pathlib import Path
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python

# Set up tree-sitter parser for Python
PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)


def extract_related_files(target_file: Path) -> dict[str, list[Path]]:
    """
    Extract file paths that have relationships with the target Python file.
    Handles both absolute and relative imports.
    """
    project_root = find_project_root(target_file)
    all_py_files = list(project_root.rglob("*.py"))

    # The absolute module name of our target (e.g., "hinty.core.project_manager")
    target_module = get_module_name(target_file, project_root)

    result = {
        "imported_by": [],
    }

    # Query to capture imports
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

    for file in all_py_files:
        if file.resolve() == target_file.resolve():
            continue

        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()
        except (FileNotFoundError, UnicodeDecodeError):
            continue

        # Get the module name of the CURRENT file being scanned
        current_file_module = get_module_name(file, project_root)

        tree = parser.parse(bytes(code, "utf-8"))
        captures = query_cursor.captures(tree.root_node)

        found_match = False

        for capture_name in ("import_name", "module_name"):
            if capture_name in captures:
                for node in captures[capture_name]:
                    import_str = code[node.start_byte : node.end_byte]

                    # Resolve the import string to an absolute module path
                    resolved_import = resolve_relative_import(
                        import_str, current_file_module
                    )

                    # Check for exact match or submodule match
                    if (
                        resolved_import == target_module
                        or resolved_import.startswith(target_module + ".")
                    ):
                        if file not in result["imported_by"]:
                            result["imported_by"].append(file)
                        found_match = True
                        break
            if found_match:
                break

    return result


def extract_key_relationships(target_file: Path) -> dict[str, list[str]]:
    """
    Extract key classes and functions from the target file and their usages across the project.
    Returns a dict where keys are class or function names and values are lists of "file:function" strings.

    This improved version:
    1. Only checks files that actually import from the target file
    2. Uses AST to find actual identifier usage, not string matching
    3. Tracks usage in function/method bodies properly
    """
    project_root = find_project_root(target_file)

    # First, get all files that import from our target
    related_files = extract_related_files(target_file)
    importing_files = related_files["imported_by"]

    # Query to find class definitions in the target file
    class_query = Query(
        PY_LANGUAGE,
        """
        (class_definition
          name: (identifier) @class_name)
        """,
    )

    # Query to find function definitions in the target file
    function_query = Query(
        PY_LANGUAGE,
        """
        (function_definition
          name: (identifier) @function_name)
        """,
    )

    # Query to find ALL identifiers used in the code
    # This captures actual variable/class references
    usage_query = Query(
        PY_LANGUAGE,
        """
        (function_definition
          name: (identifier) @func_name
          body: (block) @func_body)
        
        (identifier) @identifier
        """,
    )

    # Parse target file to get classes and functions
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            target_code = f.read()
    except (FileNotFoundError, UnicodeDecodeError):
        return {}

    target_tree = parser.parse(bytes(target_code, "utf-8"))
    class_cursor = QueryCursor(class_query)
    class_captures = class_cursor.captures(target_tree.root_node)

    classes = []
    if "class_name" in class_captures:
        for node in class_captures["class_name"]:
            class_name = target_code[node.start_byte : node.end_byte]
            classes.append(class_name)

    function_cursor = QueryCursor(function_query)
    function_captures = function_cursor.captures(target_tree.root_node)

    functions = []
    if "function_name" in function_captures:
        for node in function_captures["function_name"]:
            function_name = target_code[node.start_byte : node.end_byte]
            functions.append(function_name)

    # Now, find usages in files that import from our target
    usages = {item: [] for item in classes + functions}

    for file in importing_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()
        except (FileNotFoundError, UnicodeDecodeError):
            continue

        tree = parser.parse(bytes(code, "utf-8"))

        # Find all function definitions
        func_query = Query(
            PY_LANGUAGE,
            """
            (function_definition
              name: (identifier) @func_name
              body: (block) @func_body)
            """,
        )

        func_cursor = QueryCursor(func_query)
        func_captures = func_cursor.captures(tree.root_node)

        if "func_name" not in func_captures or "func_body" not in func_captures:
            continue

        # For each function, check if it uses our classes
        for i, func_node in enumerate(func_captures["func_name"]):
            func_name = code[func_node.start_byte : func_node.end_byte]
            body_node = func_captures["func_body"][i]

            # Now search for identifiers within this function body
            identifier_query = Query(PY_LANGUAGE, "(identifier) @id")

            id_cursor = QueryCursor(identifier_query)
            id_captures = id_cursor.captures(body_node)

            if "id" in id_captures:
                used_items = set()
                for id_node in id_captures["id"]:
                    identifier = code[id_node.start_byte : id_node.end_byte]
                    if identifier in classes or identifier in functions:
                        used_items.add(identifier)

                # Add usage for each item found
                for item in used_items:
                    usage_str = f"{file}:{func_name}"
                    if usage_str not in usages[item]:
                        usages[item].append(usage_str)

    return usages


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
    parts = current_module.split(".")

    if dot_count > len(parts):
        return import_str

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
        target_file = Path("src/hinty/core/llm.py")

    if not target_file.is_absolute():
        target_file = Path.cwd() / target_file

    if not target_file.exists():
        print(f"Error: File not found: {target_file}")
        return

    print(f"Analyzing file: {target_file}")
    result = extract_related_files(target_file)
    usages = extract_key_relationships(target_file)

    print(f"\n=== Related files for {target_file.name} ===")
    for key, files in result.items():
        print(f"\n{key} ({len(files)} files):")
        for f in files:
            print(f"  - {f}")

    print("\n=== Key class and function usages ===")
    for item, funcs in usages.items():
        if funcs:
            print(f"\n{item}:")
            for func in funcs:
                print(f"  -> {func}")
        else:
            print(f"\n{item}: (no usages found in functions)")


if __name__ == "__main__":
    main()
