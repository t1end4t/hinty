import os
import sys
from pathlib import Path
from tree_sitter import Language, Node, Parser, Query, QueryCursor
import tree_sitter_python

# Set up tree-sitter parser for Python
PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)


def _get_definitions(file_path: Path) -> dict[str, str]:
    """Extract class and function definitions from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except (FileNotFoundError, UnicodeDecodeError):
        return {}

    tree = parser.parse(bytes(code, "utf-8"))
    defs = {}

    def_query = Query(
        PY_LANGUAGE,
        """
        (class_definition name: (identifier) @class_name)
        (function_definition name: (identifier) @func_name)
        """,
    )
    def_cursor = QueryCursor(def_query)
    captures = def_cursor.captures(tree.root_node)

    for node in captures.get("class_name", []):
        name = code[node.start_byte : node.end_byte]
        defs[name] = "class"

    for node in captures.get("func_name", []):
        name = code[node.start_byte : node.end_byte]
        defs[name] = "function"

    return defs


def _find_enclosing_class_or_function(node: Node) -> Node | None:
    """Find the nearest enclosing class or function definition."""
    current = node.parent
    while current:
        if current.type in ("class_definition", "function_definition"):
            return current
        current = current.parent
    return None


def _get_name_from_node(node: Node, code: str) -> str:
    """Extract the name from a class or function definition node."""
    for child in node.children:
        if child.type == "identifier":
            return code[child.start_byte : child.end_byte]
    return "unknown"


def _extract_import_from(node: Node, code: str) -> tuple[str, list[str]]:
    """Extract module_name and list of names from an import_from_statement node."""
    sub_query = Query(
        PY_LANGUAGE,
        """
        (import_from_statement
          module_name: [
            (dotted_name)
            (relative_import)
          ] @module_name
          name: (dotted_name) @name)
        """,
    )
    sub_cursor = QueryCursor(sub_query)
    sub_captures = sub_cursor.captures(node)
    module_names = [
        code[n.start_byte : n.end_byte]
        for n in sub_captures.get("module_name", [])
    ]
    names = [
        code[n.start_byte : n.end_byte] for n in sub_captures.get("name", [])
    ]
    module_name = module_names[0] if module_names else ""
    return module_name, names


def _module_to_file(module: str, root: Path) -> Path | None:
    """Convert module name to file path relative to root."""
    if not module:
        return None
    rel_path = module.replace(".", os.sep) + ".py"
    file_path = root / rel_path
    return file_path if file_path.exists() else None


def _get_imported_files_and_names(
    project_root: Path, target_file: Path, code: str, tree
) -> tuple[list[Path], dict[str, Path]]:
    """Extract imported files and map imported names to their file paths."""
    query = Query(
        PY_LANGUAGE,
        """
        (import_from_statement) @import_from
        """,
    )
    query_cursor = QueryCursor(query)
    captures = query_cursor.captures(tree.root_node)

    current_file_module = _get_module_name(target_file, project_root)
    imported_from = []
    imported_names = {}  # name -> file_path

    for node in captures.get("import_from", []):
        module_str, names = _extract_import_from(node, code)
        resolved_import = _resolve_relative_import(
            module_str, current_file_module
        )
        file_path = _module_to_file(resolved_import, project_root)
        if file_path and file_path.exists():
            if file_path not in imported_from:
                imported_from.append(file_path)
            for name in names:
                imported_names[name] = file_path

    return imported_from, imported_names


def _collect_definitions(
    imported_files: list[Path],
) -> dict[Path, dict[str, str]]:
    """Collect definitions (classes/functions) from imported files."""
    definitions = {}
    for file_path in imported_files:
        definitions[file_path] = _get_definitions(file_path)
    return definitions


def _find_usages(
    code: str,
    tree,
    imported_names: dict[str, Path],
    definitions: dict[Path, dict[str, str]],
) -> list[str]:
    """Find usages of imported names and build usage strings."""
    usage_query = Query(PY_LANGUAGE, "(identifier) @usage")
    usage_cursor = QueryCursor(usage_query)
    usage_captures = usage_cursor.captures(tree.root_node)
    usage_set = set()

    if "usage" in usage_captures:
        for node in usage_captures["usage"]:
            name = code[node.start_byte : node.end_byte]
            if name in imported_names:
                file_path = imported_names[name]
                def_dict = definitions[file_path]
                imported_type = def_dict.get(name, "unknown")
                enclosing = _find_enclosing_class_or_function(node)
                if enclosing:
                    enclosing_name = _get_name_from_node(enclosing, code)
                    enclosing_type = (
                        "class"
                        if enclosing.type == "class_definition"
                        else "function"
                    )
                    class_name = None
                    if enclosing.type == "function_definition":
                        parent = enclosing.parent
                        while parent:
                            if parent.type == "class_definition":
                                class_name = _get_name_from_node(parent, code)
                                break
                            parent = parent.parent
                    enclosing_str = (
                        f"{class_name}.{enclosing_name}"
                        if class_name
                        else f"{enclosing_type} {enclosing_name}"
                    )
                    usage_str = f"{imported_type} {name} -> {enclosing_str}"
                    usage_set.add(usage_str)

    return list(usage_set)


def _extract_related_files(
    project_root: Path, target_file: Path
) -> dict[str, list[Path] | list[str]]:
    """
    Extract file paths that have relationships with the target Python file.
    Handles both absolute and relative imports.
    Also extracts usages of imported classes/functions within the target file.
    """
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            code = f.read()
    except (FileNotFoundError, UnicodeDecodeError):
        return {"imported_from": [], "usages": []}

    tree = parser.parse(bytes(code, "utf-8"))
    imported_from, imported_names = _get_imported_files_and_names(
        project_root, target_file, code, tree
    )
    definitions = _collect_definitions(imported_from)
    usages = _find_usages(code, tree, imported_names, definitions)

    return {"imported_from": imported_from, "usages": usages}


def _resolve_relative_import(import_str: str, current_module: str) -> str:
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


def _get_module_name(file: Path, root: Path) -> str:
    """Convert file path to module name relative to root."""
    file = file.resolve()
    root = root.resolve()
    try:
        rel = file.relative_to(root)
    except ValueError:
        return ""  # File is outside root

    rel_str = str(rel.with_suffix(""))
    return rel_str.replace(os.sep, ".")


def analyze_related_files(
    project_root: Path, target_file: Path
) -> dict[str, list[Path] | list[str]]:
    """Analyze related files for the given target file within the project root."""
    if not target_file.is_absolute():
        target_file = project_root / target_file

    if not target_file.exists():
        raise FileNotFoundError(f"File not found: {target_file}")

    return _extract_related_files(project_root, target_file)


def _main():
    if len(sys.argv) > 2:
        project_root = Path(sys.argv[1])
        target_file = Path(sys.argv[2])
    else:
        project_root = Path.cwd()
        target_file = Path("src/hinty/cli/commands.py")

    result = analyze_related_files(project_root, target_file)

    print(f"Analyzing file: {target_file}")
    print("\n=== Related files for", target_file.name, "===")
    for key, files in result.items():
        if key == "usages":
            print(f"\n{key} ({len(files)} usages):")
            for usage in files:
                print(f"  - {usage}")
        else:
            print(f"\n{key} ({len(files)} files):")
            for f in files:
                print(f"  - {f}")


if __name__ == "__main__":
    _main()
