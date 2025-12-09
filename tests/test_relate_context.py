import os
from pathlib import Path
from tree_sitter import Language, Parser
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
    - uses: Files used by the target (for now, same as imports_from).
    - used_by: Files that use the target (for now, same as imported_by).
    - tests: Test files related to the target.

    Uses tree-sitter to parse Python code for import analysis.
    """
    project_root = find_project_root(target_file)
    all_py_files = list(project_root.rglob('*.py'))
    target_module = get_module_name(target_file, project_root)

    result = {
        'imports_from': [],
        'imported_by': [],
        'uses': [],
        'used_by': [],
        'tests': []
    }

    # Parse target file to get imports_from
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        return result  # Return empty if file not found

    tree = parser.parse(bytes(code, 'utf-8'))

    # Tree-sitter query for import statements
    query = PY_LANGUAGE.query("""
    (import_statement
      name: (dotted_name) @import_name)
    (import_from_statement
      module_name: (dotted_name) @module_name)
    """)

    captures = query.captures(tree.root_node)
    for node, name in captures:
        if name in ('import_name', 'module_name'):
            import_str = code[node.start_byte:node.end_byte]
            file_path = import_to_file(import_str, project_root)
            if file_path and file_path.exists() and file_path not in result['imports_from']:
                result['imports_from'].append(file_path)

    # Find imported_by: scan other files for imports of target_module
    for file in all_py_files:
        if file == target_file:
            continue
        try:
            with open(file, 'r', encoding='utf-8') as f:
                code = f.read()
        except (FileNotFoundError, UnicodeDecodeError):
            continue
        tree = parser.parse(bytes(code, 'utf-8'))
        captures = query.captures(tree.root_node)
        for node, name in captures:
            if name in ('import_name', 'module_name'):
                import_str = code[node.start_byte:node.end_byte]
                if import_str == target_module or import_str.startswith(target_module + '.'):
                    if file not in result['imported_by']:
                        result['imported_by'].append(file)
                    break  # No need to check further in this file

    # For now, uses and used_by are the same as imports_from and imported_by
    result['uses'] = result['imports_from'][:]
    result['used_by'] = result['imported_by'][:]

    # Find tests: files in tests/ directory with similar name
    target_name = target_file.stem.lower()
    for file in all_py_files:
        if 'test' in str(file).lower() and target_name in file.stem.lower():
            if file not in result['tests']:
                result['tests'].append(file)

    return result


def find_project_root(path: Path) -> Path:
    """Find the project root by looking for .git directory."""
    current = path.parent
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return path.parent  # Fallback to parent if no .git found


def get_module_name(file: Path, root: Path) -> str:
    """Convert file path to module name relative to root."""
    rel = file.relative_to(root)
    return str(rel.with_suffix('')).replace(os.sep, '.')


def import_to_file(import_str: str, root: Path) -> Path | None:
    """Convert import string to file path."""
    parts = import_str.split('.')
    # Try direct .py file
    path = root / Path(*parts).with_suffix('.py')
    if path.exists():
        return path
    # Try package __init__.py
    path = root / Path(*parts) / '__init__.py'
    if path.exists():
        return path
    return None
